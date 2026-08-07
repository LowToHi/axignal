import type { Metadata } from "next";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Pricing — AXIGNAL Opportunity Intelligence",
  description:
    "Plan hypotheses for AXIGNAL Opportunity Intelligence. Prices shown are hypotheses until billing is authorized.",
  robots: { index: true, follow: true }
};

type Price = {
  price_id: string;
  plan_id: string;
  amount_cents: number;
  currency: string;
  interval_unit: string;
  active: boolean;
};

type Plan = {
  plan_id: string;
  name: string;
  seats: number;
  status: string;
};

async function fetchPricing(): Promise<{
  plans: Plan[];
  prices: Price[];
}> {
  try {
    const apiUrl = process.env.AXIGNAL_API_URL?.replace(/\/$/, "");
    if (!apiUrl) {
      return { plans: [], prices: [] };
    }
    const response = await fetch(`${apiUrl}/v1/billing/sandbox/catalog`, {
      cache: "no-store",
      signal: AbortSignal.timeout(8_000)
    });
    if (!response.ok) {
      return { plans: [], prices: [] };
    }
    const data = await response.json();
    return {
      plans: Array.isArray(data.plans) ? data.plans : [],
      prices: Array.isArray(data.prices) ? data.prices : []
    };
  } catch {
    return { plans: [], prices: [] };
  }
}

function priceForPlan(prices: Price[], planId: string): Price | undefined {
  return prices.find(
    (price) => price.plan_id === planId && price.active
  );
}

function formatPrice(price: Price): string {
  return `${(price.amount_cents / 100).toFixed(2)} ${price.currency}/${price.interval_unit}`;
}

export default async function PricingPage() {
  const { plans, prices } = await fetchPricing();
  const shell1Plans = plans.filter(
    (plan) => plan.plan_id.startsWith("plan-oi-")
  );
  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1>Pricing</h1>
      <p>
        Pricing hypotheses for AXIGNAL Opportunity Intelligence. No charge is
        made until billing is authorized.
      </p>
      {shell1Plans.length === 0 ? (
        <p>Pricing unavailable (API not reachable).</p>
      ) : (
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Plan</th>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Seats</th>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Hypothesis</th>
            </tr>
          </thead>
          <tbody>
            {shell1Plans.map((plan) => {
              const price = priceForPlan(prices, plan.plan_id);
              return (
                <tr key={plan.plan_id}>
                  <td style={{ padding: "0.5rem" }}>{plan.name}</td>
                  <td style={{ padding: "0.5rem" }}>{plan.seats}</td>
                  <td style={{ padding: "0.5rem" }}>
                    {price ? formatPrice(price) : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
      <p>
        <em>
          Disclosure: these are pricing hypotheses. Live billing is not
          authorized in the current contract state.
        </em>
      </p>
    </main>
  );
}
