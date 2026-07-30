import type { Metadata } from "next";
import { getMessages, languageAlternates, localePath, type Locale } from "./i18n";

const openGraphLocales: Record<Locale, string> = {
  en: "en_US",
  es: "es_ES",
  fr: "fr_FR",
  pt: "pt_PT",
  de: "de_DE",
  it: "it_IT"
};

export function buildLandingMetadata(locale: Locale): Metadata {
  const messages = getMessages(locale);
  const path = localePath(locale);

  return {
    title: messages.meta.title,
    description: messages.meta.description,
    applicationName: "AXIGNAL",
    category: "Public Procurement Intelligence",
    alternates: {
      canonical: path,
      languages: languageAlternates
    },
    openGraph: {
      title: messages.meta.title,
      description: messages.meta.description,
      url: path,
      type: "website",
      siteName: "AXIGNAL",
      locale: openGraphLocales[locale],
      images: [
        {
          url: "/opengraph-image.jpg",
          width: 1200,
          height: 630,
          alt: "AXIGNAL — evidence-governed public procurement intelligence"
        }
      ]
    },
    twitter: {
      card: "summary_large_image",
      title: messages.meta.title,
      description: messages.meta.description,
      images: ["/twitter-image.jpg"]
    },
    robots: {
      index: true,
      follow: true,
      googleBot: {
        index: true,
        follow: true,
        "max-image-preview": "large",
        "max-snippet": -1
      }
    }
  };
}

export function buildStructuredData(locale: Locale) {
  const messages = getMessages(locale);
  const url = `https://axignal.com${localePath(locale) === "/" ? "" : localePath(locale)}`;

  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Organization",
        "@id": "https://axignal.com/#organization",
        name: "AXIGNAL",
        url: "https://axignal.com",
        logo: "https://axignal.com/brand/axignal-logo.svg",
        description: messages.hero.descriptor
      },
      {
        "@type": "SoftwareApplication",
        "@id": `${url}#software`,
        name: "AXIGNAL",
        applicationCategory: "BusinessApplication",
        operatingSystem: "Web",
        inLanguage: locale,
        url,
        description: messages.meta.description,
        publisher: { "@id": "https://axignal.com/#organization" }
      },
      {
        "@type": "FAQPage",
        "@id": `${url}#faq`,
        mainEntity: messages.faq.items.map(([question, answer]) => ({
          "@type": "Question",
          name: question,
          acceptedAnswer: { "@type": "Answer", text: answer }
        }))
      }
    ]
  };
}
