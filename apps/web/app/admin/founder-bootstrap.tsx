"use client";

import { useState } from "react";

import styles from "./founder-admin.module.css";

export function FounderBootstrap() {
  const [state, setState] = useState<"idle" | "busy" | "error">("idle");

  async function bootstrap() {
    setState("busy");
    const response = await fetch("/api/admin/organic", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action: "test-bootstrap" })
    });
    if (!response.ok) {
      setState("error");
      return;
    }
    window.location.reload();
  }

  return (
    <main className={styles.shell} data-testid="founder-bootstrap">
      <section className={styles.content}>
        <div className={styles.viewport}>
          <section className={styles.contractModule}>
            <div>
              <span className={styles.eyebrow}>TEST RUNTIME ONLY</span>
              <h2>Provision the founder control principal.</h2>
              <p>The server allowlist already recognises this AAL2 identity. The database principal remains unprovisioned, so no founder mutation is authorised yet.</p>
              <button type="button" className={styles.bootstrapButton} disabled={state === "busy"} onClick={bootstrap}>
                {state === "busy" ? "Provisioning…" : "Provision test founder principal"}
              </button>
              {state === "error" && <p>Provisioning was denied.</p>}
            </div>
            <ul>
              <li><span>✓</span>Recent passkey verification required</li>
              <li><span>✓</span>Server-side subject allowlist required</li>
              <li><span>✓</span>Test environment and test runtime required</li>
              <li><span>✓</span>No production bootstrap endpoint</li>
            </ul>
          </section>
        </div>
      </section>
    </main>
  );
}
