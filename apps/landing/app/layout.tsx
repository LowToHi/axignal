import type { Metadata, Viewport } from "next";
import "@axignal/design-tokens/tokens.css";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://axignal.com"),
  title: "AXIGNAL — Global Opportunity Intelligence",
  description:
    "Discover global opportunities through persistent investigations, verifiable evidence, visible contradictions and bounded human authority.",
  applicationName: "AXIGNAL",
  alternates: { canonical: "/" },
  openGraph: {
    title: "AXIGNAL — Global Opportunity Intelligence",
    description: "See what is changing before it becomes obvious.",
    type: "website",
    siteName: "AXIGNAL"
  },
  robots: {
    index: true,
    follow: true
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
