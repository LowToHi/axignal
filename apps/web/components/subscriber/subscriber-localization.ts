import type { IntelligenceWorkspaceCopy } from "./intelligence";

export const shellLocales = ["en", "es", "fr", "de", "pt", "it"] as const;
export type ShellLocale = (typeof shellLocales)[number];

export const localeNames: Record<ShellLocale, string> = {
  en: "English",
  es: "Español",
  fr: "Français",
  de: "Deutsch",
  pt: "Português",
  it: "Italiano",
};

export type ShellNavKey =
  | "axent"
  | "commandCenter"
  | "opportunities"
  | "investigations"
  | "workspaces"
  | "libraries"
  | "alerts"
  | "reports"
  | "team"
  | "billing"
  | "settings"
  | "methodology"
  | "help";

export type WorkspaceSectionKey =
  | "overview"
  | "qualification"
  | "requirements"
  | "evidence"
  | "documents"
  | "workplan"
  | "clarifications"
  | "changes"
  | "commercial"
  | "team"
  | "submission"
  | "outcome"
  | "audit";

type ShellCopy = {
  nav: Record<ShellNavKey, string>;
  sections: Record<WorkspaceSectionKey, string>;
  productNavigation: string;
  currentWorkspaceSections: string;
  more: string;
  backToWorkspaces: string;
  tenderWorkspaceNavigation: string;
  workspaceSections: string;
  governedProcurement: string;
  readiness: (value: number) => string;
  readinessLabel: string;
  blockingRequirements: (count: number) => string;
  skipToMain: string;
  fixtureNotice: string;
  closeNavigationOverlay: string;
  mobileProductNavigation: string;
  closeNavigation: string;
  expandNavigation: string;
  collapseNavigation: string;
  collapse: string;
  openNavigation: string;
  currentOrganisation: (organisation: string) => string;
  searchTrigger: string;
  shortcutDescription: string;
  language: string;
  notifications: string;
  help: string;
  accountMenuFor: (name: string) => string;
  notificationsDialog: string;
  notificationsAttention: string;
  evidenceExpiry: string;
  amendmentWaiting: string;
  accountMenu: string;
  accountSettings: string;
  signOut: string;
  signingOut: string;
  logoutFailed: (status: number) => string;
  logoutUnknown: string;
  searchCommand: string;
  closeCommandPalette: string;
  navigate: string;
  enterOpen: string;
  escapeClose: string;
  intelligence: IntelligenceWorkspaceCopy;
};

const intelligenceEnglish: IntelligenceWorkspaceCopy = {
  navigatorTitle: "AXIGNAL NAVIGATOR",
  online: "ONLINE",
  composerPlaceholder: "Write a command or question…",
  send: "Send",
  lensLabel: "Select intelligence lens",
  opportunitiesTitle: "OPPORTUNITIES",
  orderByPotential: "Order by: Potential",
  expectedReturn: "Evidence fit",
  confidence: "Assessment confidence",
  claimsTitle: "CLAIM & EVIDENCE RAIL",
  allClaims: "All",
  fact: "Fact",
  inference: "Inference",
  prediction: "Prediction",
  contradiction: "Contradiction",
  unknown: "Unknown",
  view: "View",
  fixtureNotice: "ENGINEERING FIXTURE · NOT LIVE DATA",
  stateTitle: "This intelligence view is not available",
  retry: "Retry",
};

export const shellCopy: Record<ShellLocale, ShellCopy> = {
  en: {
    nav: { axent: "AXENT", commandCenter: "Command Center", opportunities: "Opportunities", investigations: "Investigations", workspaces: "Workspaces", libraries: "Libraries", alerts: "Alerts", reports: "Reports", team: "Team", billing: "Plan & Billing", settings: "Settings", methodology: "Methodology", help: "Help" },
    sections: { overview: "Overview", qualification: "Qualification", requirements: "Requirements", evidence: "Evidence", documents: "Documents", workplan: "Workplan", clarifications: "Clarifications", changes: "Changes", commercial: "Commercial", team: "Team & Approvals", submission: "Submission", outcome: "Outcome & Learning", audit: "Audit" },
    productNavigation: "Product navigation", currentWorkspaceSections: "Current workspace sections", more: "More", backToWorkspaces: "Back to Workspaces", tenderWorkspaceNavigation: "Tender workspace navigation", workspaceSections: "Workspace sections", governedProcurement: "GOVERNED PROCUREMENT · TENANT SCOPED", readiness: (value) => `Readiness ${value} percent`, readinessLabel: "readiness", blockingRequirements: (count) => `${count} blocking requirements`, skipToMain: "Skip to main content", fixtureNotice: "ENGINEERING FIXTURE · NOT LIVE DATA", closeNavigationOverlay: "Close navigation overlay", mobileProductNavigation: "Mobile product navigation", closeNavigation: "Close navigation", expandNavigation: "Expand navigation", collapseNavigation: "Collapse navigation", collapse: "Collapse", openNavigation: "Open navigation", currentOrganisation: (value) => `Current organisation: ${value}`, searchTrigger: "Search opportunities, entities, sources…", shortcutDescription: "Command K on Apple, Control K on Windows and Linux", language: "Language", notifications: "Notifications", help: "Help", accountMenuFor: (name) => `Account menu for ${name}`, notificationsDialog: "Notifications", notificationsAttention: "2 items require attention", evidenceExpiry: "Blocking evidence expires in 4 days", amendmentWaiting: "Amendment review is waiting", accountMenu: "Account menu", accountSettings: "Account settings", signOut: "Sign out and clear local AXENT history", signingOut: "Signing out…", logoutFailed: (status) => `Logout failed with ${status}.`, logoutUnknown: "Logout could not be completed.", searchCommand: "Search or enter a command", closeCommandPalette: "Close command palette", navigate: "Navigate", enterOpen: "open", escapeClose: "close", intelligence: intelligenceEnglish,
  },
  es: {
    nav: { axent: "AXENT", commandCenter: "Centro de mando", opportunities: "Oportunidades", investigations: "Investigaciones", workspaces: "Espacios de trabajo", libraries: "Bibliotecas", alerts: "Alertas", reports: "Informes", team: "Equipo", billing: "Plan y facturación", settings: "Configuración", methodology: "Metodología", help: "Ayuda" },
    sections: { overview: "Resumen", qualification: "Calificación", requirements: "Requisitos", evidence: "Evidencia", documents: "Documentos", workplan: "Plan de trabajo", clarifications: "Aclaraciones", changes: "Cambios", commercial: "Comercial", team: "Equipo y aprobaciones", submission: "Presentación", outcome: "Resultado y aprendizaje", audit: "Auditoría" },
    productNavigation: "Navegación del producto", currentWorkspaceSections: "Secciones del espacio de trabajo actual", more: "Más", backToWorkspaces: "Volver a Espacios de trabajo", tenderWorkspaceNavigation: "Navegación del espacio de licitación", workspaceSections: "Secciones del espacio de trabajo", governedProcurement: "CONTRATACIÓN GOBERNADA · ÁMBITO DEL TENANT", readiness: (value) => `Preparación ${value} por ciento`, readinessLabel: "preparación", blockingRequirements: (count) => `${count} requisitos bloqueantes`, skipToMain: "Saltar al contenido principal", fixtureNotice: "FIXTURE DE INGENIERÍA · NO SON DATOS EN VIVO", closeNavigationOverlay: "Cerrar superposición de navegación", mobileProductNavigation: "Navegación móvil del producto", closeNavigation: "Cerrar navegación", expandNavigation: "Expandir navegación", collapseNavigation: "Contraer navegación", collapse: "Contraer", openNavigation: "Abrir navegación", currentOrganisation: (value) => `Organización actual: ${value}`, searchTrigger: "Buscar oportunidades, entidades y fuentes…", shortcutDescription: "Comando K en Apple, Control K en Windows y Linux", language: "Idioma", notifications: "Notificaciones", help: "Ayuda", accountMenuFor: (name) => `Menú de cuenta de ${name}`, notificationsDialog: "Notificaciones", notificationsAttention: "2 elementos requieren atención", evidenceExpiry: "La evidencia bloqueante caduca en 4 días", amendmentWaiting: "La revisión de una modificación está pendiente", accountMenu: "Menú de cuenta", accountSettings: "Configuración de la cuenta", signOut: "Cerrar sesión y borrar el historial local de AXENT", signingOut: "Cerrando sesión…", logoutFailed: (status) => `El cierre de sesión falló con ${status}.`, logoutUnknown: "No se pudo cerrar la sesión.", searchCommand: "Buscar o introducir un comando", closeCommandPalette: "Cerrar paleta de comandos", navigate: "Navegar", enterOpen: "abrir", escapeClose: "cerrar", intelligence: { navigatorTitle: "NAVEGADOR AXIGNAL", online: "EN LÍNEA", composerPlaceholder: "Escribe un comando o una pregunta…", send: "Enviar", lensLabel: "Seleccionar lente de inteligencia", opportunitiesTitle: "OPORTUNIDADES", orderByPotential: "Ordenar por: potencial", expectedReturn: "Ajuste de evidencia", confidence: "Confianza de la evaluación", claimsTitle: "RAÍL DE AFIRMACIONES Y EVIDENCIA", allClaims: "Todas", fact: "Hecho", inference: "Inferencia", prediction: "Predicción", contradiction: "Contradicción", unknown: "Desconocido", view: "Ver", fixtureNotice: "FIXTURE DE INGENIERÍA · NO SON DATOS EN VIVO", stateTitle: "Esta vista de inteligencia no está disponible", retry: "Reintentar" },
  },
  fr: {
    nav: { axent: "AXENT", commandCenter: "Centre de commande", opportunities: "Opportunités", investigations: "Investigations", workspaces: "Espaces de travail", libraries: "Bibliothèques", alerts: "Alertes", reports: "Rapports", team: "Équipe", billing: "Offre et facturation", settings: "Paramètres", methodology: "Méthodologie", help: "Aide" },
    sections: { overview: "Vue d’ensemble", qualification: "Qualification", requirements: "Exigences", evidence: "Éléments probants", documents: "Documents", workplan: "Plan de travail", clarifications: "Clarifications", changes: "Modifications", commercial: "Commercial", team: "Équipe et approbations", submission: "Soumission", outcome: "Résultat et apprentissage", audit: "Audit" },
    productNavigation: "Navigation du produit", currentWorkspaceSections: "Sections de l’espace de travail actuel", more: "Plus", backToWorkspaces: "Retour aux espaces de travail", tenderWorkspaceNavigation: "Navigation de l’espace d’appel d’offres", workspaceSections: "Sections de l’espace de travail", governedProcurement: "ACHATS GOUVERNÉS · PÉRIMÈTRE DU TENANT", readiness: (value) => `Préparation ${value} pour cent`, readinessLabel: "préparation", blockingRequirements: (count) => `${count} exigences bloquantes`, skipToMain: "Aller au contenu principal", fixtureNotice: "FIXTURE D’INGÉNIERIE · PAS DE DONNÉES EN DIRECT", closeNavigationOverlay: "Fermer la superposition de navigation", mobileProductNavigation: "Navigation mobile du produit", closeNavigation: "Fermer la navigation", expandNavigation: "Développer la navigation", collapseNavigation: "Réduire la navigation", collapse: "Réduire", openNavigation: "Ouvrir la navigation", currentOrganisation: (value) => `Organisation actuelle : ${value}`, searchTrigger: "Rechercher des opportunités, entités et sources…", shortcutDescription: "Commande K sur Apple, Contrôle K sous Windows et Linux", language: "Langue", notifications: "Notifications", help: "Aide", accountMenuFor: (name) => `Menu du compte de ${name}`, notificationsDialog: "Notifications", notificationsAttention: "2 éléments nécessitent votre attention", evidenceExpiry: "Un élément probant bloquant expire dans 4 jours", amendmentWaiting: "La revue d’une modification est en attente", accountMenu: "Menu du compte", accountSettings: "Paramètres du compte", signOut: "Se déconnecter et effacer l’historique AXENT local", signingOut: "Déconnexion…", logoutFailed: (status) => `La déconnexion a échoué avec ${status}.`, logoutUnknown: "La déconnexion n’a pas pu être effectuée.", searchCommand: "Rechercher ou saisir une commande", closeCommandPalette: "Fermer la palette de commandes", navigate: "Naviguer", enterOpen: "ouvrir", escapeClose: "fermer", intelligence: { navigatorTitle: "NAVIGATEUR AXIGNAL", online: "EN LIGNE", composerPlaceholder: "Écrivez une commande ou une question…", send: "Envoyer", lensLabel: "Sélectionner la perspective d’intelligence", opportunitiesTitle: "OPPORTUNITÉS", orderByPotential: "Trier par : potentiel", expectedReturn: "Adéquation des preuves", confidence: "Confiance de l’évaluation", claimsTitle: "VOLET DES AFFIRMATIONS ET PREUVES", allClaims: "Toutes", fact: "Fait", inference: "Inférence", prediction: "Prédiction", contradiction: "Contradiction", unknown: "Inconnu", view: "Voir", fixtureNotice: "FIXTURE D’INGÉNIERIE · PAS DE DONNÉES EN DIRECT", stateTitle: "Cette vue d’intelligence n’est pas disponible", retry: "Réessayer" },
  },
  de: {
    nav: { axent: "AXENT", commandCenter: "Kommandozentrale", opportunities: "Chancen", investigations: "Untersuchungen", workspaces: "Arbeitsbereiche", libraries: "Bibliotheken", alerts: "Warnungen", reports: "Berichte", team: "Team", billing: "Tarif und Abrechnung", settings: "Einstellungen", methodology: "Methodik", help: "Hilfe" },
    sections: { overview: "Übersicht", qualification: "Qualifizierung", requirements: "Anforderungen", evidence: "Nachweise", documents: "Dokumente", workplan: "Arbeitsplan", clarifications: "Klärungen", changes: "Änderungen", commercial: "Kaufmännisch", team: "Team und Freigaben", submission: "Einreichung", outcome: "Ergebnis und Lernen", audit: "Audit" },
    productNavigation: "Produktnavigation", currentWorkspaceSections: "Abschnitte des aktuellen Arbeitsbereichs", more: "Mehr", backToWorkspaces: "Zurück zu Arbeitsbereichen", tenderWorkspaceNavigation: "Navigation des Vergabearbeitsbereichs", workspaceSections: "Arbeitsbereichsabschnitte", governedProcurement: "GEREGELTE BESCHAFFUNG · MANDANTENBEREICH", readiness: (value) => `Bereitschaft ${value} Prozent`, readinessLabel: "Bereitschaft", blockingRequirements: (count) => `${count} blockierende Anforderungen`, skipToMain: "Zum Hauptinhalt springen", fixtureNotice: "ENGINEERING-FIXTURE · KEINE LIVE-DATEN", closeNavigationOverlay: "Navigationsüberlagerung schließen", mobileProductNavigation: "Mobile Produktnavigation", closeNavigation: "Navigation schließen", expandNavigation: "Navigation erweitern", collapseNavigation: "Navigation reduzieren", collapse: "Reduzieren", openNavigation: "Navigation öffnen", currentOrganisation: (value) => `Aktuelle Organisation: ${value}`, searchTrigger: "Chancen, Entitäten und Quellen suchen…", shortcutDescription: "Befehl K auf Apple, Steuerung K unter Windows und Linux", language: "Sprache", notifications: "Benachrichtigungen", help: "Hilfe", accountMenuFor: (name) => `Kontomenü für ${name}`, notificationsDialog: "Benachrichtigungen", notificationsAttention: "2 Einträge benötigen Aufmerksamkeit", evidenceExpiry: "Ein blockierender Nachweis läuft in 4 Tagen ab", amendmentWaiting: "Eine Änderungsprüfung wartet", accountMenu: "Kontomenü", accountSettings: "Kontoeinstellungen", signOut: "Abmelden und lokalen AXENT-Verlauf löschen", signingOut: "Abmeldung…", logoutFailed: (status) => `Abmeldung mit ${status} fehlgeschlagen.`, logoutUnknown: "Abmeldung konnte nicht abgeschlossen werden.", searchCommand: "Suchen oder Befehl eingeben", closeCommandPalette: "Befehlspalette schließen", navigate: "Navigieren", enterOpen: "öffnen", escapeClose: "schließen", intelligence: { navigatorTitle: "AXIGNAL-NAVIGATOR", online: "ONLINE", composerPlaceholder: "Befehl oder Frage eingeben…", send: "Senden", lensLabel: "Intelligence-Perspektive auswählen", opportunitiesTitle: "CHANCEN", orderByPotential: "Sortieren nach: Potenzial", expectedReturn: "Nachweisabdeckung", confidence: "Bewertungssicherheit", claimsTitle: "AUSSAGEN- UND NACHWEISLEISTE", allClaims: "Alle", fact: "Fakt", inference: "Schlussfolgerung", prediction: "Prognose", contradiction: "Widerspruch", unknown: "Unbekannt", view: "Anzeigen", fixtureNotice: "ENGINEERING-FIXTURE · KEINE LIVE-DATEN", stateTitle: "Diese Intelligence-Ansicht ist nicht verfügbar", retry: "Erneut versuchen" },
  },
  pt: {
    nav: { axent: "AXENT", commandCenter: "Centro de comando", opportunities: "Oportunidades", investigations: "Investigações", workspaces: "Espaços de trabalho", libraries: "Bibliotecas", alerts: "Alertas", reports: "Relatórios", team: "Equipa", billing: "Plano e faturação", settings: "Definições", methodology: "Metodologia", help: "Ajuda" },
    sections: { overview: "Visão geral", qualification: "Qualificação", requirements: "Requisitos", evidence: "Evidência", documents: "Documentos", workplan: "Plano de trabalho", clarifications: "Esclarecimentos", changes: "Alterações", commercial: "Comercial", team: "Equipa e aprovações", submission: "Submissão", outcome: "Resultado e aprendizagem", audit: "Auditoria" },
    productNavigation: "Navegação do produto", currentWorkspaceSections: "Secções do espaço de trabalho atual", more: "Mais", backToWorkspaces: "Voltar aos espaços de trabalho", tenderWorkspaceNavigation: "Navegação do espaço de concurso", workspaceSections: "Secções do espaço de trabalho", governedProcurement: "CONTRATAÇÃO GOVERNADA · ÂMBITO DO TENANT", readiness: (value) => `Preparação ${value} por cento`, readinessLabel: "preparação", blockingRequirements: (count) => `${count} requisitos bloqueadores`, skipToMain: "Saltar para o conteúdo principal", fixtureNotice: "FIXTURE DE ENGENHARIA · NÃO SÃO DADOS EM DIRETO", closeNavigationOverlay: "Fechar sobreposição de navegação", mobileProductNavigation: "Navegação móvel do produto", closeNavigation: "Fechar navegação", expandNavigation: "Expandir navegação", collapseNavigation: "Recolher navegação", collapse: "Recolher", openNavigation: "Abrir navegação", currentOrganisation: (value) => `Organização atual: ${value}`, searchTrigger: "Pesquisar oportunidades, entidades e fontes…", shortcutDescription: "Comando K em Apple, Controlo K em Windows e Linux", language: "Idioma", notifications: "Notificações", help: "Ajuda", accountMenuFor: (name) => `Menu da conta de ${name}`, notificationsDialog: "Notificações", notificationsAttention: "2 itens requerem atenção", evidenceExpiry: "A evidência bloqueadora expira em 4 dias", amendmentWaiting: "A revisão de uma alteração está pendente", accountMenu: "Menu da conta", accountSettings: "Definições da conta", signOut: "Terminar sessão e apagar o histórico local do AXENT", signingOut: "A terminar sessão…", logoutFailed: (status) => `O fim de sessão falhou com ${status}.`, logoutUnknown: "Não foi possível terminar a sessão.", searchCommand: "Pesquisar ou introduzir um comando", closeCommandPalette: "Fechar paleta de comandos", navigate: "Navegar", enterOpen: "abrir", escapeClose: "fechar", intelligence: { navigatorTitle: "NAVEGADOR AXIGNAL", online: "ONLINE", composerPlaceholder: "Escreva um comando ou uma pergunta…", send: "Enviar", lensLabel: "Selecionar perspetiva de inteligência", opportunitiesTitle: "OPORTUNIDADES", orderByPotential: "Ordenar por: potencial", expectedReturn: "Adequação da evidência", confidence: "Confiança da avaliação", claimsTitle: "PAINEL DE ALEGAÇÕES E EVIDÊNCIA", allClaims: "Todas", fact: "Facto", inference: "Inferência", prediction: "Previsão", contradiction: "Contradição", unknown: "Desconhecido", view: "Ver", fixtureNotice: "FIXTURE DE ENGENHARIA · NÃO SÃO DADOS EM DIRETO", stateTitle: "Esta vista de inteligência não está disponível", retry: "Tentar novamente" },
  },
  it: {
    nav: { axent: "AXENT", commandCenter: "Centro di comando", opportunities: "Opportunità", investigations: "Indagini", workspaces: "Spazi di lavoro", libraries: "Biblioteche", alerts: "Avvisi", reports: "Rapporti", team: "Team", billing: "Piano e fatturazione", settings: "Impostazioni", methodology: "Metodologia", help: "Aiuto" },
    sections: { overview: "Panoramica", qualification: "Qualificazione", requirements: "Requisiti", evidence: "Evidenze", documents: "Documenti", workplan: "Piano di lavoro", clarifications: "Chiarimenti", changes: "Modifiche", commercial: "Commerciale", team: "Team e approvazioni", submission: "Presentazione", outcome: "Esito e apprendimento", audit: "Audit" },
    productNavigation: "Navigazione del prodotto", currentWorkspaceSections: "Sezioni dello spazio di lavoro corrente", more: "Altro", backToWorkspaces: "Torna agli spazi di lavoro", tenderWorkspaceNavigation: "Navigazione dello spazio di gara", workspaceSections: "Sezioni dello spazio di lavoro", governedProcurement: "APPALTI GOVERNATI · AMBITO DEL TENANT", readiness: (value) => `Preparazione ${value} percento`, readinessLabel: "preparazione", blockingRequirements: (count) => `${count} requisiti bloccanti`, skipToMain: "Vai al contenuto principale", fixtureNotice: "FIXTURE DI INGEGNERIA · NON SONO DATI IN TEMPO REALE", closeNavigationOverlay: "Chiudi sovrapposizione di navigazione", mobileProductNavigation: "Navigazione mobile del prodotto", closeNavigation: "Chiudi navigazione", expandNavigation: "Espandi navigazione", collapseNavigation: "Riduci navigazione", collapse: "Riduci", openNavigation: "Apri navigazione", currentOrganisation: (value) => `Organizzazione corrente: ${value}`, searchTrigger: "Cerca opportunità, entità e fonti…", shortcutDescription: "Comando K su Apple, Controllo K su Windows e Linux", language: "Lingua", notifications: "Notifiche", help: "Aiuto", accountMenuFor: (name) => `Menu account di ${name}`, notificationsDialog: "Notifiche", notificationsAttention: "2 elementi richiedono attenzione", evidenceExpiry: "Un’evidenza bloccante scade tra 4 giorni", amendmentWaiting: "La revisione di una modifica è in attesa", accountMenu: "Menu account", accountSettings: "Impostazioni account", signOut: "Disconnetti e cancella la cronologia AXENT locale", signingOut: "Disconnessione…", logoutFailed: (status) => `Disconnessione non riuscita con ${status}.`, logoutUnknown: "Non è stato possibile completare la disconnessione.", searchCommand: "Cerca o inserisci un comando", closeCommandPalette: "Chiudi tavolozza comandi", navigate: "Naviga", enterOpen: "apri", escapeClose: "chiudi", intelligence: { navigatorTitle: "NAVIGATORE AXIGNAL", online: "ONLINE", composerPlaceholder: "Scrivi un comando o una domanda…", send: "Invia", lensLabel: "Seleziona prospettiva di intelligence", opportunitiesTitle: "OPPORTUNITÀ", orderByPotential: "Ordina per: potenziale", expectedReturn: "Adeguatezza delle evidenze", confidence: "Affidabilità della valutazione", claimsTitle: "PANNELLO DI AFFERMAZIONI ED EVIDENZE", allClaims: "Tutte", fact: "Fatto", inference: "Inferenza", prediction: "Previsione", contradiction: "Contraddizione", unknown: "Sconosciuto", view: "Visualizza", fixtureNotice: "FIXTURE DI INGEGNERIA · NON SONO DATI IN TEMPO REALE", stateTitle: "Questa vista di intelligence non è disponibile", retry: "Riprova" },
  },
};

export function isShellLocale(value: string | null | undefined): value is ShellLocale {
  return shellLocales.includes(value as ShellLocale);
}
