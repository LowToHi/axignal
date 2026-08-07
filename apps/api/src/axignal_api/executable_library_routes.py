"""Executable libraries HTTP API (Prioridad 4)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from axignal_api.coverage_disclosure import CoverageDisclosure
from axignal_api.identity import AuthenticatedIdentity, require_identity
from axignal_api.library_ingestion import (
    FIXTURES,
    LIBRARY_NAMES,
    ExecutableLibraryRepository,
    LibraryIngestionPipeline,
)

router = APIRouter(prefix="/v1/opportunities/executable-libraries", tags=["executable-libraries"])
Authenticated = Annotated[AuthenticatedIdentity, Depends(require_identity)]

FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "tests" / "fixtures"


def _pipeline() -> LibraryIngestionPipeline:
    dsn = os.environ.get("AXIGNAL_DATABASE_URL")
    if not dsn:
        raise HTTPException(status_code=503, detail="AXIGNAL_DATABASE_URL is required")
    return LibraryIngestionPipeline(dsn)


class IngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    library_id: str = Field(pattern=r"^O0[2-9]$")
    source_id: str = Field(min_length=3, max_length=200)


@router.get("/{library_id}")
def list_library_objects(
    library_id: str, identity: Authenticated
) -> list[dict[str, object]]:
    if library_id not in LIBRARY_NAMES:
        raise HTTPException(status_code=404, detail="unknown library")
    dsn = os.environ.get("AXIGNAL_DATABASE_URL")
    if not dsn:
        raise HTTPException(status_code=503, detail="AXIGNAL_DATABASE_URL is required")
    return ExecutableLibraryRepository(dsn).list_library_objects(
        tenant_id=identity.tenant_id, library_id=library_id
    )


@router.get("/{library_id}/coverage")
def library_coverage(library_id: str) -> CoverageDisclosure:
    if library_id not in LIBRARY_NAMES:
        raise HTTPException(status_code=404, detail="unknown library")
    from datetime import UTC, datetime, timedelta

    return CoverageDisclosure(
        scope_id=f"library:{library_id}",
        scope_type="LIBRARY",
        source_scope=f"fixture:{FIXTURES[library_id]}",
        completeness_note=(
            f"Library {library_id} ({LIBRARY_NAMES[library_id]}) is exercised by a "
            "versioned internal fixture. TECHNICAL_IMPLEMENTATION=PASS; "
            "COMMERCIAL_ADMISSION=BLOCKED_EXTERNAL until Legal/Privacy authorisation."
        ),
        evidence_refs=[f"fixture:{FIXTURES[library_id]}"],
        expires_at=datetime.now(UTC) + timedelta(days=30),
        update_cadence="STATIC",
    )


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
def ingest_fixture(
    request: IngestRequest, identity: Authenticated
) -> dict[str, object]:
    """Ingest the versioned fixture for a library (idempotent, tenant-scoped)."""
    fixture_name = FIXTURES.get(request.library_id)
    if fixture_name is None:
        raise HTTPException(status_code=404, detail="no fixture for library")
    fixture_path = FIXTURE_ROOT / fixture_name
    if not fixture_path.exists():
        raise HTTPException(status_code=503, detail=f"fixture {fixture_name} missing")
    try:
        result = _pipeline().ingest_fixture(
            tenant_id=identity.tenant_id,
            library_id=request.library_id,
            fixture_path=fixture_path,
            source_id=request.source_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result
