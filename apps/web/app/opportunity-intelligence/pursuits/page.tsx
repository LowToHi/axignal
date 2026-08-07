import type { Metadata } from "next";

import { TransitionPursuitForm } from "@/components/opportunities/transition-pursuit-form";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Pursuits — AXIGNAL",
  description: "Private pursuit workspace.",
  robots: { index: false, follow: false }
};

type Pursuit = {
  pursuit_ref: string;
  opportunity_ref: string;
  state: string;
  created_at: string;
  decided_by?: string | null;
  outcome_ref?: string | null;
};

async function fetchPursuits(): Promise<Pursuit[]> {
  try {
    const response = await fetch(
      `${process.env.AXIGNAL_PUBLIC_ORIGIN ?? "http://localhost:18080"}/api/opportunities/pursuits`,
      { cache: "no-store", signal: AbortSignal.timeout(8_000) }
    );
    if (!response.ok) {
      return [];
    }
    const data = await response.json();
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export default async function PursuitsPage() {
  const pursuits = await fetchPursuits();
  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1>Pursuits</h1>
      <p>Tenant-scoped pursuit lifecycle sobre la API real.</p>
      {pursuits.length === 0 ? (
        <p>No hay pursuits todavía.</p>
      ) : (
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Reference</th>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Opportunity</th>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>State</th>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {pursuits.map((pursuit) => (
              <tr key={pursuit.pursuit_ref}>
                <td style={{ padding: "0.5rem" }}>{pursuit.pursuit_ref}</td>
                <td style={{ padding: "0.5rem" }}>{pursuit.opportunity_ref}</td>
                <td style={{ padding: "0.5rem" }}>{pursuit.state}</td>
                <td style={{ padding: "0.5rem" }}>
                  <TransitionPursuitForm pursuitRef={pursuit.pursuit_ref} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
