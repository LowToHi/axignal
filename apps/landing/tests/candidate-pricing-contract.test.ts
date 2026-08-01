import assert from "node:assert/strict";
import { test } from "node:test";

import {
  parseCandidatePlans,
  type CommercialRuntime
} from "../lib/candidate-pricing-contract";

function validRuntime(): CommercialRuntime {
  return {
    pricing_contract: {
      status: "CANDIDATE_ONLY",
      currency: "EUR",
      plans: [
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
        }
      ]
    }
  };
}

function cloneRuntime(): CommercialRuntime {
  return structuredClone(validRuntime());
}

test("candidate price book materialises the exact controlled offers", () => {
  const plans = parseCandidatePlans(validRuntime());

  assert.equal(plans.length, 3);
  assert.deepEqual(
    plans.map((plan) => [plan.planCode, plan.amountMinor, plan.seatCeiling]),
    [
      ["CONTROLLED_TRIAL_7D", 0, null],
      ["PROFESSIONAL_MONTHLY", 14_900, 3],
      ["TEAM_MONTHLY", 39_900, 15]
    ]
  );
  assert.equal(plans[0]?.durationDays, 7);
  assert.equal(plans[0]?.aiTokenBudget, 1_000_000);
  assert.equal(plans[0]?.activationState, "CONTROLLED_TRIAL_ONLY");
  assert.equal(plans[1]?.activationState, "CONTROLLED_ACCESS_ONLY");
});

test("candidate price book fails closed for non-candidate status or currency", () => {
  const active = cloneRuntime();
  if (active.pricing_contract) active.pricing_contract.status = "ACTIVE";
  assert.throws(
    () => parseCandidatePlans(active),
    /candidate price book is not available/
  );

  const wrongCurrency = cloneRuntime();
  if (wrongCurrency.pricing_contract) {
    wrongCurrency.pricing_contract.currency = "USD";
  }
  assert.throws(
    () => parseCandidatePlans(wrongCurrency),
    /candidate price book is not available/
  );
});

test("candidate price book rejects any commercially authorised offer", () => {
  const runtime = cloneRuntime();
  const professional = runtime.pricing_contract?.plans?.find(
    (plan) => plan.plan_code === "PROFESSIONAL_MONTHLY"
  );
  if (professional) professional.commercial_activation_authorised = true;

  assert.throws(
    () => parseCandidatePlans(runtime),
    /incomplete or commercially activated/
  );
});

test("controlled trial must remain seven days, bounded and non-self-service", () => {
  const runtime = cloneRuntime();
  const trial = runtime.pricing_contract?.plans?.find(
    (plan) => plan.plan_code === "CONTROLLED_TRIAL_7D"
  );
  if (trial) trial.ai_token_budget = 0;

  assert.throws(
    () => parseCandidatePlans(runtime),
    /incomplete or commercially activated/
  );
});

test("paid plans require positive amounts and coherent seat bounds", () => {
  const invalidAmount = cloneRuntime();
  const professional = invalidAmount.pricing_contract?.plans?.find(
    (plan) => plan.plan_code === "PROFESSIONAL_MONTHLY"
  );
  if (professional) professional.amount_minor = 0;
  assert.throws(
    () => parseCandidatePlans(invalidAmount),
    /incomplete or commercially activated/
  );

  const invalidSeats = cloneRuntime();
  const team = invalidSeats.pricing_contract?.plans?.find(
    (plan) => plan.plan_code === "TEAM_MONTHLY"
  );
  if (team) team.seat_ceiling = 3;
  assert.throws(
    () => parseCandidatePlans(invalidSeats),
    /incomplete or commercially activated/
  );
});

test("unknown plans cannot replace any required controlled offer", () => {
  const runtime = cloneRuntime();
  runtime.pricing_contract?.plans?.pop();
  runtime.pricing_contract?.plans?.push({
    plan_code: "UNREVIEWED_PLAN",
    billing_mode: "RECURRING_MONTHLY",
    amount_minor: 999,
    seat_floor: 1,
    seat_ceiling: 1,
    commercial_activation_authorised: false
  });

  assert.throws(
    () => parseCandidatePlans(runtime),
    /incomplete or commercially activated/
  );
});
