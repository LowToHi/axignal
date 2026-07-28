import type { Metadata } from "next";
import "@axignal/design-tokens/tokens.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "AXIGNAL — Discover global opportunities before they become obvious",
  description: "Global Opportunity Intelligence through Globe, Graph, Timeline, claims and verifiable evidence."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="dark">
      <body>{children}</body>
    </html>
  );
}
