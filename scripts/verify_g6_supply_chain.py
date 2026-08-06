from __future__ import annotations

import json
import re
import sys
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_LOCK = ROOT / "requirements/python-runtime.lock"
DEV_LOCK = ROOT / "requirements/python-dev.lock"
IMAGE_LOCK = ROOT / "data/supply-chain/image-lock.v1.json"
PYPROJECT = ROOT / "pyproject.toml"

SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}$")
ACTION_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PACKAGE_RE = re.compile(
    r"^([A-Za-z0-9_.-]+)(?:\[[^]]+\])?==([^\s;\\]+)"
)
FROM_RE = re.compile(
    r"^\s*FROM\s+(?:--platform=\S+\s+)?(\S+)(?:\s+AS\s+(\S+))?",
    re.I,
)
IMAGE_LINE_RE = re.compile(r"^\s*image:\s*[\"']?([^\"'\s#]+)")
USES_RE = re.compile(r"^\s*-?\s*uses:\s*[\"']?([^\"'\s#]+)")
DYNAMIC_RELEASE_IMAGE_RE = re.compile(
    r"^\$\{([A-Z0-9_]+)_IMAGE_REPOSITORY:\?required\}:"
    r"\$\{\1_IMAGE_TAG:\?required\}@sha256:"
    r"\$\{\1_IMAGE_DIGEST:\?required\}$"
)


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    message: str

    def as_dict(self) -> dict[str, object]:
        return {"path": self.path, "line": self.line, "message": self.message}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def record(
    findings: list[Finding], path: str | Path, line: int, message: str
) -> None:
    rendered_path = rel(path) if isinstance(path, Path) else path
    findings.append(Finding(rendered_path, line, message))


def normalise_package(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def direct_requirement_name(requirement: str) -> str:
    match = re.match(r"^\s*([A-Za-z0-9_.-]+)", requirement)
    if not match:
        raise ValueError(f"invalid requirement declaration: {requirement!r}")
    return normalise_package(match.group(1))


def logical_lock_statements(path: Path) -> list[tuple[int, str]]:
    statements: list[tuple[int, str]] = []
    current: list[str] = []
    start = 0
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = raw.strip()
        if not current and (not stripped or stripped.startswith("#")):
            continue
        if not current:
            start = number
        current.append(stripped)
        if stripped.endswith("\\"):
            continue
        statement = " ".join(current)
        current = []
        if statement and not statement.startswith("#"):
            statements.append((start, statement))
    if current:
        statements.append((start, " ".join(current)))
    return statements


def inspect_lock(path: Path, findings: list[Finding]) -> set[str]:
    packages: set[str] = set()
    for line, statement in logical_lock_statements(path):
        if statement.startswith("--"):
            record(
                findings,
                path,
                line,
                "global pip options are not permitted in the lock",
            )
            continue
        match = PACKAGE_RE.match(statement)
        if not match:
            record(
                findings,
                path,
                line,
                "requirement is not an exact package==version pin",
            )
            continue
        package = normalise_package(match.group(1))
        packages.add(package)
        hashes = re.findall(r"--hash=(sha256:[0-9a-f]{64})", statement)
        if not hashes:
            record(
                findings,
                path,
                line,
                f"{package} has no SHA-256 distribution hash",
            )
        if " @ " in statement or "git+" in statement or "-e " in statement:
            record(
                findings,
                path,
                line,
                f"{package} uses a non-registry or editable source",
            )
    if not packages:
        record(findings, path, 1, "lock contains no exact packages")
    return packages


def inspect_pyproject(
    runtime_packages: set[str],
    dev_packages: set[str],
    findings: list[Finding],
) -> None:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    runtime = data["project"]["dependencies"]
    development = data["project"]["optional-dependencies"]["dev"]
    build_requirements = data["build-system"]["requires"]

    for requirement in runtime:
        package = direct_requirement_name(requirement)
        if package not in runtime_packages:
            record(
                findings,
                PYPROJECT,
                1,
                f"runtime dependency {package} is absent from runtime lock",
            )
        if package not in dev_packages:
            record(
                findings,
                PYPROJECT,
                1,
                f"runtime dependency {package} is absent from dev lock",
            )

    for requirement in development:
        package = direct_requirement_name(requirement)
        if package not in dev_packages:
            record(
                findings,
                PYPROJECT,
                1,
                f"development dependency {package} is absent from dev lock",
            )

    for requirement in build_requirements:
        if "==" not in requirement:
            record(
                findings,
                PYPROJECT,
                1,
                f"build requirement is not exact: {requirement}",
            )
        package = direct_requirement_name(requirement)
        if package not in dev_packages:
            record(
                findings,
                PYPROJECT,
                1,
                f"build requirement {package} is absent from dev lock",
            )


def load_image_lock(findings: list[Finding]) -> dict[str, str]:
    try:
        payload = json.loads(IMAGE_LOCK.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        record(findings, IMAGE_LOCK, 1, f"cannot load image lock: {exc}")
        return {}

    expected_toolchain = {
        "schema": "axignal.g6-supply-chain-lock.v1",
        "python": "3.13.14",
        "pip": "26.1.2",
        "pip_tools": "7.6.0",
    }
    for key, expected in expected_toolchain.items():
        if payload.get(key) != expected:
            record(
                findings,
                IMAGE_LOCK,
                1,
                f"unexpected {key}: {payload.get(key)!r}",
            )

    result: dict[str, str] = {}
    for index, item in enumerate(payload.get("images", []), 1):
        reference = item.get("reference")
        digest = item.get("digest")
        if not isinstance(reference, str) or not isinstance(digest, str):
            record(
                findings,
                IMAGE_LOCK,
                index,
                "image entry is not a string reference/digest pair",
            )
            continue
        if reference in result:
            record(
                findings,
                IMAGE_LOCK,
                index,
                f"duplicate image reference {reference}",
            )
        if not SHA256_RE.fullmatch(digest):
            record(
                findings,
                IMAGE_LOCK,
                index,
                f"invalid digest for {reference}",
            )
        result[reference] = digest
    return result


def verify_image_reference(
    path: Path,
    line: int,
    reference: str,
    image_lock: dict[str, str],
    findings: list[Finding],
) -> bool:
    if reference == "scratch":
        return False
    if DYNAMIC_RELEASE_IMAGE_RE.fullmatch(reference):
        return True
    if "@" not in reference:
        record(findings, path, line, f"mutable image reference: {reference}")
        return False
    named, digest = reference.rsplit("@", 1)
    if ":" not in named.rsplit("/", 1)[-1]:
        record(
            findings,
            path,
            line,
            f"image lacks a human-readable tag before digest: {reference}",
        )
    if not SHA256_RE.fullmatch(digest):
        record(findings, path, line, f"invalid image digest: {reference}")
        return False
    expected = image_lock.get(named)
    if expected is None:
        record(
            findings,
            path,
            line,
            f"image is not governed by image lock: {named}",
        )
    elif expected != digest:
        record(
            findings,
            path,
            line,
            f"digest differs from image lock for {named}",
        )
    return False


def dockerfiles() -> Iterable[Path]:
    for path in ROOT.rglob("Dockerfile*"):
        excluded = {".git", "node_modules", ".next", ".venv"}
        if any(part in excluded for part in path.parts):
            continue
        if path.is_file():
            yield path


def inspect_dockerfiles(image_lock: dict[str, str], findings: list[Finding]) -> int:
    count = 0
    for path in sorted(dockerfiles()):
        aliases: set[str] = set()
        lines = path.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, 1):
            match = FROM_RE.match(line)
            if not match:
                continue
            image, alias = match.groups()
            if image not in aliases:
                verify_image_reference(path, number, image, image_lock, findings)
                count += 1
            if alias:
                aliases.add(alias)
    return count


def yaml_supply_chain_files() -> Iterable[Path]:
    candidates = {ROOT / "compose.yaml"}
    candidates.update(ROOT.glob("compose*.yml"))
    candidates.update(ROOT.glob("compose*.yaml"))
    candidates.update((ROOT / "infra").rglob("*.yml"))
    candidates.update((ROOT / "infra").rglob("*.yaml"))
    candidates.update((ROOT / ".github/workflows").glob("*.yml"))
    candidates.update((ROOT / ".github/workflows").glob("*.yaml"))
    return sorted(path for path in candidates if path.is_file())


def inspect_yaml_images(
    image_lock: dict[str, str], findings: list[Finding]
) -> tuple[int, int]:
    count = 0
    dynamic_release_count = 0
    for path in yaml_supply_chain_files():
        lines = path.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, 1):
            match = IMAGE_LINE_RE.match(line)
            if not match:
                continue
            dynamic_release_count += int(
                verify_image_reference(
                    path,
                    number,
                    match.group(1),
                    image_lock,
                    findings,
                )
            )
            count += 1
    return count, dynamic_release_count


def inspect_workflow_actions(findings: list[Finding]) -> int:
    count = 0
    workflow_paths = sorted((ROOT / ".github/workflows").glob("*.yml"))
    workflow_paths += sorted((ROOT / ".github/workflows").glob("*.yaml"))
    for path in workflow_paths:
        lines = path.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, 1):
            match = USES_RE.match(line)
            if not match:
                continue
            reference = match.group(1)
            count += 1
            if reference.startswith("./"):
                continue
            if reference.startswith("docker://"):
                if "@sha256:" not in reference:
                    record(
                        findings,
                        path,
                        number,
                        f"mutable docker action: {reference}",
                    )
                continue
            if "@" not in reference:
                record(
                    findings,
                    path,
                    number,
                    f"action has no immutable revision: {reference}",
                )
                continue
            revision = reference.rsplit("@", 1)[1]
            if not ACTION_SHA_RE.fullmatch(revision):
                record(
                    findings,
                    path,
                    number,
                    f"action is not pinned to a 40-character SHA: {reference}",
                )
    return count


def inspect_release_build_contract(findings: list[Finding]) -> None:
    runtime_path = ROOT / "infra/runtime/Dockerfile"
    runtime = runtime_path.read_text(encoding="utf-8")
    for required in (
        "requirements/python-runtime.lock",
        "--require-hashes",
        "--only-binary=:all:",
        "PYTHONPATH=/app/apps/api/src",
    ):
        if required not in runtime:
            record(
                findings,
                "infra/runtime/Dockerfile",
                1,
                f"missing runtime build invariant: {required}",
            )
    for prohibited in ("pip install --no-cache-dir .", "pip install .", "-e ."):
        if prohibited in runtime:
            record(
                findings,
                "infra/runtime/Dockerfile",
                1,
                f"floating project installation remains: {prohibited}",
            )

    for dockerfile in ("infra/pilot/Dockerfile.web", "infra/landing/Dockerfile"):
        content = (ROOT / dockerfile).read_text(encoding="utf-8")
        if "pnpm install --frozen-lockfile" not in content:
            record(
                findings,
                dockerfile,
                1,
                "web build does not enforce pnpm frozen lockfile",
            )

    landing_path = ROOT / "infra/landing/compose.yaml"
    landing_compose = landing_path.read_text(encoding="utf-8")
    required_reference = (
        "${AXIGNAL_LANDING_IMAGE_REPOSITORY:?required}:"
        "${AXIGNAL_LANDING_IMAGE_TAG:?required}@sha256:"
        "${AXIGNAL_LANDING_IMAGE_DIGEST:?required}"
    )
    if required_reference not in landing_compose:
        record(
            findings,
            "infra/landing/compose.yaml",
            1,
            "landing release image is not forced into tag@sha256 form",
        )


def main() -> int:
    findings: list[Finding] = []
    runtime_packages = inspect_lock(RUNTIME_LOCK, findings)
    dev_packages = inspect_lock(DEV_LOCK, findings)
    inspect_pyproject(runtime_packages, dev_packages, findings)
    image_lock = load_image_lock(findings)
    docker_froms = inspect_dockerfiles(image_lock, findings)
    yaml_images, dynamic_release_images = inspect_yaml_images(image_lock, findings)
    workflow_actions = inspect_workflow_actions(findings)
    inspect_release_build_contract(findings)

    payload = {
        "schema": "axignal.g6-supply-chain-verification.v1",
        "status": "PASS" if not findings else "FAIL",
        "runtime_packages": len(runtime_packages),
        "development_packages": len(dev_packages),
        "governed_images": len(image_lock),
        "docker_from_references": docker_froms,
        "yaml_image_references": yaml_images,
        "dynamic_release_image_references": dynamic_release_images,
        "workflow_action_references": workflow_actions,
        "findings": [finding.as_dict() for finding in findings],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
