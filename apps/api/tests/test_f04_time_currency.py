"""WP3-T04 — F04 Time/Currency/Value/Units tests."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from axignal_api.foundations.f04_time_currency import (
    FxRate,
    MonetaryValue,
    TemporalPoint,
    ValueRange,
)


class TestTemporalPoint:
    def test_all_roles_available(self) -> None:
        for role in (
            "PUBLICATION",
            "OBSERVATION",
            "VALIDITY",
            "DEADLINE",
            "AWARD",
            "EXECUTION",
            "CORRECTION",
            "CANCELLATION",
        ):
            TemporalPoint(role=role, value=datetime(2026, 8, 7))

    def test_deadline_typed(self) -> None:
        point = TemporalPoint(role="DEADLINE", value=datetime(2026, 9, 1, 12, 0))
        assert point.role == "DEADLINE"

    def test_unknown_role_rejected(self) -> None:
        with pytest.raises(ValueError):
            TemporalPoint(role="WHATEVER", value=datetime(2026, 1, 1))


class TestMonetaryValue:
    def test_eur_value(self) -> None:
        value = MonetaryValue(amount=149.0, currency="EUR")
        assert value.value_class == "NOMINAL"
        assert value.unknown is False

    def test_unknown_currency_rejected(self) -> None:
        with pytest.raises(ValueError, match="currency"):
            MonetaryValue(amount=1.0, currency="XXX")

    def test_tax_included_requires_rate(self) -> None:
        with pytest.raises(ValueError, match="tax_rate_pct"):
            MonetaryValue(amount=100.0, currency="EUR", tax_included=True)

    def test_tax_included_with_rate_ok(self) -> None:
        value = MonetaryValue(amount=121.0, currency="EUR", tax_included=True, tax_rate_pct=21.0)
        assert value.tax_rate_pct == 21.0

    def test_real_vs_nominal(self) -> None:
        nominal = MonetaryValue(amount=100.0, currency="EUR", value_class="NOMINAL")
        real = MonetaryValue(amount=98.0, currency="EUR", value_class="REAL")
        assert nominal.value_class != real.value_class

    def test_negative_amount_rejected(self) -> None:
        with pytest.raises(ValueError):
            MonetaryValue(amount=-5.0, currency="EUR")


class TestFxRate:
    def test_versioned_fx(self) -> None:
        rate = FxRate(
            from_currency="EUR",
            to_currency="USD",
            rate=1.08,
            valid_from=date(2026, 1, 1),
            source_id="src_ecb",
        )
        assert rate.rate == 1.08

    def test_self_mapping_rejected(self) -> None:
        with pytest.raises(ValueError, match="itself"):
            FxRate(
                from_currency="EUR",
                to_currency="EUR",
                rate=1.0,
                valid_from=date(2026, 1, 1),
            )

    def test_unknown_currency_rejected(self) -> None:
        with pytest.raises(ValueError, match="from_currency"):
            FxRate(
                from_currency="XXX",
                to_currency="EUR",
                rate=1.0,
                valid_from=date(2026, 1, 1),
            )

    def test_validity_window(self) -> None:
        with pytest.raises(ValueError, match="valid_to"):
            FxRate(
                from_currency="EUR",
                to_currency="USD",
                rate=1.08,
                valid_from=date(2026, 1, 1),
                valid_to=date(2025, 1, 1),
            )


class TestValueRange:
    def test_bounded_range(self) -> None:
        rng = ValueRange(min_value=100.0, max_value=500.0, currency="EUR")
        assert rng.unknown is False

    def test_min_max_ordering(self) -> None:
        with pytest.raises(ValueError, match="min_value"):
            ValueRange(min_value=500.0, max_value=100.0, currency="EUR")

    def test_unknown_explicit(self) -> None:
        rng = ValueRange(unknown=True)
        assert rng.unknown is True

    def test_unknown_cannot_carry_bounds(self) -> None:
        with pytest.raises(ValueError, match="unknown=true"):
            ValueRange(min_value=100.0, unknown=True)

    def test_bounded_requires_bound(self) -> None:
        with pytest.raises(ValueError, match="requires min or max"):
            ValueRange()

    def test_unit_vocabulary(self) -> None:
        with pytest.raises(ValueError, match="unit"):
            ValueRange(min_value=1.0, unit="WIDGETS")
        rng = ValueRange(min_value=10.0, max_value=50.0, unit="MWH")
        assert rng.unit == "MWH"
