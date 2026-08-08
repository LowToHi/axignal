"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface AxentSegment {
  text: string;
  epistemic_class: string;
  citations: string[];
}

interface AxentMessage {
  role: "user" | "assistant";
  content: string;
}

/**
 * AXENT global assistant: floating conversational panel available from
 * any product surface. Talks to the real API through the server proxy
 * (/api/axent/*), which carries the identity assertion.
 */
export function AxentGlobalAssistant() {
  const [open, setOpen] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<AxentMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [degraded, setDegraded] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  const ensureConversation = useCallback(async () => {
    if (conversationId) return conversationId;
    const response = await fetch("/api/axent/conversations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "AXENT global" }),
    });
    if (!response.ok) throw new Error(`conversation: ${response.status}`);
    const created = await response.json();
    setConversationId(created.conversation_id);
    return created.conversation_id as string;
  }, [conversationId]);

  useEffect(() => {
    if (!open) return;
    fetch("/api/axent/context", { cache: "no-store" })
      .then((response) => response.json())
      .then((body) => {
        if (body?.identity?.subject) {
          setDegraded(false);
        }
      })
      .catch(() => setDegraded(true));
  }, [open]);

  useEffect(() => {
    listRef.current?.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setBusy(true);
    setError(null);
    setMessages((previous) => [...previous, { role: "user", content: text }]);
    try {
      const id = await ensureConversation();
      const response = await fetch(
        `/api/axent/conversations/${id}/messages`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: text }),
        }
      );
      if (!response.ok) throw new Error(`message: ${response.status}`);
      const payload = await response.json();
      const segments: AxentSegment[] = payload.segments ?? [];
      const assistantText = segments
        .map((segment) => segment.text)
        .join("\n");
      setMessages((previous) => [
        ...previous,
        { role: "assistant", content: assistantText },
      ]);
      if (payload.bundle?.query_plan) {
        setDegraded(false);
      }
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "AXENT no respondió"
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <button
        type="button"
        aria-label="Abrir AXENT"
        onClick={() => setOpen((value) => !value)}
        style={{
          position: "fixed",
          right: 20,
          bottom: 20,
          zIndex: 1000,
          width: 56,
          height: 56,
          borderRadius: 28,
          border: "none",
          background: "#0f62fe",
          color: "#fff",
          fontSize: 22,
          cursor: "pointer",
          boxShadow: "0 4px 14px rgba(0,0,0,0.25)",
        }}
      >
        {open ? "×" : "✦"}
      </button>
      {open && (
        <section
          aria-label="AXENT asistente"
          style={{
            position: "fixed",
            right: 20,
            bottom: 88,
            zIndex: 999,
            width: 380,
            maxWidth: "calc(100vw - 40px)",
            height: 480,
            background: "#fff",
            border: "1px solid #d9d9d9",
            borderRadius: 12,
            display: "flex",
            flexDirection: "column",
            boxShadow: "0 8px 30px rgba(0,0,0,0.2)",
            fontFamily: "system-ui, sans-serif",
          }}
        >
          <header
            style={{
              padding: "10px 14px",
              borderBottom: "1px solid #eee",
              fontWeight: 600,
              display: "flex",
              justifyContent: "space-between",
            }}
          >
            <span>AXENT</span>
            {degraded ? (
              <span style={{ color: "#b26a00", fontSize: 12 }}>
                modo determinista
              </span>
            ) : (
              <span style={{ color: "#1a7f37", fontSize: 12 }}>conectado</span>
            )}
          </header>
          <div
            ref={listRef}
            style={{
              flex: 1,
              overflowY: "auto",
              padding: 12,
              display: "flex",
              flexDirection: "column",
              gap: 8,
            }}
          >
            {messages.length === 0 && (
              <p style={{ color: "#666", fontSize: 14 }}>
                Pregúntame por oportunidades, pursuits o workspaces.
              </p>
            )}
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                style={{
                  alignSelf:
                    message.role === "user" ? "flex-end" : "flex-start",
                  background:
                    message.role === "user" ? "#0f62fe" : "#f1f3f5",
                  color: message.role === "user" ? "#fff" : "#111",
                  padding: "8px 12px",
                  borderRadius: 10,
                  fontSize: 14,
                  whiteSpace: "pre-wrap",
                  maxWidth: "85%",
                }}
              >
                {message.content}
              </div>
            ))}
            {busy && (
              <div style={{ color: "#666", fontSize: 13 }}>AXENT escribe…</div>
            )}
            {error && (
              <div style={{ color: "#c0392b", fontSize: 13 }}>{error}</div>
            )}
          </div>
          <footer style={{ padding: 10, borderTop: "1px solid #eee" }}>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                aria-label="Mensaje para AXENT"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") void send();
                }}
                placeholder="Ej: muéstrame licitaciones de ciberseguridad en España"
                style={{
                  flex: 1,
                  padding: "8px 10px",
                  border: "1px solid #ccc",
                  borderRadius: 8,
                  fontSize: 14,
                }}
              />
              <button
                type="button"
                onClick={() => void send()}
                disabled={busy || !input.trim()}
                style={{
                  padding: "8px 14px",
                  border: "none",
                  borderRadius: 8,
                  background: "#0f62fe",
                  color: "#fff",
                  cursor: "pointer",
                }}
              >
                Enviar
              </button>
            </div>
          </footer>
        </section>
      )}
    </>
  );
}
