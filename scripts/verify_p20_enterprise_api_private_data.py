#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/enterprise"
SCHEMAS = ROOT / "schemas"
BASE = "3136579a4da91cd79c4cfdcd4b28b4a324565226"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def blob(path: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", f"{BASE}:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def reference() -> ModuleType:
    path = ROOT / "scripts/p20_enterprise_reference.py"
    spec = importlib.util.spec_from_file_location("p20_ref", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runtime = load(DATA / "enterprise-api-private-data-runtime.v0.1.json")
fixtures = load(DATA / "p20-conformance-fixtures.v0.1.json")
cases = load(DATA / "p20-adversarial-cases.v0.1.json")
for name, data in [
    ("runtime", runtime),
    ("fixtures", fixtures),
    ("cases", cases),
]:
    schema = load(SCHEMAS / f"enterprise-api-private-data-{name}.schema.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(data)

tasks = load(ROOT / "data/programmes/global-e2e-tasks-p20-p24.v1.4.json")
task = [
    item
    for item in tasks["tasks"]
    if item["task_id"] == "AX-GE2E-P20-T01"
]
assert len(task) == 1
assert task[0]["state"] == "BLOCKED"
assert task[0]["dependencies"]["tasks"] == ["AX-GE2E-P19-T01"]
objective = task[0]["objective"].lower()
for term in ["sso/scim", "private libraries", "api", "webhooks", "quotas"]:
    assert term in objective

bindings = [
    (
        "data/scenarios/scenarios-calibration-outcomes-runtime.v0.1.json",
        "9d57165eec0fafd6e2138f885c3d1a2959f50e6b",
    ),
    (
        "data/security/security-identity-rights-registry.v0.1.json",
        "4676a3e7d048d390327e40a75a3d7f0246671949",
    ),
    (
        "data/connectors/connector-sdk-registry.v0.1.json",
        "87d021ab5ea1c27b6cf64fcbedba92ee59ba6e6d",
    ),
    (
        "data/document-intelligence/"
        "multilingual-document-intelligence-runtime.v0.1.json",
        "5d12c3aa052f107ad02ad16abd282d87ef148c58",
    ),
    (
        "data/opportunity-operations/"
        "opportunity-operations-core-runtime.v0.1.json",
        "9bd23c7ea8753ad2bed180ae1405b75d0d9959ad",
    ),
]
assert runtime["baseline_sha"] == BASE
assert len(runtime["input_contract_bindings"]) == 5
for path, expected in bindings:
    assert blob(path) == expected

dependency = runtime["dependency_status"]
assert dependency["p19_engineering_head"] == BASE
assert dependency["p19_engineering_evidence_ready"]
for denied in [
    "p19_canonical_activation_authorised",
    "p01_dependency_satisfied",
    "all_transitive_dependencies_canonically_admitted",
    "merge_to_main_allowed",
]:
    assert not dependency[denied]

modules = runtime["domain_modules"]
assert len(modules) == 8
assert sum(len(item["record_types"]) for item in modules) == 32
assert sum(len(item["invariants"]) for item in modules) == 48
assert len(runtime["enterprise_lifecycle"]["states"]) == 12
assert len(runtime["operating_pipeline"]["stages"]) == 11
assert len(runtime["identity_modes"]) == 10
assert len(runtime["api_scope_classes"]) == 10
assert len(runtime["quota_dimensions"]) == 10
assert len(runtime["webhook_states"]) == 10
assert len(runtime["integration_types"]) == 10
assert len(runtime["residency_classes"]) == 10
assert len(runtime["authority_classes"]) == 8
assert len(runtime["risk_classes"]) == 10
assert len(runtime["readiness_gates"]) == 12
assert len(runtime["rights_dimensions"]) == 10
assert runtime["operating_pipeline"]["default_decision"] == "DENY"
assert runtime["operating_pipeline"]["indeterminate_as"] == "DENY"
assert (
    runtime["acceptance_gate"]["current_decision"]
    == "NOT_READY_FOR_CANONICAL_ACTIVATION"
)

fixture_count = len(fixtures["modules"]) * len(fixtures["fixture_classes"])
case_count = len(cases["modules"]) * len(cases["threats"])
assert fixture_count == 40
assert case_count == 72
for key in [
    "canonical_delta",
    "external_action_delta",
    "cross_tenant_disclosure_delta",
    "authority_elevation_delta",
    "model_training_delta",
]:
    assert fixtures["expected"][key] == 0
    assert cases["expected"][key] == 0
assert cases["expected"]["quota_bypass_delta"] == 0
assert cases["expected"]["decision"] == "DENY"

ref = reference()
login = ref.federated_login_decision(
    domain_verified=True,
    issuer_match=True,
    signature_valid=True,
    audience_valid=True,
    nonce_valid=True,
    assertion_fresh=True,
    principal_active=True,
    tenant_resolved_server_side=True,
)
assert login["decision"] == "ALLOW_AUTHENTICATED"
assert ref.federated_login_decision(
    domain_verified=True,
    issuer_match=True,
    signature_valid=True,
    audience_valid=True,
    nonce_valid=True,
    assertion_fresh=True,
    principal_active=True,
    tenant_resolved_server_side=False,
)["decision"] == "DENY"

assert ref.scim_mutation_decision(
    operation="UPDATE",
    client_active=True,
    target_tenant_match=True,
    mapping_human_approved=False,
    privileged_role_requested=True,
    deprovision_revokes_sessions=True,
)["reason"] == "PRIVILEGED_MAPPING_UNAPPROVED"

assert ref.private_library_access_decision(
    request_tenant_id="tenant-a",
    resource_tenant_id="tenant-b",
    workspace_match=True,
    classification_known=True,
    rights_active=True,
    purpose_allowed=True,
    residency_route_allowed=True,
    deletion_pending=False,
)["reason"] == "CROSS_TENANT_ACCESS"

api_allow = ref.api_authorisation_decision(
    credential_active=True,
    principal_active=True,
    requested_scope="PRIVATE_LIBRARY_READ",
    credential_scopes={"PRIVATE_LIBRARY_READ"},
    effective_capabilities={"private_library:read"},
    required_capability="private_library:read",
    resource_filter_match=True,
    tenant_resolved_server_side=True,
    rights_pass=True,
)
assert api_allow["decision"] == "ALLOW"
assert ref.api_authorisation_decision(
    credential_active=True,
    principal_active=True,
    requested_scope="AUDIT_READ",
    credential_scopes={"PRIVATE_LIBRARY_READ"},
    effective_capabilities={"audit:read"},
    required_capability="audit:read",
    resource_filter_match=True,
    tenant_resolved_server_side=True,
    rights_pass=True,
)["reason"] == "SCOPE_NOT_GRANTED"

reservation = ref.quota_reservation_decision(
    limit=100,
    used=50,
    reserved=10,
    requested=40,
)
assert reservation["decision"] == "RESERVE"
assert reservation["available"] == 0
assert ref.quota_reservation_decision(
    limit=100,
    used=70,
    reserved=20,
    requested=20,
)["reason"] == "QUOTA_EXHAUSTED"

payload = b'{"event_id":"evt-1","tenant_id":"tenant-a"}'
secret = b"not-a-real-secret"
digest = __import__("hmac").new(
    secret,
    payload,
    __import__("hashlib").sha256,
).hexdigest()
assert ref.verify_webhook_signature(
    secret=secret,
    canonical_payload=payload,
    supplied_hex_digest=digest,
)
assert ref.webhook_delivery_decision(
    signature_valid=True,
    timestamp_skew_seconds=10,
    maximum_skew_seconds=300,
    nonce_replayed=False,
    subscription_active=True,
    tenant_match=True,
    event_allowed=True,
   idempotency_key_present=True,
)["decision"] == "DELIVER_AT_LEAST_ONCE"
assert ref.webhook_delivery_decision(
    signature_valid=True,
    timestamp_skew_seconds=10,
    maximum_skew_seconds=300,
    nonce_replayed=True,
    subscription_active=True,
    tenant_match=True,
    event_allowed=True,
    idempotency_key_present=True,
)["reason"] == "NONCE_REPLAY"

assert ref.integration_activation_decision(
    installation_tenant_match=True,
    secret_reference_only=True,
    endpoint_allowlisted=True,
    egress_policy_pass=True,
    rights_pass=True,
    human_approval_current=True,
    source_admission_requested=True,
)["reason"] == "P20_HAS_NO_SOURCE_ADMISSION_AUTHORITY"

assert ref.support_access_decision(
    human_principal=True,
    ticket_reference_present=True,
    independent_approval=True,
    minimal_scope=True,
    short_expiry=True,
    strong_authentication=True,
    continuous_audit=True,
)["decision"] == "ALLOW_TIME_BOUNDED"

assert ref.max_promote_private_data_to_global_canonical(
    p20_authority="TYPED_HUMAN_APPROVAL",
    independent_admission_passed=True,
)["decision"] == "DENY"

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": "AX-GE2E-P20-T01",
            "input_contract_bindings": 5,
            "domain_modules": 8,
            "record_types": 32,
            "domain_invariants": 48,
            "lifecycle_states": 12,
            "pipeline_stages": 11,
            "readiness_gates": 12,
            "conformance_fixtures": fixture_count,
            "adversarial_cases": case_count,
            "canonical_activation_authorised": False,
        },
        sort_keys=True,
    )
)
