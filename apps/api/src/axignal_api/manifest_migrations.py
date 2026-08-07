"""Manifest schema migration strategy — WP2-T11.

Defines how LibraryManifest/SourceManifest documents evolve between
schema versions without breaking consumers:

- every migration is additive (additive-only rule): fields may be added
  with defaults, never removed or renamed without a major version bump
  and a compatibility shim;
- migrations are ordered and idempotent: applying migration N+1 twice
  yields the same result as applying it once;
- a migration must never change the meaning of an existing field;
- breaking changes require a major version and a written migration path;
- registry: manifest_kind -> ordered list of migrations.

The SQL layer follows the same discipline: infra/postgres/NNN-*.sql
files are applied in numeric order and are additive (the repository's
migration matrix contract).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from axignal_api.manifest_state_machine import (
    VersioningError,
    compare_versions,
)

ManifestDict = dict[str, Any]
MigrationFn = Callable[[ManifestDict], ManifestDict]


@dataclass(frozen=True)
class ManifestMigration:
    """A single ordered, additive manifest migration."""

    from_version: str
    to_version: str
    kind: Literal["major", "minor", "patch"]
    description: str
    apply: MigrationFn

    def __post_init__(self) -> None:
        if compare_versions(self.to_version, self.from_version) <= 0:
            raise VersioningError(
                "migration to_version must be greater than from_version: "
                f"{self.from_version} -> {self.to_version}"
            )


class MigrationNotApplicable(ValueError):
    """Raised when a manifest cannot be migrated from its current version."""


class ManifestMigrationRegistry:
    """Ordered, versioned migration paths per manifest kind."""

    def __init__(self) -> None:
        self._migrations: dict[str, list[ManifestMigration]] = {}

    def register(self, kind: str, migration: ManifestMigration) -> None:
        self._migrations.setdefault(kind, []).append(migration)
        # Keep migrations strictly ordered by from_version.
        self._migrations[kind].sort(key=lambda m: m.from_version)

    def migrate(self, kind: str, manifest: ManifestDict) -> ManifestDict:
        """Apply all applicable migrations in order (idempotent)."""
        if kind not in self._migrations:
            return manifest
        current = manifest.get("schema_version", "1.0.0")
        result = dict(manifest)
        applied: list[str] = []
        for _ in range(len(self._migrations[kind]) + 1):
            progressed = False
            for migration in self._migrations[kind]:
                if compare_versions(current, migration.from_version) == 0:
                    result = dict(migration.apply(result))
                    result["schema_version"] = migration.to_version
                    current = migration.to_version
                    applied.append(f"{migration.from_version}->{migration.to_version}")
                    progressed = True
            if not progressed:
                break
        return result

    def can_migrate(self, kind: str, version: str) -> bool:
        if kind not in self._migrations:
            return False
        for migration in self._migrations[kind]:
            if compare_versions(version, migration.from_version) == 0:
                return True
        return False

    def migrations_for(self, kind: str) -> tuple[ManifestMigration, ...]:
        return tuple(self._migrations.get(kind, []))


def _add_field(
    manifest: ManifestDict,
    field: str,
    default: Any,
) -> ManifestDict:
    """Add a field with a default if missing (additive-only rule)."""
    if field not in manifest:
        manifest[field] = default
    return manifest


# Canonical registry used by the API.
DEFAULT_MIGRATION_REGISTRY = ManifestMigrationRegistry()

# LibraryManifest 1.0.0 -> 1.1.0 (minor): add source_manifests/coverage defaults.
DEFAULT_MIGRATION_REGISTRY.register(
    "library",
    ManifestMigration(
        from_version="1.0.0",
        to_version="1.1.0",
        kind="minor",
        description="add source_manifests and coverage defaults (additive)",
        apply=lambda m: _add_field(_add_field(m, "source_manifests", []), "coverage", {}),
    ),
)

# SourceManifest 1.0.0 -> 1.1.0 (minor): add outage_profile default.
DEFAULT_MIGRATION_REGISTRY.register(
    "source",
    ManifestMigration(
        from_version="1.0.0",
        to_version="1.1.0",
        kind="minor",
        description="add outage_profile default (additive)",
        apply=lambda m: _add_field(m, "outage_profile", {}),
    ),
)
