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
      seat_floor?: number;
      seat_ceiling?: number | null;
      commercial_activation_authorised?: boolean;
    }>;
  };
};

const supportedPlans = new Map([
  ["PROFESSIONAL_MONTHLY", { name: "Professional", description: "For focused research teams" }],
  ["TEAM_MONTHLY", { name: "Team", description: "For shared research and review" }]
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
    const presentation = plan.plan_code ? supportedPlans.get(plan.plan_code) : undefined;
    if (
      !presentation ||
      plan.billing_mode !== "RECURRING_MONTHLY" ||
      typeof plan.amount_minor !== "number" ||
      typeof plan.seat_floor !== "number" ||
      typeof plan.seat_ceiling !== "number" ||
      plan.commercial_activation_authorised !== false
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
        seatFloor: plan.seat_floor,
        seatCeiling: plan.seat_ceiling,
        activationState: "CONTROLLED_ACCESS_ONLY"
      }
    ];
  });

  if (plans.length !== supportedPlans.size) {
    throw new Error("The landing price presentation is incomplete or commercially activated.");
  }

  return plans;
}
