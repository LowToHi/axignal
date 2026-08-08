import type { Metadata } from "next";
import { cookies } from "next/headers";
import Script from "next/script";
import { AxentGlobalAssistant } from "@/components/axent/axent-global";
import "@axignal/design-tokens/tokens.css";
import "./globals.css";
import "./context.css";
import "./auth.css";
import "./human-review.css";
import "./alert-confirm.css";
import "./reduced-motion.css";
import "./accessibility.css";

export const metadata: Metadata = {
  title: "AXIGNAL — Global Opportunity Intelligence",
  description: "Authenticated investigation shell for AXIGNAL.",
  icons: {
    icon: "/icon.svg",
  },
};

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const cookieStore = await cookies();
  const storedTheme = cookieStore.get("axignal_theme")?.value;
  const storedLocale = cookieStore.get("axignal_locale")?.value;
  const theme = storedTheme === "light" ? "light" : "dark";
  const locale = ["en", "es", "fr", "de", "pt", "it"].includes(
    storedLocale ?? "",
  )
    ? storedLocale!
    : "en";
  return (
    <html
      lang={locale}
      data-theme={theme}
      style={{ colorScheme: theme }}
      suppressHydrationWarning
    >
      <body>
        <Script src="/theme-bootstrap.js" strategy="beforeInteractive" />
        {children}
        <AxentGlobalAssistant />
      </body>
    </html>
  );
}
