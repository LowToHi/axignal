export type SourceState =
  | "ADMITTED"
  | "TECHNICAL_PROBE"
  | "DISCOVERED"
  | "CANDIDATE"
  | "BLOCKED"
  | "RIGHTS_REVIEW"
  | "UNAVAILABLE";

export type SourcePoint = {
  id: string;
  name: string;
  jurisdiction: string;
  latitude: number;
  longitude: number;
  state: SourceState;
  priority: "P0" | "P1" | "P2" | "P3" | "P4";
  access: "PRIVATE_AUTHENTICATED_PILOT" | "DISCOVERY_ONLY" | "RIGHTS_REVIEW";
};

export const sourcePoints: readonly SourcePoint[] = [
  {
    id: "EU_TED",
    name: "Tenders Electronic Daily",
    jurisdiction: "European Union",
    latitude: 50.8503,
    longitude: 4.3517,
    state: "ADMITTED",
    priority: "P0",
    access: "PRIVATE_AUTHENTICATED_PILOT"
  },
  {
    id: "UK_FIND_A_TENDER",
    name: "Find a Tender Service",
    jurisdiction: "United Kingdom",
    latitude: 51.5072,
    longitude: -0.1276,
    state: "DISCOVERED",
    priority: "P1",
    access: "DISCOVERY_ONLY"
  },
  {
    id: "US_SAM_OPPORTUNITIES",
    name: "SAM.gov Contract Opportunities",
    jurisdiction: "United States",
    latitude: 38.9072,
    longitude: -77.0369,
    state: "DISCOVERED",
    priority: "P1",
    access: "DISCOVERY_ONLY"
  },
  {
    id: "CA_CANADABUYS",
    name: "CanadaBuys",
    jurisdiction: "Canada",
    latitude: 45.4215,
    longitude: -75.6972,
    state: "DISCOVERED",
    priority: "P1",
    access: "DISCOVERY_ONLY"
  },
  {
    id: "BR_COMPRAS_GOV",
    name: "Compras.gov.br",
    jurisdiction: "Brazil",
    latitude: -15.7939,
    longitude: -47.8828,
    state: "DISCOVERED",
    priority: "P1",
    access: "DISCOVERY_ONLY"
  },
  {
    id: "ZA_ETENDERS_OCDS",
    name: "eTenders OCDS",
    jurisdiction: "South Africa",
    latitude: -25.7479,
    longitude: 28.2293,
    state: "DISCOVERED",
    priority: "P2",
    access: "DISCOVERY_ONLY"
  },
  {
    id: "IN_CPPP_EPROCURE",
    name: "Central Public Procurement Portal",
    jurisdiction: "India",
    latitude: 28.6139,
    longitude: 77.209,
    state: "RIGHTS_REVIEW",
    priority: "P1",
    access: "RIGHTS_REVIEW"
  },
  {
    id: "AU_AUSTENDER",
    name: "AusTender",
    jurisdiction: "Australia",
    latitude: -35.2809,
    longitude: 149.13,
    state: "DISCOVERED",
    priority: "P1",
    access: "DISCOVERY_ONLY"
  }
] as const;

export const sourceStateOrder: readonly SourceState[] = [
  "ADMITTED",
  "TECHNICAL_PROBE",
  "DISCOVERED",
  "CANDIDATE",
  "RIGHTS_REVIEW",
  "BLOCKED",
  "UNAVAILABLE"
];

export function isActiveCoverage(state: SourceState) {
  return state === "ADMITTED";
}

export type ImpactInputs = {
  opportunities: number;
  hours: number;
  reductionPercent: number;
  hourlyRate: number;
};

export type ImpactResult = {
  redirectedHours: number;
  illustrativeValue: number;
};

export function calculateIllustrativeImpact({
  opportunities,
  hours,
  reductionPercent,
  hourlyRate
}: ImpactInputs): ImpactResult {
  const boundedOpportunities = Math.max(0, Math.min(1_000, opportunities));
  const boundedHours = Math.max(0, Math.min(200, hours));
  const boundedReduction = Math.max(0, Math.min(100, reductionPercent)) / 100;
  const boundedRate = Math.max(0, Math.min(2_000, hourlyRate));
  const redirectedHours = boundedOpportunities * boundedHours * boundedReduction;

  return {
    redirectedHours: Math.round(redirectedHours * 10) / 10,
    illustrativeValue: Math.round(redirectedHours * boundedRate)
  };
}
