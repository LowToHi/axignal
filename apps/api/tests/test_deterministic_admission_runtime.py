from __future__ import annotations

from uuid import UUID

import pytest

from axignal_api.admission_queue import AdmissionReviewJob
from axignal_api.admission_repository import AdmissionRepository

TENANT_ID = UUID("77777777-7777-4777-8777-777777777777")
RUN_ID = UUID("88888888-8888-4888-8888-888888888888")
HANDOFF_ID = UUID("99999999-9999-4999-8999-999999999999")
CANDIDATE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
EVIDENCE_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
HASH = "sha256:" + ("a" * 64)


def test_admission_job_round_trip_and_policy_lock() -> None:
    job = AdmissionReviewJob(
        admission_handoff_id=HANDOFF_ID,
        research_run_id=RUN_ID,
        tenant_id=TENANT_ID,
        expected_package_hash=HASH,
    )
    assert AdmissionReviewJob.from_payload(job.as_payload()) == job
    payload = job.as_payload() | {"policy_version": "untrusted@9"}
    with pytest.raises(ValueError, match="policy version"):
        AdmissionReviewJob.from_payload(payload)


def _fixture(value: str = "2.3") -> tuple[dict, dict, dict, dict, dict, dict]:
    fragment = {
        "fragment_id": "frag_gdp",
        "text_content": (
            "The World Bank's Russia Economic Report records that real GDP growth "
            "reached 2.3 percent in 2018."
        ),
        "content_hash": HASH,
    }
    evidence = {
        EVIDENCE_ID: {
            "evidence_id": EVIDENCE_ID,
            "evidence_key": "ev_gdp",
            "payload": {
                "fragment_id": "frag_gdp",
                "quote_hash": HASH,
                "text": fragment["text_content"],
            },
            "content_hash": "sha256:" + ("b" * 64),
            "rights_status": "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
        }
    }
    packaged_candidate = {
        "persistent_candidate_claim_id": str(CANDIDATE_ID),
        "evidence_keys": ["ev_gdp"],
        "subject_id": "geo_country_rus",
        "predicate": "real_gdp_growth_annual_pct",
        "relationship": "SUPPORTING",
    }
    candidate = {
        "candidate_claim_id": CANDIDATE_ID,
        "kind": "FACT",
        "subject_id": "geo_country_rus",
        "predicate": "real_gdp_growth_annual_pct",
        "object_value": {
            "value": value,
            "unit": "percent_annual",
            "period": "2018",
        },
        "producer_type": "LOCAL_MODEL",
        "evidence_ids": [EVIDENCE_ID],
    }
    package = {
        "document": {"content_hash": "sha256:" + ("c" * 64)},
        "candidate_claims": [packaged_candidate],
        "evidence": [{
            "evidence_key": "ev_gdp",
            "fragment_id": "frag_gdp",
            "quote_hash": HASH,
            "content_hash": "sha256:" + ("b" * 64),
        }],
    }
    source = {
        "admission_state": "ADMITTED",
        "kill_switch": False,
        "commercial_use": True,
        "redistribution": True,
        "rights_status": "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
    }
    source_object = {"content_hash": package["document"]["content_hash"]}
    return package, candidate, packaged_candidate, source, source_object, {
        "fragments": {"frag_gdp": fragment},
        "evidence": evidence,
    }


def test_numeric_fact_is_rederived_without_model_authority() -> None:
    package, candidate, packaged, source, source_object, records = _fixture()
    decision = AdmissionRepository._evaluate_candidate(
        package=package,
        candidate=candidate,
        packaged_candidate=packaged,
        source=source,
        source_object=source_object,
        fragments=records["fragments"],
        evidence=records["evidence"],
    )
    assert decision["outcome"] == "ADMITTED_REDERIVED"
    assert decision["rederived"]["object_value"] == {
        "value": "2.3",
        "unit": "percent_annual",
        "period": "2018",
    }
    assert decision["gate_results"]["VALUE_UNIT_PERIOD_EXACT_MATCH"] is True


def test_model_value_mismatch_is_rejected() -> None:
    package, candidate, packaged, source, source_object, records = _fixture("2.4")
    decision = AdmissionRepository._evaluate_candidate(
        package=package,
        candidate=candidate,
        packaged_candidate=packaged,
        source=source,
        source_object=source_object,
        fragments=records["fragments"],
        evidence=records["evidence"],
    )
    assert decision["outcome"] == "REJECTED"
    assert decision["gate_results"]["VALUE_UNIT_PERIOD_EXACT_MATCH"] is False


def test_limitation_requires_human_review() -> None:
    package, candidate, packaged, source, source_object, records = _fixture()
    candidate["kind"] = "LIMITATION"
    decision = AdmissionRepository._evaluate_candidate(
        package=package,
        candidate=candidate,
        packaged_candidate=packaged,
        source=source,
        source_object=source_object,
        fragments=records["fragments"],
        evidence=records["evidence"],
    )
    assert decision["outcome"] == "HUMAN_REVIEW_REQUIRED"
    assert decision["rederived"] is None


def test_model_unit_mismatch_is_rejected() -> None:
    package, candidate, packaged, source, source_object, records = _fixture()
    candidate["object_value"]["unit"] = "percentage_points"
    decision = AdmissionRepository._evaluate_candidate(
        package=package,
        candidate=candidate,
        packaged_candidate=packaged,
        source=source,
        source_object=source_object,
        fragments=records["fragments"],
        evidence=records["evidence"],
    )
    assert decision["outcome"] == "REJECTED"
    assert decision["gate_results"]["VALUE_UNIT_PERIOD_EXACT_MATCH"] is False


def test_model_period_mismatch_is_rejected() -> None:
    package, candidate, packaged, source, source_object, records = _fixture()
    candidate["object_value"]["period"] = "2019"
    decision = AdmissionRepository._evaluate_candidate(
        package=package,
        candidate=candidate,
        packaged_candidate=packaged,
        source=source,
        source_object=source_object,
        fragments=records["fragments"],
        evidence=records["evidence"],
    )
    assert decision["outcome"] == "REJECTED"
    assert decision["gate_results"]["VALUE_UNIT_PERIOD_EXACT_MATCH"] is False
