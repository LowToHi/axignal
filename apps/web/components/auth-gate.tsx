"use client";

import { FormEvent, useState } from "react";

export function AuthGate() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [state, setState] = useState<"idle" | "submitting" | "error">("idle");
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (state === "submitting") return;
    setState("submitting");
    setError("");
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    if (!response.ok) {
      const body = (await response.json().catch(() => null)) as { error?: string } | null;
      setError(body?.error ?? "No se pudo autenticar la identidad.");
      setState("error");
      return;
    }
    window.location.reload();
  }

  return (
    <main className="auth-shell">
      <section className="auth-card" aria-label="Acceso a AXIGNAL">
        <span className="auth-kicker">IDENTITY BOUNDARY</span>
        <h1>AXIGNAL</h1>
        <p>Autentícate para resolver el tenant en el servidor y abrir el InvestigationContext persistente.</p>
        <form onSubmit={submit}>
          <label>
            Email
            <input type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label>
            Contraseña
            <input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          {error && <p className="auth-error" role="alert">{error}</p>}
          <button type="submit" disabled={state === "submitting"}>{state === "submitting" ? "Verificando…" : "Entrar"}</button>
        </form>
        <small>La identidad del navegador no puede declarar ni cambiar el tenant.</small>
      </section>
    </main>
  );
}
