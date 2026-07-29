export type ClaimState = "OBSERVED" | "CALCULATED" | "INFERRED" | "CONTRADICTED" | "UNKNOWN";

export type StoryStep = {
  id: string;
  index: string;
  eyebrow: string;
  title: string;
  body: string;
  signal: string;
  claimState: ClaimState;
  metric: string;
  detail: string;
};

export type CitySignal = {
  id: string;
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  score: number;
  state: ClaimState;
  label: string;
};

export const storySteps: readonly StoryStep[] = [
  {
    id: "noise",
    index: "01",
    eyebrow: "THE SIGNAL PROBLEM",
    title: "The world produces more information than decisions can absorb.",
    body: "Markets, policy, infrastructure and ownership move at different speeds. AXIGNAL keeps the uncertainty visible instead of compressing it into a confident answer.",
    signal: "6,412",
    claimState: "UNKNOWN",
    metric: "unresolved observations",
    detail: "Synthetic demonstration · no live market data"
  },
  {
    id: "question",
    index: "02",
    eyebrow: "NAVIGATOR",
    title: "Begin with a question. Preserve the investigation.",
    body: "Navigator turns intent into a persistent ResearchRun. Every lens, filter, claim, source and contradiction remains attached to the same context.",
    signal: "1",
    claimState: "OBSERVED",
    metric: "persistent investigation",
    detail: "Ask → explore → verify → compare → track"
  },
  {
    id: "geography",
    index: "03",
    eyebrow: "GLOBE",
    title: "Geography becomes an analytical surface.",
    body: "The Globe reveals where signals converge across Madrid, London, Paris and Berlin without pretending that attention is evidence.",
    signal: "4",
    claimState: "CALCULATED",
    metric: "candidate locations",
    detail: "Synthetic European opportunity map"
  },
  {
    id: "relationships",
    index: "04",
    eyebrow: "RELATIONSHIPS",
    title: "Opportunity is rarely local.",
    body: "Capital, regulation, infrastructure and supply chains transmit effects across borders. Typed relationships expose the route, not just the destination.",
    signal: "9",
    claimState: "INFERRED",
    metric: "typed transmissions",
    detail: "Inference remains separate from observation"
  },
  {
    id: "evidence",
    index: "05",
    eyebrow: "CLAIMS + EVIDENCE",
    title: "Every claim carries its support and its limits.",
    body: "Source provenance, freshness, transformations and coverage stay inspectable. Contradictions remain first-class objects.",
    signal: "14",
    claimState: "OBSERVED",
    metric: "evidence objects",
    detail: "Original source references preserved"
  },
  {
    id: "boundary",
    index: "06",
    eyebrow: "ADMISSION BOUNDARY",
    title: "AI may propose. It does not admit truth.",
    body: "Candidate claims pass deterministic gates. Unsupported certainty is rejected, and material counter-evidence remains visible.",
    signal: "3",
    claimState: "CONTRADICTED",
    metric: "claims held for review",
    detail: "Fail-closed admission policy"
  },
  {
    id: "review",
    index: "07",
    eyebrow: "HUMAN AUTHORITY",
    title: "High-cost decisions retain a bounded human gate.",
    body: "AXIGNAL accelerates research while preserving accountable review, explicit uncertainty and a complete audit trail.",
    signal: "100%",
    claimState: "CALCULATED",
    metric: "traceable state transitions",
    detail: "No execution, custody or personalised advice"
  },
  {
    id: "outcome",
    index: "08",
    eyebrow: "PRIVATE PILOT",
    title: "See the opportunity. Then interrogate it.",
    body: "The private pilot is designed for qualified analysts, investors, family offices and strategy teams who need evidence before action.",
    signal: "EARLY",
    claimState: "UNKNOWN",
    metric: "access cohort",
    detail: "Deployment and commercial terms remain gated"
  }
] as const;

export const citySignals: readonly CitySignal[] = [
  {
    id: "madrid",
    city: "Madrid",
    country: "Spain",
    latitude: 40.4168,
    longitude: -3.7038,
    score: 82,
    state: "OBSERVED",
    label: "Infrastructure acceleration"
  },
  {
    id: "london",
    city: "London",
    country: "United Kingdom",
    latitude: 51.5072,
    longitude: -0.1276,
    score: 73,
    state: "CONTRADICTED",
    label: "Capital depth / policy friction"
  },
  {
    id: "paris",
    city: "Paris",
    country: "France",
    latitude: 48.8566,
    longitude: 2.3522,
    score: 76,
    state: "CALCULATED",
    label: "Transition investment density"
  },
  {
    id: "berlin",
    city: "Berlin",
    country: "Germany",
    latitude: 52.52,
    longitude: 13.405,
    score: 69,
    state: "INFERRED",
    label: "Industrial reconfiguration"
  }
] as const;

export const evidenceRail = [
  {
    state: "OBSERVED",
    title: "Transport investment increased",
    source: "Admitted institutional source",
    freshness: "T−14d"
  },
  {
    state: "CALCULATED",
    title: "Cross-border exposure concentrated",
    source: "Versioned transformation",
    freshness: "T−8d"
  },
  {
    state: "INFERRED",
    title: "Demand may transmit along the corridor",
    source: "Explicit inference",
    freshness: "T−2d"
  },
  {
    state: "CONTRADICTED",
    title: "Financing conditions weaken the signal",
    source: "Material counter-evidence",
    freshness: "T−1d"
  }
] as const;

export const outcomeCards = [
  ["Persistent context", "Resume the investigation without rebuilding assumptions."],
  ["Visible uncertainty", "Unknown coverage never becomes a weak numerical value."],
  ["Reproducible evidence", "Transformations and source lineage remain inspectable."],
  ["Bounded authority", "Proposal, admission and human acceptance stay separated."]
] as const;
