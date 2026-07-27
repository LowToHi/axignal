from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path

from axignal_api.connectors.world_bank import SourceRetrievalError, WorldBankConnector

OUTPUT = Path("world-bank-live-source-evidence.json")


def main() -> int:
    last_error: Exception | None = None
    observation = None
    for attempt in range(1, 4):
        try:
            observation = WorldBankConnector(live_enabled=True).fetch_latest_inflation()
            break
        except SourceRetrievalError as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(attempt * 2)
    if observation is None:
        raise RuntimeError(f"World Bank live source smoke failed: {last_error}")

    evidence = {
        "goal_id": "AXIGNAL-GOAL-001",
        "source_id": observation.source_id,
        "retrieval_mode": observation.retrieval_mode,
        "country_code": observation.country_code,
        "indicator_code": observation.indicator_code,
        "period": observation.period,
        "value": observation.value,
        "unit": observation.unit,
        "request_url": observation.request_url,
        "retrieved_at": observation.retrieved_at.isoformat(),
        "source_updated_at": observation.source_updated_at,
        "content_hash": observation.content_hash,
        "rights_status": "COMMERCIAL_REUSE_WITH_ATTRIBUTION",
        "license_id": "CC-BY-4.0",
        "attribution": (
            "World Bank Open Data — World Development Indicators; "
            "changes and derived interpretation by AXIGNAL."
        ),
        "raw_payload_persisted_in_artifact": False,
        "smoke_completed_at": datetime.now(UTC).isoformat(),
    }
    OUTPUT.write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    print(
        "PASS live World Bank source",
        observation.country_code,
        observation.indicator_code,
        observation.period,
        observation.content_hash,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
