from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from uuid import UUID

ALLOWED_SOURCE = "world-bank-rer41"
ALLOWED_SUBJECT = "geo_country_rus"
ALLOWED_PREDICATE = "real_gdp_growth_annual_pct"
ALLOWED_UNIT = "percent_annual"
NUMBER_PATTERN = re.compile(
    r"real GDP growth reached\s+([0-9]+(?:\.[0-9]+)?)\s+percent\s+in\s+(\d{4})",
    re.IGNORECASE,
)


class AdmissionRuntimeError(RuntimeError):
    pass


class AdmissionIntegrityError(AdmissionRuntimeError):
    pass


class AdmissionPolicyError(AdmissionRuntimeError):
    pass


@dataclass(frozen=True)
class AdmissionRunResult:
    admission_batch_id: UUID | None
    canonical_claim_ids: tuple[UUID, ...]
    outcomes: tuple[str, ...]
    idempotent_replay: bool
    model_calls: int = 0

    def as_payload(self) -> dict[str, Any]:
        return {
            "admission_batch_id": (
                str(self.admission_batch_id) if self.admission_batch_id else None
            ),
            "canonical_claim_ids": [str(item) for item in self.canonical_claim_ids],
            "outcomes": list(self.outcomes),
            "idempotent_replay": self.idempotent_replay,
            "model_calls": self.model_calls,
        }
