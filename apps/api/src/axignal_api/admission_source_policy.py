from __future__ import annotations

from typing import Any

from axignal_api.admission_types import (
    ALLOWED_SOURCE,
    AdmissionIntegrityError,
    AdmissionPolicyError,
)
from axignal_api.document_proposals import (
    DeterministicInstitutionalParser,
    InstitutionalDocument,
    PromptInjectionScanner,
    canonical_hash,
)


class AdmissionSourcePolicyMixin:
    @staticmethod
    def _load_authoritative_inputs(
        cursor: Any,
        package: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
        packaged_source = package["source"]
        source_id = packaged_source.get("source_id")
        if source_id != ALLOWED_SOURCE:
            raise AdmissionPolicyError("Source is outside the first admission profile")
        cursor.execute(
            "SELECT * FROM axignal_global.sources WHERE source_id = %s",
            (source_id,),
        )
        source = cursor.fetchone()
        if source is None:
            raise AdmissionIntegrityError("Source registry record is absent")
        current_checks = {
            "admission_state": "ADMITTED",
            "rights_status": "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
            "license_id": "CC-BY-4.0",
        }
        for key, expected in current_checks.items():
            if source[key] != expected:
                raise AdmissionPolicyError(f"Source gate failed: {key}")
            if packaged_source.get(key) != expected:
                raise AdmissionIntegrityError(f"Source snapshot mismatch: {key}")
        if source["kill_switch"] or packaged_source.get("kill_switch") is not False:
            raise AdmissionPolicyError("Source kill switch is enabled")
        if not source["commercial_use"] or not source["redistribution"]:
            raise AdmissionPolicyError("Source reuse permissions are incomplete")

        document = package["document"]
        try:
            parsed = DeterministicInstitutionalParser().parse(
                InstitutionalDocument.model_validate(document)
            )
            PromptInjectionScanner().inspect(parsed)
        except Exception as exc:
            raise AdmissionIntegrityError(
                "Document failed independent parse or security validation"
            ) from exc
        parsed_fragments = [
            item.model_dump(mode="json") for item in parsed.fragments
        ]
        if parsed_fragments != package["fragments"]:
            raise AdmissionIntegrityError("Fragments do not match independent reparse")
        if document["source_id"] != source_id:
            raise AdmissionIntegrityError("Document source identity differs")
        if document["rights_status"] != source["rights_status"]:
            raise AdmissionIntegrityError("Document rights differ from source registry")
        if document["license_id"] != source["license_id"]:
            raise AdmissionIntegrityError("Document license differs from source registry")
        cursor.execute(
            """
            SELECT * FROM axignal_global.source_objects
            WHERE source_id = %s AND content_hash = %s
            """,
            (source_id, document["content_hash"]),
        )
        source_object = cursor.fetchone()
        if source_object is None:
            raise AdmissionIntegrityError("Immutable source object is absent")
        if source_object["raw_payload"] != document:
            raise AdmissionIntegrityError("Raw source object differs from handoff document")
        rights = source_object["rights_snapshot"]
        for key in ("rights_status", "license_id"):
            if rights.get(key) != source[key]:
                raise AdmissionIntegrityError(f"Persisted rights snapshot mismatch: {key}")

        cursor.execute(
            """
            SELECT * FROM axignal_global.document_fragments
            WHERE source_object_id = %s AND document_id = %s
            ORDER BY ordinal
            """,
            (source_object["source_object_id"], document["document_id"]),
        )
        rows = cursor.fetchall()
        fragments = {row["fragment_id"]: row for row in rows}
        if len(rows) != len(package["fragments"]):
            raise AdmissionIntegrityError("Fragment count differs")
        for packaged in package["fragments"]:
            row = fragments.get(packaged["fragment_id"])
            expected_hash = canonical_hash({
                "document_id": packaged["document_id"],
                "ordinal": packaged["ordinal"],
                "text": packaged["text"],
            })
            if row is None or expected_hash != packaged["content_hash"]:
                raise AdmissionIntegrityError("Packaged fragment hash differs")
            comparisons = {
                "document_id": packaged["document_id"],
                "ordinal": packaged["ordinal"],
                "start_char": packaged["start_char"],
                "end_char": packaged["end_char"],
                "text_content": packaged["text"],
                "content_hash": packaged["content_hash"],
                "parser_version": packaged["parser_version"],
                "security_scan_state": "CLEAR",
            }
            if any(row[key] != value for key, value in comparisons.items()):
                raise AdmissionIntegrityError("Persistent fragment differs from handoff")
        return source, source_object, fragments
