import { expect, test } from "@playwright/test";

const locales = {
  en: {
    language: "Language",
    openNavigation: "Open navigation",
    investigations: "Investigations",
    workspaces: "Workspaces",
    searchCommand: "Search or enter a command",
    navigate: "Navigate",
    accountMenu: /Account menu for/,
    accountDialog: "Account menu",
    accountSettings: "Account settings",
    signOut: "Sign out and clear local AXENT history",
  },
  es: {
    language: "Idioma",
    openNavigation: "Abrir navegación",
    investigations: "Investigaciones",
    workspaces: "Espacios de trabajo",
    searchCommand: "Buscar o introducir un comando",
    navigate: "Navegar",
    accountMenu: /Menú de cuenta de/,
    accountDialog: "Menú de cuenta",
    accountSettings: "Configuración de la cuenta",
    signOut: "Cerrar sesión y borrar el historial local de AXENT",
  },
  fr: {
    language: "Langue",
    openNavigation: "Ouvrir la navigation",
    investigations: "Investigations",
    workspaces: "Espaces de travail",
    searchCommand: "Rechercher ou saisir une commande",
    navigate: "Naviguer",
    accountMenu: /Menu du compte de/,
    accountDialog: "Menu du compte",
    accountSettings: "Paramètres du compte",
    signOut: "Se déconnecter et effacer l’historique AXENT local",
  },
  de: {
    language: "Sprache",
    openNavigation: "Navigation öffnen",
    investigations: "Untersuchungen",
    workspaces: "Arbeitsbereiche",
    searchCommand: "Suchen oder Befehl eingeben",
    navigate: "Navigieren",
    accountMenu: /Kontomenü für/,
    accountDialog: "Kontomenü",
    accountSettings: "Kontoeinstellungen",
    signOut: "Abmelden und lokalen AXENT-Verlauf löschen",
  },
  pt: {
    language: "Idioma",
    openNavigation: "Abrir navegação",
    investigations: "Investigações",
    workspaces: "Espaços de trabalho",
    searchCommand: "Pesquisar ou introduzir um comando",
    navigate: "Navegar",
    accountMenu: /Menu da conta de/,
    accountDialog: "Menu da conta",
    accountSettings: "Definições da conta",
    signOut: "Terminar sessão e apagar o histórico local do AXENT",
  },
  it: {
    language: "Lingua",
    openNavigation: "Apri navigazione",
    investigations: "Indagini",
    workspaces: "Spazi di lavoro",
    searchCommand: "Cerca o inserisci un comando",
    navigate: "Naviga",
    accountMenu: /Menu account di/,
    accountDialog: "Menu account",
    accountSettings: "Impostazioni account",
    signOut: "Disconnetti e cancella la cronologia AXENT locale",
  },
} as const;

test.describe.configure({ mode: "serial" });

test.afterEach(async ({ page }) => {
  await page.goto("/axent");
  const language = page.locator("header select");
  await language.selectOption("en");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(language).toHaveValue("en");
});

test("renders equivalent Shell routes and controls in all six locales", async ({
  page,
}) => {
  await page.goto("/axent");
  const language = page.locator("header select");

  for (const [locale, copy] of Object.entries(locales)) {
    await language.selectOption(locale);
    await expect(page.locator("html")).toHaveAttribute("lang", locale);
    await expect(language).toHaveAttribute("aria-label", copy.language);

    const compact = (page.viewportSize()?.width ?? 1280) <= 900;
    if (compact) {
      await page.getByRole("button", { name: copy.openNavigation, exact: true }).click();
    }

    await expect(
      page.getByRole("link", { name: copy.investigations, exact: true }),
    ).toHaveAttribute("href", "/investigations");
    await expect(
      page.getByRole("link", { name: copy.workspaces, exact: true }).first(),
    ).toHaveAttribute("href", "/workspaces");

    if (compact) await page.keyboard.press("Escape");

    await page.keyboard.press("Control+K");
    const commandDialog = page.getByRole("dialog", { name: copy.navigate });
    await expect(commandDialog).toBeVisible();
    await expect(
      page.getByRole("textbox", { name: copy.searchCommand }),
    ).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(commandDialog).toBeHidden();

    await page.getByRole("button", { name: copy.accountMenu }).click();
    const account = page.getByRole("menu", { name: copy.accountDialog });
    await expect(account).toBeVisible();
    await expect(
      account.getByRole("menuitem", { name: copy.accountSettings }),
    ).toHaveAttribute("href", "/settings");
    await expect(
      account.getByRole("menuitem", { name: copy.signOut }),
    ).toBeVisible();
    await page.keyboard.press("Escape");
  }
});

test("persists the selected locale across a full navigation and keeps route authority", async ({
  page,
}) => {
  await page.goto("/axent");
  await page.locator("header select").selectOption("es");
  await expect(page.locator("html")).toHaveAttribute("lang", "es");

  await page.goto("/investigations");
  await expect(page.locator("html")).toHaveAttribute("lang", "es");
  await expect(
    page.getByRole("link", { name: "Espacios de trabajo", exact: true }).first(),
  ).toHaveAttribute("href", "/workspaces");
  await expect(page.locator("header select")).toHaveValue("es");
});
