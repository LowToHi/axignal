import type { Metadata } from "next";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Opportunities — AXIGNAL",
  description: "Pipeline opportunities and claims.",
  robots: { index: false, follow: false }
};

type Opportunity = {
  opportunity_ref: string;
  library_id: string;
  publication_number: string | null;
  version: number;
  state: string;
  produced_by: string;
  produced_at: string;
};

async function fetchOpportunities(): Promise<Opportunity[]> {
  try {
    const response = await fetch(
      `${process.env.AXIGNAL_PUBLIC_ORIGIN ?? "http://localhost:18080"}/api/opportunities/opportunities`,
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

export default async function OpportunitiesPage() {
  const opportunities = await fetchOpportunities();
  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1>Opportunities</h1>
      <p>Oportunidades producidas por el pipeline de ingestión (tenant-scoped).</p>
      {opportunities.length === 0 ? (
        <p>
          No hay oportunidades todavía. Ejecuta una ingestión O01 para que el
          pipeline las materialice.
        </p>
      ) : (
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Opportunity</th>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Library</th>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Notice</th>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Version</th>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>State</th>
            </tr>
          </thead>
          <tbody>
            {opportunities.map((opportunity) => (
              <tr key={opportunity.opportunity_ref}>
                <td style={{ padding: "0.5rem" }}>
                  <a href={`/opportunity-intelligence/opportunities/${opportunity.opportunity_ref}`}>
                    {opportunity.opportunity_ref}
                  </a>
                </td>
                <td style={{ padding: "0.5rem" }}>{opportunity.library_id}</td>
                <td style={{ padding: "0.5rem" }}>
                  {opportunity.publication_number ?? "—"}
                </td>
                <td style={{ padding: "0.5rem" }}>{opportunity.version}</td>
                <td style={{ padding: "0.5rem" }}>{opportunity.state}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
