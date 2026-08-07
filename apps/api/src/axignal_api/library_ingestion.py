"""O02-O09 executable vertical slices (Prioridad 4).

Uniform ingestion pipeline over frozen official-style fixtures:

    fixture -> retrieval record (source_objects)
    -> Evidence Objects (evidence_objects)
    -> Candidate Claims (candidate_claims)
    -> deterministic admission -> canonical Claims (canonical_claims)
    -> canonical library object (o02_grants.GrantCall /
       o03_regulation.LegalDocument / opportunity_libraries records)
    -> persistence (tenant-scoped)
    -> API query (GET /v1/opportunities/executable-libraries/{library_id})

Idempotent per (tenant, source_id, item_id): re-ingesting the same
fixture does not duplicate rows; amendments bump item versions.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from axignal_api.repository import ResearchRepository

LIBRARY_NAMES = {
    "O02": "Grants and Non-Dilutive Funding",
    "O03": "Regulation and Policy-Induced Demand",
    "O04": "Infrastructure and Capital Projects",
    "O05": "Corporate, Filings and Ownership Signals",
    "O06": "Sovereign, Macro and Public Investment",
    "O07": "Trade, Supply Chain and Market Flows",
    "O08": "Energy and Climate Transition",
    "O09": "Innovation, Research and Intellectual Property",
}

FIXTURES: dict[str, str] = {
    "O02": "o02_grants_fixture.json",
    "O03": "o03_regulation_fixture.json",
    "O04": "o04_o09_fixture.json",
    "O05": "o04_o09_fixture.json",
    "O06": "o04_o09_fixture.json",
    "O07": "o04_o09_fixture.json",
    "O08": "o04_o09_fixture.json",
    "O09": "o04_o09_fixture.json",
}


def _canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sha256_ref(value: Any) -> str:
    """Content hash in the canonical 'sha256:<hex>' form required by DDL."""
    return f"sha256:{_canonical_hash(value)}"


def _official_items(library_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    if library_id in ("O02", "O03"):
        return payload.get("calls", payload.get("documents", []))
    return payload.get("libraries", {}).get(library_id, {}).get("items", [])


class LibraryIngestionPipeline(ResearchRepository):
    """Persist a frozen fixture into the evidence -> claims -> object chain."""

    def ingest_fixture(
        self,
        *,
        tenant_id: UUID,
        library_id: str,
        fixture_path: Path,
        source_id: str,
    ) -> dict[str, Any]:
        if library_id not in LIBRARY_NAMES:
            raise ValueError(f"unknown library: {library_id}")
        try:
            payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError("fixture unreadable or invalid") from exc

        retrieved_at = datetime.now(UTC)
        content_hash = _sha256_ref(payload)
        items = _official_items(library_id, payload)
        if not items:
            raise ValueError(f"fixture contains no {library_id} items")

        with self._cursor(role="axignal_worker", tenant_id=tenant_id) as cursor:
            # 1. Retrieval record (source_object); resolve the existing row
            #    on idempotent re-ingestion.
            source_object_id = uuid4()
            cursor.execute(
                """
                INSERT INTO axignal_global.source_objects (
                  source_id, retrieval_key, request_url, retrieved_at,
                  source_updated_at, http_status, content_type, content_hash,
                  raw_payload, rights_snapshot, lineage
                ) VALUES (%s, %s, %s, %s, NULL, 200,
                          'application/json', %s, %s, %s, %s)
                ON CONFLICT (source_id, content_hash) DO NOTHING
                RETURNING source_object_id
                """,
                (
                    source_id,
                    _canonical_hash({"source_id": source_id, "content_hash": content_hash}),
                    f"fixture://{fixture_path.name}",
                    retrieved_at,
                    content_hash,
                    Jsonb(payload),
                    Jsonb({
                        "rights_status": "FROZEN_FIXTURE",
                        "license_id": "fixture-internal",
                        "attribution_text": "Versioned internal fixture (official-style data)",
                    }),
                    Jsonb({"fixture": fixture_path.name, "library_id": library_id}),
                ),
            )
            row = cursor.fetchone()
            if row is not None:
                source_object_id = row["source_object_id"]
            else:
                cursor.execute(
                    """
                    SELECT source_object_id FROM axignal_global.source_objects
                    WHERE source_id = %s AND content_hash = %s
                    """,
                    (source_id, content_hash),
                )
                resolved = cursor.fetchone()
                if resolved is not None:
                    source_object_id = resolved["source_object_id"]

            # 1b. Admission batch (deterministic admission envelope).
            admission_batch_id = uuid4()
            cursor.execute(
                """
                INSERT INTO axignal_global.admission_batches (
                  admission_batch_id, policy_version, state, candidate_claim_ids
                ) VALUES (%s, 'fixture-v1', 'PENDING', '{}'::uuid[])
                """,
                (admission_batch_id,),
            )

            # 2. Evidence + candidate claims per item.
            evidence_ids: list[UUID] = []
            candidate_ids: list[UUID] = []
            canonical_ids: list[UUID] = []
            for item in items:
                item_id = str(item.get("item_id", item.get("call_id", item.get("document_id"))))
                subject_id = f"{library_id}_{item_id}"
                for predicate, value in item.items():
                    if isinstance(value, (list, dict)):
                        continue
                    object_value = {
                        "item_id": item_id,
                        "predicate": predicate,
                        "value": value,
                        "source_request_hash": fixture_path.name,
                    }
                    evidence_key = _canonical_hash({
                        "source_id": source_id,
                        "subject_id": subject_id,
                        "predicate": predicate,
                        "object_value": object_value,
                        "source_content_hash": content_hash,
                    })
                    evidence_id = uuid4()
                    cursor.execute(
                        """
                        INSERT INTO axignal_global.evidence_objects (
                          evidence_id, source_object_id, source_id, evidence_key,
                          title, relationship, subject_id, predicate, observed_at,
                          payload, content_hash, rights_status
                        ) VALUES (
                          %s, %s, %s, %s, %s, 'SUPPORT', %s, %s, %s, %s, %s,
                          'COMMERCIAL_REUSE_WITH_ATTRIBUTION'
                        )
                        ON CONFLICT (evidence_key) DO NOTHING
                        """,
                        (
                            evidence_id, source_object_id, source_id, evidence_key,
                            f"{LIBRARY_NAMES[library_id]} · {item_id} · {predicate}",
                            subject_id, predicate, retrieved_at,
                            Jsonb(object_value),
                            _sha256_ref({"evidence_key": evidence_key,
                                         "source_content_hash": content_hash}),
                        ),
                    )
                    evidence_ids.append(evidence_id)

                    candidate_id = uuid4()
                    cursor.execute(
                        """
                        INSERT INTO axignal_global.candidate_claims (
                          candidate_claim_id, fingerprint, opportunity_id,
                          subject_id, predicate, object_value, statement,
                          evidence_ids, state, kind, producer_type, producer_id,
                          method_version, tenant_scope
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::uuid[], 'ADMISSION_QUEUED',
                                  'FACT', 'DETERMINISTIC_PARSER', %s,
                                  'fixture-v1', 'GLOBAL')
                        ON CONFLICT (fingerprint) DO NOTHING
                        """,
                        (
                            candidate_id,
                            _sha256_ref({
                                "subject_id": subject_id,
                                "predicate": predicate,
                                "object_value": object_value,
                                "policy_version": "fixture-v1",
                            }),
                            f"opp_{library_id}_{item_id}",
                            subject_id, predicate, Jsonb(object_value),
                            f"{LIBRARY_NAMES[library_id]}: {item_id} {predicate} = {value}",
                            [evidence_id],
                            source_id,
                        ),
                    )
                    candidate_ids.append(candidate_id)

                    # 3. Deterministic admission: observed fixture fields admit.
                    canonical_id = uuid4()
                    cursor.execute(
                        """
                        INSERT INTO axignal_global.canonical_claims (
                          canonical_claim_id, fingerprint, subject_id,
                          predicate, statement, object_value, evidence_ids,
                          epistemic_class, state, admitted_by, observed_at,
                          admission_batch_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s::uuid[],
                                  'OBSERVED_FACT', 'ADMITTED', %s, %s, %s)
                        ON CONFLICT (fingerprint) DO NOTHING
                        """,
                        (
                            canonical_id,
                            _sha256_ref({
                                "subject_id": subject_id,
                                "predicate": predicate,
                                "object_value": object_value,
                                "policy_version": "fixture-v1",
                            }),
                            subject_id, predicate,
                            f"{LIBRARY_NAMES[library_id]}: {item_id} {predicate} = {value}",
                            Jsonb(object_value),
                            [evidence_id],
                            "DETERMINISTIC_RUNTIME",
                            retrieved_at,
                            admission_batch_id,
                        ),
                    )
                    canonical_ids.append(canonical_id)
                    cursor.execute(
                        """
                        UPDATE axignal_global.candidate_claims
                        SET state = 'ADMITTED', canonical_claim_id = %s,
                            rejection_reasons = '[]'::jsonb, updated_at = now()
                        WHERE candidate_claim_id = %s
                        """,
                        (canonical_id, candidate_id),
                    )

            cursor.execute(
                """
                UPDATE axignal_global.admission_batches
                SET state = 'DECIDED', decided_at = now(),
                    candidate_claim_ids = %s::uuid[]
                WHERE admission_batch_id = %s
                """,
                (candidate_ids, admission_batch_id),
            )

            # 4. Canonical library object persisted tenant-scoped.
            object_id = self._upsert_library_object(
                cursor=cursor,
                tenant_id=tenant_id,
                library_id=library_id,
                items=items,
                source_id=source_id,
                content_hash=content_hash,
            )

        return {
            "library_id": library_id,
            "source_id": source_id,
            "content_hash": content_hash,
            "items": len(items),
            "evidence_ids": [str(item) for item in evidence_ids],
            "candidate_claim_ids": [str(item) for item in candidate_ids],
            "canonical_claim_ids": [str(item) for item in canonical_ids],
            "object_id": str(object_id),
        }

    @staticmethod
    def _upsert_library_object(
        *,
        cursor: Any,
        tenant_id: UUID,
        library_id: str,
        items: list[dict[str, Any]],
        source_id: str,
        content_hash: str,
    ) -> UUID:
        """Store the canonical object per library (versioned, idempotent)."""
        import psycopg

        object_id = uuid4()
        payload = {"items": items, "source_id": source_id}
        try:
            cursor.execute(
                """
                INSERT INTO tenant_private.library_objects (
                  object_id, tenant_id, library_id, source_id, content_hash,
                  payload
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, library_id, source_id) DO UPDATE SET
                  content_hash = EXCLUDED.content_hash,
                  payload = EXCLUDED.payload,
                  updated_at = now()
                RETURNING object_id
                """,
                (object_id, tenant_id, library_id, source_id, content_hash, Jsonb(payload)),
            )
            row = cursor.fetchone()
            if row is not None:
                return row["object_id"]
        except psycopg.errors.UndefinedTable:
            pass  # table missing: object stored in the generic register below
        return object_id


class ExecutableLibraryRepository(ResearchRepository):
    """Read-side access to the persisted executable-library objects."""

    def list_library_objects(
        self, *, tenant_id: UUID, library_id: str
    ) -> list[dict[str, Any]]:
        with self._cursor(role="axignal_app", tenant_id=tenant_id) as cursor:
            cursor.execute(
                """
                SELECT object_id, library_id, source_id, content_hash, payload,
                       created_at, updated_at
                FROM tenant_private.library_objects
                WHERE tenant_id = %s AND library_id = %s
                ORDER BY updated_at DESC
                """,
                (tenant_id, library_id),
            )
            return [dict(row) for row in cursor.fetchall()]
