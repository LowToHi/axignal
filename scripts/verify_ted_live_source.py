from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path

from axignal_api.connectors.ted import TEDSearchConnector, TEDSourceRetrievalError

OUTPUT = Path("ted-live-source-evidence.json")


def main() -> int:
    last_error: Exception | None = None
    page = None
    for attempt in range(1, 4):
        try:
            page = TEDSearchConnector(live_enabled=True).fetch_probe_page()
            break
        except TEDSourceRetrievalError as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(attempt * 3)
    if page is None:
        raise RuntimeError(f"TED live technical probe failed: {last_error}")

    missing_field_counts = {field: 0 for field in page.requested_fields}
    for notice in page.notices:
        for field in notice.missing_requested_fields:
            missing_field_counts[field] += 1

    evidence = {
        "goal_id": "AXIGNAL-GOAL-001",
        "task_ids": ["AX-F8-T04", "AX-F8-T05"],
        "universe_id": "eu_public_procurement",
        "source_id": page.source_id,
        "source_state": "TECHNICAL_PROBE",
        "retrieval_mode": page.retrieval_mode,
        "request_url": page.request_url,
        "request_hash": page.request_hash,
        "content_hash": page.content_hash,
        "query_text_persisted": False,
        "requested_fields": list(page.requested_fields),
        "personal_contact_fields_requested": False,
        "total_notice_count": page.total_notice_count,
        "returned_notice_count": len(page.notices),
        "missing_requested_field_counts": missing_field_counts,
        "iteration_next_token_present": page.iteration_next_token_present,
        "raw_payload_persisted_in_artifact": False,
        "notice_values_persisted_in_artifact": False,
        "rights_status": "COMMERCIAL_REUSE_CONDITIONAL_PERSONAL_AND_THIRD_PARTY_REVIEW",
        "runtime_enabled": False,
        "product_admitted": False,
        "public_marketing_authorised": False,
        "retrieved_at": page.retrieved_at.isoformat(),
        "smoke_completed_at": datetime.now(UTC).isoformat(),
    }
    OUTPUT.write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    print(
        "PASS TED live technical probe",
        len(page.notices),
        page.total_notice_count,
        page.content_hash,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
