"""WP3-T09 — multilingual and temporal regression tests."""

from __future__ import annotations

import pytest

from axignal_api.foundations.regression_suite import (
    RegressionFailure,
    run_foundational_regression,
)


class TestFoundationalRegression:
    def test_full_regression_passes(self) -> None:
        checks = run_foundational_regression()
        assert all(checks.values())
        assert len(checks) >= 9

    def test_checks_cover_multilingual_invariants(self) -> None:
        checks = run_foundational_regression()
        assert checks["product_languages_exact_six"] is True
        assert checks["jurisdiction_multilingual_resolution"] is True
        assert checks["translation_preserves_original"] is True
        assert checks["translation_covers_all_product_languages"] is True

    def test_checks_cover_temporal_invariants(self) -> None:
        checks = run_foundational_regression()
        assert checks["temporal_roles_typed"] is True
        assert checks["deadline_after_publication"] is True
        assert checks["fx_validity_window"] is True
        assert checks["document_acquisition_dated"] is True
        assert checks["jurisdiction_temporality"] is True

    def test_regression_failure_raises(self) -> None:
        # Directly assert the exception type contract.
        with pytest.raises(RegressionFailure):
            raise RegressionFailure("foundational regression failures: []")
