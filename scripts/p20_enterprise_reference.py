#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def federated_login_decision(
    *,
    domain_verified: bool,
    issuer_match: bool,
    signature_valid: bool,
    audience_valid: bool,
    nonce_valid: bool,
    assertion_fresh: bool,
    principal_active: bool,
    tenant_resolved_server_side: bool,
) -> dict[str, str]:
    checks = {
        "DOMAIN_NOT_VERIFIED": domain_verified,
        "ISSUER_MISMATCH": issuer_match,
        "SIGNATURE_INVALID": signature_valid,
        "AUDIENCE_INVALID": audience_valid,
        "NONCE_INVALID": nonce_valid,
        "ASSERTION_STALE": assertion_fresh,
        "PRINCIPAL_INACTIVE": principal_active,
        "SERVER_TENANT_UNRESOLVED": tenant_resolved_server_side,
    }
    for reason, passed in checks.items():
        if not passed:
            return {"decision": "DENY", "reason": reason}
    return {"decision": "ALLOW_AUTHENTICATED", "reason": "FEDERATION_VERIFIED"}


def scim_mutation_decision(
    *,
    operation: str,
    client_active: bool,
    target_tenant_match: bool,
    mapping_human_approved: bool,
    privileged_role_requested: bool,
    deprovision_revokes_sessions: bool,
) -> dict[str, str]:
    if not client_active:
        return {"decision": "DENY", "reason": "SCIM_CLIENT_INACTIVE"}
    if not target_tenant_match:
        return {"decision": "DENY", "reason": "CROSS_TENANT_TARGET"}
    if privileged_role_requested and not mapping_human_approved:
        return {"decision": "DENY", "reason": "PRIVILEGED_MAPPING_UNAPPROVED"}
    if operation == "DEPROVISION" and not deprovision_revokes_sessions:
        return {"decision": "DENY", "reason": "SESSION_REVOCATION_REQUIRED"}
    if operation not in {"CREATE", "UPDATE", "SUSPEND", "DEPROVISION"}:
        return {"decision": "DENY", "reason": "UNSUPPORTED_OPERATION"}
    return {"decision": "ALLOW_BOUNDED_MUTATION", "reason": "SCIM_POLICY_PASS"}


def private_library_access_decision(
    *,
    request_tenant_id: str,
    resource_tenant_id: str,
    workspace_match: bool,
    classification_known: bool,
    rights_active: bool,
    purpose_allowed: bool,
    residency_route_allowed: bool,
    deletion_pending: bool,
) -> dict[str, str]:
    if request_tenant_id != resource_tenant_id:
        return {"decision": "DENY", "reason": "CROSS_TENANT_ACCESS"}
    checks = {
        "WORKSPACE_SCOPE_MISMATCH": workspace_match,
        "CLASSIFICATION_UNKNOWN": classification_known,
        "RIGHTS_INACTIVE": rights_active,
        "PURPOSE_NOT_ALLOWED": purpose_allowed,
        "RESIDENCY_ROUTE_DENIED": residency_route_allowed,
        "DELETION_PENDING": not deletion_pending,
    }
    for reason, passed in checks.items():
        if not passed:
            return {"decision": "DENY", "reason": reason}
    return {"decision": "ALLOW_PRIVATE_ONLY", "reason": "PRIVATE_SCOPE_PASS"}


def api_authorisation_decision(
    *,
    credential_active: bool,
    principal_active: bool,
    requested_scope: str,
    credential_scopes: set[str],
    effective_capabilities: set[str],
    required_capability: str,
    resource_filter_match: bool,
    tenant_resolved_server_side: bool,
    rights_pass: bool,
) -> dict[str, str]:
    if not credential_active or not principal_active:
        return {"decision": "DENY", "reason": "INACTIVE_CREDENTIAL_OR_PRINCIPAL"}
    if requested_scope not in credential_scopes:
        return {"decision": "DENY", "reason": "SCOPE_NOT_GRANTED"}
    if required_capability not in effective_capabilities:
        return {"decision": "DENY", "reason": "CAPABILITY_NOT_EFFECTIVE"}
    if not resource_filter_match:
        return {"decision": "DENY", "reason": "RESOURCE_FILTER_MISMATCH"}
    if not tenant_resolved_server_side:
        return {"decision": "DENY", "reason": "SERVER_TENANT_UNRESOLVED"}
    if not rights_pass:
        return {"decision": "DENY", "reason": "RIGHTS_DENY"}
    return {"decision": "ALLOW", "reason": "SCOPE_CAPABILITY_RIGHTS_INTERSECTION"}


def quota_reservation_decision(
    *,
    limit: int,
    used: int,
    reserved: int,
    requested: int,
    idempotency_reused: bool = False,
) -> dict[str, int | str]:
    values = (limit, used, reserved, requested)
    if any(value < 0 for value in values):
        return {"decision": "DENY", "reason": "INVALID_QUOTA_VALUE", "available": 0}
    available = max(limit - used - reserved, 0)
    if idempotency_reused:
        return {
            "decision": "REUSE_EXISTING_RESERVATION",
            "reason": "IDEMPOTENT_RETRY",
            "available": available,
        }
    if requested > available:
        return {"decision": "DENY", "reason": "QUOTA_EXHAUSTED", "available": available}
    return {
        "decision": "RESERVE",
        "reason": "CAPACITY_AVAILABLE",
        "available": available - requested,
    }


def verify_webhook_signature(
    *,
    secret: bytes,
    canonical_payload: bytes,
    supplied_hex_digest: str,
) -> bool:
    expected = hmac.new(secret, canonical_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, supplied_hex_digest)


def webhook_delivery_decision(
    *,
    signature_valid: bool,
    timestamp_skew_seconds: int,
    maximum_skew_seconds: int,
    nonce_replayed: bool,
    subscription_active: bool,
    tenant_match: bool,
    event_allowed: bool,
    idempotency_key_present: bool,
) -> dict[str, str]:
    if not signature_valid:
        return {"decision": "DENY", "reason": "SIGNATURE_INVALID"}
    if abs(timestamp_skew_seconds) > maximum_skew_seconds:
        return {"decision": "DENY", "reason": "TIMESTAMP_OUTSIDE_WINDOW"}
    if nonce_replayed:
        return {"decision": "DENY", "reason": "NONCE_REPLAY"}
    checks = {
        "SUBSCRIPTION_INACTIVE": subscription_active,
        "TENANT_MISMATCH": tenant_match,
        "EVENT_NOT_ALLOWED": event_allowed,
        "IDEMPOTENCY_KEY_MISSING": idempotency_key_present,
    }
    for reason, passed in checks.items():
        if not passed:
            return {"decision": "DENY", "reason": reason}
    return {"decision": "DELIVER_AT_LEAST_ONCE", "reason": "WEBHOOK_POLICY_PASS"}


def integration_activation_decision(
    *,
    installation_tenant_match: bool,
    secret_reference_only: bool,
    endpoint_allowlisted: bool,
    egress_policy_pass: bool,
    rights_pass: bool,
    human_approval_current: bool,
    source_admission_requested: bool,
) -> dict[str, str]:
    if source_admission_requested:
        return {"decision": "DENY", "reason": "P20_HAS_NO_SOURCE_ADMISSION_AUTHORITY"}
    checks = {
        "INSTALLATION_TENANT_MISMATCH": installation_tenant_match,
        "SECRET_REFERENCE_REQUIRED": secret_reference_only,
        "ENDPOINT_NOT_ALLOWLISTED": endpoint_allowlisted,
        "EGRESS_POLICY_DENY": egress_policy_pass,
        "RIGHTS_DENY": rights_pass,
        "HUMAN_APPROVAL_REQUIRED": human_approval_current,
    }
    for reason, passed in checks.items():
        if not passed:
            return {"decision": "DENY", "reason": reason}
    return {"decision": "ALLOW_PRIVATE_INTEGRATION", "reason": "INTEGRATION_GATE_PASS"}


def support_access_decision(
    *,
    human_principal: bool,
    ticket_reference_present: bool,
    independent_approval: bool,
    minimal_scope: bool,
    short_expiry: bool,
    strong_authentication: bool,
    continuous_audit: bool,
) -> dict[str, str]:
    checks = {
        "HUMAN_PRINCIPAL_REQUIRED": human_principal,
        "TICKET_REFERENCE_REQUIRED": ticket_reference_present,
        "INDEPENDENT_APPROVAL_REQUIRED": independent_approval,
        "MINIMAL_SCOPE_REQUIRED": minimal_scope,
        "SHORT_EXPIRY_REQUIRED": short_expiry,
        "STRONG_AUTHENTICATION_REQUIRED": strong_authentication,
        "CONTINUOUS_AUDIT_REQUIRED": continuous_audit,
    }
    for reason, passed in checks.items():
        if not passed:
            return {"decision": "DENY", "reason": reason}
    return {"decision": "ALLOW_TIME_BOUNDED", "reason": "SUPPORT_ACCESS_PASS"}


def may_promote_private_data_to_global_canonical(
    *,
    p20_authority: str,
    independent_admission_passed: bool,
) -> dict[str, str]:
    if p20_authority != "INDEPENDENT_CANONICAL_ADMISSION_RUNTIME":
        return {"decision": "DENY", "reason": "INDEPENDENT_ADMISSION_REQUIRED"}
    if not independent_admission_passed:
        return {"decision": "DENY", "reason": "ADMISSION_GATE_NOT_PASSED"}
    return {"decision": "ALLOW_ELIGIBLE_HANDOFF", "reason": "OUTSIDE_P20_AUTHORITY"}
