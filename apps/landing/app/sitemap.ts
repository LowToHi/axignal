import type { MetadataRoute } from "next";
import { localePath, locales } from "@/lib/i18n";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return locales.map((locale) => ({
    url: `https://axignal.com${localePath(locale) === "/" ? "" : localePath(locale)}`,
    lastModified: now,
    changeFrequency: "weekly",
    priority: locale === "en" ? 1 : 0.9,
    alternates: {
      languages: {
        en: "https://axignal.com",
        es: "https://axignal.com/es",
        fr: "https://axignal.com/fr",
        pt: "https://axignal.com/pt",
        de: "https://axignal.com/de",
        it: "https://axignal.com/it"
      }
    }
  }));
}
