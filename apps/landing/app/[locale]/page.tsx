import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { LandingExperience } from "@/components/landing-experience";
import { getMessages, isLocale, locales } from "@/lib/i18n";
import { buildLandingMetadata, buildStructuredData } from "@/lib/metadata";

type LocalePageProps = {
  params: Promise<{ locale: string }>;
};

export function generateStaticParams() {
  return locales.filter((locale) => locale !== "en").map((locale) => ({ locale }));
}

export async function generateMetadata({ params }: LocalePageProps): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale) || locale === "en") return {};
  return buildLandingMetadata(locale);
}

export default async function LocalizedLandingPage({ params }: LocalePageProps) {
  const { locale } = await params;
  if (!isLocale(locale) || locale === "en") notFound();
  const structuredData = buildStructuredData(locale);

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData).replace(/</g, "\\u003c") }}
      />
      <LandingExperience locale={locale} messages={getMessages(locale)} />
    </>
  );
}
