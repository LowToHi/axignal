import de from "@/messages/de.json";
import en from "@/messages/en.json";
import es from "@/messages/es.json";
import fr from "@/messages/fr.json";
import it from "@/messages/it.json";
import pt from "@/messages/pt.json";

export const locales = ["en", "es", "fr", "pt", "de", "it"] as const;
export type Locale = (typeof locales)[number];
export type LandingMessages = typeof en;

const dictionaries: Record<Locale, LandingMessages> = {
  en,
  es: es as LandingMessages,
  fr: fr as LandingMessages,
  pt: pt as LandingMessages,
  de: de as LandingMessages,
  it: it as LandingMessages
};

export const localeLabels: Record<Locale, string> = {
  en: "English",
  es: "Español",
  fr: "Français",
  pt: "Português",
  de: "Deutsch",
  it: "Italiano"
};

export const htmlLanguages: Record<Locale, string> = {
  en: "en",
  es: "es",
  fr: "fr",
  pt: "pt",
  de: "de",
  it: "it"
};

export function isLocale(value: string): value is Locale {
  return (locales as readonly string[]).includes(value);
}

export function getMessages(locale: Locale): LandingMessages {
  return dictionaries[locale];
}

export function localePath(locale: Locale, fragment = "") {
  const base = locale === "en" ? "/" : `/${locale}`;
  return fragment ? `${base === "/" ? "" : base}${fragment}` : base;
}

export const languageAlternates = {
  "x-default": "https://axignal.com/",
  en: "https://axignal.com/",
  es: "https://axignal.com/es",
  fr: "https://axignal.com/fr",
  pt: "https://axignal.com/pt",
  de: "https://axignal.com/de",
  it: "https://axignal.com/it"
} as const;
