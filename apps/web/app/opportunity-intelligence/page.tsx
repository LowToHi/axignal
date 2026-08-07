import type { Metadata } from "next";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "AXIGNAL Opportunity Intelligence",
  description:
    "Global opportunity intelligence and evidence-governed investigation for public procurement and beyond.",
  robots: { index: true, follow: true }
};

type Library = {
  library_id: string;
  name: string;
  library_type?: string;
  product_shell_ids?: string[];
};

async function fetchLibraries(): Promise<Library[]> {
  try {
    const apiUrl = process.env.AXIGNAL_API_URL?.replace(/\/$/, "");
    if (!apiUrl) {
      return [];
    }
    const response = await fetch(`${apiUrl}/v1/opportunities/libraries`, {
      cache: "no-store",
      signal: AbortSignal.timeout(8_000)
    });
    if (!response.ok) {
      return [];
    }
    const data = await response.json();
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

const descriptions: Record<string, string> = {
  O01: "Tenders and bid intelligence.",
  O02: "Funding calls and applications.",
  O03: "Legal obligations and compliance.",
  O04: "Projects and procurement links.",
  O05: "Filings, ownership, expansion signals.",
  O06: "Indicators and scenario context.",
  O07: "Flows, tariffs, dependencies.",
  O08: "Assets, transitions, obligations.",
  O09: "Patents, families, R&D."
};

export default async function OpportunityIntelligencePage() {
  const libraries = await fetchLibraries();
  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1>AXIGNAL Opportunity Intelligence</h1>
      <p>
        Global opportunity intelligence and evidence-governed investigation.
        Signals become admitted evidence, candidate claims, opportunities and
        operational workspaces — never unsupported conclusions.
      </p>
      <h2>Libraries</h2>
      {libraries.length === 0 ? (
        <p>Libraries unavailable (API not reachable).</p>
      ) : (
        <ul>
          {libraries.map((library) => (
            <li key={library.library_id}>
              <a href={`/opportunity-intelligence/libraries/${library.library_id}`}>
                {library.name}
              </a>
              {" — "}
              {descriptions[library.library_id] ?? "Opportunity library."}
            </li>
          ))}
        </ul>
      )}
      <p>
        <a href="/opportunity-intelligence/pricing">Pricing</a>
      </p>
    </main>
  );
}
