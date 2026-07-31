from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.founder_identity import require_founder_identity
from axignal_api.identity import AuthenticatedIdentity, require_recent_aal2
from axignal_api.identity_config import IdentityRuntimeSettings
from axignal_api.identity_delivery import verify_bot_token
from axignal_api.organic_config import OrganicDiscoverySettings
from axignal_api.organic_delivery import TenderAlertDelivery
from axignal_api.organic_repository import OrganicDiscoveryRepository

router = APIRouter(tags=["organic-discovery"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_founder_identity)]
PageKind = Literal["TENDER_HUB", "MARKET_INTELLIGENCE", "TENDER_DETAIL"]
SlugPath = Annotated[str, Path(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]


class PublishPageCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    ttl_hours: int = Field(default=24, ge=1, le=168)
    confirm_publication: Literal[True]


class TenderAlertCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320)
    country_code: str = Field(pattern=r"^[A-Z]{2}$")
    sector_slug: str = Field(
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        max_length=120,
    )
    locale: str = Field(default="en", pattern=r"^[a-z]{2}(-[A-Z]{2})?$")
    cadence: Literal["IMMEDIATE", "DAILY", "WEEKLY"] = "DAILY"
    source_path: str = Field(pattern=r"^/[A-Za-z0-9_/?=&.-]{1,500}$")
    bot_token: str = Field(min_length=8, max_length=2048)


class CitationCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["CHATGPT", "COPILOT", "GOOGLE_AI", "PERPLEXITY", "OTHER"]
    surface: str = Field(min_length=1, max_length=200)
    cited_url: str = Field(pattern=r"^https://", max_length=2048)
    query: str = Field(min_length=1, max_length=2000)
    source: Literal["BING_WEBMASTER", "ANALYTICS", "MANUAL", "API"]
    metadata: dict[str, object] = Field(default_factory=dict)
    observed_at: datetime


def _settings_repository() -> tuple[
    OrganicDiscoverySettings,
    OrganicDiscoveryRepository,
]:
    settings = OrganicDiscoverySettings.from_env()
    try:
        settings.require_runtime()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    assert settings.database_url is not None
    return settings, OrganicDiscoveryRepository(settings.database_url)


def _digest(value: str, pepper: str) -> str:
    return hmac.new(
        pepper.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _founder(
    identity: AuthenticatedIdentity,
) -> tuple[OrganicDiscoverySettings, OrganicDiscoveryRepository]:
    settings, repository = _settings_repository()
    try:
        require_recent_aal2(identity)
        settings.require_founder_subject(identity.subject)
    except (RuntimeError, HTTPException) as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(
            status_code=403,
            detail="Founder admin authority required",
        ) from exc
    if not repository.founder_authorized(subject=identity.subject):
        raise HTTPException(status_code=403, detail="Founder admin authority required")
    return settings, repository


def _store_error(exc: Exception) -> None:
    message = str(exc)
    if "seo_page_not_found" in message:
        raise HTTPException(status_code=404, detail="SEO page candidate not found") from exc
    if "seo_page_not_indexable" in message:
        raise HTTPException(
            status_code=409,
            detail="Page has not passed the IndexabilityGate",
        ) from exc
    if "founder_admin_required" in message:
        raise HTTPException(status_code=403, detail="Founder admin authority required") from exc
    if "content_hash_invalid" in message or "snapshot_expiry_invalid" in message:
        raise HTTPException(status_code=422, detail="Invalid publication contract") from exc
    raise HTTPException(
        status_code=503,
        detail="Organic discovery authority unavailable",
    ) from exc


@router.get("/v1/public/discovery/{page_kind}/{country_slug}/{sector_slug}")
def public_discovery_page(
    page_kind: PageKind,
    country_slug: SlugPath,
    sector_slug: SlugPath,
    locale: str = "en",
) -> dict[str, object]:
    settings, repository = _settings_repository()
    try:
        settings.require_public_indexing()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=404,
            detail="Published discovery page not found",
        ) from exc
    result = repository.public_page(
        country_slug=country_slug,
        sector_slug=sector_slug,
        page_kind=page_kind,
        locale=locale,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Published discovery page not found")
    return result


@router.get("/v1/public/discovery-sitemap")
def public_discovery_sitemap() -> list[dict[str, object]]:
    settings, repository = _settings_repository()
    try:
        settings.require_public_indexing()
    except RuntimeError:
        return []
    return repository.sitemap()


@router.post("/v1/public/tender-alerts", status_code=status.HTTP_202_ACCEPTED)
def subscribe_tender_alert(
    command: TenderAlertCommand,
    request: Request,
) -> dict[str, object]:
    settings, repository = _settings_repository()
    try:
        settings.require_public_alerts()
        identity_settings = IdentityRuntimeSettings.from_env()
        verify_bot_token(
            settings=identity_settings,
            token=command.bot_token,
            remote_ip=request.client.host if request.client else None,
        )
        delivery = TenderAlertDelivery(identity_settings)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Tender alerts are unavailable") from exc

    email = command.email.strip().casefold()
    assert settings.hmac_pepper is not None
    confirmation_token = secrets.token_urlsafe(32)
    try:
        result = repository.subscribe_alert(
            email=email,
            email_hmac=_digest(f"email:{email}", settings.hmac_pepper),
            confirmation_token_digest=hashlib.sha256(
                confirmation_token.encode("utf-8")
            ).hexdigest(),
            country_code=command.country_code,
            sector_slug=command.sector_slug,
            locale=command.locale,
            cadence=command.cadence,
            source_path=command.source_path,
        )
        receipt = delivery.deliver_confirmation(
            recipient=email,
            token=confirmation_token,
            country_code=command.country_code,
            sector_slug=command.sector_slug,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Tender alert could not be prepared",
        ) from exc

    response: dict[str, object] = {
        "accepted": True,
        "state": result.get("state", "PENDING_CONFIRMATION"),
        "message": "Check your email to confirm the alert.",
        "trial_created": False,
        "tenant_created": False,
    }
    if receipt.provider == "TEST":
        response["test_confirmation_token"] = receipt.test_confirmation_token
    return response


@router.get("/v1/admin/overview")
def founder_overview(identity: Authenticated) -> dict[str, object]:
    _, repository = _founder(identity)
    try:
        return repository.overview(actor_subject=identity.subject)
    except Exception as exc:
        _store_error(exc)
    raise AssertionError("Unreachable")


@router.get("/v1/admin/seo/pages")
def founder_pages(identity: Authenticated) -> list[dict[str, object]]:
    _, repository = _founder(identity)
    try:
        return repository.pages(actor_subject=identity.subject)
    except Exception as exc:
        _store_error(exc)
    raise AssertionError("Unreachable")


@router.post("/v1/admin/seo/pages/{page_id}/evaluate")
def evaluate_page(page_id: UUID, identity: Authenticated) -> dict[str, object]:
    _, repository = _founder(identity)
    try:
        return repository.evaluate(page_id=page_id, actor_subject=identity.subject)
    except Exception as exc:
        _store_error(exc)
    raise AssertionError("Unreachable")


@router.post("/v1/admin/seo/pages/{page_id}/publish")
def publish_page(
    page_id: UUID,
    command: PublishPageCommand,
    identity: Authenticated,
) -> dict[str, object]:
    _, repository = _founder(identity)
    try:
        return repository.publish(
            page_id=page_id,
            actor_subject=identity.subject,
            content_hash=command.content_hash,
            ttl_hours=command.ttl_hours,
        )
    except Exception as exc:
        _store_error(exc)
    raise AssertionError("Unreachable")


@router.get("/v1/admin/crm/contacts")
def founder_contacts(identity: Authenticated) -> list[dict[str, object]]:
    _, repository = _founder(identity)
    try:
        return repository.contacts(actor_subject=identity.subject)
    except Exception as exc:
        _store_error(exc)
    raise AssertionError("Unreachable")


@router.get("/v1/admin/tender-alerts")
def founder_alerts(identity: Authenticated) -> list[dict[str, object]]:
    _, repository = _founder(identity)
    try:
        return repository.alerts(actor_subject=identity.subject)
    except Exception as exc:
        _store_error(exc)
    raise AssertionError("Unreachable")


@router.post("/v1/admin/ai-citations", status_code=status.HTTP_201_CREATED)
def record_ai_citation(
    command: CitationCommand,
    identity: Authenticated,
) -> dict[str, object]:
    settings, repository = _founder(identity)
    assert settings.hmac_pepper is not None
    try:
        citation_id = repository.record_citation(
            actor_subject=identity.subject,
            provider=command.provider,
            surface=command.surface,
            cited_url=command.cited_url,
            query_hmac=_digest(f"query:{command.query}", settings.hmac_pepper),
            source=command.source,
            metadata=command.metadata,
            observed_at=command.observed_at,
        )
    except Exception as exc:
        _store_error(exc)
        raise AssertionError("Unreachable") from exc
    return {"citation_event_id": citation_id, "recorded": True}


@router.post("/v1/admin/test/bootstrap-founder")
def test_bootstrap_founder(identity: Authenticated) -> dict[str, object]:
    settings, repository = _settings_repository()
    try:
        settings.require_test_runtime()
        settings.require_founder_subject(identity.subject)
        require_recent_aal2(identity)
        repository.test_bootstrap_founder(subject=identity.subject)
    except (RuntimeError, HTTPException) as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=404, detail="Not found") from exc
    return {"subject": identity.subject, "founder_admin": True}
