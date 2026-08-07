"""WP7 — O03 Regulation tests."""

from __future__ import annotations

from datetime import date
from uuid import UUID

import pytest

from axignal_api.o03_regulation import (
    AmendmentRecord,
    ComplianceState,
    LegalDocument,
    LegalDocumentState,
    MarketEntryWorkspace,
    Obligation,
    regulation_source_manifest,
)

TENANT = UUID("11111111-1111-4111-8111-111111111111")
WS_ID = UUID("33333333-3333-4333-8333-333333333333")


def in_force_document(**overrides: object) -> LegalDocument:
    base: dict[str, object] = {
        "document_id": "doc-1",
        "official_citation": "Regulation (EU) 2024/1234",
        "jurisdiction_id": "EU",
        "state": "IN_FORCE",
        "published_at": date(2024, 5, 1),
        "effective_at": date(2024, 6, 1),
        "official_url": "https://eur-lex.europa.eu/eli/reg/2024/1234",
    }
    base.update(overrides)
    return LegalDocument(**base)


class TestSourceAdmission:
    def test_manifest(self) -> None:
        manifest = regulation_source_manifest()
        assert manifest["library_id"] == "O03"
        assert manifest["state"] == "DISCOVERED"
        assert manifest["product_shell"] == "AXIGNAL_OPPORTUNITY_INTELLIGENCE"


class TestLegalDocument:
    def test_in_force_requires_effective_date(self) -> None:
        with pytest.raises(ValueError, match="effective_at"):
            LegalDocument(
                document_id="doc-1",
                official_citation="Regulation (EU) 2024/1234",
                jurisdiction_id="EU",
                state="IN_FORCE",
                official_url="https://eur-lex.europa.eu/eli/reg/2024/1234",
            )

    def test_in_force_requires_official_url(self) -> None:
        with pytest.raises(ValueError, match="official_url"):
            LegalDocument(
                document_id="doc-1",
                official_citation="Regulation (EU) 2024/1234",
                jurisdiction_id="EU",
                state="IN_FORCE",
                effective_at=date(2024, 6, 1),
            )

    def test_valid_in_force_document(self) -> None:
        document = in_force_document()
        assert document.state == LegalDocumentState.IN_FORCE
        assert document.official_url.startswith("https://")

    def test_pending_publication_ok(self) -> None:
        document = LegalDocument(
            document_id="doc-2",
            official_citation="Draft Regulation",
            jurisdiction_id="EU",
        )
        assert document.state == LegalDocumentState.PENDING_PUBLICATION

    def test_date_ordering(self) -> None:
        with pytest.raises(ValueError, match="published_at"):
            in_force_document(
                published_at=date(2024, 7, 1),
                effective_at=date(2024, 6, 1),
            )

    def test_jurisdiction_pattern(self) -> None:
        with pytest.raises(ValueError):
            LegalDocument(
                document_id="doc-3",
                official_citation="Law",
                jurisdiction_id="europe",
            )


class TestObligation:
    def test_deadline_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="evidence_ref"):
            Obligation(
                obligation_id="obl-1",
                document_id="doc-1",
                article_ref="Art. 5",
                subject="Notify the authority within 30 days.",
                obligation_type="DEADLINE",
            )

    def test_valid_obligation(self) -> None:
        obligation = Obligation(
            obligation_id="obl-1",
            document_id="doc-1",
            article_ref="Art. 5",
            subject="Notify the authority within 30 days.",
            obligation_type="DEADLINE",
            evidence_ref="evidence-1",
        )
        assert obligation.article_ref == "Art. 5"

    def test_requirement_type(self) -> None:
        obligation = Obligation(
            obligation_id="obl-2",
            document_id="doc-1",
            article_ref="Art. 6",
            subject="Maintain records.",
            obligation_type="REQUIREMENT",
        )
        assert obligation.obligation_type == "REQUIREMENT"


class TestAmendment:
    def test_self_amendment_rejected(self) -> None:
        with pytest.raises(ValueError, match="amend itself"):
            AmendmentRecord(
                amendment_id="amd-1",
                amends_document_id="doc-1",
                amended_by_document_id="doc-1",
                kind="AMENDMENT",
                effective_at=date(2025, 1, 1),
                evidence_ref="evidence-1",
            )

    def test_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="evidence_ref"):
            AmendmentRecord(
                amendment_id="amd-1",
                amends_document_id="doc-1",
                amended_by_document_id="doc-2",
                kind="REPEAL",
                effective_at=date(2025, 1, 1),
            )

    def test_valid_amendment(self) -> None:
        amendment = AmendmentRecord(
            amendment_id="amd-1",
            amends_document_id="doc-1",
            amends_article_ref="Art. 5",
            amended_by_document_id="doc-2",
            kind="AMENDMENT",
            effective_at=date(2025, 1, 1),
            evidence_ref="evidence-1",
        )
        assert amendment.kind == "AMENDMENT"


class TestMarketEntryWorkspace:
    def test_assessing_initial(self) -> None:
        workspace = MarketEntryWorkspace(
            workspace_id=WS_ID,
            tenant_id=TENANT,
            document_id="doc-1",
            created_by="user-1",
        )
        assert workspace.state == ComplianceState.ASSESSING
        assert workspace.legal_authority_disclosed is False

    def test_compliant_requires_disclosure(self) -> None:
        with pytest.raises(ValueError, match="legal-authority disclosure"):
            MarketEntryWorkspace(
                workspace_id=WS_ID,
                tenant_id=TENANT,
                document_id="doc-1",
                state="COMPLIANT",
                created_by="user-1",
            )

    def test_compliant_with_disclosure_ok(self) -> None:
        workspace = MarketEntryWorkspace(
            workspace_id=WS_ID,
            tenant_id=TENANT,
            document_id="doc-1",
            state="COMPLIANT",
            created_by="user-1",
            legal_authority_disclosed=True,
        )
        assert workspace.state == ComplianceState.COMPLIANT

    def test_close_requires_disclosure(self) -> None:
        workspace = MarketEntryWorkspace(
            workspace_id=WS_ID,
            tenant_id=TENANT,
            document_id="doc-1",
            created_by="user-1",
        )
        with pytest.raises(ValueError, match="legal-authority disclosure"):
            workspace.close(disclosed=False)

    def test_close_with_disclosure(self) -> None:
        workspace = MarketEntryWorkspace(
            workspace_id=WS_ID,
            tenant_id=TENANT,
            document_id="doc-1",
            created_by="user-1",
        )
        closed = workspace.close(disclosed=True)
        assert closed.state == ComplianceState.CLOSED
        assert closed.legal_authority_disclosed is True

    def test_workspace_never_asserts_legal_authority(self) -> None:
        # The model records obligations; it does not issue legal advice.
        workspace = MarketEntryWorkspace(
            workspace_id=WS_ID,
            tenant_id=TENANT,
            document_id="doc-1",
            created_by="user-1",
        )
        assert workspace.legal_authority_disclosed is False
        assert workspace.state == ComplianceState.ASSESSING
