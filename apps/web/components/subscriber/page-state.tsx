import { AlertTriangle, CircleOff, LoaderCircle, LockKeyhole, RefreshCw, WifiOff } from "lucide-react";

import styles from "./workspace-content.module.css";

export type RouteState = "loading" | "empty" | "ready" | "partial" | "stale" | "restricted" | "read_only" | "source_unavailable" | "recoverable_error" | "terminal_error";

export function PageState({ state, title, detail, onRetry }: { state: Exclude<RouteState, "ready">; title?: string; detail?: string; onRetry?: () => void }) {
  const content = {
    loading: [LoaderCircle, "Loading workspace", "Your current work is safe. AXIGNAL is resolving the server-authoritative context."],
    empty: [CircleOff, "Nothing here yet", "Create or save an item to begin. No data has been inferred from an empty result."],
    partial: [AlertTriangle, "Some information is unavailable", "Available evidence is shown. Missing records are marked unknown and do not contribute to readiness."],
    stale: [RefreshCw, "A newer source version exists", "Your work is preserved. Review the amendment impact before relying on prior approvals."],
    restricted: [LockKeyhole, "Access restricted", "Your role or entitlement does not grant this capability. Ask an organisation administrator for access."],
    read_only: [LockKeyhole, "Read-only access", "You can inspect evidence and history, but your current role cannot change this record."],
    source_unavailable: [WifiOff, "Source unavailable", "AXIGNAL did not substitute fixture data. Existing persisted work remains available where safe."],
    recoverable_error: [AlertTriangle, "This view could not be reconciled", "No success was recorded. Retry without losing the last persisted revision."],
    terminal_error: [CircleOff, "Workspace cannot be opened", "Recovery requires an administrator or service owner. The failed operation was not applied."]
  } as const;
  const [Icon, fallbackTitle, fallbackDetail] = content[state];
  return <section className={styles.pageState} role={state === "loading" ? "status" : "alert"} aria-live="polite"><Icon className={state === "loading" ? styles.spin : undefined} size={24} /><div><h1>{title ?? fallbackTitle}</h1><p>{detail ?? fallbackDetail}</p>{onRetry && <button type="button" onClick={onRetry}><RefreshCw size={15} /> Retry</button>}</div></section>;
}
