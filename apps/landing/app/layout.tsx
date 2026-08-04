import type { Metadata, Viewport } from "next";
import { headers } from "next/headers";
import "@axignal/design-tokens/tokens.css";
import "./globals.css";

import { htmlLanguages, isLocale } from "@/lib/i18n";

export const metadata: Metadata = {
  metadataBase: new URL("https://axignal.com"),
  title: {
    default: "AXIGNAL — Public Procurement Intelligence",
    template: "%s · AXIGNAL"
  },
  description:
    "Evidence-governed intelligence for organisations that sell to government.",
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
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
