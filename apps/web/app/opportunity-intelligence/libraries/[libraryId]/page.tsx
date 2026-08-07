import type { Metadata } from "next";
import { notFound } from "next/navigation";

export const dynamic = "force-dynamic";

const libraries: Record<string, { name: string; description: string }> = {
  O01: {
    name: "Public Procurement",
    description:
      "TED-based opportunity intelligence: notices, lots, buyer resolution, awards and bid workspaces. Coverage is limited to admitted sources."
  },
  O02: {
    name: "Grants",
    description:
      "Funding calls, eligibility rules, topics, budgets and application workspaces."
  },
  O03: {
    name: "Regulation",
    description:
      "Legal document lifecycle, obligations, amendments and compliance workspaces. AXIGNAL records what regulations say; it does not issue legal advice."
  },
  O04: {
    name: "Infrastructure",
    description: "Projects, promoters, stages, permits and procurement links."
  },
  O05: {
    name: "Corporate",
    description:
      "Company identifiers, filings, ownership and material events with observed/inferred separation."
  },
  O06: {
    name: "Sovereign & Macro",
    description:
      "Indicators, budgets, policy priorities and scenario boundaries. Scenarios are hypotheses, never facts."
  },
  O07: {
    name: "Trade & Supply",
    description: "Flows, tariffs, restrictions and supply dependencies."
  },
  O08: {
    name: "Energy & Climate",
    description: "Assets, capacity, transition plans and climate obligations."
  },
  O09: {
    name: "Innovation & IP",
    description:
      "Patents, families, legal status and research organisations with legal-limit disclosures."
  }
};

export async function generateStaticParams() {
  return Object.keys(libraries).map((libraryId) => ({ libraryId }));
}

export async function generateMetadata({
  params
}: {
  params: Promise<{ libraryId: string }>;
}): Promise<Metadata> {
  const { libraryId } = await params;
  const library = libraries[libraryId];
  if (!library) {
    return { title: "Not found" };
  }
  return {
    title: `${library.name} — AXIGNAL Opportunity Intelligence`,
    description: library.description,
    robots: { index: true, follow: true }
  };
}

export default async function LibraryPage({
  params
}: {
  params: Promise<{ libraryId: string }>;
}) {
  const { libraryId } = await params;
  const library = libraries[libraryId];
  if (!library) {
    notFound();
  }
  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "2rem 1rem" }}>
      <p>
        <a href="/opportunity-intelligence">← Opportunity Intelligence</a>
      </p>
      <h1>{library.name}</h1>
      <p>{library.description}</p>
      <p>
        <em>
          Coverage disclosure: this library&apos;s intelligence is limited to
          sources admitted under AXIGNAL&apos;s source-admission contract.
        </em>
      </p>
    </main>
  );
}
