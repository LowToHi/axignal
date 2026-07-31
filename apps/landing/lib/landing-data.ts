export type ClaimState =
  | "OBSERVED"
  | "CALCULATED"
  | "INFERRED"
  | "CONTRADICTED"
  | "UNKNOWN";

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

export type CandidatePlan = {
  planCode: string;
  name: string;
  description: string;
  amountMinor: number;
  currency: string;
  billingPeriod: "month";
  seatFloor: number;
  seatCeiling: number;
  activationState: "CONTROLLED_ACCESS_ONLY";
};

export const MESSAGE_VERSION = "buyer-outcome-v1.0";

export const storySteps: readonly StoryStep[] = [
  {
    id: "fragmentation",
    index: "01",
    eyebrow: "THE RESEARCH BOTTLENECK",
    title: "Important decisions begin with evidence scattered across too many places.",
    body:
      "Documents, web sources, internal notes and changing signals rarely arrive in one usable workflow. AXIGNAL keeps them attached to the question they are meant to answer.",
    signal: "6,412",
    claimState: "UNKNOWN",
    metric: "unresolved observations",
    detail: "Synthetic demonstration · no live market data"
  },
  {
    id: "decision",
    index: "02",
    eyebrow: "START WITH THE DECISION",
    title: "Define what the team needs to decide before collecting more information.",
    body:
      "Navigator converts the research intent into a persistent ResearchRun. Scope, lenses, sources, claims and review state remain part of the same investigation.",
    signal: "1",
    claimState: "OBSERVED",
    metric: "persistent investigation",
    detail: "Ask → investigate → verify → review"
  },
  {
    id: "geography",
    index: "03",
    eyebrow: "COMPARE THE CONTEXT",
    title: "See where signals converge without mistaking attention for evidence.",
    body:
      "The Globe provides a comparative analytical surface across locations while preserving the source and status behind every displayed signal.",
    signal: "4",
    claimState: "CALCULATED",
    metric: "candidate locations",
    detail: "Synthetic European research scenario"
  },
  {
    id: "relationships",
    index: "04",
    eyebrow: "FOLLOW THE RELATIONSHIPS",
    title: "Trace how policy, ownership, capital and infrastructure affect one another.",
    body:
      "Typed relationships make the route between observations inspectable. The team can see what is linked, what is inferred and what remains unsupported.",
    signal: "9",
    claimState: "INFERRED",
    metric: "typed transmissions",
    detail: "Inference remains separate from observation"
  },
  {
    id: "evidence",
    index: "05",
    eyebrow: "KEEP THE SUPPORT ATTACHED",
    title: "Every claim retains its sources, transformations, freshness and limits.",
    body:
      "The evidence trail stays available after the summary is written, so reviewers can inspect why a claim exists and whether its support is still current.",
    signal: "14",
    claimState: "OBSERVED",
    metric: "evidence objects",
    detail: "Original source references preserved"
  },
  {
    id: "contradiction",
    index: "06",
    eyebrow: "SURFACE THE COUNTER-EVIDENCE",
    title: "Contradictions remain visible instead of disappearing inside a confident answer.",
    body:
      "Candidate claims pass deterministic checks. Unsupported certainty is held for review, and material counter-evidence remains part of the decision record.",
    signal: "3",
    claimState: "CONTRADICTED",
    metric: "claims held for review",
    detail: "Fail-closed admission policy"
  },
  {
    id: "review",
    index: "07",
    eyebrow: "REVIEW BEFORE RELIANCE",
    title: "The team decides what can be relied upon, shared or promoted.",
    body:
      "AXIGNAL accelerates the research work while preserving accountable review, explicit uncertainty and a traceable history of state changes.",
    signal: "100%",
    claimState: "CALCULATED",
    metric: "traceable state transitions",
    detail: "No execution, custody or personalised advice"
  },
  {
    id: "outcome",
    index: "08",
    eyebrow: "DECISION-READY OUTPUT",
    title: "Leave with a decision record the next reviewer can inspect.",
    body:
      "The controlled-access programme is designed for strategy, investment and intelligence teams that need faster research without losing the evidence trail.",
    signal: "EARLY",
    claimState: "UNKNOWN",
    metric: "access cohort",
    detail: "Deployment and commercial activation remain gated"
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
  ["One research record", "Resume the work without reconstructing assumptions from slides and chats."],
  ["Visible uncertainty", "Unknown coverage remains explicit instead of becoming false precision."],
  ["Reviewable support", "Sources, transformations and claim lineage remain available to inspect."],
  ["Bounded authority", "Proposal, admission and accountable human acceptance stay separated."]
] as const;

export const buyerProblems = [
  ["Scattered evidence", "Sources, notes and internal documents are separated from the decision they support."],
  ["Hidden disagreement", "Conflicts are often flattened into summaries before a reviewer can inspect them."],
  ["Lost research context", "Teams repeat work because assumptions, filters and prior decisions are not persistent."]
] as const;

export const frequentlyAskedQuestions = [
  [
    "Does AXIGNAL guarantee that every conclusion is true?",
    "No. AXIGNAL keeps sources, provenance, uncertainty and review state visible so the team can understand what supports a conclusion and what remains unresolved."
  ],
  [
    "Does AXIGNAL make decisions automatically?",
    "No. It can coordinate research and produce bounded proposals. Human and policy gates retain admission, decision and publication authority."
  ],
  [
    "Can AXIGNAL work with private company information?",
    "The architecture supports tenant-private libraries and bounded integrations, subject to classification, rights, retention and security controls."
  ],
  [
    "Is paid self-service access available now?",
    "No. Professional and Team are candidate controlled-access packages. Stripe live checkout and public commercial activation remain disabled."
  ]
] as const;
