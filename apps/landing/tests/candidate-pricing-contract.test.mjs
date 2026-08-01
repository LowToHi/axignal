import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { candidatePlansFromRuntime } from "../lib/candidate-pricing-contract.ts";

const validPlans = [
  {
    plan_code: "CONTROLLED_TRIAL_7D",
    billing_mode: "NO_CHARGE",
    amount_minor: 0,
    duration_days: 7,
    ai_token_budget: 1_000_000,
    self_service_activation: false,
    commercial_activation_authorised: false
  },
  {
    plan_code: "PROFESSIONAL_MONTHLY",
    billing_mode: "RECURRING_MONTHLY",
    amount_minor: 14_900,
    seat_floor: 1,
    seat_ceiling: 3,
    commercial_activation_authorised: false
  },
  {
    plan_code: "TEAM_MONTHLY",
    billing_mode: "RECURRING_MONTHLY",
    amount_minor: 39_900,
    seat_floor: 4,
    seat_ceiling: 15,
    commercial_activation_authorised: false
  },
  {
    plan_code: "ENTERPRISE_CONTRACT",
    billing_mode: "QUOTE_ONLY",
    amount_minor: null,
    seat_floor: 10,
    seat_ceiling: null,
    commercial_activation_authorised: false
  }
];

function validRuntime() {
  return {
    pricing_contract: {
      status: "CANDIDATE_ONLY",
      currency: "EUR",
      plans: structuredClone(validPlans)
    }
  };
}

test("the repository price book exposes only the three controlled offers", async () => {
  const runtime = JSON.parse(
    await readFile(
      new URL(
        "../../../data/commercial/commercial-runtime-pricing-stripe-runtime.v0.1.json",
        import.meta.url
      ),
      "utf8"
    )
  );
  const plans = candidatePlansFromRuntime(runtime);

  assert.deepEqual(
    plans.map((plan) => plan.planCode),
    ["CONTROLLED_TRIAL_7D", "PROFESSIONAL_MONTHLY", "TEAM_MONTHLY"]
  );
  assert.equal(plans[0].amountMinor, 0);
  assert.equal(plans[0].durationDays, 7);
  assert.equal(plans[0].aiTokenBudget, 1_000_000);
  assert.equal(plans[1].amountMinor, 14_900);
  assert.deepEqual([plans[1].seatFloor, plans[1].seatCeiling], [1, 3]);
  assert.equal(plans[2].amountMinor, 39_900);
  assert.deepEqual([plans[2].seatFloor, plans[2].seatCeiling], [4, 15]);
});

test("candidate pricing rejects a non-candidate or non-EUR price book", () => {
  const active = validRuntime();
  active.pricing_contract.status = "ACTIVE";
  assert.throws(
    () => candidatePlansFromRuntime(active),
    /controlled-access candidate price book is not available/
  );

  const dollars = validRuntime();
  dollars.pricing_contract.currency = "USD";
  assert.throws(
    () => candidatePlansFromRuntime(dollars),
    /controlled-access candidate price book is not available/
  );
});

test("candidate pricing fails closed when any supported offer is commercially active", () => {
  const runtime = validRuntime();
  runtime.pricing_contract.plans[1].commercial_activation_authorised = true;

  assert.throws(
    () => candidatePlansFromRuntime(runtime),
    /offer presentation is incomplete or commercially activated/
  );
});

test("the trial remains no-charge, bounded and manually activated", () => {
  const runtime = validRuntime();
  runtime.pricing_contract.plans[0].self_service_activation = true;

  assert.throws(
    () => candidatePlansFromRuntime(runtime),
    /offer presentation is incomplete or commercially activated/
  );
});

test("monthly offers require explicit finite seat boundaries", () => {
  const runtime = validRuntime();
  runtime.pricing_contract.plans[2].seat_ceiling = null;

  assert.throws(
    () => candidatePlansFromRuntime(runtime),
    /offer presentation is incomplete or commercially activated/
  );
});

test("unsupported quote-only packages never leak into self-service presentation", () => {
  const plans = candidatePlansFromRuntime(validRuntime());

  assert.equal(plans.length, 3);
  assert.equal(plans.some((plan) => plan.planCode === "ENTERPRISE_CONTRACT"), false);
  assert.equal(plans.every((plan) => plan.currency === "EUR"), true);
});
