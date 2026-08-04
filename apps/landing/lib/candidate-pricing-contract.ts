import { AXIGNAL_PRICE_BOOK } from "./canonical-commercial-contract";

export type CandidatePlan = {
  planCode: string;
  name: string;
  description: string;
  amountMinor: number;
  currency: "EUR";
  billingPeriod: "trial" | "month";
  durationDays: number | null;
  aiTokenBudget: number | null;
  seatFloor: number | null;
  seatCeiling: number | null;
  activationState: "CONTROLLED_TRIAL_ONLY" | "CONTROLLED_ACCESS_ONLY";
  ctaLabel: string;
};

type OfferPresentation = {
  name: string;
  description: string;
  activationState: "CONTROLLED_TRIAL_ONLY" | "CONTROLLED_ACCESS_ONLY";
  ctaLabel: string;
};

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

const supportedOffers: ReadonlyMap<string, OfferPresentation> = new Map([
  [
    AXIGNAL_PRICE_BOOK.plans.controlledTrial.code,
    {
      name: "7-day B2G trial",
      description: "Test one public-procurement market and qualification workflow",
      activationState: "CONTROLLED_TRIAL_ONLY",
      ctaLabel: "Request 7-day trial"
    }
  ],
  [
    AXIGNAL_PRICE_BOOK.plans.professional.code,
    {
      name: "Professional",
      description: "For focused B2G and tender-intelligence teams",
      activationState: "CONTROLLED_ACCESS_ONLY",
      ctaLabel: "Discuss Professional"
    }
  ],
  [
    AXIGNAL_PRICE_BOOK.plans.team.code,
    {
      name: "Team",
      description: "For shared public-sector pipeline qualification and review",
      activationState: "CONTROLLED_ACCESS_ONLY",
      ctaLabel: "Discuss Team"
    }
  ]
]);

export function parseCandidatePlans(
  runtime: CommercialRuntime
): readonly CandidatePlan[] {
  const pricing = runtime.pricing_contract;

  if (
    pricing?.status !== "CANDIDATE_ONLY" ||
    pricing.currency !== AXIGNAL_PRICE_BOOK.currency
  ) {
    throw new Error("The controlled-access candidate price book is not available.");
  }

  const plans = (pricing.plans ?? []).flatMap((plan): CandidatePlan[] => {
    const planCode = plan.plan_code;
    if (!planCode) return [];

    const presentation = supportedOffers.get(planCode);
    if (!presentation || plan.commercial_activation_authorised !== false) {
      return [];
    }

    if (planCode === AXIGNAL_PRICE_BOOK.plans.controlledTrial.code) {
      const canonicalTrial = AXIGNAL_PRICE_BOOK.plans.controlledTrial;
      if (
        plan.billing_mode !== "NO_CHARGE" ||
        plan.amount_minor !== canonicalTrial.amountMinor ||
        plan.duration_days !== canonicalTrial.durationDays ||
        plan.ai_token_budget !== canonicalTrial.cumulativeTokens ||
        plan.self_service_activation !== false
      ) {
        return [];
      }

      return [
        {
          planCode,
          name: presentation.name,
          description: presentation.description,
          amountMinor: canonicalTrial.amountMinor,
          currency: AXIGNAL_PRICE_BOOK.currency,
          billingPeriod: "trial",
          durationDays: canonicalTrial.durationDays,
          aiTokenBudget: canonicalTrial.cumulativeTokens,
          seatFloor: null,
          seatCeiling: null,
          activationState: presentation.activationState,
          ctaLabel: presentation.ctaLabel
        }
      ];
    }

    const canonicalAmount =
      planCode === AXIGNAL_PRICE_BOOK.plans.professional.code
        ? AXIGNAL_PRICE_BOOK.plans.professional.amountMinor
        : planCode === AXIGNAL_PRICE_BOOK.plans.team.code
          ? AXIGNAL_PRICE_BOOK.plans.team.amountMinor
          : null;

    if (
      canonicalAmount === null ||
      plan.billing_mode !== "RECURRING_MONTHLY" ||
      plan.amount_minor !== canonicalAmount ||
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
        amountMinor: canonicalAmount,
        currency: AXIGNAL_PRICE_BOOK.currency,
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
