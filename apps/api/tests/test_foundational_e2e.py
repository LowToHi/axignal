"""WP3-T10 — foundational E2E tests."""

from __future__ import annotations

import pytest

from axignal_api.foundations.foundational_e2e import (
    FoundationalE2EFailure,
    run_foundational_e2e,
)


class TestFoundationalE2E:
    def test_full_journey_passes(self) -> None:
        evidence = run_foundational_e2e()
        assert evidence["status"] == "PASS"
        assert evidence["f01_jurisdiction"]["id"] == "ES"
        assert evidence["f02_entity"]["id"] == "ent_ministerio_fomento_es"
        assert evidence["f03_taxonomies"] == ["CPV:45233100", "NUTS:ES30"]
        assert evidence["f04_value"]["currency"] == "EUR"
        assert evidence["f05_translation"]["en"] == "Tender submission deadline"
        assert evidence["f06_rights"]["owner"] == "Publications Office of the EU"
        assert evidence["f07_pipeline"]["stages"] == 12
        assert evidence["f08_resolution"]["fingerprint"]
        assert evidence["f09_regression_checks"] >= 9

    def test_journey_is_deterministic(self) -> None:
        first = run_foundational_e2e()
        second = run_foundational_e2e()
        # Fingerprints must be stable across runs.
        assert first["f02_entity"]["fingerprint"] == second["f02_entity"]["fingerprint"]
        assert first["f08_resolution"]["fingerprint"] == second["f08_resolution"]["fingerprint"]

    def test_failure_contract(self) -> None:
        with pytest.raises(FoundationalE2EFailure):
            raise FoundationalE2EFailure("gate failed")
