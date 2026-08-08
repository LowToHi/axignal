import type { ShellLocale } from "./subscriber/subscriber-localization";

export type AuthMode = "login" | "signup" | "recovery";

export type AuthCopy = {
  workspaceLabel: string;
  pageFooter: string;
  eyebrow: string;
  heroLine1: string;
  heroLine2: string;
  heroBody: string;
  trustItems: readonly [string, string, string];
  pilotLabel: string;
  cardKicker: string;
  cardTitle: string;
  cardBody: string;
  tabs: Record<AuthMode, string>;
  loginButton: string;
  loginBusy: string;
  loginHint: string;
  signupEmail: string;
  emailPlaceholder: string;
  continue: string;
  sending: string;
  recoveryEmail: string;
  recoveryCode: string;
  recoveryPlaceholder: string;
  createPasskey: string;
  verifying: string;
  securityCheck: string;
  statusEmailSent: string;
  emailVerifiedStepUp: string;
  emailVerified: string;
  saveCodesKicker: string;
  saveCodesTitle: string;
  saveCodesBody: string;
  codesSaved: string;
  footer: string;
  testVerify: string;
  completeSecurity: string;
  browserUnsupported: string;
  registrationCancelled: string;
  authenticationCancelled: string;
  signupFailed: string;
  verifyEmailFailed: string;
  loginFailed: string;
  recoveryFailed: string;
  errorTitle: string;
  retryHint: string;
  statusTitle: string;
  legacyKicker: string;
  legacyTitle: string;
  legacyBody: string;
  legacyPassword: string;
  legacySubmit: string;
  legacySubmitting: string;
  legacyFooter: string;
};

export const authCopy: Record<ShellLocale, AuthCopy> = {
  en: {
    workspaceLabel: "Private workspace",
    pageFooter: "Evidence-governed opportunity operations",
    eyebrow: "B2G OPPORTUNITY INTELLIGENCE",
    heroLine1: "Turn public signals into",
    heroLine2: "defensible decisions.",
    heroBody: "AXIGNAL connects official sources, governed evidence and the work your bid team needs to move an opportunity forward.",
    trustItems: ["Phishing-resistant access", "Server-resolved organisation", "Auditable evidence trail"],
    pilotLabel: "Controlled private pilot",
    cardKicker: "SECURE ACCESS",
    cardTitle: "Welcome to AXIGNAL",
    cardBody: "Use your passkey to enter the workspace. No password is stored or sent.",
    tabs: { login: "Sign in", signup: "Create account", recovery: "Recover" },
    loginButton: "Continue with passkey",
    loginBusy: "Waiting for your passkey…",
    loginHint: "Your device will open its secure passkey dialog.",
    signupEmail: "Work email",
    emailPlaceholder: "name@company.com",
    continue: "Continue",
    sending: "Sending…",
    recoveryEmail: "Account email",
    recoveryCode: "Recovery code",
    recoveryPlaceholder: "Enter one unused code",
    createPasskey: "Create a new passkey",
    verifying: "Verifying…",
    securityCheck: "Adaptive security check",
    statusEmailSent: "If the address can be used, you will receive a verification link.",
    emailVerifiedStepUp: "Email verified. Trial activation requires one additional check.",
    emailVerified: "Email verified. Create a passkey to finish.",
    saveCodesKicker: "ACCOUNT RECOVERY",
    saveCodesTitle: "Save your recovery codes",
    saveCodesBody: "Each code can be used once. AXIGNAL will not show them again.",
    codesSaved: "I have saved the codes",
    footer: "Your email verifies the address. Your passkey authenticates you. A new account does not grant another trial.",
    testVerify: "Verify test email and create passkey",
    completeSecurity: "Complete the security check before continuing.",
    browserUnsupported: "This browser does not support passkeys. Use a current version of Chrome, Edge, Safari or Firefox.",
    registrationCancelled: "Passkey creation was cancelled or timed out. Try again and approve the security prompt on your device.",
    authenticationCancelled: "The passkey request was cancelled or timed out. Try again and approve the security prompt on your device.",
    signupFailed: "We could not start account creation.",
    verifyEmailFailed: "We could not verify the email address.",
    loginFailed: "We could not sign you in.",
    recoveryFailed: "We could not recover the account.",
    errorTitle: "We could not complete that step",
    retryHint: "Nothing has been changed. You can try again safely.",
    statusTitle: "Check your inbox",
    legacyKicker: "IDENTITY BOUNDARY",
    legacyTitle: "Secure access",
    legacyBody: "Sign in to resolve your organisation on the server and open your persistent InvestigationContext.",
    legacyPassword: "Password",
    legacySubmit: "Sign in",
    legacySubmitting: "Verifying…",
    legacyFooter: "The browser cannot declare or change the organisation.",
  },
  es: {
    workspaceLabel: "Espacio de trabajo privado",
    pageFooter: "Operaciones de oportunidades gobernadas por evidencia",
    eyebrow: "INTELIGENCIA DE OPORTUNIDADES B2G",
    heroLine1: "Convierte señales públicas en",
    heroLine2: "decisiones defendibles.",
    heroBody: "AXIGNAL conecta fuentes oficiales, evidencia gobernada y el trabajo que tu equipo necesita para avanzar cada oportunidad.",
    trustItems: ["Acceso resistente al phishing", "Organización resuelta en el servidor", "Trazabilidad completa de la evidencia"],
    pilotLabel: "Piloto privado controlado",
    cardKicker: "ACCESO SEGURO",
    cardTitle: "Te damos la bienvenida a AXIGNAL",
    cardBody: "Usa tu passkey para entrar. No almacenamos ni enviamos ninguna contraseña.",
    tabs: { login: "Entrar", signup: "Crear cuenta", recovery: "Recuperar" },
    loginButton: "Continuar con passkey",
    loginBusy: "Esperando tu passkey…",
    loginHint: "Tu dispositivo abrirá su ventana segura de passkeys.",
    signupEmail: "Email profesional",
    emailPlaceholder: "nombre@empresa.com",
    continue: "Continuar",
    sending: "Enviando…",
    recoveryEmail: "Email de la cuenta",
    recoveryCode: "Código de recuperación",
    recoveryPlaceholder: "Introduce un código sin usar",
    createPasskey: "Crear una passkey nueva",
    verifying: "Verificando…",
    securityCheck: "Comprobación de seguridad adaptativa",
    statusEmailSent: "Si la dirección puede utilizarse, recibirás un enlace de verificación.",
    emailVerifiedStepUp: "Email verificado. La activación del periodo de prueba requiere una comprobación adicional.",
    emailVerified: "Email verificado. Crea una passkey para terminar.",
    saveCodesKicker: "RECUPERACIÓN DE CUENTA",
    saveCodesTitle: "Guarda tus códigos de recuperación",
    saveCodesBody: "Cada código puede usarse una sola vez. AXIGNAL no volverá a mostrarlos.",
    codesSaved: "He guardado los códigos",
    footer: "El email verifica la dirección. La passkey te autentica. Crear otra cuenta no concede otro periodo de prueba.",
    testVerify: "Verificar email de prueba y crear passkey",
    completeSecurity: "Completa la comprobación de seguridad antes de continuar.",
    browserUnsupported: "Este navegador no admite passkeys. Usa una versión actual de Chrome, Edge, Safari o Firefox.",
    registrationCancelled: "La creación de la passkey se canceló o agotó el tiempo. Inténtalo de nuevo y confirma la ventana de seguridad del dispositivo.",
    authenticationCancelled: "La solicitud de passkey se canceló o agotó el tiempo. Inténtalo de nuevo y confirma la ventana de seguridad del dispositivo.",
    signupFailed: "No hemos podido iniciar la creación de la cuenta.",
    verifyEmailFailed: "No hemos podido verificar el email.",
    loginFailed: "No hemos podido iniciar sesión.",
    recoveryFailed: "No hemos podido recuperar la cuenta.",
    errorTitle: "No hemos podido completar este paso",
    retryHint: "No se ha cambiado nada. Puedes volver a intentarlo con seguridad.",
    statusTitle: "Revisa tu correo",
    legacyKicker: "LÍMITE DE IDENTIDAD",
    legacyTitle: "Acceso seguro",
    legacyBody: "Inicia sesión para resolver tu organización en el servidor y abrir tu InvestigationContext persistente.",
    legacyPassword: "Contraseña",
    legacySubmit: "Entrar",
    legacySubmitting: "Verificando…",
    legacyFooter: "El navegador no puede declarar ni cambiar la organización.",
  },
  fr: {
    workspaceLabel: "Espace de travail privé",
    pageFooter: "Opérations d’opportunité gouvernées par les preuves",
    eyebrow: "INTELLIGENCE DES OPPORTUNITÉS B2G",
    heroLine1: "Transformez les signaux publics en",
    heroLine2: "décisions défendables.",
    heroBody: "AXIGNAL relie les sources officielles, les preuves gouvernées et le travail nécessaire à votre équipe pour faire avancer chaque opportunité.",
    trustItems: ["Accès résistant au phishing", "Organisation résolue côté serveur", "Traçabilité complète des preuves"],
    pilotLabel: "Pilote privé contrôlé",
    cardKicker: "ACCÈS SÉCURISÉ",
    cardTitle: "Bienvenue dans AXIGNAL",
    cardBody: "Utilisez votre passkey pour accéder à l’espace de travail. Aucun mot de passe n’est stocké ni envoyé.",
    tabs: { login: "Se connecter", signup: "Créer un compte", recovery: "Récupérer" },
    loginButton: "Continuer avec une passkey",
    loginBusy: "En attente de votre passkey…",
    loginHint: "Votre appareil ouvrira sa fenêtre sécurisée de passkey.",
    signupEmail: "E-mail professionnel",
    emailPlaceholder: "nom@entreprise.com",
    continue: "Continuer",
    sending: "Envoi…",
    recoveryEmail: "E-mail du compte",
    recoveryCode: "Code de récupération",
    recoveryPlaceholder: "Saisissez un code inutilisé",
    createPasskey: "Créer une nouvelle passkey",
    verifying: "Vérification…",
    securityCheck: "Contrôle de sécurité adaptatif",
    statusEmailSent: "Si l’adresse peut être utilisée, vous recevrez un lien de vérification.",
    emailVerifiedStepUp: "E-mail vérifié. L’activation de l’essai nécessite un contrôle supplémentaire.",
    emailVerified: "E-mail vérifié. Créez une passkey pour terminer.",
    saveCodesKicker: "RÉCUPÉRATION DU COMPTE",
    saveCodesTitle: "Enregistrez vos codes de récupération",
    saveCodesBody: "Chaque code est à usage unique. AXIGNAL ne les affichera plus.",
    codesSaved: "J’ai enregistré les codes",
    footer: "L’e-mail vérifie l’adresse. La passkey vous authentifie. Un nouveau compte ne donne pas droit à un autre essai.",
    testVerify: "Vérifier l’e-mail de test et créer une passkey",
    completeSecurity: "Effectuez le contrôle de sécurité avant de continuer.",
    browserUnsupported: "Ce navigateur ne prend pas en charge les passkeys. Utilisez une version récente de Chrome, Edge, Safari ou Firefox.",
    registrationCancelled: "La création de la passkey a été annulée ou a expiré. Réessayez et validez la demande de sécurité sur votre appareil.",
    authenticationCancelled: "La demande de passkey a été annulée ou a expiré. Réessayez et validez la demande de sécurité sur votre appareil.",
    signupFailed: "Impossible de démarrer la création du compte.",
    verifyEmailFailed: "Impossible de vérifier l’adresse e-mail.",
    loginFailed: "Impossible de vous connecter.",
    recoveryFailed: "Impossible de récupérer le compte.",
    errorTitle: "Cette étape n’a pas pu être terminée",
    retryHint: "Aucune modification n’a été effectuée. Vous pouvez réessayer en toute sécurité.",
    statusTitle: "Consultez votre boîte de réception",
    legacyKicker: "PÉRIMÈTRE D’IDENTITÉ",
    legacyTitle: "Accès sécurisé",
    legacyBody: "Connectez-vous pour résoudre votre organisation côté serveur et ouvrir votre InvestigationContext persistant.",
    legacyPassword: "Mot de passe",
    legacySubmit: "Se connecter",
    legacySubmitting: "Vérification…",
    legacyFooter: "Le navigateur ne peut ni déclarer ni modifier l’organisation.",
  },
  de: {
    workspaceLabel: "Privater Arbeitsbereich",
    pageFooter: "Evidenzgesteuerte Opportunity Operations",
    eyebrow: "B2G-OPPORTUNITY-INTELLIGENCE",
    heroLine1: "Machen Sie aus öffentlichen Signalen",
    heroLine2: "belastbare Entscheidungen.",
    heroBody: "AXIGNAL verbindet offizielle Quellen, gesteuerte Evidenz und die Arbeit, die Ihr Team benötigt, um Chancen voranzubringen.",
    trustItems: ["Phishing-resistenter Zugang", "Serverseitig aufgelöste Organisation", "Vollständige Evidenzspur"],
    pilotLabel: "Kontrollierter privater Pilot",
    cardKicker: "SICHERER ZUGANG",
    cardTitle: "Willkommen bei AXIGNAL",
    cardBody: "Verwenden Sie Ihren Passkey, um den Arbeitsbereich zu öffnen. Es wird kein Passwort gespeichert oder übertragen.",
    tabs: { login: "Anmelden", signup: "Konto erstellen", recovery: "Wiederherstellen" },
    loginButton: "Mit Passkey fortfahren",
    loginBusy: "Passkey wird erwartet…",
    loginHint: "Ihr Gerät öffnet den sicheren Passkey-Dialog.",
    signupEmail: "Geschäftliche E-Mail",
    emailPlaceholder: "name@unternehmen.de",
    continue: "Fortfahren",
    sending: "Wird gesendet…",
    recoveryEmail: "Konto-E-Mail",
    recoveryCode: "Wiederherstellungscode",
    recoveryPlaceholder: "Ungenutzten Code eingeben",
    createPasskey: "Neuen Passkey erstellen",
    verifying: "Wird geprüft…",
    securityCheck: "Adaptive Sicherheitsprüfung",
    statusEmailSent: "Wenn die Adresse verwendet werden kann, erhalten Sie einen Bestätigungslink.",
    emailVerifiedStepUp: "E-Mail bestätigt. Für die Aktivierung des Tests ist eine weitere Prüfung erforderlich.",
    emailVerified: "E-Mail bestätigt. Erstellen Sie zum Abschluss einen Passkey.",
    saveCodesKicker: "KONTOWIEDERHERSTELLUNG",
    saveCodesTitle: "Wiederherstellungscodes speichern",
    saveCodesBody: "Jeder Code kann einmal verwendet werden. AXIGNAL zeigt diese Codes nicht erneut an.",
    codesSaved: "Codes wurden gespeichert",
    footer: "Die E-Mail bestätigt die Adresse. Der Passkey authentifiziert Sie. Ein neues Konto gewährt keinen weiteren Test.",
    testVerify: "Test-E-Mail bestätigen und Passkey erstellen",
    completeSecurity: "Schließen Sie die Sicherheitsprüfung ab, bevor Sie fortfahren.",
    browserUnsupported: "Dieser Browser unterstützt keine Passkeys. Verwenden Sie eine aktuelle Version von Chrome, Edge, Safari oder Firefox.",
    registrationCancelled: "Die Passkey-Erstellung wurde abgebrochen oder ist abgelaufen. Versuchen Sie es erneut und bestätigen Sie die Sicherheitsabfrage auf Ihrem Gerät.",
    authenticationCancelled: "Die Passkey-Anfrage wurde abgebrochen oder ist abgelaufen. Versuchen Sie es erneut und bestätigen Sie die Sicherheitsabfrage auf Ihrem Gerät.",
    signupFailed: "Die Kontoerstellung konnte nicht gestartet werden.",
    verifyEmailFailed: "Die E-Mail-Adresse konnte nicht bestätigt werden.",
    loginFailed: "Die Anmeldung war nicht möglich.",
    recoveryFailed: "Das Konto konnte nicht wiederhergestellt werden.",
    errorTitle: "Dieser Schritt konnte nicht abgeschlossen werden",
    retryHint: "Es wurde nichts geändert. Sie können es sicher erneut versuchen.",
    statusTitle: "Posteingang prüfen",
    legacyKicker: "IDENTITÄTSGRENZE",
    legacyTitle: "Sicherer Zugang",
    legacyBody: "Melden Sie sich an, um Ihre Organisation serverseitig aufzulösen und Ihren persistenten InvestigationContext zu öffnen.",
    legacyPassword: "Passwort",
    legacySubmit: "Anmelden",
    legacySubmitting: "Wird geprüft…",
    legacyFooter: "Der Browser kann die Organisation weder festlegen noch ändern.",
  },
  pt: {
    workspaceLabel: "Espaço de trabalho privado",
    pageFooter: "Operações de oportunidades governadas por evidências",
    eyebrow: "INTELIGÊNCIA DE OPORTUNIDADES B2G",
    heroLine1: "Transforme sinais públicos em",
    heroLine2: "decisões defensáveis.",
    heroBody: "A AXIGNAL liga fontes oficiais, evidências governadas e o trabalho de que a sua equipa necessita para fazer avançar cada oportunidade.",
    trustItems: ["Acesso resistente a phishing", "Organização resolvida no servidor", "Rastreabilidade completa das evidências"],
    pilotLabel: "Piloto privado controlado",
    cardKicker: "ACESSO SEGURO",
    cardTitle: "Bem-vindo à AXIGNAL",
    cardBody: "Utilize a sua passkey para entrar. Nenhuma palavra-passe é armazenada ou enviada.",
    tabs: { login: "Entrar", signup: "Criar conta", recovery: "Recuperar" },
    loginButton: "Continuar com passkey",
    loginBusy: "A aguardar a passkey…",
    loginHint: "O seu dispositivo abrirá a janela segura da passkey.",
    signupEmail: "E-mail profissional",
    emailPlaceholder: "nome@empresa.pt",
    continue: "Continuar",
    sending: "A enviar…",
    recoveryEmail: "E-mail da conta",
    recoveryCode: "Código de recuperação",
    recoveryPlaceholder: "Introduza um código não utilizado",
    createPasskey: "Criar uma nova passkey",
    verifying: "A verificar…",
    securityCheck: "Verificação de segurança adaptativa",
    statusEmailSent: "Se o endereço puder ser utilizado, receberá uma ligação de verificação.",
    emailVerifiedStepUp: "E-mail verificado. A ativação do teste requer uma verificação adicional.",
    emailVerified: "E-mail verificado. Crie uma passkey para terminar.",
    saveCodesKicker: "RECUPERAÇÃO DA CONTA",
    saveCodesTitle: "Guarde os códigos de recuperação",
    saveCodesBody: "Cada código só pode ser utilizado uma vez. A AXIGNAL não voltará a mostrá-los.",
    codesSaved: "Guardei os códigos",
    footer: "O e-mail verifica o endereço. A passkey autentica-o. Criar outra conta não concede outro teste.",
    testVerify: "Verificar e-mail de teste e criar passkey",
    completeSecurity: "Conclua a verificação de segurança antes de continuar.",
    browserUnsupported: "Este navegador não suporta passkeys. Utilize uma versão atual do Chrome, Edge, Safari ou Firefox.",
    registrationCancelled: "A criação da passkey foi cancelada ou expirou. Tente novamente e confirme o pedido de segurança no seu dispositivo.",
    authenticationCancelled: "O pedido de passkey foi cancelado ou expirou. Tente novamente e confirme o pedido de segurança no seu dispositivo.",
    signupFailed: "Não foi possível iniciar a criação da conta.",
    verifyEmailFailed: "Não foi possível verificar o e-mail.",
    loginFailed: "Não foi possível iniciar sessão.",
    recoveryFailed: "Não foi possível recuperar a conta.",
    errorTitle: "Não foi possível concluir este passo",
    retryHint: "Nada foi alterado. Pode tentar novamente em segurança.",
    statusTitle: "Consulte o seu e-mail",
    legacyKicker: "LIMITE DE IDENTIDADE",
    legacyTitle: "Acesso seguro",
    legacyBody: "Inicie sessão para resolver a sua organização no servidor e abrir o InvestigationContext persistente.",
    legacyPassword: "Palavra-passe",
    legacySubmit: "Entrar",
    legacySubmitting: "A verificar…",
    legacyFooter: "O navegador não pode declarar nem alterar a organização.",
  },
  it: {
    workspaceLabel: "Area di lavoro privata",
    pageFooter: "Operazioni sulle opportunità governate dalle evidenze",
    eyebrow: "INTELLIGENCE DELLE OPPORTUNITÀ B2G",
    heroLine1: "Trasforma i segnali pubblici in",
    heroLine2: "decisioni difendibili.",
    heroBody: "AXIGNAL collega fonti ufficiali, evidenze governate e il lavoro necessario al tuo team per far avanzare ogni opportunità.",
    trustItems: ["Accesso resistente al phishing", "Organizzazione risolta sul server", "Tracciabilità completa delle evidenze"],
    pilotLabel: "Pilota privato controllato",
    cardKicker: "ACCESSO SICURO",
    cardTitle: "Benvenuto in AXIGNAL",
    cardBody: "Usa la tua passkey per entrare nell’area di lavoro. Nessuna password viene memorizzata o inviata.",
    tabs: { login: "Accedi", signup: "Crea account", recovery: "Recupera" },
    loginButton: "Continua con passkey",
    loginBusy: "In attesa della passkey…",
    loginHint: "Il dispositivo aprirà la finestra sicura della passkey.",
    signupEmail: "E-mail di lavoro",
    emailPlaceholder: "nome@azienda.it",
    continue: "Continua",
    sending: "Invio…",
    recoveryEmail: "E-mail dell’account",
    recoveryCode: "Codice di recupero",
    recoveryPlaceholder: "Inserisci un codice non utilizzato",
    createPasskey: "Crea una nuova passkey",
    verifying: "Verifica…",
    securityCheck: "Controllo di sicurezza adattivo",
    statusEmailSent: "Se l’indirizzo può essere utilizzato, riceverai un link di verifica.",
    emailVerifiedStepUp: "E-mail verificata. L’attivazione della prova richiede un controllo aggiuntivo.",
    emailVerified: "E-mail verificata. Crea una passkey per completare.",
    saveCodesKicker: "RECUPERO DELL’ACCOUNT",
    saveCodesTitle: "Salva i codici di recupero",
    saveCodesBody: "Ogni codice può essere usato una sola volta. AXIGNAL non li mostrerà di nuovo.",
    codesSaved: "Ho salvato i codici",
    footer: "L’e-mail verifica l’indirizzo. La passkey ti autentica. Un nuovo account non concede un’altra prova.",
    testVerify: "Verifica l’e-mail di test e crea la passkey",
    completeSecurity: "Completa il controllo di sicurezza prima di continuare.",
    browserUnsupported: "Questo browser non supporta le passkey. Usa una versione aggiornata di Chrome, Edge, Safari o Firefox.",
    registrationCancelled: "La creazione della passkey è stata annullata o è scaduta. Riprova e conferma la richiesta di sicurezza sul dispositivo.",
    authenticationCancelled: "La richiesta della passkey è stata annullata o è scaduta. Riprova e conferma la richiesta di sicurezza sul dispositivo.",
    signupFailed: "Non è stato possibile avviare la creazione dell’account.",
    verifyEmailFailed: "Non è stato possibile verificare l’e-mail.",
    loginFailed: "Non è stato possibile accedere.",
    recoveryFailed: "Non è stato possibile recuperare l’account.",
    errorTitle: "Non è stato possibile completare questo passaggio",
    retryHint: "Non è stato modificato nulla. Puoi riprovare in sicurezza.",
    statusTitle: "Controlla la posta",
    legacyKicker: "CONFINE DI IDENTITÀ",
    legacyTitle: "Accesso sicuro",
    legacyBody: "Accedi per risolvere la tua organizzazione sul server e aprire il tuo InvestigationContext persistente.",
    legacyPassword: "Password",
    legacySubmit: "Accedi",
    legacySubmitting: "Verifica…",
    legacyFooter: "Il browser non può dichiarare o modificare l’organizzazione.",
  },
};

function rawMessage(cause: unknown): string {
  if (cause instanceof Error) return cause.message;
  return typeof cause === "string" ? cause : "";
}

export function humanizeAuthError(
  locale: ShellLocale,
  cause: unknown,
  fallback: keyof Pick<AuthCopy, "signupFailed" | "verifyEmailFailed" | "loginFailed" | "recoveryFailed">,
  operation: "registration" | "authentication" | "generic" = "generic",
): string {
  const copy = authCopy[locale];
  const message = rawMessage(cause);
  const name = cause instanceof DOMException ? cause.name : cause instanceof Error ? cause.name : "";

  if (
    name === "NotAllowedError" ||
    name === "AbortError" ||
    /timed out|not allowed|w3\.org\/TR\/webauthn/i.test(message)
  ) {
    return operation === "registration"
      ? copy.registrationCancelled
      : copy.authenticationCancelled;
  }

  if (name === "NotSupportedError" || /does not support passkeys|no admite passkeys|PublicKeyCredential/i.test(message)) {
    return copy.browserUnsupported;
  }

  if (/security check|comprobación de seguridad|bot_token/i.test(message)) {
    return copy.completeSecurity;
  }

  if (!message || /Identity operation failed/i.test(message)) {
    return copy[fallback];
  }

  return message;
}
