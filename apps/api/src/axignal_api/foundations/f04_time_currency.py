"""F04 — Time, Currency, Value and Units (WP3-T04).

Canonical temporal/value model per contract F04:

Distinct temporal roles:
- PUBLICATION, OBSERVATION, VALIDITY, DEADLINE, AWARD, EXECUTION,
  CORRECTION, CANCELLATION.

Value support:
- currencies (ISO 4217);
- versioned FX rates (rate with valid window and source);
- nominal/real distinction;
- tax handling;
- ranges (min/max with currency/unit);
- units and magnitudes;
- intervals and explicit unknown.

Rule: temporal roles and value types are typed; unknown is explicit and
never silently zero.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

TemporalRole = Literal[
    "PUBLICATION",
    "OBSERVATION",
    "VALIDITY",
    "DEADLINE",
    "AWARD",
    "EXECUTION",
    "CORRECTION",
    "CANCELLATION",
]

KNOWN_CURRENCIES = (
    "EUR",
    "USD",
    "GBP",
    "CHF",
    "PLN",
    "SEK",
    "NOK",
    "DKK",
    "CZK",
    "HUF",
    "RON",
    "BGN",
    "HRK",
)

KNOWN_UNITS = (
    "UNIT",
    "PERCENT",
    "EUR_PER_UNIT",
    "KG",
    "TONNE",
    "MWH",
    "KWH",
    "M2",
    "M3",
    "KM",
    "MONTH",
    "YEAR",
    "FTE",
)


class TemporalPoint(BaseModel):
    """A typed temporal reference."""

    schema_version: Literal["axignal.f04.temporal.v1"] = "axignal.f04.temporal.v1"
    role: TemporalRole
    value: datetime | date
    source_id: str | None = None
    precision_note: str | None = None


class MonetaryValue(BaseModel):
    """A typed monetary value with currency and nominal/real distinction."""

    schema_version: Literal["axignal.f04.monetary.v1"] = "axignal.f04.monetary.v1"
    amount: float = Field(ge=0.0)
    currency: str = Field(min_length=3, max_length=3)
    value_class: Literal["NOMINAL", "REAL", "UNKNOWN_CLASS"] = "NOMINAL"
    tax_included: bool = False
    tax_rate_pct: float | None = Field(default=None, ge=0.0, le=100.0)
    fx_reference: str | None = None
    unknown: Literal[False] = False

    @model_validator(mode="after")
    def validate_currency(self) -> MonetaryValue:
        if self.currency not in KNOWN_CURRENCIES:
            raise ValueError(
                f"currency must be one of {KNOWN_CURRENCIES}; got {self.currency!r}"
            )
        if self.tax_included and self.tax_rate_pct is None:
            raise ValueError("tax_included=true requires tax_rate_pct")
        return self


class FxRate(BaseModel):
    """A versioned FX rate with validity window."""

    schema_version: Literal["axignal.f04.fx.v1"] = "axignal.f04.fx.v1"
    from_currency: str
    to_currency: str
    rate: float = Field(gt=0.0)
    valid_from: date
    valid_to: date | None = None
    source_id: str | None = None

    @model_validator(mode="after")
    def validate_fx(self) -> FxRate:
        if self.from_currency not in KNOWN_CURRENCIES:
            raise ValueError(f"unknown from_currency {self.from_currency!r}")
        if self.to_currency not in KNOWN_CURRENCIES:
            raise ValueError(f"unknown to_currency {self.to_currency!r}")
        if self.from_currency == self.to_currency:
            raise ValueError("FX rate cannot map a currency to itself")
        if self.valid_to and self.valid_to < self.valid_from:
            raise ValueError("valid_to must be >= valid_from")
        return self


class ValueRange(BaseModel):
    """A bounded or open range with unit and explicit unknown."""

    schema_version: Literal["axignal.f04.range.v1"] = "axignal.f04.range.v1"
    min_value: float | None = None
    max_value: float | None = None
    currency: str | None = None
    unit: str | None = None
    unknown: bool = False

    @model_validator(mode="after")
    def validate_range(self) -> ValueRange:
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            raise ValueError("min_value must be <= max_value")
        if self.unit is not None and self.unit not in KNOWN_UNITS:
            raise ValueError(f"unknown unit {self.unit!r}")
        if self.unknown and (self.min_value is not None or self.max_value is not None):
            raise ValueError("unknown=true cannot carry explicit bounds")
        if self.unknown and self.min_value is None and self.max_value is None:
            return self
        if not self.unknown and self.min_value is None and self.max_value is None:
            raise ValueError("a bounded range requires min or max")
        return self
