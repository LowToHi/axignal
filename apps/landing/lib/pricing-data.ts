import type { Locale } from "./i18n";

export type PricingPlanId = "controlled-trial" | "professional" | "team" | "enterprise";

type PlanDefinition = {
  id: PricingPlanId;
  name: string;
  price: string;
  period: string;
  cta: string;
  availability: string;
  values: readonly string[];
};

export const pricingRowKeys = [
  "users",
  "investigations",
  "sources",
  "dossiers",
  "exports",
  "collaboration",
  "concurrency",
  "support",
  "security",
  "integrations",
  "operationalLimits",
  "aiSemantics"
] as const;

type PricingCopy = {
  indicative: string;
  designPartnerLabel: string;
  designPartnerTitle: string;
  designPartnerBody: string;
  designPartnerPrice: string;
  designPartnerCta: string;
  comparisonTitle: string;
  comparisonBody: string;
  rowLabels: Record<(typeof pricingRowKeys)[number], string>;
  plans: readonly PlanDefinition[];
};

const sharedPlanValues = {
  trial: [
    "Up to 3 verified users",
    "3 active",
    "TED bounded pilot profile",
    "3",
    "Watermarked PDF only",
    "Shared review",
    "1 processing job",
    "Guided onboarding",
    "Verified organisation",
    "None",
    "7 days · read-only at expiry",
    "1,000,000 cumulative tokens / organisation · no overage"
  ],
  professional: [
    "1 user",
    "25 active",
    "Admitted sources in plan scope",
    "25 active",
    "PDF + evidence bundle",
    "Personal workspace",
    "2 processing jobs",
    "Standard",
    "MFA",
    "Evidence export",
    "Fair-use processing and storage limits",
    "Unlimited monthly AI within AXIGNAL scope"
  ],
  team: [
    "Up to 10 users",
    "100 active",
    "Expanded admitted-source scope",
    "100 active",
    "Governed team exports",
    "Assignments + review",
    "6 processing jobs",
    "Priority",
    "MFA + roles + audit trail",
    "Workflow connectors",
    "Contracted processing and storage limits",
    "Unlimited monthly AI within AXIGNAL scope"
  ],
  enterprise: [
    "Contracted",
    "Contracted",
    "Contracted jurisdiction packs",
    "Contracted",
    "Governed bulk and API rights",
    "Advanced governance",
    "Contracted",
    "Named support",
    "SSO/SCIM + controls",
    "API + private connectors",
    "SLA, throughput and retention by contract",
    "Unlimited monthly AI within AXIGNAL scope"
  ]
} as const;

const english: PricingCopy = {
  indicative: "Indicative candidate pricing",
  designPartnerLabel: "SPECIAL VALIDATION PROGRAMME",
  designPartnerTitle: "Design Partner",
  designPartnerBody:
    "A bounded, paid programme for organisations prepared to validate one expensive procurement workflow and provide structured evidence.",
  designPartnerPrice: "€300–600 / organisation / month",
  designPartnerCta: "Apply for Design Partner access",
  comparisonTitle: "Choose the operating boundary—not a token bundle.",
  comparisonBody:
    "Paid monthly AI is unlimited within AXIGNAL scope. Processing, concurrency, exports, API access and source entitlements remain explicitly bounded.",
  rowLabels: {
    users: "Users",
    investigations: "Investigations",
    sources: "Sources",
    dossiers: "Dossiers",
    exports: "Exports",
    collaboration: "Collaboration",
    concurrency: "Concurrency",
    support: "Support",
    security: "Security",
    integrations: "Integrations",
    operationalLimits: "Operational limits",
    aiSemantics: "AI semantics"
  },
  plans: [
    {
      id: "controlled-trial",
      name: "Controlled Free Trial",
      price: "7 days",
      period: "approval required",
      cta: "Apply for controlled trial",
      availability: "PUBLIC TRIAL DISABLED · APPLICATION ONLY",
      values: sharedPlanValues.trial
    },
    {
      id: "professional",
      name: "Professional",
      price: "€349–499",
      period: "per month",
      cta: "Apply for Professional",
      availability: "INDICATIVE CANDIDATE PLAN",
      values: sharedPlanValues.professional
    },
    {
      id: "team",
      name: "Team / Growth",
      price: "€899–1,499",
      period: "per month",
      cta: "Apply for Team / Growth",
      availability: "INDICATIVE CANDIDATE PLAN",
      values: sharedPlanValues.team
    },
    {
      id: "enterprise",
      name: "Enterprise",
      price: "€18k–45k",
      period: "per year",
      cta: "Discuss Enterprise",
      availability: "INDICATIVE CANDIDATE PLAN",
      values: sharedPlanValues.enterprise
    }
  ]
};

export const pricingCopy: Record<Locale, PricingCopy> = {
  en: english,
  es: {
    ...english,
    indicative: "Precios candidatos indicativos",
    designPartnerLabel: "PROGRAMA ESPECIAL DE VALIDACIÓN",
    designPartnerBody:
      "Programa acotado y de pago para organizaciones dispuestas a validar un flujo costoso de contratación y aportar evidencia estructurada.",
    designPartnerCta: "Solicitar acceso Design Partner",
    comparisonTitle: "Elige el límite operativo, no un paquete de tokens.",
    comparisonBody:
      "La IA mensual de pago es ilimitada dentro del alcance AXIGNAL. Procesamiento, concurrencia, exports, API y fuentes siguen expresamente acotados.",
    rowLabels: {
      users: "Usuarios",
      investigations: "Investigaciones",
      sources: "Fuentes",
      dossiers: "Dossiers",
      exports: "Exports",
      collaboration: "Colaboración",
      concurrency: "Concurrencia",
      support: "Soporte",
      security: "Seguridad",
      integrations: "Integraciones",
      operationalLimits: "Límites operativos",
      aiSemantics: "Semántica de IA"
    }
  },
  fr: {
    ...english,
    indicative: "Tarification candidate indicative",
    designPartnerLabel: "PROGRAMME SPÉCIAL DE VALIDATION",
    designPartnerBody:
      "Programme payant et limité pour les organisations prêtes à valider un flux de marché public coûteux et à fournir des preuves structurées.",
    designPartnerCta: "Demander l’accès Design Partner",
    comparisonTitle: "Choisissez la limite opérationnelle, pas un lot de jetons.",
    comparisonBody:
      "L’IA mensuelle payante est illimitée dans le périmètre AXIGNAL. Traitement, concurrence, exports, API et sources restent explicitement limités.",
    rowLabels: {
      users: "Utilisateurs",
      investigations: "Investigations",
      sources: "Sources",
      dossiers: "Dossiers",
      exports: "Exports",
      collaboration: "Collaboration",
      concurrency: "Concurrence",
      support: "Support",
      security: "Sécurité",
      integrations: "Intégrations",
      operationalLimits: "Limites opérationnelles",
      aiSemantics: "Sémantique IA"
    }
  },
  pt: {
    ...english,
    indicative: "Preços candidatos indicativos",
    designPartnerLabel: "PROGRAMA ESPECIAL DE VALIDAÇÃO",
    designPartnerBody:
      "Programa pago e limitado para organizações dispostas a validar um fluxo dispendioso de contratação e fornecer evidências estruturadas.",
    designPartnerCta: "Candidatar-se ao acesso Design Partner",
    comparisonTitle: "Escolha o limite operacional, não um pacote de tokens.",
    comparisonBody:
      "A IA mensal paga é ilimitada dentro do âmbito AXIGNAL. Processamento, concorrência, exports, API e fontes permanecem explicitamente limitados.",
    rowLabels: {
      users: "Utilizadores",
      investigations: "Investigações",
      sources: "Fontes",
      dossiers: "Dossiers",
      exports: "Exports",
      collaboration: "Colaboração",
      concurrency: "Concorrência",
      support: "Suporte",
      security: "Segurança",
      integrations: "Integrações",
      operationalLimits: "Limites operacionais",
      aiSemantics: "Semântica de IA"
    }
  },
  de: {
    ...english,
    indicative: "Indikative Kandidatenpreise",
    designPartnerLabel: "BESONDERES VALIDIERUNGSPROGRAMM",
    designPartnerBody:
      "Begrenztes, bezahltes Programm für Organisationen, die einen teuren Beschaffungsablauf validieren und strukturierte Evidenz liefern.",
    designPartnerCta: "Design-Partner-Zugang beantragen",
    comparisonTitle: "Wählen Sie die Betriebsgrenze, kein Token-Paket.",
    comparisonBody:
      "Bezahlte monatliche KI ist im AXIGNAL-Umfang unbegrenzt. Verarbeitung, Parallelität, Exports, API und Quellen bleiben ausdrücklich begrenzt.",
    rowLabels: {
      users: "Benutzer",
      investigations: "Untersuchungen",
      sources: "Quellen",
      dossiers: "Dossiers",
      exports: "Exports",
      collaboration: "Zusammenarbeit",
      concurrency: "Parallelität",
      support: "Support",
      security: "Sicherheit",
      integrations: "Integrationen",
      operationalLimits: "Betriebsgrenzen",
      aiSemantics: "KI-Semantik"
    }
  },
  it: {
    ...english,
    indicative: "Prezzi candidati indicativi",
    designPartnerLabel: "PROGRAMMA SPECIALE DI VALIDAZIONE",
    designPartnerBody:
      "Programma limitato e a pagamento per organizzazioni disposte a validare un flusso costoso di procurement e fornire evidenze strutturate.",
    designPartnerCta: "Richiedi accesso Design Partner",
    comparisonTitle: "Scegli il limite operativo, non un pacchetto di token.",
    comparisonBody:
      "L’IA mensile a pagamento è illimitata nell’ambito AXIGNAL. Elaborazione, concorrenza, exports, API e fonti restano esplicitamente limitati.",
    rowLabels: {
      users: "Utenti",
      investigations: "Indagini",
      sources: "Fonti",
      dossiers: "Dossier",
      exports: "Exports",
      collaboration: "Collaborazione",
      concurrency: "Concorrenza",
      support: "Supporto",
      security: "Sicurezza",
      integrations: "Integrazioni",
      operationalLimits: "Limiti operativi",
      aiSemantics: "Semantica IA"
    }
  }
};
