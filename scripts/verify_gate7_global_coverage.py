from __future__ import annotations

import json
import os
import subprocess
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "data/acceptance/global-coverage-source-language-index.v0.1.json"
INDEX_SCHEMA_PATH = ROOT / "schemas/global-coverage-source-language-index.schema.json"
REPORT_SCHEMA_PATH = (
    ROOT / "schemas/global-coverage-source-language-report.schema.json"
)
EXPECTED_LIBRARY_IDS = {
    *(f"AX-LIB-F{index:02d}" for index in range(1, 8)),
    *(f"AX-LIB-O{index:02d}" for index in range(1, 10)),
}
PASS = "PASS"
FAIL = "FAIL"
MISSING = "MISSING"


class Gate7ContractError(RuntimeError):
    """Raised when Gate 7 evidence violates a fail-closed contract."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Gate7ContractError(f"Required file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise Gate7ContractError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise Gate7ContractError(f"Expected an object in {path}")
    return payload


def validate_schema(payload: dict[str, Any], schema: dict[str, Any], label: str) -> None:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
    if not errors:
        return
    rendered = []
    for error in errors[:20]:
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        rendered.append(f"{label}:{location}: {error.message}")
    raise Gate7ContractError("\n".join(rendered))


def ensure_unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise Gate7ContractError(f"Duplicate values are forbidden in {label}")


def parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Gate7ContractError(f"Invalid timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise Gate7ContractError(f"Timestamp must include a timezone: {value}")
    return parsed.astimezone(UTC)


def baseline_is_ancestor(baseline_sha: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", baseline_sha, "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise Gate7ContractError(
        "Unable to verify Gate 7 baseline ancestry: "
        f"{result.stderr.strip() or result.stdout.strip()}"
    )


def missing_language(language: str) -> dict[str, Any]:
    return {
        "language": language,
        "ingestion": MISSING,
        "normalisation": MISSING,
        "search": MISSING,
        "presentation": MISSING,
        "evidence": [],
    }


def missing_library(
    library: dict[str, Any], required_languages: list[str]
) -> dict[str, Any]:
    return {
        "library_id": library["library_id"],
        "kind": library["kind"],
        "canonical_name": library["canonical_name"],
        "runtime_reference": library["runtime_reference"],
        "canonical_state": "BLOCKED",
        "countries_covered": [],
        "languages": [missing_language(language) for language in required_languages],
        "sectors": [],
        "historical_depth": {
            "earliest_date": None,
            "latest_date": None,
            "status": MISSING,
            "evidence": [],
        },
        "update_frequency": {
            "declared": None,
            "observed": None,
            "status": MISSING,
            "evidence": [],
        },
        "sources": {"active": [], "suspended": [], "candidate": []},
        "rights": {"status": MISSING, "evidence": []},
        "quality": {
            "status": MISSING,
            "completeness": None,
            "accuracy": None,
            "freshness": None,
            "duplicate_rate": None,
            "evidence": [],
        },
        "lag": {
            "status": MISSING,
            "p50_seconds": None,
            "p95_seconds": None,
            "max_seconds": None,
            "evidence": [],
        },
        "reviews": [],
        "limitations": [
            "No product-admitted source evidence exists for this library.",
            "Coverage, multilingual journeys, rights, quality and lag are unaccepted.",
            "This library cannot contribute to a public global-coverage claim.",
        ],
        "synthetic_data": {
            "present": False,
            "disclosed": True,
            "contributes_to_public_claim": False,
            "evidence": [],
        },
        "kill_switch": {"implemented": False, "tested": False, "evidence": []},
        "rollback": {"implemented": False, "tested": False, "evidence": []},
        "claim_decision": "DENIED",
    }


def evidence_current(evidence: list[dict[str, Any]], now: datetime) -> bool:
    return bool(evidence) and all(parse_time(item["expires_at"]) > now for item in evidence)


def source_is_admitted(source: dict[str, Any], now: datetime) -> bool:
    admission = source["admission"]
    if source["state"] != "PRODUCT_ADMITTED":
        return False
    if any(value != PASS for value in admission.values()):
        return False
    rights_expiry = source["rights_expiry"]
    if rights_expiry is not None and parse_time(rights_expiry) <= now:
        return False
    return evidence_current(source["evidence"], now)


def validate_source_boundaries(library: dict[str, Any], now: datetime) -> None:
    source_ids: list[str] = []
    for bucket_name in ("active", "suspended", "candidate"):
        for source in library["sources"][bucket_name]:
            source_ids.append(source["source_id"])
            if bucket_name == "active" and not source_is_admitted(source, now):
                raise Gate7ContractError(
                    f"{library['library_id']} exposes a non-admitted active source: "
                    f"{source['source_id']}"
                )
            if bucket_name != "active" and source["contributes_to_public_claim"]:
                raise Gate7ContractError(
                    f"{library['library_id']} lets {bucket_name} source "
                    f"{source['source_id']} contribute to a public claim"
                )
            if bucket_name == "suspended" and source["state"] not in {
                "SUSPENDED",
                "REVOKED",
            }:
                raise Gate7ContractError(
                    f"{library['library_id']} has an invalid suspended-source state"
                )
    ensure_unique(source_ids, f"{library['library_id']} source ids")



def language_journeys_pass(
    library: dict[str, Any], required_languages: list[str], now: datetime
) -> bool:
    journeys = library["languages"]
    languages = [journey["language"] for journey in journeys]
    ensure_unique(languages, f"{library['library_id']} languages")
    if set(languages) != set(required_languages):
        return False
    for journey in journeys:
        stages = (
            journey["ingestion"],
            journey["normalisation"],
            journey["search"],
            journey["presentation"],
        )
        if any(stage != PASS for stage in stages):
            return False
        if not evidence_current(journey["evidence"], now):
            return False
    return True


def reviews_pass(
    library: dict[str, Any], required_authorities: list[str], now: datetime
) -> bool:
    reviews = library["reviews"]
    authorities = [review["authority"] for review in reviews]
    ensure_unique(authorities, f"{library['library_id']} review authorities")
    if set(authorities) != set(required_authorities):
        return False
    for review in reviews:
        if review["decision"] != "APPROVE":
            return False
        if parse_time(review["reviewed_at"]) > now:
            return False
        if parse_time(review["expires_at"]) <= now:
            return False
        if not review["signature"].strip():
            return False
    return True


def metric_block_pass(block: dict[str, Any], now: datetime) -> bool:
    return block["status"] == PASS and evidence_current(block["evidence"], now)


def control_pass(control: dict[str, Any], now: datetime) -> bool:
    return (
        control["implemented"]
        and control["tested"]
        and evidence_current(control["evidence"], now)
    )


def library_passes(
    library: dict[str, Any],
    required_languages: list[str],
    required_authorities: list[str],
    now: datetime,
) -> bool:
    validate_source_boundaries(library, now)
    if library["canonical_state"] != "ACCEPTED":
        return False
    if not library["countries_covered"] or not library["sectors"]:
        return False
    if not library["limitations"]:
        return False
    if not library["sources"]["active"]:
        return False
    if any(
        not source_is_admitted(source, now)
        for source in library["sources"]["active"]
    ):
        return False
    if not language_journeys_pass(library, required_languages, now):
        return False
    if not metric_block_pass(library["historical_depth"], now):
        return False
    if not metric_block_pass(library["update_frequency"], now):
        return False
    if not metric_block_pass(library["rights"], now):
        return False
    if not metric_block_pass(library["quality"], now):
        return False
    if not metric_block_pass(library["lag"], now):
        return False
    if not reviews_pass(library, required_authorities, now):
        return False
    synthetic = library["synthetic_data"]
    if synthetic["present"] and not synthetic["disclosed"]:
        return False
    if synthetic["contributes_to_public_claim"]:
        return False
    if not control_pass(library["kill_switch"], now):
        return False
    if not control_pass(library["rollback"], now):
        return False
    return library["claim_decision"] == "APPROVED"


def library_rejected(library: dict[str, Any]) -> bool:
    if library["canonical_state"] == "REJECTED":
        return True
    if library["claim_decision"] == "DENIED" and any(
        review["decision"] == "REJECT" for review in library["reviews"]
    ):
        return True
    status_blocks = (
        library["historical_depth"],
        library["update_frequency"],
        library["rights"],
        library["quality"],
        library["lag"],
    )
    return any(block["status"] == FAIL for block in status_blocks)


def validate_claim_authority(report: dict[str, Any]) -> None:
    claims = report["claims"]
    claim_flags = (
        claims["global_coverage_authorised"],
        claims["multilingual_authorised"],
        claims["all_sources_admitted"],
    )
    if report["decision"] != PASS and any(claim_flags):
        raise Gate7ContractError("Gate 7 claims cannot be true before decision PASS")
    if report["decision"] == PASS:
        if not all(claim_flags):
            raise Gate7ContractError("Gate 7 PASS requires all claim flags")
        if not claims["public_claim_text"]:
            raise Gate7ContractError("Gate 7 PASS requires bounded public claim text")
    elif claims["public_claim_text"] is not None:
        raise Gate7ContractError("Public claim text is forbidden before Gate 7 PASS")


def build_report(
    index: dict[str, Any], report_schema: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    now = datetime.now(UTC)
    required_languages = index["required_languages"]
    required_authorities = index["required_authorities"]
    libraries: list[dict[str, Any]] = []
    missing_files: list[str] = []

    for entry in index["libraries"]:
        runtime_path = ROOT / entry["runtime_reference"]
        if not runtime_path.is_file():
            raise Gate7ContractError(
                f"Runtime reference does not exist: {entry['runtime_reference']}"
            )
        evidence_path = ROOT / entry["evidence_file"]
        if evidence_path.is_file():
            library = load_json(evidence_path)
        else:
            missing_files.append(entry["evidence_file"])
            library = missing_library(entry, required_languages)
        for field in ("library_id", "kind", "canonical_name", "runtime_reference"):
            if library[field] != entry[field]:
                raise Gate7ContractError(
                    f"{entry['library_id']} evidence changes indexed field {field}"
                )
        validate_source_boundaries(library, now)
        libraries.append(library)

    library_ids = [library["library_id"] for library in libraries]
    ensure_unique(library_ids, "Gate 7 library ids")
    if set(library_ids) != EXPECTED_LIBRARY_IDS:
        raise Gate7ContractError("Gate 7 must cover exactly AX-LIB-F01-F07 and O01-O09")

    rejected = any(library_rejected(library) for library in libraries)
    all_pass = not missing_files and all(
        library_passes(
            library,
            required_languages,
            required_authorities,
            now,
        )
        for library in libraries
    )
    decision = "REJECTED" if rejected else PASS if all_pass else "IN_PROGRESS"
    claim_text = None
    if decision == PASS:
        claim_text = (
            "AXIGNAL provides the countries, languages, sectors, history and sources "
            "listed in this report; disclosed limitations remain part of the claim."
        )

    report = {
        "schema_version": "axignal.global-coverage-source-language-report/v0.1",
        "gate_id": "PUBLIC-LAUNCH-GATE-7",
        "baseline_sha": index["baseline_sha"],
        "decision": decision,
        "claims": {
            "global_coverage_authorised": decision == PASS,
            "multilingual_authorised": decision == PASS,
            "all_sources_admitted": decision == PASS,
            "public_claim_text": claim_text,
        },
        "required_languages": required_languages,
        "required_authorities": required_authorities,
        "libraries": libraries,
    }
    validate_schema(report, report_schema, "report")
    validate_claim_authority(report)
    return report, missing_files


def render_markdown(report: dict[str, Any], missing_files: list[str]) -> str:
    claims = report["claims"]
    lines = [
        "# AXIGNAL Gate 7 — Global coverage, sources and multilingual acceptance",
        "",
        f"- Baseline SHA: `{report['baseline_sha']}`",
        f"- Decision: **{report['decision']}**",
        "- Global coverage claim: "
        + ("AUTHORISED" if claims["global_coverage_authorised"] else "DENIED"),
        "- Multilingual claim: "
        + ("AUTHORISED" if claims["multilingual_authorised"] else "DENIED"),
        "- All sources admitted: "
        + ("YES" if claims["all_sources_admitted"] else "NO"),
        "",
        "| Library | Canonical state | Countries | Active sources | Languages PASS | Claim |",
        "|---|---|---:|---:|---:|---|",
    ]
    for library in report["libraries"]:
        language_passes = sum(
            1
            for journey in library["languages"]
            if all(
                journey[stage] == PASS
                for stage in ("ingestion", "normalisation", "search", "presentation")
            )
        )
        lines.append(
            "| {library_id} | {state} | {countries} | {sources} | {languages} | "
            "{claim} |".format(
                library_id=library["library_id"],
                state=library["canonical_state"],
                countries=len(library["countries_covered"]),
                sources=len(library["sources"]["active"]),
                languages=language_passes,
                claim=library["claim_decision"],
            )
        )
    lines.extend(["", "## Missing library evidence files", ""])
    if missing_files:
        lines.extend(f"- `{path}`" for path in missing_files)
    else:
        lines.append("None.")
    lines.extend(
        [
            "",
            "## Binding definitions",
            "",
            "```text",
            'global = evidence-backed coverage + disclosed limitations',
            "multilingual = ingestion + normalisation + search + presentation",
            "source admitted = legal + technical + quality + rights + human authority",
            "```",
            "",
            "No absent, candidate, suspended, revoked or synthetic-only source may "
            "contribute to a public coverage claim.",
            "",
        ]
    )
    return "\n".join(lines)


def run_adversarial_contracts(report: dict[str, Any]) -> int:
    checks = 0

    premature = deepcopy(report)
    premature["claims"]["global_coverage_authorised"] = True
    try:
        validate_claim_authority(premature)
    except Gate7ContractError:
        checks += 1
    else:
        raise Gate7ContractError("Premature global claim was not rejected")

    synthetic = deepcopy(report["libraries"][0])
    synthetic["synthetic_data"]["present"] = True
    synthetic["synthetic_data"]["disclosed"] = False
    synthetic["synthetic_data"]["contributes_to_public_claim"] = True
    if library_passes(
        synthetic,
        report["required_languages"],
        report["required_authorities"],
        datetime.now(UTC),
    ):
        raise Gate7ContractError("Undisclosed synthetic data passed Gate 7")
    checks += 1

    suspended = deepcopy(report["libraries"][0])
    suspended["sources"]["suspended"] = [
        {
            "source_id": "adversarial-suspended",
            "name": "Adversarial suspended source",
            "state": "SUSPENDED",
            "contributes_to_public_claim": True,
            "admission": {
                "legal": MISSING,
                "technical": MISSING,
                "quality": MISSING,
                "rights": MISSING,
                "human_authority": MISSING,
            },
            "rights_expiry": None,
            "evidence": [],
        }
    ]
    try:
        validate_source_boundaries(suspended, datetime.now(UTC))
    except Gate7ContractError:
        checks += 1
    else:
        raise Gate7ContractError("Suspended source contributed to a public claim")

    active = deepcopy(report["libraries"][0])
    active["sources"]["active"] = [
        {
            "source_id": "adversarial-unreviewed",
            "name": "Adversarial unreviewed source",
            "state": "PRODUCT_ADMITTED",
            "contributes_to_public_claim": True,
            "admission": {
                "legal": MISSING,
                "technical": PASS,
                "quality": PASS,
                "rights": MISSING,
                "human_authority": MISSING,
            },
            "rights_expiry": None,
            "evidence": [],
        }
    ]
    try:
        validate_source_boundaries(active, datetime.now(UTC))
    except Gate7ContractError:
        checks += 1
    else:
        raise Gate7ContractError("Unreviewed active source was not rejected")

    return checks


def main() -> int:
    index = load_json(INDEX_PATH)
    index_schema = load_json(INDEX_SCHEMA_PATH)
    report_schema = load_json(REPORT_SCHEMA_PATH)
    validate_schema(index, index_schema, "index")

    library_ids = [entry["library_id"] for entry in index["libraries"]]
    ensure_unique(library_ids, "Gate 7 index library ids")
    if set(library_ids) != EXPECTED_LIBRARY_IDS:
        raise Gate7ContractError("Gate 7 index has an incomplete library set")
    if not baseline_is_ancestor(index["baseline_sha"]):
        raise Gate7ContractError("Gate 7 baseline is not an ancestor of HEAD")

    report, missing_files = build_report(index, report_schema)
    adversarial_checks = run_adversarial_contracts(report)

    evidence_dir = Path(
        os.environ.get("AXIGNAL_GATE7_EVIDENCE_DIR", "artifacts/gate7")
    )
    if not evidence_dir.is_absolute():
        evidence_dir = ROOT / evidence_dir
    evidence_dir.mkdir(parents=True, exist_ok=True)
    report_path = evidence_dir / "global-coverage-source-language-report.json"
    markdown_path = evidence_dir / "global-coverage-source-language-report.md"
    summary_path = evidence_dir / "gate7-summary.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_markdown(report, missing_files),
        encoding="utf-8",
    )
    summary = {
        "status": PASS,
        "gate_id": report["gate_id"],
        "gate_decision": report["decision"],
        "baseline_sha": report["baseline_sha"],
        "libraries": len(report["libraries"]),
        "missing_evidence_files": len(missing_files),
        "global_coverage_authorised": report["claims"][
            "global_coverage_authorised"
        ],
        "multilingual_authorised": report["claims"]["multilingual_authorised"],
        "all_sources_admitted": report["claims"]["all_sources_admitted"],
        "adversarial_checks": adversarial_checks,
        "public_launch_authorised": False,
    }
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))

    require_pass = os.environ.get("AXIGNAL_REQUIRE_GATE7_PASS") == "true"
    if require_pass and report["decision"] != PASS:
        raise Gate7ContractError(
            "Gate 7 acceptance was required, but evidence remains incomplete"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Gate7ContractError as exc:
        print(json.dumps({"status": FAIL, "error": str(exc)}, sort_keys=True))
        raise SystemExit(1) from exc
