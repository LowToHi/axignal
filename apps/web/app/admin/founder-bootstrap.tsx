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
              <p>
                This AAL2 identity exists only inside the disposable P26 test
                topology. A database principal remains required before any
                founder mutation is authorised.
              </p>
              <div className={styles.actions}>
                <button
                  type="button"
                  disabled={state === "busy"}
                  onClick={bootstrap}
                >
                  {state === "busy"
                    ? "Provisioning…"
                    : "Provision test founder principal"}
                </button>
              </div>
              {state === "error" && <p>Provisioning was denied.</p>}
            </div>
            <ul>
              <li>
                <span>✓</span>Recent passkey verification required
              </li>
              <li>
                <span>✓</span>Test environment and test runtime required
              </li>
              <li>
                <span>✓</span>Production subject allowlist remains mandatory
              </li>
              <li>
                <span>✓</span>No production bootstrap endpoint
              </li>
            </ul>
          </section>
        </div>
      </section>
    </main>
  );
}
