import type { Metadata, Viewport } from "next";
import { headers } from "next/headers";
import "@axignal/design-tokens/tokens.css";
import "./globals.css";
import "./contract-overrides.css";

import { htmlLanguages, isLocale } from "@/lib/i18n";

export const metadata: Metadata = {
  metadataBase: new URL("https://axignal.com"),
  title: {
    default: "AXIGNAL — B2G Opportunity Intelligence",
    template: "%s · AXIGNAL"
  },
  description:
    "Find, qualify and investigate public contracts with traceable evidence and human authority.",
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "32x32" },
      { url: "/favicon.svg", type: "image/svg+xml" }
    ],
    apple: [{ url: "/favicon.svg", type: "image/svg+xml" }]
  },
  manifest: "/manifest.webmanifest"
};

export const viewport: Viewport = {
  colorScheme: "dark",
  themeColor: "#030d12",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover"
};

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const requestHeaders = await headers();
  const requestedLocale = requestHeaders.get("x-axignal-locale") ?? "en";
  const locale = isLocale(requestedLocale) ? requestedLocale : "en";

  return (
    <html lang={htmlLanguages[locale]} data-theme="dark">
      <body>{children}</body>
    </html>
  );
}
