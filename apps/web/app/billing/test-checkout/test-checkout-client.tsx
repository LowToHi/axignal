"use client";

import { useEffect, useState } from "react";

import styles from "./test-checkout.module.css";

export function DeterministicTestCheckoutClient() {
  const [selectionId, setSelectionId] = useState("");
  const [planCode, setPlanCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    setSelectionId(query.get("selection_id") ?? "");
    setPlanCode(query.get("plan_code") ?? "");
  }, []);

  async function completeCheckout() {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/billing/test/provider-event", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ action: "COMPLETE_CHECKOUT" })
      });
      const body = (await response.json()) as { error?: string; detail?: string };
      if (!response.ok) throw new Error(body.detail ?? body.error ?? "Provider event failed.");
      window.location.assign("/?billing=success");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Provider event failed.");
      setBusy(false);
    }
  }

  return (
    <main className={styles.main}>
      <section className={styles.card} aria-label="Checkout determinista de prueba">
        <span className={styles.eyebrow}>DETERMINISTIC TEST PROVIDER · NO STRIPE EXTERNO</span>
        <h1>Confirmación de pago de prueba</h1>
        <p className={styles.meta}>Plan: {planCode || "desconocido"}</p>
        <p className={styles.meta}>Selection: {selectionId || "ausente"}</p>
        <p className={styles.notice}>
          Cargar esta página o volver a AXIGNAL no concede acceso. El botón entrega dos eventos
          firmados al endpoint real de webhook; el billing worker persiste después el entitlement.
          No existe cobro, tarjeta ni evidencia comercial real.
        </p>
        <button
          type="button"
          className={styles.button}
          disabled={busy || !selectionId || !planCode}
          onClick={() => void completeCheckout()}
        >
          {busy ? "Entregando eventos firmados…" : "Confirmar pago de prueba"}
        </button>
        <a className={styles.secondary} href="/?billing=cancelled">Cancelar y volver</a>
        {error && <p className={styles.error} role="alert">{error}</p>}
      </section>
    </main>
  );
}
