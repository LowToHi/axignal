import "server-only";

import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

import type { CandidatePlan } from "./landing-data";

type CommercialRuntime = {
  pricing_contract?: {
    status?: string;
    currency?: string;
    plans?: Array<{
      plan_code?: string;
      billing_mode?: string;
      amount_minor?: number | null;
      duration_days?: number;
      ai_token_budget?: number;
      self_service_activation?: boolean;
      seat_floor?: number;
      seat_ceiling?: number | null;
      commercial_activation_authorised?: boolean;
    }>;
  };
};

const supportedOffers = new Map([
  [
    "CONTROLLED_TRIAL_7D",
    {
      name: "7-day B2G trial",
      description: "Test one public-procurement market and qualification workflow",
      activationState: "CONTROLLED_TRIAL_ONLY" as const,
      ctaLabel: "Request 7-day trial"
    }
  ],
  [
    "PROFESSIONAL_MONTHLY",
    {
      name: "Professional",
      description: "For focused B2G and tender-intelligence teams",
      activationState: "CONTROLLED_ACCESS_ONLY" as const,
      ctaLabel: "Discuss Professional"
    }
  ],
  [
    "TEAM_MONTHLY",
    {
      name: "Team",
      description: "For shared public-sector pipeline qualification and review",
      activationState: "CONTROLLED_ACCESS_ONLY" as const,
      ctaLabel: "Discuss Team"
    }
  ]
]);

export async function getCandidatePlans(): Promise<readonly CandidatePlan[]> {
  const runtimePath = resolve(
    process.cwd(),
    "../../data/commercial/commercial-runtime-pricing-stripe-runtime.v0.1.json"
  );
  const runtime = JSON.parse(await readFile(runtimePath, "utf8")) as CommercialRuntime;
  const pricing = runtime.pricing_contract;

  if (pricing?.status !== "CANDIDATE_ONLY" || pricing.currency !== "EUR") {
    throw new Error("The controlled-access candidate price book is not available.");
  }

  const plans = (pricing.plans ?? []).flatMap((plan): CandidatePlan[] => {
    const presentation = plan.plan_code ? supportedOffers.get(plan.plan_code) : undefined;
    if (!presentation || plan.commercial_activation_authorised !== false) {
      return [];
    }

    if (plan.plan_code === "CONTROLLED_TRIAL_7D") {
      if (
        plan.billing_mode !== "NO_CHARGE" ||
        plan.amount_minor !== 0 ||
        plan.duration_days !== 7 ||
        typeof plan.ai_token_budget !== "number" ||
        plan.ai_token_budget <= 0 ||
        plan.self_service_activation !== false
      ) {
        return [];
      }

      return [
        {
          planCode: plan.plan_code,
          name: presentation.name,
          description: presentation.description,
          amountMinor: 0,
          currency: pricing.currency!,
          billingPeriod: "trial",
          durationDays: plan.duration_days,
          aiTokenBudget: plan.ai_token_budget,
          seatFloor: null,
          seatCeiling: null,
          activationState: presentation.activationState,
          ctaLabel: presentation.ctaLabel
        }
      ];
    }

    if (
      plan.billing_mode !== "RECURRING_MONTHLY" ||
      typeof plan.amount_minor !== "number" ||
      typeof plan.seat_floor !== "number" ||
      typeof plan.seat_ceiling !== "number"
    ) {
      return [];
    }

    return [
      {
        planCode: plan.plan_code!,
        name: presentation.name,
        description: presentation.description,
        amountMinor: plan.amount_minor,
        currency: pricing.currency!,
        billingPeriod: "month",
        durationDays: null,
        aiTokenBudget: null,
        seatFloor: plan.seat_floor,
        seatCeiling: plan.seat_ceiling,
        activationState: presentation.activationState,
        ctaLabel: presentation.ctaLabel
      }
    ];
  });

  if (plans.length !== supportedOffers.size) {
    throw new Error("The B2G offer presentation is incomplete or commercially activated.");
  }

  return plans;
}
