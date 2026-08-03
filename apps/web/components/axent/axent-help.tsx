"use client";

import { FormEvent, useEffect, useState } from "react";

type StoredMessage = {
  message_id: string;
  author_type: "USER" | "AXENT" | "HUMAN_AGENT" | "SYSTEM";
  content: string;
};

type Citation = {
  citation_id: string;
  authority_type: string;
  authority_id: string;
  authority_version: string;
};

type Notification = {
  notification_id: string;
  notification_type: string;
  payload_redacted: { resolution?: string };
  delivery_state: "PENDING" | "DELIVERED" | "FAILED";
  created_at: string;
};

export function AxentHelp() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<StoredMessage[]>([]);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [draft, setDraft] = useState("");
  const [state, setState] = useState<"ready" | "sending" | "error">("ready");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function loadNotifications() {
      const response = await fetch("/api/axent/notifications", { cache: "no-store" });
      const payload = await response.json();
      if (active && response.ok) setNotifications(payload.notifications ?? []);
    }
    void loadNotifications();
    return () => {
      active = false;
    };
  }, []);

  async function acknowledge(notificationId: string) {
    const response = await fetch(
      `/api/axent/notifications/${notificationId}/acknowledge`,
      { method: "POST" }
    );
    if (!response.ok) return;
    setNotifications((current) =>
      current.map((item) =>
        item.notification_id === notificationId
          ? { ...item, delivery_state: "DELIVERED" }
          : item
      )
    );
  }

  async function ensureConversation(): Promise<string> {
    if (conversationId) return conversationId;
    const response = await fetch("/api/axent/conversations", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ language: "es" })
    });
    const payload = await response.json();
    if (!response.ok || !payload.conversation?.conversation_id) {
      throw new Error(payload.error ?? payload.detail ?? "No se pudo abrir Axent.");
    }
    const created = String(payload.conversation.conversation_id);
    setConversationId(created);
    return created;
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || state === "sending") return;
    setState("sending");
    setError(null);
    try {
      const activeConversationId = await ensureConversation();
      const response = await fetch(
        `/api/axent/conversations/${activeConversationId}/messages`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ content })
        }
      );
      const payload = await response.json();
      if (!response.ok || !payload.user_message || !payload.message) {
        throw new Error(payload.error ?? payload.detail ?? "Axent no pudo responder.");
      }
      setMessages((current) => [
        ...current,
        payload.user_message as StoredMessage,
        payload.message as StoredMessage
      ]);
      setCitations(payload.citations ?? []);
      setDraft("");
      setState("ready");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Error inesperado.");
      setState("error");
    }
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#08111d",
        color: "#eef4f8",
        padding: "clamp(1rem, 3vw, 3rem)"
      }}
    >
      <section
        aria-labelledby="axent-title"
        style={{
          width: "min(900px, 100%)",
          margin: "0 auto",
          display: "grid",
          gap: "1rem"
        }}
      >
        <header>
          <p style={{ color: "#76d7c4", margin: 0 }}>AXIGNAL HELP</p>
          <h1 id="axent-title" style={{ marginBottom: "0.4rem" }}>Axent</h1>
          <p style={{ color: "#a9b8c7", maxWidth: "70ch" }}>
            Soporte conectado a las autoridades reales de tu cuenta. Las respuestas
            materiales incluyen citas y Axent no puede modificar entitlements ni
            tomar decisiones reservadas a una persona.
          </p>
        </header>

        {notifications.map((notification) => (
          <aside
            key={notification.notification_id}
            role="status"
            style={{ border: "1px solid #76d7c4", borderRadius: 12, padding: "1rem" }}
          >
            <strong>{notification.notification_type}</strong>
            <p>{notification.payload_redacted.resolution ?? "Tu caso de soporte ha cambiado de estado."}</p>
            {notification.delivery_state === "PENDING" && (
              <button type="button" onClick={() => void acknowledge(notification.notification_id)}>
                Marcar como leído
              </button>
            )}
          </aside>
        ))}

        <div
          aria-live="polite"
          data-testid="axent-transcript"
          style={{
            minHeight: "360px",
            border: "1px solid #243548",
            borderRadius: "14px",
            padding: "1rem",
            display: "grid",
            alignContent: "start",
            gap: "0.75rem",
            background: "#0c1826"
          }}
        >
          {messages.length === 0 && (
            <p style={{ color: "#a9b8c7" }}>
              Pregunta por tu plan, asientos, facturación, investigaciones,
              workspaces, documentos o los límites de Axent.
            </p>
          )}
          {messages.map((message) => (
            <article
              key={message.message_id}
              data-author={message.author_type}
              style={{
                justifySelf: message.author_type === "USER" ? "end" : "start",
                maxWidth: "80%",
                padding: "0.8rem 1rem",
                borderRadius: "12px",
                background: message.author_type === "USER" ? "#174a4a" : "#15263a"
              }}
            >
              <strong>{message.author_type === "USER" ? "Tú" : "Axent"}</strong>
              <p style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>{message.content}</p>
            </article>
          ))}
        </div>

        {citations.length > 0 && (
          <aside aria-label="Fuentes de la última respuesta">
            <strong>Autoridades consultadas</strong>
            <ul>
              {citations.map((citation) => (
                <li key={citation.citation_id}>
                  {citation.authority_type}: {citation.authority_id} · {citation.authority_version}
                </li>
              ))}
            </ul>
          </aside>
        )}

        <form onSubmit={submit} style={{ display: "grid", gap: "0.75rem" }}>
          <label htmlFor="axent-message">Tu consulta</label>
          <textarea
            id="axent-message"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            rows={4}
            maxLength={20000}
            disabled={state === "sending"}
            style={{
              resize: "vertical",
              borderRadius: "10px",
              border: "1px solid #38506a",
              background: "#0b1724",
              color: "inherit",
              padding: "0.85rem"
            }}
          />
          <button
            type="submit"
            disabled={!draft.trim() || state === "sending"}
            style={{
              justifySelf: "start",
              border: 0,
              borderRadius: "9px",
              padding: "0.75rem 1.1rem",
              background: "#76d7c4",
              color: "#061019",
              fontWeight: 700,
              cursor: "pointer"
            }}
          >
            {state === "sending" ? "Consultando autoridades…" : "Enviar a Axent"}
          </button>
        </form>

        {error && <p role="alert" style={{ color: "#ffb4ab" }}>{error}</p>}
      </section>
    </main>
  );
}
