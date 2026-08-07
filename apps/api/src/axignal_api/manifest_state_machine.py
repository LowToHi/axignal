"""Manifest state machines and versioning — WP2-T03.

Implements the canonical state transitions and semantic versioning rules
for LibraryManifest and SourceManifest per AX-GE2E-FINISH-004 v2.1.0:

- library states: NOT_STARTED -> ENGINEERING_IN_PROGRESS ->
  ENGINEERING_EVIDENCE_READY -> ENGINEERING_E2E_PASS, with
  ENGINEERING_REJECTED and SUPERSEDED as guarded exits;
- source states (contract 11.1): DISCOVERED -> LEGAL_REVIEW ->
  PRIVACY_REVIEW -> TECHNICAL_PROBE -> EVIDENCE_READY ->
  PRODUCT_ADMITTED -> COMMERCIAL, with SUSPENDED (reversible),
  REVOKED and REJECTED (terminal) exits;
- semantic versioning: major for breaking schema changes, minor for
  additive changes, patch for corrections; versions compare semantically.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from axignal_api.library_manifest import LibraryStatus
from axignal_api.source_manifest import SourceState

SEMVER_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class VersioningError(ValueError):
    """Raised on invalid semantic versions or illegal transitions."""


@dataclass(frozen=True)
class SemanticVersion:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, version: str) -> SemanticVersion:
        match = SEMVER_PATTERN.match(version)
        if not match:
            raise VersioningError(f"invalid semantic version {version!r}")
        return cls(int(match.group(1)), int(match.group(2)), int(match.group(3)))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def bump(self, kind: Literal["major", "minor", "patch"]) -> SemanticVersion:
        if kind == "major":
            return SemanticVersion(self.major + 1, 0, 0)
        if kind == "minor":
            return SemanticVersion(self.major, self.minor + 1, 0)
        return SemanticVersion(self.major, self.minor, self.patch + 1)

    def is_valid(self) -> bool:
        return self.major >= 0 and self.minor >= 0 and self.patch >= 0


def compare_versions(left: str, right: str) -> int:
    """Return -1/0/1 comparing two semantic version strings."""
    a, b = SemanticVersion.parse(left), SemanticVersion.parse(right)
    return (a.major > b.major) - (a.major < b.major) or (
        (a.minor > b.minor) - (a.minor < b.minor)
    ) or ((a.patch > b.patch) - (a.patch < b.patch))


# --------------------------------------------------------------------------
# Library state machine
# --------------------------------------------------------------------------

LIBRARY_FORWARD: dict[LibraryStatus, set[LibraryStatus]] = {
    LibraryStatus.NOT_STARTED: {
        LibraryStatus.ENGINEERING_IN_PROGRESS,
        LibraryStatus.ENGINEERING_REJECTED,
        LibraryStatus.SUPERSEDED,
    },
    LibraryStatus.ENGINEERING_IN_PROGRESS: {
        LibraryStatus.ENGINEERING_EVIDENCE_READY,
        LibraryStatus.ENGINEERING_REJECTED,
        LibraryStatus.SUPERSEDED,
    },
    LibraryStatus.ENGINEERING_EVIDENCE_READY: {
        LibraryStatus.ENGINEERING_E2E_PASS,
        LibraryStatus.ENGINEERING_REJECTED,
        LibraryStatus.SUPERSEDED,
    },
    LibraryStatus.ENGINEERING_E2E_PASS: {LibraryStatus.SUPERSEDED},
    LibraryStatus.ENGINEERING_REJECTED: set(),
    LibraryStatus.SUPERSEDED: set(),
}

LIBRARY_REOPEN: dict[LibraryStatus, set[LibraryStatus]] = {
    LibraryStatus.ENGINEERING_REJECTED: {
        LibraryStatus.ENGINEERING_IN_PROGRESS,
        LibraryStatus.ENGINEERING_EVIDENCE_READY,
    },
    LibraryStatus.SUPERSEDED: {
        LibraryStatus.ENGINEERING_IN_PROGRESS,
        LibraryStatus.ENGINEERING_E2E_PASS,
    },
}

LIBRARY_REVERSIBLE = {
    LibraryStatus.ENGINEERING_IN_PROGRESS,
    LibraryStatus.ENGINEERING_EVIDENCE_READY,
    LibraryStatus.ENGINEERING_E2E_PASS,
    LibraryStatus.ENGINEERING_REJECTED,
}


def library_can_transition(current: LibraryStatus, target: LibraryStatus) -> bool:
    if target in LIBRARY_FORWARD[current]:
        return True
    if target in LIBRARY_REOPEN.get(current, set()):
        return True
    return current in LIBRARY_REVERSIBLE and target in (
        LibraryStatus.ENGINEERING_IN_PROGRESS,
        LibraryStatus.ENGINEERING_EVIDENCE_READY,
    )


# --------------------------------------------------------------------------
# Source state machine (contract 11.1)
# --------------------------------------------------------------------------

SOURCE_FORWARD: dict[SourceState, set[SourceState]] = {
    SourceState.DISCOVERED: {
        SourceState.LEGAL_REVIEW,
        SourceState.PRIVACY_REVIEW,
        SourceState.TECHNICAL_PROBE,
        SourceState.REJECTED,
    },
    SourceState.LEGAL_REVIEW: {
        SourceState.PRIVACY_REVIEW,
        SourceState.TECHNICAL_PROBE,
        SourceState.REJECTED,
        SourceState.SUSPENDED,
    },
    SourceState.PRIVACY_REVIEW: {
        SourceState.TECHNICAL_PROBE,
        SourceState.LEGAL_REVIEW,
        SourceState.REJECTED,
        SourceState.SUSPENDED,
    },
    SourceState.TECHNICAL_PROBE: {
        SourceState.EVIDENCE_READY,
        SourceState.LEGAL_REVIEW,
        SourceState.PRIVACY_REVIEW,
        SourceState.REJECTED,
        SourceState.SUSPENDED,
    },
    SourceState.EVIDENCE_READY: {
        SourceState.PRODUCT_ADMITTED,
        SourceState.TECHNICAL_PROBE,
        SourceState.REJECTED,
        SourceState.SUSPENDED,
    },
    SourceState.PRODUCT_ADMITTED: {
        SourceState.COMMERCIAL,
        SourceState.SUSPENDED,
        SourceState.REVOKED,
        SourceState.REJECTED,
    },
    SourceState.COMMERCIAL: {
        SourceState.SUSPENDED,
        SourceState.REVOKED,
        SourceState.REJECTED,
    },
    SourceState.SUSPENDED: {
        SourceState.PRODUCT_ADMITTED,
        SourceState.COMMERCIAL,
        SourceState.REVOKED,
        SourceState.REJECTED,
    },
    SourceState.REVOKED: set(),
    SourceState.REJECTED: set(),
}

SOURCE_TERMINAL = {SourceState.REVOKED, SourceState.REJECTED}


def source_can_transition(current: SourceState, target: SourceState) -> bool:
    return target in SOURCE_FORWARD[current]


def source_is_terminal(state: SourceState) -> bool:
    return state in SOURCE_TERMINAL


# --------------------------------------------------------------------------
# Versioning helpers
# --------------------------------------------------------------------------

def bump_version(version: str, kind: Literal["major", "minor", "patch"]) -> str:
    """Bump a semantic version string."""
    return str(SemanticVersion.parse(version).bump(kind))


def validate_schema_version(version: str) -> bool:
    return SEMVER_PATTERN.match(version) is not None


def version_bump_kind(old: str, new: str) -> str | None:
    """Infer the bump kind between two valid versions, or None if not a bump."""
    a, b = SemanticVersion.parse(old), SemanticVersion.parse(new)
    if a.major != b.major and b.minor == 0 and b.patch == 0:
        return "major"
    if a.minor != b.minor and b.patch == 0:
        return "minor"
    if a.patch != b.patch:
        return "patch"
    return None


TransitionFn = Callable[[str, str], bool]

TRANSITIONS: dict[str, TransitionFn] = {
    "library": lambda current, target: library_can_transition(
        LibraryStatus(current), LibraryStatus(target)
    ),
    "source": lambda current, target: source_can_transition(
        SourceState(current), SourceState(target)
    ),
}


def assert_transition_allowed(kind: str, current: str, target: str) -> None:
    """Raise VersioningError when a manifest state transition is illegal."""
    if kind not in TRANSITIONS:
        raise VersioningError(f"unknown manifest kind {kind!r}")
    if not TRANSITIONS[kind](current, target):
        raise VersioningError(
            f"illegal {kind} state transition {current!r} -> {target!r}"
        )
