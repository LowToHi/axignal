#!/usr/bin/env python3
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft202012Validator

from p06_document_intelligence_reference import (
    least_document_authority,
    may_write_document_canonical,
    ocr_confidence_decision,
    parse_localized_decimal,
    preserve_source_text,
    preserve_unknown,
    semantic_parity_decision,
    validate_anchor,
    validate_language_tag,
)

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCHEMA = ROOT / "schemas/multilingual-document-intelligence-runtime.schema.json"
CASES_SCHEMA = ROOT / "schemas/multilingual-document-intelligence-cases.schema.json"
FIXTURES_SCHEMA = ROOT / "schemas/multilingual-document-intelligence-fixtures.schema.json"
RUNTIME = ROOT / "data/document-intelligence/multilingual-document-intelligence-runtime.v0.1.json"
CASES = ROOT / "data/document-intelligence/p06-adversarial-cases.v0.1.json"
FIXTURES = ROOT / "data/document-intelligence/p06-conformance-fixtures.v0.1.json"
PROGRAMME = ROOT / "data/programmes/global-e2e-tasks-p05-p09.v1.4.json"
P03_SECURITY = ROOT / "data/security/security-identity-rights-registry.v0.1.json"
P04_CONNECTORS = ROOT / "data/connectors/connector-sdk-registry.v0.1.json"
P05_FOUNDATIONS = ROOT / "data/foundations/foundational-library-runtime.v0.1.json"

paths = (
    RUNTIME_SCHEMA,
    CASES_SCHEMA,
    FIXTURES_SCHEMA,
    RUNTIME,
    CASES,
    FIXTURES,
    PROGRAMME,
    P03_SECURITY,
    P04_CONNECTORS,
    P05_FOUNDATIONS,
)
for path in paths:
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"

runtime_schema = json.loads(RUNTIME_SCHEMA.read_text(encoding="utf-8"))
cases_schema = json.loads(CASES_SCHEMA.read_text(encoding="utf-8"))
fixtures_schema = json.loads(FIXTURES_SCHEMA.read_text(encoding="utf-8"))
runtime = json.loads(RUNTIME.read_text(encoding="utf-8"))
cases = json.loads(CASES.read_text(encoding="utf-8"))
fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
programme = json.loads(PROGRAMME.read_text(encoding="utf-8"))
p03 = json.loads(P03_SECURITY.read_text(encoding="utf-8"))
p04 = json.loads(P04_CONNECTORS.read_text(encoding="utf-8"))
p05 = json.loads(P05_FOUNDATIONS.read_text(encoding="utf-8"))

for schema in (runtime_schema, cases_schema, fixtures_schema):
    Draft202012Validator.check_schema(schema)

Draft202012Validator(runtime_schema).validate(runtime)
Draft202012Validator(cases_schema).validate(cases)
Draft202012Validator(fixtures_schema).validate(fixtures)

task = next(item for item in programme["tasks"] if item["task_id"] == "AX-GE2E-P06-T01")
assert task["state"] == "BLOCKED"
assert task["dependencies"]["tasks"] == ["AX-GE2E-P05-T01"]
assert task["dependencies"]["phases"] == ["P05"]
assert task["acceptance_evidence"][0]["status"] == "MISSING"

dependency = runtime["dependency_status"]
assert dependency["p05_engineering_head"] == (
    "07de87e4ff79b19110394c8901db6a98e0be87b2"
)
assert dependency["p05_engineering_evidence_ready"] is True
for key in (
    "p05_canonical_activation_authorised",
    "p04_canonical_activation_authorised",
    "p03_canonical_activation_authorised",
    "p02_canonical_activation_authorised",
    "p01_dependency_satisfied",
    "merge_to_main_allowed",
):
    assert dependency[key] is False
assert runtime["canonical_activation_authorised"] is False
assert runtime["acceptance_gate"]["current_decision"] == (
    "NOT_READY_FOR_CANONICAL_ACTIVATION"
)

expected_languages = ["en", "es", "fr", "de", "pt", "it"]
actual_languages = [
    item["language_tag"] for item in runtime["language_profile"]["languages"]
]
assert actual_languages == expected_languages
assert all(validate_language_tag(item) for item in actual_languages)
assert len(runtime["language_profile"]["parity_dimensions"]) == 12
assert len(runtime["document_pipeline"]["stages"]) == 9
assert len(runtime["anchor_contract"]["anchor_types"]) == 6
assert runtime["language_profile"]["source_native_text_immutable"] is True
assert runtime["language_profile"]["translation_is_legal_equivalence"] is False

rights = runtime["rights_dimensions"]
assert rights == p03["source_rights_enforcement_contract"]["required_rights_dimensions"]
assert rights == p04["source_profile_contract"]["rights_dimensions"]
assert rights == p05["rights_dimensions"]
assert len(rights) == 10

assert fixtures["languages"] == expected_languages
assert len(fixtures["templates"]) == 5
assert fixtures["invariants"]["canonical_write"] is False
assert fixtures["invariants"]["source_text_preserved"] is True
assert fixtures["invariants"]["document_version_pinned"] is True
fixture_count = len(fixtures["languages"]) * len(fixtures["templates"])
assert fixture_count == 30

assert cases["languages"] == expected_languages
assert len(cases["language_vectors"]) == 7
assert len(cases["cross_document_vectors"]) == 12
assert cases["invariants"]["canonical_delta"] == 0
assert cases["invariants"]["source_text_preserved"] is True
case_count = (
    len(cases["languages"]) * len(cases["language_vectors"])
    + len(cases["cross_document_vectors"])
)
assert case_count == 54

preserved = preserve_source_text("original", "translation")
assert preserved["source_text"] == "original"
assert preserved["translated_text"] == "translation"
assert ocr_confidence_decision(Decimal("0.91")) == "CANDIDATE"
assert ocr_confidence_decision(Decimal("0.80")) == "REVIEW_REQUIRED"
assert ocr_confidence_decision(Decimal("0.70")) == "QUARANTINE"
assert validate_anchor("v2", "sha256:a", "v2", "sha256:a", True, True) == "RESOLVED"
assert validate_anchor("v2", "sha256:a", "v1", "sha256:a", True, True) == "INVALID"
dimension_results = {
    dimension: "MATCH"
    for dimension in runtime["semantic_parity_contract"]["critical_dimensions"]
}
assert semantic_parity_decision(dimension_results) == "PASS"
dimension_results["negation"] = "MISMATCH"
assert semantic_parity_decision(dimension_results) == "DENY"
dimension_results["negation"] = "UNKNOWN"
assert semantic_parity_decision(dimension_results) == "REVIEW_REQUIRED"
assert least_document_authority(
    ["HUMAN_REVIEWED", "TRANSLATION_CANDIDATE", "ADMITTED"]
) == "TRANSLATION_CANDIDATE"
assert may_write_document_canonical("SEMANTIC_MODEL", True) is False
assert may_write_document_canonical(
    "INDEPENDENT_ADMISSION_RUNTIME", True
) is True
assert may_write_document_canonical(
    "INDEPENDENT_ADMISSION_RUNTIME", False
) is False
assert parse_localized_decimal("1.234,56", "es") == Decimal("1234.56")
assert parse_localized_decimal("1,234.56", "en") == Decimal("1234.56")
assert preserve_unknown(None, "UNKNOWN") == (None, "UNKNOWN")

result = {
    "status": "PASS",
    "task_id": "AX-GE2E-P06-T01",
    "languages": len(actual_languages),
    "parity_dimensions": len(runtime["language_profile"]["parity_dimensions"]),
    "pipeline_stages": len(runtime["document_pipeline"]["stages"]),
    "extraction_modes": len(runtime["extraction_contract"]["modes"]),
    "anchor_types": len(runtime["anchor_contract"]["anchor_types"]),
    "rights_dimensions": len(rights),
    "conformance_fixtures": fixture_count,
    "adversarial_cases": case_count,
    "canonical_activation_authorised": runtime[
        "canonical_activation_authorised"
    ],
    "p05_canonical_activation_authorised": dependency[
        "p05_canonical_activation_authorised"
    ],
    "p04_canonical_activation_authorised": dependency[
        "p04_canonical_activation_authorised"
    ],
    "p03_canonical_activation_authorised": dependency[
        "p03_canonical_activation_authorised"
    ],
    "p02_canonical_activation_authorised": dependency[
        "p02_canonical_activation_authorised"
    ],
    "p01_dependency_satisfied": dependency["p01_dependency_satisfied"],
}
print(json.dumps(result, sort_keys=True))
