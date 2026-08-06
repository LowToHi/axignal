"use client";

import type { Locale } from "./i18n";

export type LandingEventName =
  | "landing_view"
  | "cta_click"
  | "demo_chapter_view"
  | "globe_layer_change"
  | "globe_source_select"
  | "calculator_update"
  | "pricing_plan_select"
  | "intake_step_complete"
  | "intake_submit_result"
  | "language_change";

type SafeProperties = {
  locale?: Locale;
  cta_origin?: "header" | "hero" | "pricing" | "footer";
  chapter?: number;
  layer?: string;
  source_state?: string;
  plan?: string;
  result?: "accepted" | "rejected" | "unavailable" | "rate_limited";
  landing_variant?: "b2g_v1";
};

const allowedKeys = new Set<keyof SafeProperties>([
  "locale",
  "cta_origin",
  "chapter",
  "layer",
  "source_state",
  "plan",
  "result",
  "landing_variant"
]);

export function trackLandingEvent(name: LandingEventName, properties: SafeProperties = {}) {
  if (typeof window === "undefined") return;

  const safeProperties = Object.fromEntries(
    Object.entries(properties).filter(([key, value]) => allowedKeys.has(key as keyof SafeProperties) && value != null)
  );
  const detail = { name, properties: safeProperties, schema: "axignal.landing-event.v1" };

  window.dispatchEvent(new CustomEvent("axignal:analytics", { detail }));
  const provider = (window as Window & { axignalAnalytics?: { track: (event: string, values: object) => void } })
    .axignalAnalytics;
  provider?.track(name, safeProperties);
}
