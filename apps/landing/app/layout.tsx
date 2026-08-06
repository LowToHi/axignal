import type { Metadata, Viewport } from "next";

import "@axignal/design-tokens/tokens.css";
import "./globals.css";
import "./responsive-polish.css";
import "./message-copy.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://axignal.com"),
  title: "AXIGNAL — Business-to-Government (B2G) Opportunity Intelligence",
  description:
    "Find and qualify public contracts and global tenders. AXIGNAL connects procurement notices, government buyers, awards, companies and evidence for disciplined B2G decisions.",
  applicationName: "AXIGNAL",
  alternates: { canonical: "/" },
  openGraph: {
    title: "AXIGNAL — Find the public contracts your business is built to pursue",
    description:
      "Business-to-Government opportunity intelligence for discovering, qualifying and investigating public contracts with a traceable evidence trail.",
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
