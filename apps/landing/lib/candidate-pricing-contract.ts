import type { CandidatePlan } from "./landing-data";

export type CommercialRuntime = {
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

export function parseCandidatePlans(
  runtime: CommercialRuntime
): readonly CandidatePlan[] {
  const pricing = runtime.pricing_contract;
  const currency = pricing?.currency;

  if (pricing?.status !== "CANDIDATE_ONLY" || currency !== "EUR") {
    throw new Error("The controlled-access candidate price book is not available.");
  }

  const plans = (pricing.plans ?? []).flatMap((plan): CandidatePlan[] => {
    const planCode = plan.plan_code;
    if (!planCode) return [];

    const presentation = supportedOffers.get(planCode);
    if (!presentation || plan.commercial_activation_authorised !== false) {
      return [];
    }

    if (planCode === "CONTROLLED_TRIAL_7D") {
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
          planCode,
          name: presentation.name,
          description: presentation.description,
          amountMinor: 0,
          currency,
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
      plan.amount_minor <= 0 ||
      typeof plan.seat_floor !== "number" ||
      typeof plan.seat_ceiling !== "number" ||
      plan.seat_floor <= 0 ||
      plan.seat_ceiling < plan.seat_floor
    ) {
      return [];
    }

    return [
      {
        planCode,
        name: presentation.name,
        description: presentation.description,
        amountMinor: plan.amount_minor,
        currency,
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
    throw new Error(
      "The B2G offer presentation is incomplete or commercially activated."
    );
  }

  return plans;
}
