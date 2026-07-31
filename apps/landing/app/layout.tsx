import type { Metadata, Viewport } from "next";

import "@axignal/design-tokens/tokens.css";
import "./globals.css";
import "./responsive-polish.css";
import "./message-copy.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://axignal.com"),
  title: "AXIGNAL — Evidence-backed research for high-stakes decisions",
  description:
    "Turn scattered sources into a decision your team can verify. AXIGNAL keeps questions, evidence, uncertainty and review in one governed research workspace.",
  applicationName: "AXIGNAL",
  alternates: { canonical: "/" },
  openGraph: {
    title: "AXIGNAL — Turn scattered sources into a decision your team can verify",
    description:
      "Evidence-backed research for strategy, investment and intelligence teams, with the evidence trail kept intact.",
    type: "website",
    siteName: "AXIGNAL"
  },
  robots: {
    index: false,
    follow: false,
    nocache: true,
    googleBot: {
      index: false,
      follow: false,
      noimageindex: true
    }
  }
};

export const viewport: Viewport = {
  colorScheme: "dark",
  themeColor: "#050a0d"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="dark">
      <body>{children}</body>
    </html>
  );
}
