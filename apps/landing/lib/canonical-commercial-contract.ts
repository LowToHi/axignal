export const AXIGNAL_PRICE_BOOK = {
  schema: "axignal.price-book.v1",
  version: "2026-08-04",
  currency: "EUR",
  plans: {
    controlledTrial: {
      code: "CONTROLLED_TRIAL_7D",
      amountMinor: 0,
      durationDays: 7,
      cumulativeTokens: 1_000_000,
      cardRequired: false,
      automaticConversion: false
    },
    professional: {
      code: "PROFESSIONAL_MONTHLY",
      amountMinor: 14_900,
      interval: "month"
    },
    team: {
      code: "TEAM_MONTHLY",
      amountMinor: 39_900,
      interval: "month"
    }
  }
} as const;

export const AXIGNAL_TRIAL_INTAKE = {
  schema: "axignal.b2g-trial-intake.v1",
  source: "landing_b2g_opportunity_v1_0",
  messageVersion: "b2g-opportunity-v1.0",
  consentVersion: "b2g-trial-intake-2026-08-04"
} as const;

type LocaleCode = "en" | "es" | "fr" | "pt" | "de" | "it";

type CanonicalCommercialCopy = {
  meta: { title: string; description: string };
  navCta: string;
  hero: {
    eyebrow: string;
    title: string;
    accent: string;
    descriptor: string;
    summary: string;
    primary: string;
    secondary: string;
    status: string;
  };
  storyIntroBody: string;
  sourceAct: { title: string; body: string; metric: string; detail: string };
  trialAct: { eyebrow: string; title: string; body: string; signal: string; metric: string; detail: string };
  navigatorResponse: string;
  globeActiveRule: string;
  pricing: {
    eyebrow: string;
    title: string;
    body: string;
    candidate: string;
    current: string;
    cta: string;
    plans: [string, string, string, string][];
  };
  faqItems: [string, string][];
  form: {
    eyebrow: string;
    title: string;
    body: string;
    identity: string;
    fit: string;
    countries: string;
    volume: string;
    process: string;
    useCase: string;
    problem: string;
    consent: string;
    submit: string;
    success: string;
    error: string;
    privacy: string;
  };
};

export const canonicalCommercialCopy: Record<LocaleCode, CanonicalCommercialCopy> = {
  en: {
    meta: {
      title: "AXIGNAL — B2G Opportunity Intelligence",
      description: "Find, qualify and investigate public contracts with traceable evidence and human authority over every commercial decision."
    },
    navCta: "Request your 7-day B2G trial",
    hero: {
      eyebrow: "BUSINESS-TO-GOVERNMENT (B2G) OPPORTUNITY INTELLIGENCE",
      title: "Find the public contracts your business is built to pursue.",
      accent: "Turn global procurement into a qualified B2G pipeline.",
      descriptor: "Business-to-Government opportunity intelligence with traceable evidence.",
      summary: "AXIGNAL connects public tenders, contracting authorities, awards, suppliers and ownership signals so B2G teams can discover, qualify and investigate the opportunities worth pursuing—without losing the evidence behind the decision.",
      primary: "Request your 7-day B2G trial",
      secondary: "See a public-contract investigation",
      status: "Product demonstration · public source coverage remains bounded by current admission evidence"
    },
    storyIntroBody: "Follow a synthetic public-contract investigation. Source states describe evidence boundaries, not a claim of global product coverage.",
    sourceAct: {
      title: "See where public demand, capability fit and admitted evidence intersect.",
      body: "The Globe distinguishes admitted coverage, discovery candidates and unavailable systems. Visual prominence never changes source authority.",
      metric: "admitted public-source profiles",
      detail: "Bounded coverage · authority remains server governed"
    },
    trialAct: {
      eyebrow: "08 · CONTROLLED TRIAL",
      title: "Test AXIGNAL against a real B2G qualification workflow.",
      body: "The 7-day controlled trial is application-only, includes 1,000,000 cumulative tokens, requires no card and never converts automatically.",
      signal: "7 DAYS",
      metric: "controlled trial",
      detail: "Application only · no card · no automatic renewal"
    },
    navigatorResponse: "I created a bounded investigation using only source profiles whose current admission state permits the requested operation.",
    globeActiveRule: "Only ADMITTED sources count as active product coverage. Coverage remains bounded by the current evidence report.",
    pricing: {
      eyebrow: "CONTROLLED COMMERCIAL ACCESS",
      title: "A clear trial and two versioned monthly plans.",
      body: "Trial access is application-only. Paid activation and checkout remain disabled until the commercial round trip is formally authorised.",
      candidate: "Canonical price book",
      current: "Current controlled access",
      cta: "Request access",
      plans: [
        ["Controlled Trial", "€0", "7 days", "1,000,000 cumulative tokens, no card and no automatic conversion."],
        ["Professional", "€149", "month", "Individual B2G investigation, dossiers, monitoring and evidence exports."],
        ["Team", "€399", "month", "Shared investigations, review workflow, governance and team usage." ]
      ]
    },
    faqItems: [
      ["Does AXIGNAL cover public procurement globally today?", "No. Coverage claims are limited to sources, countries, fields, languages and notice types supported by the current evidence report."],
      ["Which sources are active in the product?", "Only source profiles with current rights, technical, quality and human-authority approval are active. Discovery candidates are not product coverage."],
      ["Does AXIGNAL write or submit bids?", "No. AXIGNAL supports discovery, qualification and investigation. Final bid/no-bid, communication, signature and submission remain human decisions."],
      ["What are the current prices?", "Professional is €149 per month and Team is €399 per month. Activation remains controlled until the commercial round trip is authorised."],
      ["How does the free trial work?", "The controlled trial lasts 7 days, includes 1,000,000 cumulative tokens, requires no card, has no renewal or overage and becomes read-only at expiry."]
    ],
    form: {
      eyebrow: "7-DAY B2G TRIAL INTAKE",
      title: "Bring one real public-contract qualification workflow.",
      body: "Tell us what your company sells to government, the buyers or markets you target and where qualification currently consumes time or budget.",
      identity: "Your company and B2G role",
      fit: "Target market and qualification bottleneck",
      countries: "Target markets, public buyers or tender types",
      volume: "Opportunities reviewed per month",
      process: "Current qualification process or tools",
      useCase: "What your company sells to government",
      problem: "Main qualification bottleneck",
      consent: "I agree that AXIGNAL may use this information only to assess and respond to this controlled B2G trial request. No lead details are sent to analytics.",
      submit: "Request your 7-day B2G trial",
      success: "Trial request received. AXIGNAL will review eligibility and respond through the configured channel.",
      error: "The B2G trial intake channel is unavailable. No success was recorded.",
      privacy: "Purpose-limited trial review · no subscription created · no PII analytics"
    }
  },
  es: {
    meta: { title: "AXIGNAL — Inteligencia de oportunidades B2G", description: "Encuentra, cualifica e investiga contratos públicos con evidencia trazable y autoridad humana." },
    navCta: "Solicita tu prueba B2G de 7 días",
    hero: { eyebrow: "INTELIGENCIA DE OPORTUNIDADES BUSINESS-TO-GOVERNMENT (B2G)", title: "Encuentra los contratos públicos para los que está preparada tu empresa.", accent: "Convierte la contratación pública global en un pipeline B2G cualificado.", descriptor: "Inteligencia de oportunidades B2G con evidencia trazable.", summary: "AXIGNAL conecta licitaciones, organismos contratantes, adjudicaciones, proveedores y señales de propiedad para descubrir, cualificar e investigar oportunidades sin perder la evidencia de la decisión.", primary: "Solicita tu prueba B2G de 7 días", secondary: "Ver una investigación de contrato público", status: "Demostración del producto · la cobertura pública sigue limitada por la evidencia de admisión vigente" },
    storyIntroBody: "Sigue una investigación sintética de un contrato público. Los estados de fuente expresan límites de evidencia, no cobertura global.",
    sourceAct: { title: "Observa dónde coinciden demanda pública, capacidad y evidencia admitida.", body: "El Globo distingue cobertura admitida, candidatos de descubrimiento y sistemas no disponibles. La prominencia visual no cambia la autoridad.", metric: "perfiles de fuente pública admitidos", detail: "Cobertura acotada · autoridad gobernada en servidor" },
    trialAct: { eyebrow: "08 · PRUEBA CONTROLADA", title: "Prueba AXIGNAL con un flujo real de cualificación B2G.", body: "La prueba controlada de 7 días requiere solicitud, incluye 1.000.000 de tokens acumulados, no exige tarjeta y nunca convierte automáticamente.", signal: "7 DÍAS", metric: "prueba controlada", detail: "Sólo solicitud · sin tarjeta · sin renovación automática" },
    navigatorResponse: "He creado una investigación acotada usando sólo perfiles cuyo estado de admisión permite la operación solicitada.",
    globeActiveRule: "Sólo las fuentes ADMITTED cuentan como cobertura activa. La cobertura queda limitada por el informe de evidencia vigente.",
    pricing: { eyebrow: "ACCESO COMERCIAL CONTROLADO", title: "Una prueba clara y dos planes mensuales versionados.", body: "La prueba requiere solicitud. La activación de pago y el checkout siguen deshabilitados hasta autorizar el round trip comercial.", candidate: "Libro de precios canónico", current: "Acceso controlado actual", cta: "Solicitar acceso", plans: [["Prueba controlada", "0 €", "7 días", "1.000.000 de tokens acumulados, sin tarjeta y sin conversión automática."], ["Professional", "149 €", "mes", "Investigación B2G individual, dossiers, seguimiento y exportación de evidencia."], ["Team", "399 €", "mes", "Investigaciones compartidas, revisión, gobernanza y uso de equipo."]] },
    faqItems: [["¿AXIGNAL cubre hoy toda la contratación pública mundial?", "No. Las afirmaciones de cobertura se limitan a la evidencia vigente por fuente, país, campo, idioma y tipo de anuncio."], ["¿Qué fuentes están activas?", "Sólo los perfiles con derechos, validación técnica, calidad y autoridad humana vigentes. Los candidatos de descubrimiento no son cobertura."], ["¿AXIGNAL redacta o presenta ofertas?", "No. Ayuda a descubrir, cualificar e investigar. La decisión, comunicación, firma y presentación siguen siendo humanas."], ["¿Cuáles son los precios actuales?", "Professional cuesta 149 € al mes y Team 399 € al mes. La activación sigue controlada."], ["¿Cómo funciona la prueba?", "Dura 7 días, incluye 1.000.000 de tokens acumulados, no requiere tarjeta, no renueva y queda en sólo lectura al expirar."]],
    form: { eyebrow: "SOLICITUD DE PRUEBA B2G DE 7 DÍAS", title: "Trae un flujo real de cualificación de contratos públicos.", body: "Indica qué vende tu empresa al sector público, qué compradores o mercados busca y dónde se concentra el coste de cualificación.", identity: "Tu empresa y rol B2G", fit: "Mercado objetivo y cuello de botella", countries: "Mercados, compradores públicos o tipos de licitación", volume: "Oportunidades revisadas al mes", process: "Proceso o herramientas actuales", useCase: "Qué vende tu empresa al sector público", problem: "Principal cuello de botella de cualificación", consent: "Acepto que AXIGNAL use esta información sólo para evaluar y responder a esta solicitud de prueba B2G. Los datos no se envían a analítica.", submit: "Solicitar prueba B2G de 7 días", success: "Solicitud recibida. AXIGNAL revisará la elegibilidad y responderá por el canal configurado.", error: "El canal de solicitud no está disponible. No se ha registrado ningún éxito.", privacy: "Evaluación limitada · sin suscripción · sin PII en analítica" }
  },
  fr: {
    meta: { title: "AXIGNAL — Intelligence d’opportunités B2G", description: "Trouvez, qualifiez et analysez les marchés publics avec preuves traçables et autorité humaine." },
    navCta: "Demander l’essai B2G de 7 jours",
    hero: { eyebrow: "INTELLIGENCE D’OPPORTUNITÉS BUSINESS-TO-GOVERNMENT (B2G)", title: "Trouvez les marchés publics que votre entreprise est prête à poursuivre.", accent: "Transformez la commande publique mondiale en pipeline B2G qualifié.", descriptor: "Intelligence d’opportunités B2G avec preuves traçables.", summary: "AXIGNAL relie appels d’offres, acheteurs publics, attributions, fournisseurs et signaux de propriété afin de qualifier les opportunités sans perdre les preuves de la décision.", primary: "Demander l’essai B2G de 7 jours", secondary: "Voir une investigation de marché public", status: "Démonstration produit · couverture limitée par les preuves d’admission actuelles" },
    storyIntroBody: "Suivez une investigation synthétique. Les états des sources expriment des limites de preuve, pas une couverture mondiale.",
    sourceAct: { title: "Voyez où se rencontrent demande publique, capacité et preuves admises.", body: "Le Globe distingue couverture admise, candidats de découverte et systèmes indisponibles. La visibilité ne change jamais l’autorité.", metric: "profils de sources publiques admis", detail: "Couverture limitée · autorité serveur" },
    trialAct: { eyebrow: "08 · ESSAI CONTRÔLÉ", title: "Testez AXIGNAL sur un vrai flux de qualification B2G.", body: "L’essai de 7 jours est soumis à demande, comprend 1 000 000 de jetons cumulés, sans carte ni conversion automatique.", signal: "7 JOURS", metric: "essai contrôlé", detail: "Sur demande · sans carte · sans renouvellement automatique" },
    navigatorResponse: "J’ai créé une investigation limitée utilisant uniquement les profils dont l’état d’admission autorise l’opération.", globeActiveRule: "Seules les sources ADMITTED constituent une couverture active. La couverture reste limitée par le rapport de preuve actuel.",
    pricing: { eyebrow: "ACCÈS COMMERCIAL CONTRÔLÉ", title: "Un essai clair et deux offres mensuelles versionnées.", body: "L’essai est soumis à demande. L’activation payante et le checkout restent désactivés jusqu’à autorisation.", candidate: "Catalogue tarifaire canonique", current: "Accès contrôlé actuel", cta: "Demander l’accès", plans: [["Essai contrôlé", "0 €", "7 jours", "1 000 000 de jetons cumulés, sans carte ni conversion automatique."], ["Professional", "149 €", "mois", "Investigation B2G individuelle, dossiers, suivi et export de preuves."], ["Team", "399 €", "mois", "Investigations partagées, revue, gouvernance et usage équipe."]] },
    faqItems: [["AXIGNAL couvre-t-il aujourd’hui toute la commande publique mondiale ?", "Non. Les affirmations sont limitées aux preuves actuelles par source, pays, champ, langue et type d’avis."], ["Quelles sources sont actives ?", "Uniquement les profils disposant de droits, validation technique, qualité et autorité humaine actuels."], ["AXIGNAL rédige-t-il ou dépose-t-il les offres ?", "Non. Les décisions, communications, signatures et dépôts restent humains."], ["Quels sont les prix actuels ?", "Professional coûte 149 € par mois et Team 399 € par mois."], ["Comment fonctionne l’essai ?", "Il dure 7 jours, comprend 1 000 000 de jetons cumulés, sans carte, sans renouvellement et passe en lecture seule à expiration."]],
    form: { eyebrow: "DEMANDE D’ESSAI B2G DE 7 JOURS", title: "Apportez un vrai flux de qualification de marché public.", body: "Indiquez ce que votre entreprise vend au secteur public, les acheteurs visés et le principal coût de qualification.", identity: "Votre entreprise et rôle B2G", fit: "Marché cible et blocage de qualification", countries: "Marchés, acheteurs publics ou types d’appels d’offres", volume: "Opportunités examinées par mois", process: "Processus ou outils actuels", useCase: "Ce que votre entreprise vend au secteur public", problem: "Principal blocage de qualification", consent: "J’accepte qu’AXIGNAL utilise ces informations uniquement pour évaluer et répondre à cette demande d’essai B2G.", submit: "Demander l’essai B2G de 7 jours", success: "Demande reçue. AXIGNAL examinera l’éligibilité et répondra par le canal configuré.", error: "Le canal de demande est indisponible. Aucun succès n’a été enregistré.", privacy: "Évaluation limitée · aucun abonnement · aucune PII analytique" }
  },
  pt: {
    meta: { title: "AXIGNAL — Inteligência de oportunidades B2G", description: "Encontre, qualifique e investigue contratos públicos com evidência rastreável e autoridade humana." }, navCta: "Solicitar teste B2G de 7 dias",
    hero: { eyebrow: "INTELIGÊNCIA DE OPORTUNIDADES BUSINESS-TO-GOVERNMENT (B2G)", title: "Encontre os contratos públicos que a sua empresa está preparada para disputar.", accent: "Transforme a contratação pública global num pipeline B2G qualificado.", descriptor: "Inteligência de oportunidades B2G com evidência rastreável.", summary: "AXIGNAL liga concursos, compradores públicos, adjudicações, fornecedores e sinais de propriedade para descobrir, qualificar e investigar oportunidades sem perder a evidência da decisão.", primary: "Solicitar teste B2G de 7 dias", secondary: "Ver uma investigação de contrato público", status: "Demonstração do produto · cobertura limitada pela evidência de admissão atual" },
    storyIntroBody: "Acompanhe uma investigação sintética. Os estados das fontes representam limites de evidência, não cobertura global.", sourceAct: { title: "Veja onde procura pública, capacidade e evidência admitida se encontram.", body: "O Globo distingue cobertura admitida, candidatos de descoberta e sistemas indisponíveis. A visibilidade não muda a autoridade.", metric: "perfis de fonte pública admitidos", detail: "Cobertura limitada · autoridade no servidor" }, trialAct: { eyebrow: "08 · TESTE CONTROLADO", title: "Teste o AXIGNAL num fluxo real de qualificação B2G.", body: "O teste de 7 dias requer candidatura, inclui 1.000.000 de tokens acumulados, não exige cartão e nunca converte automaticamente.", signal: "7 DIAS", metric: "teste controlado", detail: "Por candidatura · sem cartão · sem renovação automática" }, navigatorResponse: "Criei uma investigação limitada usando apenas perfis cujo estado de admissão permite a operação.", globeActiveRule: "Apenas fontes ADMITTED contam como cobertura ativa. A cobertura permanece limitada pelo relatório atual.",
    pricing: { eyebrow: "ACESSO COMERCIAL CONTROLADO", title: "Um teste claro e dois planos mensais versionados.", body: "O teste requer candidatura. A ativação paga e checkout permanecem desativados até autorização.", candidate: "Livro de preços canónico", current: "Acesso controlado atual", cta: "Solicitar acesso", plans: [["Teste controlado", "0 €", "7 dias", "1.000.000 de tokens acumulados, sem cartão e sem conversão automática."], ["Professional", "149 €", "mês", "Investigação B2G individual, dossiers, monitorização e exportação de evidência."], ["Team", "399 €", "mês", "Investigações partilhadas, revisão, governação e utilização em equipa."]] },
    faqItems: [["O AXIGNAL cobre hoje toda a contratação pública mundial?", "Não. As afirmações de cobertura são limitadas pela evidência atual."], ["Que fontes estão ativas?", "Apenas perfis com direitos, validação técnica, qualidade e autoridade humana atuais."], ["O AXIGNAL escreve ou submete propostas?", "Não. Decisões, comunicações, assinatura e submissão permanecem humanas."], ["Quais são os preços atuais?", "Professional custa 149 € por mês e Team 399 € por mês."], ["Como funciona o teste?", "Dura 7 dias, inclui 1.000.000 de tokens acumulados, sem cartão, sem renovação e fica só de leitura no fim."]],
    form: { eyebrow: "PEDIDO DE TESTE B2G DE 7 DIAS", title: "Traga um fluxo real de qualificação de contratos públicos.", body: "Diga o que a empresa vende ao governo, os mercados ou compradores alvo e o principal bloqueio de qualificação.", identity: "Empresa e função B2G", fit: "Mercado alvo e bloqueio", countries: "Mercados, compradores públicos ou tipos de concurso", volume: "Oportunidades revistas por mês", process: "Processo ou ferramentas atuais", useCase: "O que a empresa vende ao governo", problem: "Principal bloqueio de qualificação", consent: "Aceito que a AXIGNAL use estes dados apenas para avaliar e responder ao pedido de teste B2G.", submit: "Solicitar teste B2G de 7 dias", success: "Pedido recebido. A AXIGNAL avaliará a elegibilidade e responderá pelo canal configurado.", error: "O canal está indisponível. Nenhum sucesso foi registado.", privacy: "Avaliação limitada · sem subscrição · sem PII analítica" }
  },
  de: {
    meta: { title: "AXIGNAL — B2G Opportunity Intelligence", description: "Öffentliche Aufträge mit nachvollziehbarer Evidenz und menschlicher Entscheidungshoheit finden und qualifizieren." }, navCta: "7-tägigen B2G-Test anfragen",
    hero: { eyebrow: "BUSINESS-TO-GOVERNMENT (B2G) OPPORTUNITY INTELLIGENCE", title: "Finden Sie die öffentlichen Aufträge, für die Ihr Unternehmen geschaffen ist.", accent: "Machen Sie globale Beschaffung zu einer qualifizierten B2G-Pipeline.", descriptor: "B2G Opportunity Intelligence mit nachvollziehbarer Evidenz.", summary: "AXIGNAL verbindet Ausschreibungen, öffentliche Auftraggeber, Vergaben, Lieferanten und Eigentumssignale, damit B2G-Teams relevante Chancen qualifizieren können.", primary: "7-tägigen B2G-Test anfragen", secondary: "Untersuchung eines öffentlichen Auftrags ansehen", status: "Produktdemonstration · Abdeckung bleibt durch aktuelle Zulassungsevidenz begrenzt" }, storyIntroBody: "Verfolgen Sie eine synthetische Untersuchung. Quellenzustände beschreiben Evidenzgrenzen, keine globale Abdeckung.", sourceAct: { title: "Sehen Sie, wo öffentliche Nachfrage, Eignung und zugelassene Evidenz zusammentreffen.", body: "Der Globus trennt zugelassene Abdeckung, Discovery-Kandidaten und nicht verfügbare Systeme. Sichtbarkeit ändert keine Autorität.", metric: "zugelassene öffentliche Quellenprofile", detail: "Begrenzte Abdeckung · Serverautorität" }, trialAct: { eyebrow: "08 · KONTROLLIERTER TEST", title: "Testen Sie AXIGNAL an einem realen B2G-Qualifizierungsprozess.", body: "Der 7-tägige Test ist antragsbasiert, enthält 1.000.000 kumulierte Tokens, benötigt keine Karte und konvertiert nie automatisch.", signal: "7 TAGE", metric: "kontrollierter Test", detail: "Nur Antrag · keine Karte · keine automatische Verlängerung" }, navigatorResponse: "Ich habe eine begrenzte Untersuchung mit ausschließlich dafür zugelassenen Quellenprofilen erstellt.", globeActiveRule: "Nur ADMITTED-Quellen zählen als aktive Abdeckung. Die Abdeckung bleibt durch den aktuellen Evidenzbericht begrenzt.",
    pricing: { eyebrow: "KONTROLLIERTER KOMMERZIELLER ZUGANG", title: "Ein klarer Test und zwei versionierte Monatspläne.", body: "Der Test ist antragsbasiert. Bezahlte Aktivierung und Checkout bleiben bis zur Freigabe deaktiviert.", candidate: "Kanonisches Preisbuch", current: "Aktueller kontrollierter Zugang", cta: "Zugang anfragen", plans: [["Kontrollierter Test", "0 €", "7 Tage", "1.000.000 kumulierte Tokens, keine Karte, keine automatische Konvertierung."], ["Professional", "149 €", "Monat", "Individuelle B2G-Untersuchungen, Dossiers, Monitoring und Evidenzexporte."], ["Team", "399 €", "Monat", "Gemeinsame Untersuchungen, Review, Governance und Teamnutzung."]] },
    faqItems: [["Deckt AXIGNAL heute die weltweite öffentliche Beschaffung ab?", "Nein. Aussagen sind auf die aktuelle Evidenz begrenzt."], ["Welche Quellen sind aktiv?", "Nur Profile mit aktuellen Rechten, technischer Prüfung, Qualität und menschlicher Autorität."], ["Erstellt oder übermittelt AXIGNAL Angebote?", "Nein. Entscheidung, Kommunikation, Signatur und Einreichung bleiben menschlich."], ["Wie lauten die aktuellen Preise?", "Professional kostet 149 € pro Monat und Team 399 € pro Monat."], ["Wie funktioniert der Test?", "7 Tage, 1.000.000 kumulierte Tokens, keine Karte, keine Verlängerung, danach nur Lesen."]],
    form: { eyebrow: "ANTRAG FÜR 7-TÄGIGEN B2G-TEST", title: "Bringen Sie einen realen Qualifizierungsprozess für öffentliche Aufträge mit.", body: "Beschreiben Sie Angebot, Zielauftraggeber und den wichtigsten Qualifizierungsengpass.", identity: "Unternehmen und B2G-Rolle", fit: "Zielmarkt und Engpass", countries: "Zielmärkte, öffentliche Käufer oder Ausschreibungstypen", volume: "Geprüfte Chancen pro Monat", process: "Aktueller Prozess oder Werkzeuge", useCase: "Was Ihr Unternehmen an Behörden verkauft", problem: "Wichtigster Qualifizierungsengpass", consent: "Ich stimme zu, dass AXIGNAL diese Daten nur zur Bewertung und Beantwortung des B2G-Testantrags verwendet.", submit: "7-tägigen B2G-Test anfragen", success: "Anfrage eingegangen. AXIGNAL prüft die Berechtigung und antwortet über den konfigurierten Kanal.", error: "Der Kanal ist nicht verfügbar. Es wurde kein Erfolg gespeichert.", privacy: "Zweckgebundene Prüfung · kein Abonnement · keine PII-Analyse" }
  },
  it: {
    meta: { title: "AXIGNAL — Intelligence delle opportunità B2G", description: "Trova, qualifica e analizza contratti pubblici con evidenze tracciabili e autorità umana." }, navCta: "Richiedi la prova B2G di 7 giorni",
    hero: { eyebrow: "BUSINESS-TO-GOVERNMENT (B2G) OPPORTUNITY INTELLIGENCE", title: "Trova i contratti pubblici che la tua impresa è pronta a perseguire.", accent: "Trasforma gli appalti globali in una pipeline B2G qualificata.", descriptor: "Intelligence delle opportunità B2G con evidenze tracciabili.", summary: "AXIGNAL collega gare, enti appaltanti, aggiudicazioni, fornitori e segnali proprietari per qualificare le opportunità senza perdere le evidenze della decisione.", primary: "Richiedi la prova B2G di 7 giorni", secondary: "Guarda un’indagine su un contratto pubblico", status: "Dimostrazione del prodotto · copertura limitata dalle evidenze di ammissione correnti" }, storyIntroBody: "Segui un’indagine sintetica. Gli stati delle fonti rappresentano limiti di evidenza, non copertura globale.", sourceAct: { title: "Osserva dove domanda pubblica, capacità ed evidenza ammessa si incontrano.", body: "Il Globo distingue copertura ammessa, candidati discovery e sistemi non disponibili. La visibilità non cambia l’autorità.", metric: "profili di fonti pubbliche ammessi", detail: "Copertura limitata · autorità server" }, trialAct: { eyebrow: "08 · PROVA CONTROLLATA", title: "Prova AXIGNAL su un vero flusso di qualificazione B2G.", body: "La prova di 7 giorni richiede domanda, include 1.000.000 di token cumulativi, non richiede carta e non converte automaticamente.", signal: "7 GIORNI", metric: "prova controllata", detail: "Solo domanda · senza carta · senza rinnovo automatico" }, navigatorResponse: "Ho creato un’indagine limitata usando soltanto profili il cui stato di ammissione consente l’operazione.", globeActiveRule: "Solo le fonti ADMITTED contano come copertura attiva. La copertura resta limitata dal rapporto corrente.",
    pricing: { eyebrow: "ACCESSO COMMERCIALE CONTROLLATO", title: "Una prova chiara e due piani mensili versionati.", body: "La prova richiede domanda. Attivazione a pagamento e checkout restano disabilitati fino all’autorizzazione.", candidate: "Listino canonico", current: "Accesso controllato attuale", cta: "Richiedi accesso", plans: [["Prova controllata", "0 €", "7 giorni", "1.000.000 di token cumulativi, senza carta e senza conversione automatica."], ["Professional", "149 €", "mese", "Indagine B2G individuale, dossier, monitoraggio ed export delle evidenze."], ["Team", "399 €", "mese", "Indagini condivise, revisione, governance e utilizzo del team."]] },
    faqItems: [["AXIGNAL copre oggi tutti gli appalti pubblici mondiali?", "No. Le affermazioni sono limitate alle evidenze correnti."], ["Quali fonti sono attive?", "Solo profili con diritti, verifica tecnica, qualità e autorità umana correnti."], ["AXIGNAL scrive o presenta offerte?", "No. Decisione, comunicazione, firma e presentazione restano umane."], ["Quali sono i prezzi attuali?", "Professional costa 149 € al mese e Team 399 € al mese."], ["Come funziona la prova?", "Dura 7 giorni, include 1.000.000 di token cumulativi, senza carta, senza rinnovo e poi sola lettura."]],
    form: { eyebrow: "RICHIESTA PROVA B2G DI 7 GIORNI", title: "Porta un vero flusso di qualificazione di contratti pubblici.", body: "Descrivi cosa vende l’impresa alla PA, i mercati o buyer obiettivo e il principale collo di bottiglia.", identity: "Impresa e ruolo B2G", fit: "Mercato obiettivo e collo di bottiglia", countries: "Mercati, buyer pubblici o tipi di gara", volume: "Opportunità esaminate al mese", process: "Processo o strumenti attuali", useCase: "Cosa vende l’impresa alla pubblica amministrazione", problem: "Principale collo di bottiglia", consent: "Accetto che AXIGNAL usi questi dati solo per valutare e rispondere alla richiesta di prova B2G.", submit: "Richiedi la prova B2G di 7 giorni", success: "Richiesta ricevuta. AXIGNAL valuterà l’idoneità e risponderà tramite il canale configurato.", error: "Il canale non è disponibile. Nessun successo è stato registrato.", privacy: "Valutazione limitata · nessun abbonamento · nessuna PII analytics" }
  }
};
