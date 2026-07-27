import type { Metadata } from "next";
import "@axignal/design-tokens/tokens.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "AXIGNAL — Global Opportunity Intelligence",
  description: "Prototype investigation shell for AXIGNAL."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es" data-theme="dark">
      <body>{children}</body>
    </html>
  );
}
