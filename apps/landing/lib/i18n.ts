import de from "@/messages/de.json";
import en from "@/messages/en.json";
import es from "@/messages/es.json";
import fr from "@/messages/fr.json";
import it from "@/messages/it.json";
import pt from "@/messages/pt.json";
import { canonicalCommercialCopy } from "./canonical-commercial-contract";

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
  const base = dictionaries[locale];
  const canonical = canonicalCommercialCopy[locale];
  const acts = base.acts.map((act, index) => {
    if (index === 2) return { ...act, ...canonical.sourceAct };
    if (index === 7) return { ...act, ...canonical.trialAct };
    return act;
  });

  return {
    ...base,
    meta: canonical.meta,
    nav: { ...base.nav, cta: canonical.navCta },
    hero: { ...base.hero, ...canonical.hero },
    storyIntro: { ...base.storyIntro, body: canonical.storyIntroBody },
    acts,
    navigator: { ...base.navigator, response: canonical.navigatorResponse },
    globe: { ...base.globe, activeRule: canonical.globeActiveRule },
    pricing: { ...base.pricing, ...canonical.pricing },
    faq: { ...base.faq, items: canonical.faqItems },
    form: { ...base.form, ...canonical.form }
  } as LandingMessages;
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
