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
  billingPeriod: "trial" | "month";
  durationDays: number | null;
  aiTokenBudget: number | null;
  seatFloor: number | null;
  seatCeiling: number | null;
  activationState: "CONTROLLED_TRIAL_ONLY" | "CONTROLLED_ACCESS_ONLY";
  ctaLabel: string;
};

export const MESSAGE_VERSION = "b2g-opportunity-v1.0";

export const storySteps: readonly StoryStep[] = [
  {
    id: "market",
    index: "01",
    eyebrow: "DEFINE THE B2G MARKET",
    title: "Start with what your company can credibly sell to government.",
    body:
      "Describe capabilities, sectors, geographies, contract sizes and delivery constraints. AXIGNAL keeps that business profile attached to every opportunity it evaluates.",
    signal: "1",
    claimState: "OBSERVED",
    metric: "bounded company profile",
    detail: "Capability profile before opportunity volume"
  },
  {
    id: "procurement",
    index: "02",
    eyebrow: "FOLLOW PUBLIC DEMAND",
    title: "Bring tenders, prior notices, amendments and awards into one investigation.",
    body:
      "Official procurement records are normalised without turning one portal into the product. Coverage, freshness and source limitations remain explicit for every market.",
    signal: "6,412",
    claimState: "UNKNOWN",
    metric: "candidate procurement records",
    detail: "Synthetic demonstration · no live procurement data"
  },
  {
    id: "fit",
    index: "03",
    eyebrow: "QUALIFY THE OPPORTUNITY",
    title: "Match the contract to real delivery capability—not keywords alone.",
    body:
      "Scope, lots, deadlines, geography, eligibility and technical requirements are compared with the company profile so weak-fit notices can be rejected earlier.",
    signal: "82",
    claimState: "CALCULATED",
    metric: "synthetic capability-fit score",
    detail: "Fit is a review aid, not a win prediction"
  },
  {
    id: "buyer",
    index: "04",
    eyebrow: "UNDERSTAND THE BUYER",
    title: "Connect the contracting authority to prior awards and purchasing patterns.",
    body:
      "The opportunity record retains the buyer, previous procedures, award history and related public signals so the team can investigate demand before committing pursuit effort.",
    signal: "14",
    claimState: "OBSERVED",
    metric: "linked buyer records",
    detail: "Public buyer context remains source-linked"
  },
  {
    id: "market-structure",
    index: "05",
    eyebrow: "MAP THE COMPETITIVE CONTEXT",
    title: "Trace suppliers, ownership relationships and potential delivery partners.",
    body:
      "Corporate and ownership context helps teams inspect incumbents, related entities and capability gaps while keeping observed relationships separate from inferred ones.",
    signal: "9",
    claimState: "INFERRED",
    metric: "typed company relationships",
    detail: "Inference remains separate from observation"
  },
  {
    id: "requirements",
    index: "06",
    eyebrow: "EXPOSE THE PURSUIT RISK",
    title: "Keep requirements, deadlines, amendments and unresolved conditions visible.",
    body:
      "AXIGNAL surfaces the conditions that can invalidate a pursuit. Missing certification, unclear eligibility or contradictory documents remain open issues rather than disappearing inside a summary.",
    signal: "3",
    claimState: "CONTRADICTED",
    metric: "conditions held for review",
    detail: "Fail-closed qualification policy"
  },
  {
    id: "evidence",
    index: "07",
    eyebrow: "KEEP THE EVIDENCE ATTACHED",
    title: "Every opportunity claim retains its source, transformation, freshness and limits.",
    body:
      "The evidence trail remains available after qualification, so bid, sales and management teams can inspect why an opportunity entered the pipeline and what may still change.",
    signal: "100%",
    claimState: "CALCULATED",
    metric: "traceable state transitions",
    detail: "No unsupported certainty admitted"
  },
  {
    id: "decision",
    index: "08",
    eyebrow: "HUMAN BID / NO-BID",
    title: "Leave with an opportunity record your team can defend—or reject early.",
    body:
      "AXIGNAL accelerates Business-to-Government research while preserving human authority over qualification, pursuit, partnership and bid decisions.",
    signal: "HUMAN",
    claimState: "OBSERVED",
    metric: "final pursuit authority",
    detail: "No autonomous bid, submission or commercial commitment"
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
    label: "Digital public-services programme"
  },
  {
    id: "london",
    city: "London",
    country: "United Kingdom",
    latitude: 51.5072,
    longitude: -0.1276,
    score: 73,
    state: "CONTRADICTED",
    label: "Transport framework / eligibility risk"
  },
  {
    id: "paris",
    city: "Paris",
    country: "France",
    latitude: 48.8566,
    longitude: 2.3522,
    score: 76,
    state: "CALCULATED",
    label: "Public-building efficiency procurement"
  },
  {
    id: "berlin",
    city: "Berlin",
    country: "Germany",
    latitude: 52.52,
    longitude: 13.405,
    score: 69,
    state: "INFERRED",
    label: "Industrial infrastructure tender"
  }
] as const;

export const evidenceRail = [
  {
    state: "OBSERVED",
    title: "Tender notice and amendment identified",
    source: "Official procurement record",
    freshness: "T−1d"
  },
  {
    state: "OBSERVED",
    title: "Contracting authority and prior awards linked",
    source: "Admitted award records",
    freshness: "T−7d"
  },
  {
    state: "CALCULATED",
    title: "Company capability overlap assessed",
    source: "Versioned qualification rule",
    freshness: "T−0d"
  },
  {
    state: "UNKNOWN",
    title: "Local certification requirement unresolved",
    source: "Open qualification condition",
    freshness: "REVIEW"
  }
] as const;

export const outcomeCards = [
  ["A cleaner B2G pipeline", "Prioritise public contracts that fit the company instead of forwarding every keyword match."],
  ["Faster tender qualification", "Review scope, lots, deadlines, eligibility and buyer context in one persistent opportunity record."],
  ["Better bid / no-bid decisions", "Protect pursuit time and budget by making fit, risk, evidence and unknowns visible before commitment."],
  ["A defensible pursuit history", "Keep the sources and reasoning behind each qualified, rejected or deferred opportunity."]
] as const;

export const buyerProblems = [
  [
    "Procurement is fragmented",
    "Tenders, amendments, awards and buyer records are distributed across portals, jurisdictions, languages and classifications."
  ],
  [
    "Alerts create noise",
    "Keyword matching produces volume, but not a reliable view of delivery fit, eligibility, timing or pursuit value."
  ],
  [
    "Bid context arrives too late",
    "Buyer history, incumbents, company relationships and unresolved requirements are often reconstructed after the deadline is already close."
  ]
] as const;

export const frequentlyAskedQuestions = [
  [
    "What does Business-to-Government (B2G) mean?",
    "B2G describes companies selling goods and services to governments, public agencies and publicly funded bodies. AXIGNAL focuses initially on the opportunity-intelligence work around public contracts and tenders."
  ],
  [
    "Is AXIGNAL only another tender-alert service?",
    "No. Tender discovery is the entry point. AXIGNAL is designed to connect the notice with the contracting authority, award history, requirements, suppliers, ownership context and the evidence used for a human qualification decision."
  ],
  [
    "Does AXIGNAL guarantee that we will win a contract?",
    "No. It does not claim a guaranteed win rate or guaranteed truth. It helps the team investigate fit, risk and evidence while retaining human bid and commercial authority."
  ],
  [
    "Does AXIGNAL depend on one procurement portal?",
    "No. Individual portals are libraries, not the product identity. Coverage is declared source by source, and missing or stale coverage must remain visible rather than being presented as global completeness."
  ],
  [
    "How does the 7-day trial work?",
    "The candidate trial provides seven days and a bounded 1,000,000-token AI budget, with no card and no Stripe checkout. Activation is reviewed and one-time eligibility is preserved by the commercial entitlement policy."
  ],
  [
    "Can AXIGNAL use private company capability information?",
    "The architecture supports tenant-private libraries and bounded integrations, subject to classification, rights, retention and security controls."
  ]
] as const;
