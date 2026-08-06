import type { Metadata } from "next";
import { cookies } from "next/headers";
import "@axignal/design-tokens/tokens.css";
import "./globals.css";
import "./context.css";
import "./auth.css";
import "./human-review.css";
import "./alert-confirm.css";

export const metadata: Metadata = {
  title: "AXIGNAL — Global Opportunity Intelligence",
  description: "Authenticated investigation shell for AXIGNAL."
};

export default async function RootLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  const cookieStore = await cookies();
  const storedTheme = cookieStore.get("axignal_theme")?.value;
  const storedLocale = cookieStore.get("axignal_locale")?.value;
  const theme = storedTheme === "light" ? "light" : "dark";
  const locale = ["en", "es", "fr", "de", "pt", "it"].includes(storedLocale ?? "") ? storedLocale! : "en";
  return (
    <html lang={locale} data-theme={theme} suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
