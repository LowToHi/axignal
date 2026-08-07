"""WP3-T07 — F07 Documents/Content tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from axignal_api.foundations.f07_documents import (
    MINIMUM_FORMATS,
    PIPELINE_STAGES,
    DocumentRecord,
    DocumentStage,
    run_acquisition_pipeline,
)


def document(**overrides: object) -> DocumentRecord:
    base: dict[str, object] = {
        "document_id": "doc-1",
        "source_id": "src_x",
        "format": "PDF",
        "content_hash": f"sha256:{'a' * 64}",
        "acquired_at": datetime.now(UTC),
    }
    base.update(overrides)
    return DocumentRecord(**base)


class TestDocumentRecord:
    def test_minimum_formats_exact(self) -> None:
        assert MINIMUM_FORMATS == (
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

    def test_valid_document(self) -> None:
        doc = document()
        assert doc.malware_scan == "PENDING"
        assert doc.final_state == "PENDING"

    def test_unknown_format_rejected(self) -> None:
        with pytest.raises(ValueError, match="format must be one of"):
            document(format="TXT")

    def test_infected_quarantine_required(self) -> None:
        with pytest.raises(ValueError, match="INFECTED"):
            document(malware_scan="INFECTED")

    def test_ocr_only_when_necessary(self) -> None:
        with pytest.raises(ValueError, match="ocr_required"):
            document(ocr_used=True, ocr_required=False)

    def test_ocr_when_required_ok(self) -> None:
        doc = document(ocr_used=True, ocr_required=True)
        assert doc.ocr_used is True

    def test_final_state_requires_claims(self) -> None:
        with pytest.raises(ValueError, match="claims"):
            document(final_state="ADMITTED", claims_proposed=False)

    def test_final_state_with_claims_ok(self) -> None:
        doc = document(
            final_state="ADMITTED",
            claims_proposed=True,
            evidence_references_created=True,
        )
        assert doc.final_state == "ADMITTED"

    def test_content_hash_pattern(self) -> None:
        with pytest.raises(ValueError):
            document(content_hash="md5:abc")

    def test_all_pipeline_stages_typed(self) -> None:
        assert len(PIPELINE_STAGES) == 13
        assert PIPELINE_STAGES[-1] == "ADMIT_OR_REJECT"


class TestPipeline:
    def test_pipeline_completes_without_ocr(self) -> None:
        doc = document()
        result = run_acquisition_pipeline(doc, ocr_needed=False)
        assert result.pipeline_complete
        assert "OCR" not in result.completed_stages
        assert len(result.completed_stages) == 12
        # Order is preserved.
        assert result.completed_stages[:3] == ("ACQUIRE", "HASH", "MALWARE_SCAN")

    def test_pipeline_completes_with_ocr(self) -> None:
        doc = document(ocr_required=True)
        result = run_acquisition_pipeline(doc, ocr_needed=True)
        assert result.pipeline_complete
        assert "OCR" in result.completed_stages
        assert len(result.completed_stages) == 13

    def test_pipeline_never_skips_stages(self) -> None:
        doc = document()
        result = run_acquisition_pipeline(doc, ocr_needed=False)
        assert result.completed_stages == tuple(
            s for s in PIPELINE_STAGES if s != "OCR"
        )

    def test_stage_log_accumulates(self) -> None:
        doc = document()
        logged = doc.stage_completed(DocumentStage.ACQUIRE).stage_completed(
            DocumentStage.HASH
        )
        assert logged.pipeline_log == ["ACQUIRE", "HASH"]
