"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import styles from "./billing-bridge.module.css";

type Selection = {
  selection_id: string;
  plan_code: "PROFESSIONAL_MONTHLY" | "TEAM_MONTHLY";
  pending_plan_code: "PROFESSIONAL_MONTHLY" | "TEAM_MONTHLY" | null;
  state: string;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
};

type Entitlement = {
  entitlement_id: string;
  entitlement_kind: "TRIAL" | "PAID_MONTHLY";
  plan_code: string;
  state: "ACTIVE" | "READ_ONLY" | "SUSPENDED" | "CANCELLED";
  expires_at: string | null;
  unlimited_ai_tokens: boolean;
  token_budget_total: number | null;
  token_budget_reserved: number;
  token_budget_consumed: number;
};

type LedgerItem = {
  ledger_entry_id: string;
  occurred_at: string;
  event_type: string;
  plan_code: string | null;
  previous_state: string | null;
  new_state: string | null;
  provider_event_id: string | null;
  payload_digest: string | null;
  operation_actor: "USER" | "PROVIDER" | "SYSTEM";
};

type BillingSummary = {
  provider: "STRIPE" | "DETERMINISTIC_TEST_PROVIDER";
  runtime_enabled: boolean;
  checkout_enabled: boolean;
  lifecycle_enabled: boolean;
  external_stripe_verified: false;
  commercial_payment_evidence: false;
  selection: Selection | null;
  entitlement: Entitlement | null;
  ledger: LedgerItem[];
};

type ApiError = { error?: string; detail?: string | { reason?: string } };

const pendingStates = new Set([
  "SELECTED",
  "CHECKOUT_CREATED",
  "CHECKOUT_COMPLETED",
  "UPGRADE_PENDING",
  "CANCEL_PENDING"
]);

function operationId(prefix: string): string {
  return `op_${prefix}_${crypto.randomUUID().replaceAll("-", "")}`;
}

function planLabel(plan: string | null | undefined): string {
  if (plan === "PROFESSIONAL_MONTHLY") return "Professional";
  if (plan === "TEAM_MONTHLY") return "Team";
  return "Sin plan";
}

function errorMessage(value: ApiError, fallback: string): string {
  if (typeof value.detail === "string") return value.detail;
  if (value.detail && typeof value.detail === "object" && value.detail.reason) {
    return value.detail.reason;
  }
  return value.error ?? fallback;
}

export function BillingBridge() {
  const [open, setOpen] = useState(false);
  const [summary, setSummary] = useState<BillingSummary | null>(null);
  const [confirmedSelection, setConfirmedSelection] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const response = await fetch("/api/billing/summary", { cache: "no-store" });
      const body = (await response.json()) as BillingSummary | ApiError;
      if (!response.ok) throw new Error(errorMessage(body as ApiError, "Billing unavailable."));
      setSummary(body as BillingSummary);
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Billing unavailable.");
    }
  }, []);

  useEffect(() => {
    void load();
    if (window.location.search.includes("billing=success")) setOpen(true);
  }, [load]);

  useEffect(() => {
    const pending = summary?.selection && pendingStates.has(summary.selection.state);
    if (!pending) return;
    const timer = window.setInterval(() => void load(), 1_500);
    return () => window.clearInterval(timer);
  }, [load, summary?.selection]);

  const activePaid =
    summary?.entitlement?.entitlement_kind === "PAID_MONTHLY" &&
    summary.entitlement.state === "ACTIVE";
  const pendingConfirmation =
    summary?.selection?.state === "CHECKOUT_CREATED" ||
    summary?.selection?.state === "CHECKOUT_COMPLETED";
  const canUpgrade =
    activePaid &&
    summary?.selection?.plan_code === "PROFESSIONAL_MONTHLY" &&
    summary.selection.state === "ACTIVE";
  const canCancel = activePaid &&
    ["ACTIVE", "CANCEL_AT_PERIOD_END"].includes(summary?.selection?.state ?? "");
  const recentLedger = useMemo(
    () => [...(summary?.ledger ?? [])].reverse().slice(0, 8),
    [summary?.ledger]
  );

  async function post(path: string, body: object): Promise<Record<string, unknown>> {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(path, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body)
      });
      const payload = (await response.json()) as Record<string, unknown> & ApiError;
      if (!response.ok) throw new Error(errorMessage(payload, "Billing operation failed."));
      await load();
      return payload;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Billing operation failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function startCheckout(planCode: Selection["plan_code"]) {
    if (!confirmedSelection) return;
    const result = await post("/api/billing/checkout", {
      operation_id: operationId("checkout"),
      plan_code: planCode,
      confirm_paid_selection: true
    });
    const url = result.checkout_url;
    if (typeof url !== "string") {
      setError("Checkout URL missing from the server response.");
      return;
    }
    window.location.assign(url);
  }

  async function upgrade() {
    await post("/api/billing/upgrade", {
      operation_id: operationId("upgrade"),
      target_plan_code: "TEAM_MONTHLY",
      billing_effect: "IMMEDIATE_WITHOUT_PRORATION",
      confirm_upgrade: true
    });
  }

  async function cancel(cancelAtPeriodEnd: boolean) {
    await post("/api/billing/cancel", {
      operation_id: operationId(cancelAtPeriodEnd ? "cancel_period" : "cancel_now"),
      cancel_at_period_end: cancelAtPeriodEnd,
      confirm_cancellation: true
    });
  }

  return (
    <>
      <button
        type="button"
        className={styles.launcher}
        aria-expanded={open}
        aria-controls="axignal-billing-panel"
        onClick={() => setOpen((value) => !value)}
      >
        PLAN · {planLabel(summary?.entitlement?.plan_code ?? summary?.selection?.plan_code)}
      </button>
      {open && (
        <aside id="axignal-billing-panel" className={styles.panel} aria-label="Plan y facturación">
          <div className={styles.header}>
            <div>
              <h2>PLAN Y ACCESO</h2>
              <p>Estado persistente del tenant autenticado.</p>
            </div>
            <button type="button" className={styles.close} onClick={() => setOpen(false)}>
              Cerrar
            </button>
          </div>

          {summary && (
            <section className={styles.current} aria-label="Estado comercial actual">
              <div className={styles.statusRow}>
                <span className={styles.badge}>{summary.provider}</span>
                <span className={styles.state}>{summary.selection?.state ?? "NO_PLAN"}</span>
              </div>
              <p className={styles.meta}>
                Plan: {planLabel(summary.entitlement?.plan_code ?? summary.selection?.plan_code)} ·
                acceso {summary.entitlement?.state ?? "NO_ENTITLEMENT"}
              </p>
              {summary.entitlement?.entitlement_kind === "PAID_MONTHLY" && (
                <p className={styles.meta}>
                  IA mensual sin cuota de tokens: {summary.entitlement.unlimited_ai_tokens ? "sí" : "no"} ·
                  facturación por exceso de tokens: no
                </p>
              )}
              {pendingConfirmation && (
                <p className={styles.notice} role="status">
                  PAYMENT_CONFIRMATION_PENDING — volver de Checkout no concede acceso. El estado
                  cambiará únicamente después de un evento firmado y persistido.
                </p>
              )}
              {summary.selection?.cancel_at_period_end && (
                <p className={styles.notice}>
                  Cancelación programada. El acceso continúa hasta el evento terminal del periodo pagado
                  {summary.selection.current_period_end
                    ? ` (${new Date(summary.selection.current_period_end).toLocaleDateString("es-ES")})`
                    : ""}.
                </p>
              )}
            </section>
          )}

          {!activePaid && !summary?.selection && (
            <>
              <label className={styles.confirm}>
                <input
                  type="checkbox"
                  checked={confirmedSelection}
                  onChange={(event) => setConfirmedSelection(event.target.checked)}
                />
                Confirmo que estoy seleccionando explícitamente un plan de pago. Los precios siguen
                siendo candidatos hasta validación comercial; no existe conversión automática desde trial.
              </label>
              <div className={styles.grid}>
                <article className={styles.card}>
                  <h3>Professional</h3>
                  <p>Investigación AXIGNAL para una organización. Precio candidato no validado.</p>
                  <button
                    type="button"
                    className={styles.primary}
                    disabled={!confirmedSelection || busy || !summary?.checkout_enabled}
                    onClick={() => void startCheckout("PROFESSIONAL_MONTHLY")}
                  >
                    Seleccionar Professional
                  </button>
                </article>
                <article className={styles.card}>
                  <h3>Team</h3>
                  <p>Colaboración y capacidad de equipo. Precio candidato no validado.</p>
                  <button
                    type="button"
                    className={styles.primary}
                    disabled={!confirmedSelection || busy || !summary?.checkout_enabled}
                    onClick={() => void startCheckout("TEAM_MONTHLY")}
                  >
                    Seleccionar Team
                  </button>
                </article>
              </div>
            </>
          )}

          {canUpgrade && (
            <div className={styles.actionRow}>
              <button type="button" className={styles.primary} disabled={busy} onClick={() => void upgrade()}>
                Upgrade explícito a Team
              </button>
            </div>
          )}

          {canCancel && (
            <div className={styles.actionRow}>
              <button
                type="button"
                className={styles.secondary}
                disabled={busy}
                onClick={() => void cancel(true)}
              >
                Cancelar al final del periodo
              </button>
              <button
                type="button"
                className={styles.danger}
                disabled={busy}
                onClick={() => void cancel(false)}
              >
                Cancelar ahora
              </button>
            </div>
          )}

          <section className={styles.ledger} aria-label="Historial auditado de billing">
            <div className={styles.ledgerHeader}>
              <strong>LEDGER AUDITADO</strong>
              <button type="button" className={styles.close} disabled={busy} onClick={() => void load()}>
                Actualizar
              </button>
            </div>
            {recentLedger.length === 0 && <p className={styles.empty}>Sin transiciones comerciales.</p>}
            <div className={styles.ledgerList}>
              {recentLedger.map((item) => (
                <article className={styles.ledgerItem} key={item.ledger_entry_id}>
                  <strong>{item.event_type}</strong>
                  <span>{item.previous_state ?? "∅"} → {item.new_state ?? "∅"}</span>
                  <small>
                    {new Date(item.occurred_at).toLocaleString("es-ES")} · {item.operation_actor}
                    {item.provider_event_id ? ` · ${item.provider_event_id}` : ""}
                  </small>
                </article>
              ))}
            </div>
          </section>

          <p className={styles.notice}>
            Stripe sandbox externo verificado: no · evidencia de pago comercial real: no.
          </p>
          {error && <p className={styles.error} role="alert">{error}</p>}
        </aside>
      )}
    </>
  );
}
