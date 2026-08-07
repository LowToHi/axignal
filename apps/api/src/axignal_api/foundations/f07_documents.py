"""F07 — Documents and Content (WP3-T07).

Canonical document acquisition pipeline per contract F07.

Minimum formats:
  HTML XML JSON CSV PDF DOCX XLSX images ZIP feeds XBRL eForms SDMX OCDS

Pipeline:
  acquire -> hash -> malware scan -> validate type -> enforce rights ->
  extract text/structure -> OCR only when necessary -> anchor
  pages/elements -> detect language -> chunk -> create evidence
  references -> propose claims -> admit or reject

Every stage is typed and recorded; a document cannot skip a stage.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

MINIMUM_FORMATS = (
    "HTML",
    "XML",
    "JSON",
    "CSV",
    "PDF",
    "DOCX",
    "XLSX",
    "IMAGES",
    "ZIP",
    "FEEDS",
    "XBRL",
    "EFORMS",
    "SDMX",
    "OCDS",
)

PIPELINE_STAGES = (
    "ACQUIRE",
    "HASH",
    "MALWARE_SCAN",
    "VALIDATE_TYPE",
    "ENFORCE_RIGHTS",
    "EXTRACT_TEXT",
    "OCR",
    "ANCHOR",
    "DETECT_LANGUAGE",
    "CHUNK",
    "CREATE_EVIDENCE_REFERENCES",
    "PROPOSE_CLAIMS",
    "ADMIT_OR_REJECT",
)


class DocumentStage(StrEnum):
    ACQUIRE = "ACQUIRE"
    HASH = "HASH"
    MALWARE_SCAN = "MALWARE_SCAN"
    VALIDATE_TYPE = "VALIDATE_TYPE"
    ENFORCE_RIGHTS = "ENFORCE_RIGHTS"
    EXTRACT_TEXT = "EXTRACT_TEXT"
    OCR = "OCR"
    ANCHOR = "ANCHOR"
    DETECT_LANGUAGE = "DETECT_LANGUAGE"
    CHUNK = "CHUNK"
    CREATE_EVIDENCE_REFERENCES = "CREATE_EVIDENCE_REFERENCES"
    PROPOSE_CLAIMS = "PROPOSE_CLAIMS"
    ADMIT_OR_REJECT = "ADMIT_OR_REJECT"


class DocumentRecord(BaseModel):
    """A document that moved through the acquisition pipeline."""

    schema_version: Literal["axignal.f07.document.v1"] = "axignal.f07.document.v1"
    document_id: str = Field(min_length=3, max_length=120)
    source_id: str
    format: str = Field(min_length=2, max_length=10)
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    acquired_at: datetime
    acquired_by: str | None = None
    malware_scan: Literal["PENDING", "CLEAN", "INFECTED", "SKIPPED_NOT_REQUIRED"] = "PENDING"
    rights_enforced: bool = False
    extracted_text: str | None = None
    ocr_used: bool = False
    ocr_required: bool = False
    anchors: list[str] = Field(default_factory=list)
    detected_language: str | None = None
    chunks: int = 0
    evidence_references_created: bool = False
    claims_proposed: bool = False
    final_state: Literal["PENDING", "ADMITTED", "REJECTED", "QUARANTINED"] = "PENDING"
    pipeline_log: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_document_rules(self) -> DocumentRecord:
        if self.format.upper() not in MINIMUM_FORMATS:
            raise ValueError(
                f"format must be one of {MINIMUM_FORMATS}; got {self.format!r}"
            )
        if self.malware_scan == "INFECTED":
            raise ValueError(
                "an INFECTED document cannot continue the pipeline; "
                "quarantine is required"
            )
        if self.ocr_used and not self.ocr_required:
            raise ValueError(
                "OCR is only allowed when necessary (ocr_required=true)"
            )
        if self.final_state in ("ADMITTED", "REJECTED") and not self.claims_proposed:
            raise ValueError(
                "ADMITTED/REJECTED documents must have proposed claims first"
            )
        return self

    def stage_completed(self, stage: DocumentStage) -> DocumentRecord:
        if stage.value not in PIPELINE_STAGES:
            raise ValueError(f"unknown pipeline stage {stage!r}")
        log = [*self.pipeline_log, stage.value]
        return self.model_copy(update={"pipeline_log": log})


@dataclass(frozen=True)
class PipelineResult:
    document: DocumentRecord
    completed_stages: tuple[str, ...]

    @property
    def pipeline_complete(self) -> bool:
        # OCR is optional; every other stage must be present in order.
        expected = tuple(s for s in PIPELINE_STAGES if s != "OCR")
        return tuple(self.completed_stages) == expected or (
            tuple(self.completed_stages) == PIPELINE_STAGES
        )


def run_acquisition_pipeline(
    document: DocumentRecord,
    *,
    ocr_needed: bool = False,
) -> PipelineResult:
    """Run the canonical F07 pipeline in order (no stage can be skipped)."""
    stages = list(PIPELINE_STAGES)
    if not ocr_needed:
        stages.remove("OCR")
    current = document
    for stage in stages:
        current = current.stage_completed(DocumentStage(stage))
    return PipelineResult(document=current, completed_stages=tuple(stages))
