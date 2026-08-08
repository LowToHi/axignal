"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface AxentSegment {
  text: string;
  epistemic_class: string;
  citations: string[];
}

interface AxentOperation {
  tool_name?: string;
  parameters?: Record<string, unknown>;
  confirmation_id?: string;
  policy?: string;
  requires_confirmation?: boolean;
  status?: string;
  receipt?: Record<string, unknown>;
  rows?: Array<Record<string, unknown>>;
}

interface AxentBundle {
  query_plan?: Record<string, unknown>;
  matched_objects?: Array<Record<string, unknown>>;
  ranking?: Array<Record<string, unknown>>;
  operation?: AxentOperation;
}

interface AxentCitation {
  authority_id?: string;
  authority_type?: string;
  excerpt?: string;
}

interface AxentMessage {
  role: "user" | "assistant";
  content: string;
  operation?: AxentOperation;
  matched?: Array<Record<string, unknown>>;
  citations?: AxentCitation[];
}

function opportunityTitle(object: Record<string, unknown>): string {
  const payload = (object.payload as Record<string, unknown>) ?? {};
  return (payload.title as string) ?? (object.opportunity_ref as string);
}

function receiptText(receipt: Record<string, unknown> | undefined): string {
  if (!receipt) return "";
  const workspaceId = receipt.workspace_id as string;
  const pursuitRef = receipt.pursuit_ref as string;
  const taskRef = receipt.task_ref as string;
  const parts: string[] = [];
  if (workspaceId) parts.push(`Workspace ${workspaceId.slice(0, 8)}`);
  if (pursuitRef) parts.push(`Pursuit ${pursuitRef}`);
  if (taskRef) parts.push(`Tarea ${taskRef}`);
  if (parts.length) return parts.join(" · ");
  return JSON.stringify(receipt).slice(0, 120);
}

/**
 * AXENT global assistant: floating conversational panel with structured
 * opportunity results, operational previews, confirmations and links.
 */
export function AxentGlobalAssistant() {
  const [open, setOpen] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<AxentMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [degraded, setDegraded] = useState(false);
  const [pendingOp, setPendingOp] = useState<AxentOperation | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  /** Derive authorized context from the current route (server-rendered
   *  pages carry the object ref in the path). */
  const routeContext = useCallback(() => {
    if (typeof window === "undefined") return {};
    const path = window.location.pathname;
    const match = path.match(
      /\/opportunities\/([^/]+)|\/pursuits\/([^/]+)|\/workspaces\/([^/]+)/
    );
    if (!match) return {};
    const value = (match[1] ?? match[2] ?? match[3]) ?? "";
    if (match[1]) return { context_opportunity_ref: value };
    if (match[2]) return { context_pursuit_ref: value };
    return {};
  }, []);

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
  }, [messages, pendingOp]);

  const applyPayload = useCallback((payload: {
    segments?: AxentSegment[];
    bundle?: AxentBundle;
    message?: { citations?: AxentCitation[] };
  }) => {
    const segments: AxentSegment[] = payload.segments ?? [];
    const assistantText = segments.map((segment) => segment.text).join("\n");
    const operation = payload.bundle?.operation ?? null;
    const matched = payload.bundle?.matched_objects ?? [];
    const citations = payload.message?.citations ?? [];
    const assistantMessage: AxentMessage = {
      role: "assistant",
      content: assistantText,
    };
    if (operation && Object.keys(operation).length) {
      assistantMessage.operation = operation;
    }
    if (matched.length) {
      assistantMessage.matched = matched;
    }
    if (citations.length) {
      assistantMessage.citations = citations;
    }
    setMessages((previous) => [...previous, assistantMessage]);
    if (operation?.requires_confirmation && operation.status !== "EXECUTED") {
      setPendingOp(operation);
    } else {
      setPendingOp(null);
    }
    if (payload.bundle?.query_plan) {
      setDegraded(false);
    }
  }, []);

  const send = async (textOverride?: string) => {
    const text = (textOverride ?? input).trim();
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
          body: JSON.stringify({ content: text, ...routeContext() }),
        }
      );
      if (!response.ok) throw new Error(`message: ${response.status}`);
      const payload = await response.json();
      applyPayload(payload);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "AXENT no respondió"
      );
    } finally {
      setBusy(false);
    }
  };

  const confirmOperation = async (decision: "CONFIRMED" | "REJECTED") => {
    if (!pendingOp?.confirmation_id) return;
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/axent/confirmations/${pendingOp.confirmation_id}/resolve`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ decision }),
        }
      );
      if (!response.ok) throw new Error(`confirm: ${response.status}`);
      const body = await response.json();
      const executed = body.executed === true;
      const receipt = (body.receipt as Record<string, unknown>) ?? {};
      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: executed
            ? `Operación confirmada y persistida: ${receiptText(receipt) || JSON.stringify(receipt)}`
            : "Operación cancelada. No se ha modificado nada.",
          operation: {
            ...(pendingOp.tool_name
              ? { tool_name: pendingOp.tool_name }
              : {}),
            status: executed ? "EXECUTED" : "REJECTED",
            receipt,
          },
        },
      ]);
      setPendingOp(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "confirmación falló");
    } finally {
      setBusy(false);
    }
  };

  const planCriteria = (queryPlan: Record<string, unknown> | undefined) => {
    if (!queryPlan) return null;
    const parts: string[] = [];
    const keywords = queryPlan.keywords as string[] | undefined;
    if (keywords?.length) parts.push(`términos: ${keywords.join(", ")}`);
    const countries = queryPlan.countries as string[] | undefined;
    if (countries?.length) parts.push(`países: ${countries.join(", ")}`);
    const status = queryPlan.status as string[] | undefined;
    if (status?.length) parts.push(`estado: ${status.join(", ")}`);
    if (!parts.length) return null;
    return parts.join(" · ");
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
            width: 460,
            maxWidth: "calc(100vw - 40px)",
            height: 560,
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
              gap: 10,
            }}
          >
            {messages.length === 0 && (
              <p style={{ color: "#666", fontSize: 14 }}>
                Pregúntame por oportunidades, pursuits o workspaces. Ej:
                «muéstrame obras públicas», «añade la primera al workspace
                Iberia», «crea un pursuit para la primera».
              </p>
            )}
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`}>
                <div
                  style={{
                    alignSelf: message.role === "user" ? "flex-end" : "flex-start",
                    background:
                      message.role === "user" ? "#0f62fe" : "#f1f3f5",
                    color: message.role === "user" ? "#fff" : "#111",
                    padding: "8px 12px",
                    borderRadius: 10,
                    fontSize: 14,
                    whiteSpace: "pre-wrap",
                    maxWidth: "88%",
                    display: "inline-block",
                  }}
                >
                  {message.content}
                </div>
                {message.role === "assistant" && message.matched && (
                  <div
                    style={{
                      marginTop: 6,
                      display: "flex",
                      flexDirection: "column",
                      gap: 6,
                    }}
                  >
                    {message.matched.map((object, idx) => (
                      <div
                        key={String(object.opportunity_ref)}
                        style={{
                          border: "1px solid #d9d9d9",
                          borderRadius: 8,
                          padding: "8px 10px",
                          fontSize: 13,
                          background: "#fafbfc",
                        }}
                      >
                        <div style={{ fontWeight: 600 }}>
                          {idx + 1}. {opportunityTitle(object)}
                        </div>
                        <div style={{ color: "#555" }}>
                          {String(object.opportunity_ref)} ·{" "}
                          {String(object.state ?? "")} ·{" "}
                          {String(object.library_id ?? "")}
                        </div>
                        <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
                          <button
                            type="button"
                            onClick={() =>
                              void send(
                                `añade la ${idx + 1}ª al workspace Iberia`
                              )
                            }
                            style={actionButtonStyle}
                          >
                            Añadir
                          </button>
                          <button
                            type="button"
                            onClick={() =>
                              void send(`crea un pursuit para la ${idx + 1}ª`)
                            }
                            style={actionButtonStyle}
                          >
                            Pursuit
                          </button>
                          <button
                            type="button"
                            onClick={() =>
                              void send(`descarta la ${idx + 1}ª`)
                            }
                            style={{
                              ...actionButtonStyle,
                              color: "#c0392b",
                              borderColor: "#e8b4b0",
                            }}
                          >
                            Descartar
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {message.role === "assistant" && message.operation?.rows && (
                  <div
                    style={{
                      marginTop: 6,
                      border: "1px solid #d9d9d9",
                      borderRadius: 8,
                      padding: 8,
                      fontSize: 13,
                    }}
                  >
                    <strong>Comparación</strong>
                    {message.operation.rows.map((row, idx) => (
                      <div key={idx} style={{ marginTop: 4 }}>
                        {String(row.opportunity_ref)} ·{" "}
                        {opportunityTitle(row as Record<string, unknown>)} ·{" "}
                        {String(row.state ?? "")}
                      </div>
                    ))}
                  </div>
                )}
                {message.role === "assistant" && message.operation?.receipt && (
                  <div
                    style={{
                      marginTop: 6,
                      border: "1px solid #b7d8b7",
                      borderRadius: 8,
                      padding: "6px 10px",
                      fontSize: 13,
                      background: "#f2faf2",
                      color: "#1a5c1a",
                    }}
                  >
                    ✓ {receiptText(message.operation.receipt)}
                  </div>
                )}
              </div>
            ))}
            {pendingOp && (
              <div
                style={{
                  border: "1px solid #e5c07b",
                  borderRadius: 8,
                  padding: "10px 12px",
                  background: "#fffaf0",
                  fontSize: 13,
                }}
              >
                <strong>Previsualización</strong>
                <div style={{ marginTop: 4, color: "#555" }}>
                  {pendingOp.tool_name} ·{" "}
                  {JSON.stringify(pendingOp.parameters ?? {})}
                </div>
                <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                  <button
                    type="button"
                    onClick={() => void confirmOperation("CONFIRMED")}
                    style={{
                      padding: "6px 14px",
                      border: "none",
                      borderRadius: 6,
                      background: "#1a7f37",
                      color: "#fff",
                      cursor: "pointer",
                    }}
                  >
                    Confirmar
                  </button>
                  <button
                    type="button"
                    onClick={() => void confirmOperation("REJECTED")}
                    style={{
                      padding: "6px 14px",
                      border: "1px solid #ccc",
                      borderRadius: 6,
                      background: "#fff",
                      cursor: "pointer",
                    }}
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            )}
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
                placeholder="Ej: muéstrame obras públicas"
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
            {pendingOp && (
              <div style={{ marginTop: 6, fontSize: 12, color: "#555" }}>
                Criterios interpretados:{" "}
                {planCriteria(
                  messages[messages.length - 1]?.operation
                    ? undefined
                    : undefined
                ) ?? "—"}
              </div>
            )}
          </footer>
        </section>
      )}
    </>
  );
}

const actionButtonStyle: React.CSSProperties = {
  padding: "4px 10px",
  border: "1px solid #b9c8e8",
  borderRadius: 6,
  background: "#fff",
  color: "#0f62fe",
  fontSize: 12,
  cursor: "pointer",
};
