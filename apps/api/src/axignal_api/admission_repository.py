from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Literal
from uuid import UUID

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from axignal_api.admission_decision_flow import AdmissionDecisionFlowMixin
from axignal_api.admission_evidence_policy import AdmissionEvidencePolicyMixin
from axignal_api.admission_fact_policy import AdmissionFactPolicyMixin
from axignal_api.admission_failure_store import AdmissionFailureStoreMixin
from axignal_api.admission_handoff_policy import AdmissionHandoffPolicyMixin
from axignal_api.admission_ledger_store import AdmissionLedgerStoreMixin
from axignal_api.admission_outbox_store import AdmissionOutboxStoreMixin
from axignal_api.admission_source_policy import AdmissionSourcePolicyMixin

DatabaseRole = Literal["axignal_app", "axignal_admission_runtime"]


class AdmissionRepository(
    AdmissionOutboxStoreMixin,
    AdmissionHandoffPolicyMixin,
    AdmissionSourcePolicyMixin,
    AdmissionEvidencePolicyMixin,
    AdmissionFactPolicyMixin,
    AdmissionLedgerStoreMixin,
    AdmissionDecisionFlowMixin,
    AdmissionFailureStoreMixin,
):
    def __init__(
        self,
        *,
        app_dsn: str | None = None,
        admission_dsn: str | None = None,
    ) -> None:
        self.app_dsn = app_dsn
        self.admission_dsn = admission_dsn

    @contextmanager
    def _cursor(
        self,
        role: DatabaseRole,
        tenant_id: UUID | None = None,
    ) -> Iterator[psycopg.Cursor[dict[str, Any]]]:
        dsn = self.app_dsn if role == "axignal_app" else self.admission_dsn
        if not dsn:
            raise RuntimeError(f"No database credential configured for role {role}")
        with (
            psycopg.connect(dsn, row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            if role == "axignal_app":
                cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
            if tenant_id is not None:
                cursor.execute(
                    "SELECT set_config('app.tenant_id', %s, true)",
                    (str(tenant_id),),
                )
            yield cursor
