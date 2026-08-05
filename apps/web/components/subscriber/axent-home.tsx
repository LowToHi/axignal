"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import type {
  AxentConversationExport,
  AxentConversationList,
  AxentConversationSummary,
  AxentMessage
} from "@/lib/axent-server";
import type { SubscriberWorkspaceBootstrap } from "@/lib/subscriber-workspace-contract";

type AxentHomeProps = {
  bootstrap: SubscriberWorkspaceBootstrap;
  onOpenWorkspace: (workspaceId: string) => void;
  onHelp: () => void;
};

type EvidenceCard = {
  id: string;
  kind: "FACT" | "INFERENCE" | "CONTRADICTION" | "UNKNOWN";
  statement: string;
  source: string;
  confidence: number | null;
};

type AssistantResponse = {
  reply: string;
  context: {
    scope: string;
    jurisdiction: string;
    entities: string;
    framework: string;
  };
  evidence: EvidenceCard[];
  action: { workspaceId: string; title: string; description: string } | null;
  mode: "fixture" | "upstream";
};

type ApiError = { error?: string; code?: string };

function requestId(): string {
  return `axent_req_${crypto.randomUUID().replaceAll("-", "")}`;
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: { "content-type": "application/json" },
    cache: "no-store"
  });
  const body = (await response.json().catch(() => ({}))) as T & ApiError;
  if (!response.ok) throw new Error(body.error ?? "AXENT operation failed.");
  return body;
}

function displayRole(role: AxentMessage["role"]): string {
  if (role === "USER") return "You";
  if (role === "SYSTEM") return "System";
  return "AXENT";
}

function titleFromMessage(message: string): string {
  const compact = message.replace(/\s+/g, " ").trim();
  return compact.length > 72 ? `${compact.slice(0, 69)}…` : compact;
}

export function AxentHome({ bootstrap, onOpenWorkspace, onHelp }: AxentHomeProps) {
  const [conversations, setConversations] = useState<AxentConversationSummary[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [conversation, setConversation] = useState<AxentConversationExport | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [assistantContext, setAssistantContext] = useState<AssistantResponse | null>(null);

  const activeSummary = useMemo(
    () => conversations.find((item) => item.conversation_id === activeId) ?? null,
    [activeId, conversations]
  );

  const loadConversation = useCallback(async (conversationId: string) => {
    const value = await requestJson<AxentConversationExport>(
      `/api/subscriber-workspace/axent/${encodeURIComponent(conversationId)}`
    );
    setConversation(value);
    setActiveId(conversationId);
  }, []);

  const loadConversations = useCallback(async (preferredId?: string | null) => {
    const value = await requestJson<AxentConversationList>(
      "/api/subscriber-workspace/axent"
    );
    setConversations(value.conversations);
    const selected =
      preferredId && value.conversations.some((item) => item.conversation_id === preferredId)
        ? preferredId
        : value.conversations[0]?.conversation_id ?? null;
    if (selected) await loadConversation(selected);
    else {
      setActiveId(null);
      setConversation(null);
    }
  }, [loadConversation]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        await loadConversations();
        if (!cancelled) setError(null);
      } catch (cause) {
        if (!cancelled) setError(cause instanceof Error ? cause.message : "AXENT is unavailable.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [loadConversations]);

  async function createConversation(title: string): Promise<AxentConversationSummary> {
    const created = await requestJson<AxentConversationSummary>(
      "/api/subscriber-workspace/axent",
      {
        method: "POST",
        body: JSON.stringify({
          request_id: requestId(),
          title,
          retention_class: "STANDARD_90D"
        })
      }
    );
    await loadConversations(created.conversation_id);
    return created;
  }

  async function startNewConversation() {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await createConversation("New AXENT conversation");
      setAssistantContext(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Conversation creation failed.");
    } finally {
      setBusy(false);
    }
  }

  async function appendMessage(
    conversationId: string,
    role: "USER" | "ASSISTANT",
    content: string
  ): Promise<void> {
    await requestJson(
      `/api/subscriber-workspace/axent/${encodeURIComponent(conversationId)}/messages`,
      {
        method: "POST",
        body: JSON.stringify({ request_id: requestId(), role, content })
      }
    );
  }

  async function sendMessage() {
    const message = draft.trim();
    if (!message || busy) return;
    setBusy(true);
    setError(null);
    setDraft("");
    try {
      const target = activeId
        ? { conversation_id: activeId }
        : await createConversation(titleFromMessage(message));
      const conversationId = target.conversation_id;

      await appendMessage(conversationId, "USER", message);
      await loadConversation(conversationId);

      const answer = await requestJson<AssistantResponse>(
        "/api/subscriber-workspace/assistant",
        {
          method: "POST",
          body: JSON.stringify({ message, conversation_id: conversationId })
        }
      );
      await appendMessage(conversationId, "ASSISTANT", answer.reply);
      setAssistantContext(answer);
      await loadConversations(conversationId);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "AXENT could not complete the turn.");
      if (activeId) {
        try { await loadConversation(activeId); } catch { /* retain the last coherent view */ }
      }
    } finally {
      setBusy(false);
    }
  }

  async function deleteConversation() {
    if (!activeId || busy) return;
    setBusy(true);
    setError(null);
    try {
      await requestJson(
        `/api/subscriber-workspace/axent/${encodeURIComponent(activeId)}`,
        { method: "DELETE" }
      );
      setAssistantContext(null);
      await loadConversations(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Conversation deletion failed.");
    } finally {
      setBusy(false);
    }
  }

  const workspace = bootstrap.route_data.workspaces[0];

  return (
    <main className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-[1480px] gap-5 px-4 py-5 lg:grid-cols-[300px_minmax(0,1fr)_320px] lg:px-6">
      <aside className="rounded-3xl border border-white/10 bg-slate-950/70 p-4 shadow-2xl shadow-black/20">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Persistent AXENT</p>
            <h1 className="mt-1 text-xl font-semibold text-white">Conversations</h1>
          </div>
          <button
            type="button"
            disabled={busy}
            onClick={() => void startNewConversation()}
            className="rounded-xl border border-cyan-400/30 bg-cyan-400/10 px-3 py-2 text-sm font-semibold text-cyan-100 hover:bg-cyan-400/20 disabled:opacity-50"
          >
            New
          </button>
        </div>
        <p className="mt-3 text-sm leading-6 text-slate-400">
          Encrypted tenant storage. Retention, export and deletion are governed by the server authority.
        </p>
        <div className="mt-5 space-y-2">
          {loading ? <p className="text-sm text-slate-400">Loading server history…</p> : null}
          {!loading && conversations.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-white/15 p-4 text-sm text-slate-400">
              No persistent conversations yet.
            </div>
          ) : null}
          {conversations.map((item) => (
            <button
              type="button"
              key={item.conversation_id}
              onClick={() => void loadConversation(item.conversation_id).catch((cause) => setError(cause instanceof Error ? cause.message : "Conversation unavailable."))}
              className={`w-full rounded-2xl border p-3 text-left transition ${item.conversation_id === activeId ? "border-cyan-400/40 bg-cyan-400/10" : "border-white/10 bg-white/[0.03] hover:bg-white/[0.06]"}`}
            >
              <span className="block truncate text-sm font-semibold text-slate-100">{item.title}</span>
              <span className="mt-1 block text-xs text-slate-500">{item.message_count ?? 0} messages · {new Date(item.updated_at).toLocaleString()}</span>
            </button>
          ))}
        </div>
        {activeSummary ? (
          <button
            type="button"
            disabled={busy}
            onClick={() => void deleteConversation()}
            className="mt-5 w-full rounded-xl border border-rose-400/20 px-3 py-2 text-sm font-medium text-rose-200 hover:bg-rose-400/10 disabled:opacity-50"
          >
            Request deletion
          </button>
        ) : null}
      </aside>

      <section className="flex min-h-[70vh] flex-col overflow-hidden rounded-3xl border border-white/10 bg-slate-950/60 shadow-2xl shadow-black/20">
        <header className="border-b border-white/10 px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">Evidence-governed assistant</p>
          <div className="mt-1 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-xl font-semibold text-white">{conversation?.title ?? "Ask AXENT"}</h2>
            <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-200">Server persistent</span>
          </div>
        </header>

        <div className="flex-1 space-y-4 overflow-y-auto p-5" aria-live="polite">
          {!conversation?.messages.length ? (
            <div className="mx-auto mt-16 max-w-xl text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400/20 to-violet-400/20 text-2xl">✦</div>
              <h3 className="mt-5 text-2xl font-semibold text-white">Research with visible evidence boundaries</h3>
              <p className="mt-3 leading-7 text-slate-400">Ask about opportunities, investigations, requirements, sources, claims or the current Workspace. AXENT proposes; the subscriber remains the decision authority.</p>
            </div>
          ) : null}
          {conversation?.messages.map((item) => (
            <article
              key={item.message_id}
              className={`max-w-[88%] rounded-2xl border px-4 py-3 ${item.role === "USER" ? "ml-auto border-cyan-400/20 bg-cyan-400/10" : "border-white/10 bg-white/[0.04]"}`}
            >
              <div className="flex items-center justify-between gap-4 text-xs">
                <span className="font-semibold uppercase tracking-[0.14em] text-slate-300">{displayRole(item.role)}</span>
                <span className="text-slate-600">#{item.ordinal}</span>
              </div>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-slate-200">{item.content}</p>
            </article>
          ))}
          {busy ? <p className="text-sm text-cyan-200">Persisting and reconciling the AXENT turn…</p> : null}
        </div>

        <div className="border-t border-white/10 p-4">
          {error ? <div className="mb-3 rounded-xl border border-rose-400/20 bg-rose-400/10 px-3 py-2 text-sm text-rose-100">{error}</div> : null}
          <div className="flex gap-3">
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void sendMessage();
                }
              }}
              maxLength={4_000}
              rows={3}
              placeholder="Ask about an opportunity, evidence gap, claim or Workspace…"
              className="min-h-20 flex-1 resize-none rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-cyan-400/40"
            />
            <button
              type="button"
              disabled={busy || !draft.trim()}
              onClick={() => void sendMessage()}
              className="self-end rounded-2xl bg-gradient-to-r from-cyan-400 to-violet-400 px-5 py-3 text-sm font-bold text-slate-950 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Send
            </button>
          </div>
          <p className="mt-2 text-xs text-slate-500">Enter sends · Shift+Enter adds a line · no browser-local history</p>
        </div>
      </section>

      <aside className="space-y-4">
        <section className="rounded-3xl border border-white/10 bg-slate-950/70 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">Current context</p>
          <dl className="mt-4 space-y-3 text-sm">
            <div><dt className="text-slate-500">Scope</dt><dd className="mt-1 text-slate-200">{assistantContext?.context.scope ?? bootstrap.route_data.opportunities[0]?.title ?? "AXIGNAL"}</dd></div>
            <div><dt className="text-slate-500">Jurisdiction</dt><dd className="mt-1 text-slate-200">{assistantContext?.context.jurisdiction ?? bootstrap.route_data.opportunities[0]?.jurisdiction ?? "Tenant scope"}</dd></div>
            <div><dt className="text-slate-500">Retention</dt><dd className="mt-1 text-slate-200">{activeSummary?.retention_class ?? "STANDARD_90D"}</dd></div>
          </dl>
        </section>

        {assistantContext?.evidence.map((item) => (
          <section key={item.id} className="rounded-3xl border border-white/10 bg-slate-950/70 p-4">
            <div className="flex items-center justify-between gap-3">
              <span className="text-xs font-semibold tracking-[0.14em] text-cyan-200">{item.kind}</span>
              <span className="text-xs text-slate-500">{item.confidence === null ? "unknown" : `${item.confidence}%`}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-200">{item.statement}</p>
            <p className="mt-3 text-xs text-slate-500">{item.source}</p>
          </section>
        ))}

        <section className="rounded-3xl border border-white/10 bg-slate-950/70 p-4">
          <p className="text-sm font-semibold text-white">Subscriber authority</p>
          <p className="mt-2 text-sm leading-6 text-slate-400">AXENT can explain and propose navigation. It cannot approve, submit, sign or perform an external action.</p>
          <div className="mt-4 grid gap-2">
            {workspace ? (
              <button type="button" onClick={() => onOpenWorkspace(workspace.id)} className="rounded-xl border border-cyan-400/30 bg-cyan-400/10 px-3 py-2 text-sm font-semibold text-cyan-100">Open prepared Workspace</button>
            ) : null}
            <button type="button" onClick={onHelp} className="rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-300 hover:bg-white/[0.05]">Open help</button>
          </div>
        </section>
      </aside>
    </main>
  );
}
