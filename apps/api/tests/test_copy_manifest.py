"""WP18 — Copy manifest, landing gates and SEO tests (T15-T35)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from axignal_api.copy_manifest import (
    SHELL_1,
    SHELL_2,
    AnalyticsEvent,
    CommercialClaim,
    ConsentPreference,
    CopyEntry,
    CopyManifest,
    Disclosure,
    ExperimentVariant,
    LandingRoutes,
    SeoRoute,
    SeoState,
    SuperlativeGuard,
    UiState,
    build_landing_routes,
)

TENANT = UUID("11111111-1111-4111-8111-111111111111")


def approved_copy(**overrides: object) -> CopyEntry:
    base: dict[str, object] = {
        "copy_id": "copy-hero",
        "route": "/opportunity-intelligence",
        "shell_id": SHELL_1,
        "audience": "public",
        "locale": "es",
        "text": "Inteligencia de oportunidades globales",
        "status": "APPROVED",
        "approved_by": "Rafael López",
    }
    base.update(overrides)
    return CopyEntry(**base)


class TestCopyEntry:
    def test_approved_requires_approver(self) -> None:
        with pytest.raises(ValueError, match="approved_by"):
            approved_copy(status="APPROVED", approved_by=None)

    def test_valid_copy(self) -> None:
        entry = approved_copy()
        assert entry.locale == "es"
        assert entry.status == "APPROVED"

    def test_unknown_locale_rejected(self) -> None:
        with pytest.raises(ValueError, match="locale"):
            approved_copy(locale="xx")

    def test_unknown_shell_rejected(self) -> None:
        with pytest.raises(ValueError, match="shell"):
            approved_copy(shell_id="AXIGNAL_PROCUREMENT")

    def test_six_languages_supported(self) -> None:
        for locale in ("en", "es", "fr", "de", "pt", "it"):
            entry = approved_copy(copy_id=f"copy-{locale}", locale=locale)
            assert entry.locale == locale


class TestCommercialClaims:
    def test_claim_requires_evidence_or_coverage(self) -> None:
        with pytest.raises(ValueError, match="evidence_refs or coverage_ref"):
            CommercialClaim(
                claim_id="claim-1",
                copy_id="copy-hero",
                claim_text="We cover everything.",
            )

    def test_claim_with_evidence_ok(self) -> None:
        claim = CommercialClaim(
            claim_id="claim-1",
            copy_id="copy-hero",
            claim_text="Covers TED notices for EU public procurement.",
            evidence_refs=["probe-2026-08-07"],
        )
        assert claim.is_expired() is False

    def test_expired_claim_detected(self) -> None:
        claim = CommercialClaim(
            claim_id="claim-1",
            copy_id="copy-hero",
            claim_text="Covers TED notices.",
            coverage_ref="cov-1",
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        assert claim.is_expired() is True

    def test_superlative_rejected(self) -> None:
        with pytest.raises(ValueError, match="forbidden superlative"):
            SuperlativeGuard(copy_id="copy-hero", text="The best platform ever.")

    def test_guarantee_rejected(self) -> None:
        with pytest.raises(ValueError, match="forbidden superlative"):
            SuperlativeGuard(copy_id="copy-hero", text="We guarantee success.")

    def test_plain_copy_passes_guard(self) -> None:
        guard = SuperlativeGuard(
            copy_id="copy-hero",
            text="Monitors official EU tender notices.",
        )
        assert guard.text


class TestDisclosures:
    def test_required_disclosure_must_be_visible(self) -> None:
        with pytest.raises(ValueError, match="visible"):
            Disclosure(
                disclosure_id="disc-1",
                route="/opportunity-intelligence",
                kind="COVERAGE",
                text="Coverage is limited to admitted sources.",
                visible=False,
            )

    def test_valid_disclosure(self) -> None:
        disclosure = Disclosure(
            disclosure_id="disc-1",
            route="/opportunity-intelligence",
            kind="COVERAGE",
            text="Coverage is limited to admitted sources.",
        )
        assert disclosure.visible is True

    def test_pricing_hypothesis_disclosure(self) -> None:
        disclosure = Disclosure(
            disclosure_id="disc-2",
            route="/opportunity-intelligence/precios",
            kind="PRICING_HYPOTHESIS",
            text="Prices shown are hypotheses until billing is authorized.",
        )
        assert disclosure.kind == "PRICING_HYPOTHESIS"


class TestSeo:
    def test_pe_routes_cannot_be_indexable(self) -> None:
        with pytest.raises(ValueError, match="cannot be indexable"):
            SeoRoute(
                route="/empleo-publico",
                shell_id=SHELL_2,
                state=SeoState.INDEXABLE,
            )

    def test_pe_draft_forced_noindex(self) -> None:
        route = SeoRoute(route="/empleo-publico", shell_id=SHELL_2)
        assert route.state == SeoState.DRAFT
        assert route.robots == "noindex, nofollow"
        assert route.in_sitemap is False

    def test_shell1_indexable(self) -> None:
        route = SeoRoute(
            route="/opportunity-intelligence",
            shell_id=SHELL_1,
            state=SeoState.INDEXABLE,
            canonical="https://axignal.com/opportunity-intelligence",
        )
        assert route.canonical.startswith("https://")


class TestAnalyticsAndConsent:
    def test_non_pageview_requires_consent(self) -> None:
        with pytest.raises(ValueError, match="consent"):
            AnalyticsEvent(
                event_id="ev-1",
                shell_id=SHELL_1,
                route="/",
                locale="es",
                event_type="CONVERSION",
            )

    def test_pageview_without_consent_ok(self) -> None:
        event = AnalyticsEvent(
            event_id="ev-1",
            shell_id=SHELL_1,
            route="/",
            locale="es",
            event_type="PAGE_VIEW",
        )
        assert event.event_type == "PAGE_VIEW"

    def test_consent_preferences_default_functional(self) -> None:
        prefs = ConsentPreference(preference_id="pref-1", tenant_id=TENANT)
        assert prefs.analytics is False
        assert prefs.functional is True


class TestExperiments:
    def test_price_impact_rejected(self) -> None:
        with pytest.raises(ValueError, match="price discrimination"):
            ExperimentVariant(
                experiment_id="exp-1",
                variant_id="var-1",
                shell_id=SHELL_1,
                description="Test variant",
                price_impact=True,
            )

    def test_no_optout_rejected(self) -> None:
        with pytest.raises(ValueError, match="opt-out"):
            ExperimentVariant(
                experiment_id="exp-1",
                variant_id="var-1",
                shell_id=SHELL_1,
                description="Test variant",
                opt_out_available=False,
            )

    def test_valid_experiment(self) -> None:
        variant = ExperimentVariant(
            experiment_id="exp-1",
            variant_id="var-1",
            shell_id=SHELL_1,
            description="Test variant",
        )
        assert variant.opt_out_available is True


class TestUiStates:
    def test_error_requires_copy(self) -> None:
        with pytest.raises(ValueError, match="copy_ref"):
            UiState(state_id="st-1", route="/", state="ERROR")

    def test_valid_states(self) -> None:
        for state in ("LOADING", "EMPTY", "PARTIAL", "STALE", "RESTRICTED", "RECOVERY"):
            UiState(state_id=f"st-{state}", route="/", state=state)
        UiState(state_id="st-error", route="/", state="ERROR", copy_ref="copy-error")


class TestCopyManifest:
    def test_add_get_and_history(self) -> None:
        manifest = CopyManifest()
        manifest.add(approved_copy())
        assert manifest.get("copy-hero") is not None
        manifest.add(approved_copy(text="Nueva versión"))
        assert len(manifest) == 1
        assert len(manifest._history["copy-hero"]) == 1

    def test_effective_resolution(self) -> None:
        manifest = CopyManifest()
        manifest.add(approved_copy())
        effective = manifest.get_effective("/opportunity-intelligence", "es")
        assert effective is not None
        assert effective.copy_id == "copy-hero"

    def test_draft_not_effective(self) -> None:
        manifest = CopyManifest()
        manifest.add(approved_copy(status="DRAFT"))
        assert manifest.get_effective("/opportunity-intelligence", "es") is None

    def test_rollback(self) -> None:
        manifest = CopyManifest()
        manifest.add(approved_copy(text="v1"))
        manifest.add(approved_copy(text="v2"))
        rolled_back = manifest.rollback("copy-hero")
        assert rolled_back is not None
        assert rolled_back.text == "v1"

    def test_claims_bound_to_copy(self) -> None:
        manifest = CopyManifest()
        manifest.add(approved_copy())
        manifest.add_claim(
            CommercialClaim(
                claim_id="claim-1",
                copy_id="copy-hero",
                claim_text="Covers TED notices.",
                evidence_refs=["probe-1"],
            )
        )
        assert len(manifest.claims_for("copy-hero")) == 1


class TestLandingRoutes:
    def test_structure(self) -> None:
        routes = build_landing_routes()
        # 1 corporate + 1 shell1 + 1 shell2 + 2 pricing + 9 libraries.
        assert len(routes) == 14

    def test_pe_landing_not_indexable(self) -> None:
        routes = build_landing_routes()
        pe = routes.routes_for(SHELL_2)
        assert len(pe) == 2
        assert all(r["indexable"] is False for r in pe)
        assert all(r["state"] == "DRAFT_HIDDEN" for r in pe)

    def test_library_pages_in_shell1(self) -> None:
        routes = build_landing_routes()
        library_pages = [
            r for r in routes.routes_for(SHELL_1) if r["kind"] == "LIBRARY_PAGE"
        ]
        assert len(library_pages) == 9

    def test_pe_landing_forced_hidden(self) -> None:
        with pytest.raises(ValueError, match="not be indexable"):
            LandingRoutes().register(
                "/empleo-publico",
                SHELL_2,
                kind="SHELL2_LANDING",
                indexable=True,
            )
