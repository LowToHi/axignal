import type { Locale } from "./i18n";
import { AXIGNAL_PRICE_BOOK } from "./canonical-commercial-contract";

export type PricingPlanId = "controlled-trial" | "professional" | "team";

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
    "Admitted sources in controlled-trial scope",
    "3",
    "Watermarked PDF only",
    "Shared review",
    "1 processing job",
    "Guided onboarding",
    "Verified organisation",
    "None",
    "7 days · read-only at expiry",
    "1,000,000 cumulative tokens · no overage"
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
  ]
} as const;

const canonicalPlans: readonly PlanDefinition[] = [
  {
    id: "controlled-trial",
    name: "Controlled Trial",
    price: `€${AXIGNAL_PRICE_BOOK.plans.controlledTrial.amountMinor / 100}`,
    period: `${AXIGNAL_PRICE_BOOK.plans.controlledTrial.durationDays} days`,
    cta: "Request 7-day B2G trial",
    availability: "APPLICATION ONLY · NO CARD · NO AUTOMATIC CONVERSION",
    values: sharedPlanValues.trial
  },
  {
    id: "professional",
    name: "Professional",
    price: `€${AXIGNAL_PRICE_BOOK.plans.professional.amountMinor / 100}`,
    period: "per month",
    cta: "Request Professional access",
    availability: "CANONICAL PRICE · ACTIVATION CONTROLLED",
    values: sharedPlanValues.professional
  },
  {
    id: "team",
    name: "Team",
    price: `€${AXIGNAL_PRICE_BOOK.plans.team.amountMinor / 100}`,
    period: "per month",
    cta: "Request Team access",
    availability: "CANONICAL PRICE · ACTIVATION CONTROLLED",
    values: sharedPlanValues.team
  }
];

const english: PricingCopy = {
  indicative: `Canonical price book · ${AXIGNAL_PRICE_BOOK.version}`,
  designPartnerLabel: "CONTROLLED 7-DAY TRIAL",
  designPartnerTitle: "Controlled Trial",
  designPartnerBody:
    "Application-only access for one real B2G qualification workflow. No card, automatic conversion, renewal or overage.",
  designPartnerPrice: "€0 · 7 days · 1,000,000 cumulative tokens",
  designPartnerCta: "Request 7-day B2G trial",
  comparisonTitle: "Choose the contracted operating boundary—not a token bundle.",
  comparisonBody:
    "Professional is €149/month and Team is €399/month. Checkout and paid activation remain disabled until the commercial round trip is authorised.",
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
  plans: canonicalPlans
};

export const pricingCopy: Record<Locale, PricingCopy> = {
  en: english,
  es: {
    ...english,
    indicative: `Libro de precios canónico · ${AXIGNAL_PRICE_BOOK.version}`,
    designPartnerLabel: "PRUEBA CONTROLADA DE 7 DÍAS",
    designPartnerTitle: "Prueba controlada",
    designPartnerBody:
      "Acceso mediante solicitud para un flujo real de cualificación B2G. Sin tarjeta, conversión automática, renovación ni exceso.",
    designPartnerPrice: "0 € · 7 días · 1.000.000 de tokens acumulados",
    designPartnerCta: "Solicitar prueba B2G de 7 días",
    comparisonTitle: "Elige el límite operativo contratado, no un paquete de tokens.",
    comparisonBody:
      "Professional cuesta 149 €/mes y Team 399 €/mes. El checkout y la activación siguen deshabilitados hasta autorizar el round trip comercial.",
    rowLabels: {
      users: "Usuarios",
      investigations: "Investigaciones",
      sources: "Fuentes",
      dossiers: "Dossiers",
      exports: "Exportaciones",
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
    indicative: `Catalogue tarifaire canonique · ${AXIGNAL_PRICE_BOOK.version}`,
    designPartnerLabel: "ESSAI CONTRÔLÉ DE 7 JOURS",
    designPartnerTitle: "Essai contrôlé",
    designPartnerBody:
      "Accès sur demande pour un vrai flux de qualification B2G. Sans carte, conversion automatique, renouvellement ni dépassement.",
    designPartnerPrice: "0 € · 7 jours · 1 000 000 de jetons cumulés",
    designPartnerCta: "Demander l’essai B2G de 7 jours",
    comparisonTitle: "Choisissez la limite contractuelle, pas un lot de jetons.",
    comparisonBody:
      "Professional coûte 149 €/mois et Team 399 €/mois. Checkout et activation restent désactivés jusqu’à autorisation.",
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
    indicative: `Livro de preços canónico · ${AXIGNAL_PRICE_BOOK.version}`,
    designPartnerLabel: "TESTE CONTROLADO DE 7 DIAS",
    designPartnerTitle: "Teste controlado",
    designPartnerBody:
      "Acesso por candidatura para um fluxo real de qualificação B2G. Sem cartão, conversão automática, renovação ou excesso.",
    designPartnerPrice: "0 € · 7 dias · 1.000.000 de tokens acumulados",
    designPartnerCta: "Solicitar teste B2G de 7 dias",
    comparisonTitle: "Escolha o limite contratado, não um pacote de tokens.",
    comparisonBody:
      "Professional custa 149 €/mês e Team 399 €/mês. Checkout e ativação permanecem desativados até autorização.",
    rowLabels: {
      users: "Utilizadores",
      investigations: "Investigações",
      sources: "Fontes",
      dossiers: "Dossiers",
      exports: "Exportações",
      collaboration: "Colaboração",
      concurrency: "Concorrência",
      support: "Suporte",
      security: "Segurança",
      integrations: "Integrações",
      operationalLimits: "Limites operativos",
      aiSemantics: "Semântica de IA"
    }
  },
  de: {
    ...english,
    indicative: `Kanonisches Preisbuch · ${AXIGNAL_PRICE_BOOK.version}`,
    designPartnerLabel: "KONTROLLIERTER 7-TAGE-TEST",
    designPartnerTitle: "Kontrollierter Test",
    designPartnerBody:
      "Antragsbasierter Zugang für einen realen B2G-Qualifizierungsprozess. Keine Karte, automatische Konvertierung, Verlängerung oder Mehrverbrauch.",
    designPartnerPrice: "0 € · 7 Tage · 1.000.000 kumulierte Tokens",
    designPartnerCta: "7-tägigen B2G-Test anfragen",
    comparisonTitle: "Wählen Sie die Vertragsgrenze, kein Token-Paket.",
    comparisonBody:
      "Professional kostet 149 €/Monat und Team 399 €/Monat. Checkout und Aktivierung bleiben bis zur Freigabe deaktiviert.",
    rowLabels: {
      users: "Benutzer",
      investigations: "Untersuchungen",
      sources: "Quellen",
      dossiers: "Dossiers",
      exports: "Exporte",
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
    indicative: `Listino canonico · ${AXIGNAL_PRICE_BOOK.version}`,
    designPartnerLabel: "PROVA CONTROLLATA DI 7 GIORNI",
    designPartnerTitle: "Prova controllata",
    designPartnerBody:
      "Accesso su richiesta per un vero flusso di qualificazione B2G. Senza carta, conversione automatica, rinnovo o eccedenze.",
    designPartnerPrice: "0 € · 7 giorni · 1.000.000 di token cumulativi",
    designPartnerCta: "Richiedi la prova B2G di 7 giorni",
    comparisonTitle: "Scegli il limite contrattuale, non un pacchetto di token.",
    comparisonBody:
      "Professional costa 149 €/mese e Team 399 €/mese. Checkout e attivazione restano disabilitati fino all’autorizzazione.",
    rowLabels: {
      users: "Utenti",
      investigations: "Indagini",
      sources: "Fonti",
      dossiers: "Dossier",
      exports: "Esportazioni",
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
