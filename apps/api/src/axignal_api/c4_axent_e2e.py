from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from axignal_api.identity import build_identity_assertion

API_BASE_URL = "http://127.0.0.1:8000"
STATE_PATH = Path("/var/lib/axignal/objects/c4-axent-e2e-state.json")
OTHER_TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
SAME_TENANT_OTHER_SUBJECT = "usr_c4_same_tenant_other"
OTHER_TENANT_SUBJECT = "usr_c4_other_tenant"


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _content_hash(content: str) -> str:
    return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _identity_assertion(*, subject: str, email: str, tenant_id: UUID) -> str:
    return build_identity_assertion(
        secret=_required_env("AXIGNAL_IDENTITY_ASSERTION_SECRET"),
        subject=subject,
        email=email,
        tenant_id=tenant_id,
        ttl_seconds=900,
    )


def _request_json(
    *,
    assertion: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None
    headers = {
        "accept": "application/json",
        "X-AXIGNAL-Identity-Assertion": assertion,
    }
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["content-type"] = "application/json"
    request = urllib.request.Request(
        f"{API_BASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
    try:
        body = json.loads(raw.decode("utf-8")) if raw else {}
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Non-JSON response for {method} {path}: {status}") from exc
    if not isinstance(body, dict):
        raise RuntimeError(f"Invalid JSON object for {method} {path}: {status}")
    return status, body


def _expect_status(
    *,
    assertion: str,
    method: str,
    path: str,
    expected: int,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status, body = _request_json(
        assertion=assertion,
        method=method,
        path=path,
        payload=payload,
    )
    if status != expected:
        safe_body = json.dumps(body, sort_keys=True)[:500]
        raise RuntimeError(
            f"Unexpected status for {method} {path}: {status}, expected {expected}; "
            f"body={safe_body}"
        )
    return body


def _seed_active_tenants(dsn: str, tenant_ids: tuple[UUID, ...]) -> None:
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        for tenant_id in tenant_ids:
            cursor.execute(
                """
                INSERT INTO tenant_private.workspace_lifecycle (
                  tenant_id,
                  state,
                  policy_version,
                  created_at,
                  updated_at
                ) VALUES (%s, 'ACTIVE', 'c4-research-axent-e2e-v1', now(), now())
                ON CONFLICT (tenant_id) DO UPDATE
                SET state = 'ACTIVE',
                    policy_version = EXCLUDED.policy_version,
                    read_only_at = NULL,
                    deletion_requested_at = NULL,
                    purged_at = NULL,
                    updated_at = now()
                """,
                (tenant_id,),
            )


def _latest_completed_research_run(dsn: str, tenant_id: UUID) -> UUID:
    with (
        psycopg.connect(dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """
            SELECT research_run_id
            FROM tenant_private.research_runs
            WHERE tenant_id = %s
              AND state = 'COMPLETED'
            ORDER BY updated_at DESC, research_run_id DESC
            LIMIT 1
            """,
            (tenant_id,),
        )
        row = cursor.fetchone()
    if row is None:
        raise RuntimeError("A completed ResearchRun is required before C4 AXENT E2E")
    return row["research_run_id"]


def _research_context(research: dict[str, Any]) -> dict[str, Any]:
    evidence = research.get("evidence")
    canonical_claims = research.get("canonical_claims")
    dossier = research.get("dossier")
    if research.get("state") != "COMPLETED":
        raise RuntimeError("ResearchRun must be completed")
    if research.get("synthetic") is not False:
        raise RuntimeError("C4 requires a non-synthetic ResearchRun")
    if not isinstance(evidence, list) or not evidence:
        raise RuntimeError("ResearchRun must contain admitted evidence")
    if not isinstance(canonical_claims, list) or not canonical_claims:
        raise RuntimeError("ResearchRun must contain canonical claims")
    if not isinstance(dossier, dict):
        raise RuntimeError("ResearchRun must contain a dossier")

    first_evidence = evidence[0]
    first_claim = canonical_claims[0]
    attribution = dossier.get("attribution")
    if not isinstance(first_evidence, dict) or not isinstance(first_claim, dict):
        raise RuntimeError("ResearchRun evidence contract is invalid")
    if not isinstance(attribution, dict):
        raise RuntimeError("ResearchRun attribution contract is invalid")

    source_id = attribution.get("source_id") or first_evidence.get("source_id")
    if not isinstance(source_id, str) or not source_id:
        raise RuntimeError("ResearchRun source attribution is missing")

    statement = str(first_claim.get("statement", ""))[:1_200]
    return {
        "schema": "axignal.axent-research-context.v1",
        "research_run_id": str(research["research_run_id"]),
        "research_state": research["state"],
        "source_id": source_id,
        "evidence": {
            "evidence_id": str(first_evidence.get("evidence_id", "")),
            "title": str(first_evidence.get("title", ""))[:500],
            "relationship": str(first_evidence.get("relationship", ""))[:120],
            "predicate": str(first_evidence.get("predicate", ""))[:200],
            "rights_status": str(first_evidence.get("rights_status", ""))[:120],
            "provisional": bool(first_evidence.get("provisional", False)),
        },
        "canonical_claim": {
            "canonical_claim_id": str(first_claim.get("canonical_claim_id", "")),
            "fingerprint": str(first_claim.get("fingerprint", ""))[:200],
            "statement": statement,
            "state": str(first_claim.get("state", ""))[:120],
            "admitted_by": str(first_claim.get("admitted_by", ""))[:120],
        },
    }


def _append_message(
    *,
    assertion: str,
    conversation_id: str,
    request_id: str,
    role: str,
    content: str,
) -> dict[str, Any]:
    return _expect_status(
        assertion=assertion,
        method="POST",
        path=f"/v1/subscriber-workspace/axent/conversations/{conversation_id}/messages",
        expected=201,
        payload={
            "request_id": request_id,
            "role": role,
            "content": content,
        },
    )


def _verify_ciphertext(
    *,
    dsn: str,
    tenant_id: UUID,
    conversation_id: UUID,
    expected_messages: list[dict[str, str]],
) -> None:
    with (
        psycopg.connect(dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """
            SELECT ordinal, message_role, ciphertext, content_hash
            FROM tenant_private.axent_messages
            WHERE tenant_id = %s AND conversation_id = %s
            ORDER BY ordinal
            """,
            (tenant_id, conversation_id),
        )
        rows = cursor.fetchall()
        cursor.execute(
            """
            SELECT count(*) AS count
            FROM tenant_private.axent_message_receipts
            WHERE tenant_id = %s AND conversation_id = %s
            """,
            (tenant_id, conversation_id),
        )
        receipt_count = int(cursor.fetchone()["count"])

    if len(rows) != len(expected_messages):
        raise RuntimeError("AXENT encrypted message count does not match the API transcript")
    if receipt_count != len(expected_messages):
        raise RuntimeError("AXENT idempotency receipt count is invalid")

    for row, expected in zip(rows, expected_messages, strict=True):
        ciphertext = bytes(row["ciphertext"])
        plaintext = expected["content"].encode("utf-8")
        if plaintext in ciphertext:
            raise RuntimeError("AXENT ciphertext contains plaintext content")
        if row["message_role"] != expected["role"]:
            raise RuntimeError("AXENT encrypted message role is invalid")
        if row["content_hash"] != _content_hash(expected["content"]):
            raise RuntimeError("AXENT encrypted message hash is invalid")


def _app_function(
    *,
    dsn: str,
    tenant_id: UUID,
    statement: str,
    parameters: tuple[Any, ...],
) -> dict[str, Any]:
    with (
        psycopg.connect(dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SET LOCAL ROLE axignal_app")
        cursor.execute(
            "SELECT set_config('app.tenant_id', %s, true)",
            (str(tenant_id),),
        )
        cursor.execute(statement, parameters)
        row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Tenant-scoped AXENT function returned no row")
    return row


def _purge_due(dsn: str) -> int:
    with (
        psycopg.connect(dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SET LOCAL ROLE axignal_retention_worker")
        cursor.execute(
            """
            SELECT tenant_private.purge_due_axent_conversations(
              'c4-e2e-retention-worker',
              now() + interval '5 seconds'
            ) AS count
            """
        )
        row = cursor.fetchone()
    return int(row["count"] if row else 0)


def _conversation_exists(dsn: str, tenant_id: UUID, conversation_id: UUID) -> bool:
    with psycopg.connect(dsn) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT EXISTS (
              SELECT 1
              FROM tenant_private.axent_conversations
              WHERE tenant_id = %s AND conversation_id = %s
            )
            """,
            (tenant_id, conversation_id),
        )
        row = cursor.fetchone()
    return bool(row and row[0])


def prepare() -> dict[str, Any]:
    dsn = _required_env("AXIGNAL_DATABASE_URL")
    build_sha = _required_env("AXIGNAL_BUILD_SHA")
    tenant_id = UUID(_required_env("AXIGNAL_AUTH_TENANT_ID"))
    subject = _required_env("AXIGNAL_AUTH_SUBJECT")
    email = os.environ.get("AXIGNAL_AUTH_EMAIL", "pilot@example.test").strip().lower()

    _seed_active_tenants(dsn, (tenant_id, OTHER_TENANT_ID))
    owner = _identity_assertion(subject=subject, email=email, tenant_id=tenant_id)
    same_tenant_other = _identity_assertion(
        subject=SAME_TENANT_OTHER_SUBJECT,
        email="same-tenant-other@example.test",
        tenant_id=tenant_id,
    )
    other_tenant = _identity_assertion(
        subject=OTHER_TENANT_SUBJECT,
        email="other-tenant@example.test",
        tenant_id=OTHER_TENANT_ID,
    )

    research_run_id = _latest_completed_research_run(dsn, tenant_id)
    research = _expect_status(
        assertion=owner,
        method="GET",
        path=f"/v1/research-runs/{research_run_id}",
        expected=200,
    )
    context = _research_context(research)
    system_content = json.dumps(context, separators=(",", ":"), sort_keys=True)
    if len(system_content) > 4_000:
        raise RuntimeError("Bounded AXENT research context exceeds the message contract")

    run_token = research_run_id.hex
    create_request_id = f"axent_req_c4_create_{run_token}"
    create_payload = {
        "request_id": create_request_id,
        "title": f"C4 research {run_token[:12]}",
        "retention_class": "EPHEMERAL_30D",
    }
    created = _expect_status(
        assertion=owner,
        method="POST",
        path="/v1/subscriber-workspace/axent/conversations",
        expected=201,
        payload=create_payload,
    )
    replayed = _expect_status(
        assertion=owner,
        method="POST",
        path="/v1/subscriber-workspace/axent/conversations",
        expected=201,
        payload=create_payload,
    )
    conversation_id = str(created["conversation_id"])
    if replayed.get("conversation_id") != conversation_id:
        raise RuntimeError("Conversation idempotency replay created another conversation")

    conflict_payload = dict(create_payload)
    conflict_payload["title"] = "C4 idempotency conflict"
    _expect_status(
        assertion=owner,
        method="POST",
        path="/v1/subscriber-workspace/axent/conversations",
        expected=409,
        payload=conflict_payload,
    )

    system_request_id = f"axent_req_c4_system_{run_token}"
    system_message = _append_message(
        assertion=owner,
        conversation_id=conversation_id,
        request_id=system_request_id,
        role="SYSTEM",
        content=system_content,
    )
    system_replay = _append_message(
        assertion=owner,
        conversation_id=conversation_id,
        request_id=system_request_id,
        role="SYSTEM",
        content=system_content,
    )
    if system_message.get("message_id") != system_replay.get("message_id"):
        raise RuntimeError("Message idempotency replay created another message")
    _expect_status(
        assertion=owner,
        method="POST",
        path=f"/v1/subscriber-workspace/axent/conversations/{conversation_id}/messages",
        expected=409,
        payload={
            "request_id": system_request_id,
            "role": "SYSTEM",
            "content": f"{system_content} conflict",
        },
    )

    user_content = (
        "Explain the AXIGNAL evidence and admitted claim from this completed "
        f"ResearchRun: {research_run_id}."
    )
    assistant_content = (
        "C4 E2E observation: the conversation is linked to a completed, "
        "source-attributed ResearchRun. This deterministic test message does not "
        "approve, submit or extend the admitted claim."
    )
    _append_message(
        assertion=owner,
        conversation_id=conversation_id,
        request_id=f"axent_req_c4_user_{run_token}",
        role="USER",
        content=user_content,
    )
    _append_message(
        assertion=owner,
        conversation_id=conversation_id,
        request_id=f"axent_req_c4_assistant_{run_token}",
        role="ASSISTANT",
        content=assistant_content,
    )

    owner_export = _expect_status(
        assertion=owner,
        method="GET",
        path=f"/v1/subscriber-workspace/axent/conversations/{conversation_id}",
        expected=200,
    )
    if len(owner_export.get("messages", [])) != 3:
        raise RuntimeError("Owner export does not contain the complete AXENT transcript")

    same_tenant_list = _expect_status(
        assertion=same_tenant_other,
        method="GET",
        path="/v1/subscriber-workspace/axent/conversations",
        expected=200,
    )
    visible_ids = {
        str(item.get("conversation_id"))
        for item in same_tenant_list.get("conversations", [])
        if isinstance(item, dict)
    }
    if conversation_id in visible_ids:
        raise RuntimeError("AXENT leaked a conversation to another same-tenant identity")
    _expect_status(
        assertion=same_tenant_other,
        method="GET",
        path=f"/v1/subscriber-workspace/axent/conversations/{conversation_id}",
        expected=404,
    )
    _expect_status(
        assertion=other_tenant,
        method="GET",
        path=f"/v1/subscriber-workspace/axent/conversations/{conversation_id}",
        expected=404,
    )

    expected_messages = [
        {"role": "SYSTEM", "content": system_content},
        {"role": "USER", "content": user_content},
        {"role": "ASSISTANT", "content": assistant_content},
    ]
    _verify_ciphertext(
        dsn=dsn,
        tenant_id=tenant_id,
        conversation_id=UUID(conversation_id),
        expected_messages=expected_messages,
    )

    state = {
        "schema": "axignal.c4-research-axent-e2e-state.v1",
        "build_sha": build_sha,
        "tenant_id": str(tenant_id),
        "owner_subject": subject,
        "owner_email": email,
        "research_run_id": str(research_run_id),
        "source_id": context["source_id"],
        "evidence_id": context["evidence"]["evidence_id"],
        "canonical_claim_id": context["canonical_claim"]["canonical_claim_id"],
        "conversation_id": conversation_id,
        "expected_messages": [
            {"role": item["role"], "content_hash": _content_hash(item["content"])}
            for item in expected_messages
        ],
        "prepared_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    _atomic_json(STATE_PATH, state)
    return {
        "status": "PASS",
        "phase": "PREPARE_BEFORE_RESTART",
        "marker": "AX_C4_RESEARCH_AXENT_PREPARE_PASS",
        "exact_head_sha": build_sha,
        "research_run_id": str(research_run_id),
        "source_id": context["source_id"],
        "conversation_id": conversation_id,
        "research_context_persisted": True,
        "create_idempotency": True,
        "message_idempotency": True,
        "same_tenant_identity_isolation": True,
        "cross_tenant_isolation": True,
        "ciphertext_verified": True,
        "state_path": str(STATE_PATH),
    }


def verify() -> dict[str, Any]:
    if not STATE_PATH.is_file():
        raise RuntimeError("C4 persisted state is missing after restart")
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise RuntimeError("C4 persisted state is invalid")

    dsn = _required_env("AXIGNAL_DATABASE_URL")
    build_sha = _required_env("AXIGNAL_BUILD_SHA")
    if state.get("build_sha") != build_sha:
        raise RuntimeError("C4 state was produced by a different exact head")

    tenant_id = UUID(str(state["tenant_id"]))
    conversation_id = UUID(str(state["conversation_id"]))
    owner = _identity_assertion(
        subject=str(state["owner_subject"]),
        email=str(state["owner_email"]),
        tenant_id=tenant_id,
    )
    exported = _expect_status(
        assertion=owner,
        method="GET",
        path=f"/v1/subscriber-workspace/axent/conversations/{conversation_id}",
        expected=200,
    )
    messages = exported.get("messages")
    expected_messages = state.get("expected_messages")
    if not isinstance(messages, list) or not isinstance(expected_messages, list):
        raise RuntimeError("C4 restart transcript contract is invalid")
    observed = [
        {
            "role": str(message.get("role")),
            "content_hash": _content_hash(str(message.get("content", ""))),
        }
        for message in messages
        if isinstance(message, dict)
    ]
    if observed != expected_messages:
        raise RuntimeError("AXENT transcript changed across process restart")

    hold = _app_function(
        dsn=dsn,
        tenant_id=tenant_id,
        statement="""
            SELECT *
            FROM tenant_private.place_axent_legal_hold(%s, %s, %s)
        """,
        parameters=(
            conversation_id,
            "C4 verifies that legal hold blocks retention purge",
            str(state["owner_subject"]),
        ),
    )
    legal_hold_id = UUID(str(hold["legal_hold_id"]))

    _expect_status(
        assertion=owner,
        method="DELETE",
        path=f"/v1/subscriber-workspace/axent/conversations/{conversation_id}",
        expected=202,
        payload={"delete_after": datetime.now(UTC).isoformat()},
    )
    first_purge_count = _purge_due(dsn)
    if not _conversation_exists(dsn, tenant_id, conversation_id):
        raise RuntimeError("Legal hold failed to prevent AXENT conversation purge")

    _app_function(
        dsn=dsn,
        tenant_id=tenant_id,
        statement="""
            SELECT *
            FROM tenant_private.release_axent_legal_hold(%s, %s)
        """,
        parameters=(legal_hold_id, str(state["owner_subject"])),
    )
    second_purge_count = _purge_due(dsn)
    if _conversation_exists(dsn, tenant_id, conversation_id):
        raise RuntimeError("AXENT conversation remained after legal hold release and purge")

    _expect_status(
        assertion=owner,
        method="GET",
        path=f"/v1/subscriber-workspace/axent/conversations/{conversation_id}",
        expected=404,
    )
    owner_list = _expect_status(
        assertion=owner,
        method="GET",
        path="/v1/subscriber-workspace/axent/conversations",
        expected=200,
    )
    remaining_ids = {
        str(item.get("conversation_id"))
        for item in owner_list.get("conversations", [])
        if isinstance(item, dict)
    }
    if str(conversation_id) in remaining_ids:
        raise RuntimeError("Purged AXENT conversation remains visible in owner history")

    return {
        "status": "PASS",
        "phase": "VERIFY_AFTER_RESTART",
        "marker": "AX_C4_RESEARCH_AXENT_RUNTIME_PASS",
        "exact_head_sha": build_sha,
        "research_run_id": state["research_run_id"],
        "conversation_id": str(conversation_id),
        "restart_persistence": True,
        "transcript_integrity": True,
        "legal_hold_blocked_purge": True,
        "purge_count_while_held": first_purge_count,
        "legal_hold_released": True,
        "purge_count_after_release": second_purge_count,
        "governed_deletion_completed": True,
        "post_purge_api_404": True,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Execute the exact-head C4 ResearchRun-to-AXENT persistence E2E"
    )
    result.add_argument("phase", choices=("prepare", "verify"))
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        payload = prepare() if args.phase == "prepare" else verify()
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "phase": args.phase.upper(),
                    "error": f"{exc.__class__.__name__}: {exc}",
                },
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
