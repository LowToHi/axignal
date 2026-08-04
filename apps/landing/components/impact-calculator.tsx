"use client";

import { useMemo, useState } from "react";
import { trackLandingEvent } from "@/lib/analytics";
import { calculateIllustrativeImpact } from "@/lib/landing-data";
import type { LandingMessages, Locale } from "@/lib/i18n";

type ImpactCalculatorProps = {
  locale: Locale;
  messages: LandingMessages["outcomes"];
};

export function ImpactCalculator({ locale, messages }: ImpactCalculatorProps) {
  const [opportunities, setOpportunities] = useState(20);
  const [hours, setHours] = useState(6);
  const [reductionPercent, setReductionPercent] = useState(30);
  const [hourlyRate, setHourlyRate] = useState(65);

  const result = useMemo(
    () => calculateIllustrativeImpact({ opportunities, hours, reductionPercent, hourlyRate }),
    [opportunities, hours, reductionPercent, hourlyRate]
  );
  const currency = new Intl.NumberFormat(locale, {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0
  });

  const update = (setter: (value: number) => void, value: number) => {
    setter(value);
    trackLandingEvent("calculator_update", { locale });
  };

  return (
    <div className="impact-calculator">
      <div className="calculator-inputs">
        <label>
          <span>{messages.inputs.opportunities}</span>
          <input
            type="range"
            min="1"
            max="100"
            value={opportunities}
            onChange={(event) => update(setOpportunities, Number(event.currentTarget.value))}
          />
          <output>{opportunities}</output>
        </label>
        <label>
          <span>{messages.inputs.hours}</span>
          <input
            type="range"
            min="1"
            max="40"
            value={hours}
            onChange={(event) => update(setHours, Number(event.currentTarget.value))}
          />
          <output>{hours}h</output>
        </label>
        <label>
          <span>{messages.inputs.reduction}</span>
          <input
            type="range"
            min="5"
            max="60"
            step="5"
            value={reductionPercent}
            onChange={(event) => update(setReductionPercent, Number(event.currentTarget.value))}
          />
          <output>{reductionPercent}%</output>
        </label>
        <label>
          <span>{messages.inputs.rate}</span>
          <input
            type="range"
            min="20"
            max="250"
            step="5"
            value={hourlyRate}
            onChange={(event) => update(setHourlyRate, Number(event.currentTarget.value))}
          />
          <output>{currency.format(hourlyRate)}</output>
        </label>
      </div>
      <div className="calculator-results" aria-live="polite">
        <article>
          <span>{messages.result.hours}</span>
          <strong>{result.redirectedHours.toLocaleString(locale)}h</strong>
        </article>
        <article>
          <span>{messages.result.value}</span>
          <strong>{currency.format(result.illustrativeValue)}</strong>
        </article>
        <p>{messages.note}</p>
      </div>
    </div>
  );
}
