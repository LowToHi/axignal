from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from axignal_api.entitlement_repository import EntitlementRepository
from axignal_api.identity import AuthenticatedIdentity
from axignal_api.seat_repository import SeatRepository
from axignal_api.subscriber_workspace_repository import SubscriberWorkspaceRepository


@dataclass(frozen=True)
class AuthorityEnvelope:
    authority: str
    version: str
    obtained_at: str
    freshness: str
    sensitivity: str


class AxentContextBuilder:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def build(
        self,
        *,
        identity: AuthenticatedIdentity,
        workspace_id: UUID | None = None,
        research_run_id: UUID | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        entitlement = EntitlementRepository(self.database_url).current_entitlement(
            tenant_id=identity.tenant_id
        )
        seats = SeatRepository(self.database_url).summary(tenant_id=identity.tenant_id)
        projection = SubscriberWorkspaceRepository(self.database_url).bootstrap(
            tenant_id=identity.tenant_id
        )

        workspace = next(
            (
                row
                for row in projection["workspaces"]
                if workspace_id is not None and row["workspace_id"] == workspace_id
            ),
            None,
        )
        run = next(
            (
                row
                for row in projection["research_runs"]
                if research_run_id is not None
                and row["research_run_id"] == research_run_id
            ),
            None,
        )

        return {
            "schema_version": "axignal.axent-context/v1",
            "identity": {
                "subject": identity.subject,
                "tenant_id": identity.tenant_id,
                "session_id": identity.session_id,
                "roles": list(identity.role_ids),
                "assurance_level": identity.assurance_level,
                "seat_state": identity.seat_state,
                "authority": asdict(
                    AuthorityEnvelope(
                        authority="identity_session",
                        version=str(identity.session_id),
                        obtained_at=now,
                        freshness="CURRENT_SESSION",
                        sensitivity="CONFIDENTIAL",
                    )
                ),
            },
            "commercial": {
                "entitlement": entitlement,
                "seats": seats,
                "authority": asdict(
                    AuthorityEnvelope(
                        authority="commercial_ledger",
                        version=str(
                            (entitlement or {}).get("provider_event_id") or "current"
                        ),
                        obtained_at=now,
                        freshness="TRANSACTIONAL_READ",
                        sensitivity="CONFIDENTIAL",
                    )
                ),
            },
            "workspace": workspace,
            "research_run": run,
            "account_projection": {
                "workspaces": projection.get("workspaces", []),
                "research_runs": projection.get("research_runs", []),
                "documents": projection.get("documents", []),
                "exports": projection.get("exports", []),
                "audit": projection.get("audit", []),
                "authority": asdict(
                    AuthorityEnvelope(
                        authority="subscriber_workspace_repository",
                        version="bootstrap/v1",
                        obtained_at=now,
                        freshness="TRANSACTIONAL_READ",
                        sensitivity="TENANT_PRIVATE",
                    )
                ),
            },
            "operational": {
                "source": "persistent_runtime",
                "workspace_found": workspace is not None if workspace_id else None,
                "research_run_found": run is not None if research_run_id else None,
                "authority": asdict(
                    AuthorityEnvelope(
                        authority="subscriber_workspace_repository",
                        version="v1",
                        obtained_at=now,
                        freshness="TRANSACTIONAL_READ",
                        sensitivity="TENANT_PRIVATE",
                    )
                ),
            },
        }
