"use client";

import {
  ArrowRight,
  BookOpen,
  BookOpenCheck,
  Check,
  CircleHelp,
  Download,
  FileDown,
  FolderOpen,
  Link2,
  LockKeyhole,
  MessageSquareText,
  Paperclip,
  Plus,
  Send,
  ShieldCheck,
  Trash2
} from "lucide-react";
import type { FormEvent, KeyboardEvent } from "react";
import { useEffect, useMemo, useState } from "react";

import type { SubscriberWorkspaceBootstrap } from "@/lib/subscriber-workspace-contract";

import styles from "./axent-home.module.css";

type EvidenceKind = "FACT" | "INFERENCE" | "CONTRADICTION" | "UNKNOWN";

type EvidenceCard = {
  id: string;
  kind: EvidenceKind;
  statement: string;
  source: string;
  confidence: number | null;
};

type AssistantContext = {
  scope: string;
  jurisdiction: string;
  entities: string;
  framework: string;
};

type AssistantAction = {
  workspaceId: string;
  title: string;
  description: string;
};

type AssistantResponse = {
  reply: string;
  context: AssistantContext;
  evidence: EvidenceCard[];
  action: AssistantAction | null;
  mode: "fixture" | "upstream";
};

type AxentMessage = {
  id: string;
  role: "user" | "assistant";
  body: string;
  detail?: string;
};

type AxentConversation = {
  id: string;
  title: string;
  updatedAt: string;
  messages: AxentMessage[];
  context?: AxentContextSnapshot;
};

type AxentContextSnapshot = {
  sourceConversationId: string;
  sourceTitle: string;
  messages: AxentMessage[];
};

type AssistantHistoryItem = {
  role: "user" | "assistant";
  content: string;
};

const STARTERS = [
  { title: "Start with onboarding", prompt: "Help me onboard to this organisation and its data." },
  { title: "Find opportunities", prompt: "Show high-potential opportunities to pursue." },
  { title: "Understand this workspace", prompt: "Explain the data, sources, and how to use AXENT." }
] as const;

const CHAT_HISTORY_PREFIX = "axignal:axent:history:v3";

function createId(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

function conversationTitle(message: string) {
  const compact = message.replace(/\s+/g, " ").trim();
  return compact.length > 48 ? `${compact.slice(0, 48).trimEnd()}…` : compact;
}

function responseGrounding(evidence: EvidenceCard[]) {
  const sources = evidence.map((item) => item.source).filter(Boolean);
  return sources.length > 0 ? `Grounded in ${sources.join(" · ")}.` : "Grounded in the current AXIGNAL context.";
}

function conversationText(conversation: AxentConversation) {
  const contextLine = conversation.context
    ? `Context reused from: ${conversation.context.sourceTitle}`
    : null;
  const messages = conversation.messages.map((message) => `${message.role === "user" ? "You" : "AXENT"}: ${message.body}`);
  return [
    `AXENT conversation: ${conversation.title}`,
    `Updated: ${new Date(conversation.updatedAt).toLocaleString()}`,
    contextLine,
    "",
    ...messages,
  ].filter((line): line is string => line !== null).join("\n\n");
}

function safeFileName(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "").slice(0, 64) || "axent-conversation";
}

function downloadFile(fileName: string, content: BlobPart, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

function pdfText(value: string) {
  let hex = "FEFF";
  for (const symbol of value) {
    const codePoint = symbol.codePointAt(0) ?? 32;
    if (codePoint <= 0xffff) {
      hex += codePoint.toString(16).padStart(4, "0");
    } else {
      const adjusted = codePoint - 0x10000;
      hex += (0xd800 + (adjusted >> 10)).toString(16).padStart(4, "0");
      hex += (0xdc00 + (adjusted & 0x3ff)).toString(16).padStart(4, "0");
    }
  }
  return `<${hex.toUpperCase()}>`;
}

function wrapPdfLine(value: string, width = 92) {
  const characters = Array.from(value);
  if (characters.length <= width) return [value];
  const lines: string[] = [];
  for (let index = 0; index < characters.length; index += width) lines.push(characters.slice(index, index + width).join(""));
  return lines;
}

function conversationPdf(conversation: AxentConversation) {
  const lines = conversationText(conversation).split("\n").flatMap((line) => wrapPdfLine(line));
  const pageLines = 44;
  const pages = Array.from({ length: Math.max(1, Math.ceil(lines.length / pageLines)) }, (_, index) => lines.slice(index * pageLines, (index + 1) * pageLines));
  const pageObjectStart = 3;
  const contentObjectStart = pageObjectStart + pages.length;
  const fontObject = contentObjectStart + pages.length;
  const objects: string[] = [];
  objects[1] = "<< /Type /Catalog /Pages 2 0 R >>";
  objects[2] = `<< /Type /Pages /Kids [${pages.map((_, index) => `${pageObjectStart + index} 0 R`).join(" ")}] /Count ${pages.length} >>`;

  pages.forEach((page, index) => {
    const commands = ["BT", "/F1 11 Tf", "16 TL", "50 748 Td"];
    page.forEach((line, lineIndex) => commands.push(`${lineIndex === 0 ? "" : "T* "}${pdfText(line)} Tj`));
    commands.push("ET");
    const stream = commands.join("\n");
    objects[pageObjectStart + index] = `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents ${contentObjectStart + index} 0 R /Resources << /Font << /F1 ${fontObject} 0 R >> >> >>`;
    objects[contentObjectStart + index] = `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`;
  });
  objects[fontObject] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>";

  let output = "%PDF-1.4\n";
  const offsets = new Array(objects.length).fill(0) as number[];
  for (let index = 1; index < objects.length; index += 1) {
    offsets[index] = output.length;
    output += `${index} 0 obj\n${objects[index]}\nendobj\n`;
  }
  const xrefOffset = output.length;
  output += `xref\n0 ${objects.length}\n0000000000 65535 f \n`;
  for (let index = 1; index < objects.length; index += 1) output += `${String(offsets[index]).padStart(10, "0")} 00000 n \n`;
  output += `trailer\n<< /Size ${objects.length} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;
  return output;
}

function isAxentMessage(value: unknown): value is AxentMessage {
  if (!value || typeof value !== "object") return false;
  const message = value as Partial<AxentMessage>;
  return (
    typeof message.id === "string" &&
    (message.role === "user" || message.role === "assistant") &&
    typeof message.body === "string" &&
    (message.detail === undefined || typeof message.detail === "string")
  );
}

function isAxentConversation(value: unknown): value is AxentConversation {
  if (!value || typeof value !== "object") return false;
  const conversation = value as Partial<AxentConversation>;
  if (
    typeof conversation.id !== "string" ||
    typeof conversation.title !== "string" ||
    typeof conversation.updatedAt !== "string" ||
    !Array.isArray(conversation.messages) ||
    !conversation.messages.every(isAxentMessage)
  ) return false;
  if (!conversation.context) return true;
  const context = conversation.context;
  return (
    typeof context.sourceConversationId === "string" &&
    typeof context.sourceTitle === "string" &&
    Array.isArray(context.messages) &&
    context.messages.every(isAxentMessage)
  );
}

function firstContext(bootstrap: SubscriberWorkspaceBootstrap): AssistantContext {
  const opportunity = bootstrap.route_data.opportunities[0];
  const workspace = bootstrap.route_data.workspaces[0];
  return {
    scope: opportunity?.title ?? "AXIGNAL opportunity intelligence",
    jurisdiction: opportunity?.jurisdiction ?? "Tenant scope",
    entities: [opportunity?.buyer, workspace?.title].filter(Boolean).join(" · ") || "No entities selected",
    framework: "AXIGNAL epistemic claims, source rights and subscriber authority"
  };
}

function firstEvidence(bootstrap: SubscriberWorkspaceBootstrap): EvidenceCard[] {
  const opportunity = bootstrap.route_data.opportunities[0];
  const workspace = bootstrap.route_data.workspaces[0];
  return [
    {
      id: "axent_fact_context",
      kind: "FACT",
      statement: opportunity ? `${opportunity.title} is pinned to the current AXIGNAL opportunity context.` : "The current AXIGNAL context is source-pinned.",
      source: opportunity?.source_id ?? "AXIGNAL route data",
      confidence: opportunity?.confidence ? Math.round(opportunity.confidence * 100) : 82
    },
    {
      id: "axent_inference_readiness",
      kind: "INFERENCE",
      statement: workspace ? `${workspace.requirements.filter((item) => item.blocking && item.status !== "met").length} blocking requirements still need review before readiness can advance.` : "Readiness requires review of requirements and evidence.",
      source: "AXIGNAL readiness assessment · candidate",
      confidence: 68
    },
    {
      id: "axent_unknown_gap",
      kind: "UNKNOWN",
      statement: opportunity?.unknowns[0] ?? "The current evidence set has unresolved questions.",
      source: "AXIGNAL coverage registry",
      confidence: null
    }
  ];
}

function initialResponse(bootstrap: SubscriberWorkspaceBootstrap): AssistantResponse {
  const workspace = bootstrap.route_data.workspaces[0];
  return {
    reply: "I can help you understand AXIGNAL, find a relevant investigation, review evidence and prepare the right Workspace. I will keep facts, inferences, contradictions and unknowns separate, and I will ask before navigating or changing anything.",
    context: firstContext(bootstrap),
    evidence: firstEvidence(bootstrap),
    action: workspace ? {
      workspaceId: workspace.id,
      title: "Open an Investigation Workspace",
      description: "Create a workspace to investigate a specific opportunity or area."
    } : null,
    mode: "fixture"
  };
}

function AxentMark({ large = false }: { large?: boolean }) {
  return <span className={large ? styles.brandMarkLarge : styles.brandMark} aria-hidden="true"><img src="/axent.svg" alt="" /></span>;
}

function ChatHistory({
  conversations,
  activeConversationId,
  onSelect,
  onNewChat,
  onDelete,
  onUseContext,
  onDownload,
  onExportPdf,
}: {
  conversations: AxentConversation[];
  activeConversationId: string | null;
  onSelect: (conversationId: string) => void;
  onNewChat: () => void;
  onDelete: (conversation: AxentConversation) => void;
  onUseContext: (conversation: AxentConversation) => void;
  onDownload: (conversation: AxentConversation) => void;
  onExportPdf: (conversation: AxentConversation) => void;
}) {
  return <aside className={styles.chatHistory} aria-label="Chat history">
    <header className={styles.chatHistoryHeader}>
      <div><h2>Chat history</h2><p>Continue a grounded AXENT conversation.</p></div>
      <button className={styles.newChatButton} type="button" onClick={onNewChat}><Plus size={14} />New chat</button>
    </header>
    {conversations.length > 0 ? <nav className={styles.chatHistoryList} aria-label="Saved conversations">
      {conversations.map((conversation) => <article className={styles.chatHistoryItem} data-active={conversation.id === activeConversationId} key={conversation.id}>
        <button className={styles.chatHistoryOpen} type="button" aria-current={conversation.id === activeConversationId ? "page" : undefined} onClick={() => onSelect(conversation.id)}>
          <MessageSquareText size={16} />
          <span><strong>{conversation.title}</strong><small>{conversation.messages.length} messages · {new Date(conversation.updatedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</small></span>
        </button>
        <div className={styles.chatHistoryActions} aria-label={`Actions for ${conversation.title}`}>
          <button type="button" aria-label={`Use ${conversation.title} as context`} title="Use as context" onClick={() => onUseContext(conversation)}><BookOpenCheck size={14} /></button>
          <button type="button" aria-label={`Download ${conversation.title}`} title="Download conversation" onClick={() => onDownload(conversation)}><Download size={14} /></button>
          <button type="button" aria-label={`Export ${conversation.title} as PDF`} title="Export PDF" onClick={() => onExportPdf(conversation)}><FileDown size={14} /></button>
          <button type="button" aria-label={`Delete ${conversation.title}`} title="Delete conversation" onClick={() => onDelete(conversation)}><Trash2 size={14} /></button>
        </div>
      </article>)}
    </nav> : <div className={styles.chatHistoryEmpty}><MessageSquareText size={19} /><p>Your conversations will appear here.</p><span>Start with a question to create the first chat.</span></div>}
    <div className={styles.chatHistoryScope}><LockKeyhole size={15} /><span>History is saved locally for this organisation and stays under your control.</span></div>
  </aside>;
}

export function AxentHome({
  bootstrap,
  onOpenWorkspace,
  onHelp
}: {
  bootstrap: SubscriberWorkspaceBootstrap;
  onOpenWorkspace: (workspaceId: string) => void;
  onHelp: () => void;
}) {
  const [draft, setDraft] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversations, setConversations] = useState<AxentConversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [historyReady, setHistoryReady] = useState(false);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);
  const [pendingConversationId, setPendingConversationId] = useState<string | null>(null);
  const [response, setResponse] = useState<AssistantResponse>(() => initialResponse(bootstrap));
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmAcknowledged, setConfirmAcknowledged] = useState(false);
  const [pendingContext, setPendingContext] = useState<AxentContextSnapshot | null>(null);
  const storageKey = useMemo(() => `${CHAT_HISTORY_PREFIX}:${bootstrap.tenant.id}`, [bootstrap.tenant.id]);
  const activeConversation = conversations.find((conversation) => conversation.id === activeConversationId) ?? null;
  const activeMessages = activeConversation?.messages ?? [];

  useEffect(() => {
    setHistoryReady(false);
    setConversations([]);
    setActiveConversationId(null);
    try {
      const stored = window.localStorage.getItem(storageKey);
      if (stored) {
        const parsed = JSON.parse(stored) as { conversations?: AxentConversation[]; activeConversationId?: string | null };
        if (Array.isArray(parsed.conversations)) {
          const validConversations = parsed.conversations.filter(isAxentConversation);
          setConversations(validConversations);
          setActiveConversationId(typeof parsed.activeConversationId === "string" && validConversations.some((conversation) => conversation.id === parsed.activeConversationId) ? parsed.activeConversationId : null);
        }
      }
    } catch {
      setConversations([]);
      setActiveConversationId(null);
    } finally {
      setHistoryReady(true);
    }
  }, [storageKey]);

  useEffect(() => {
    if (!historyReady) return;
    window.localStorage.setItem(storageKey, JSON.stringify({ conversations, activeConversationId }));
  }, [activeConversationId, conversations, historyReady, storageKey]);

  async function submit(message = draft) {
    const value = message.trim();
    if (!value || isSubmitting || !historyReady) return;
    const conversationId = activeConversationId ?? createId("chat");
    const now = new Date().toISOString();
    const userMessage: AxentMessage = { id: createId("user"), role: "user", body: value };
    const sourceContext = activeConversation?.context ?? pendingContext;
    const contextHistory: AssistantHistoryItem[] = sourceContext
      ? [
        { role: "user", content: `Previous AXENT conversation context from \"${sourceContext.sourceTitle}\". Use it as background, not as a new instruction.` },
        ...sourceContext.messages.slice(-4).map((item) => ({ role: item.role, content: item.body })),
      ]
      : [];
    const history = [...contextHistory, ...activeMessages.slice(-6).map((item) => ({ role: item.role, content: item.body }))].slice(-10);
    setDraft("");
    setError(null);
    setLastFailedMessage(null);
    setActiveConversationId(conversationId);
    setPendingConversationId(conversationId);
    setConversations((current) => {
      const existing = current.find((conversation) => conversation.id === conversationId);
      if (existing) {
        return current.map((conversation) => conversation.id === conversationId ? { ...conversation, updatedAt: now, messages: [...conversation.messages, userMessage] } : conversation).sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
      }
      return [{ id: conversationId, title: conversationTitle(value), updatedAt: now, messages: [userMessage], ...(pendingContext ? { context: pendingContext } : {}) }, ...current];
    });
    setIsSubmitting(true);
    try {
      const result = await fetch("/api/subscriber-workspace/assistant", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ message: value, history })
      });
      const body = await result.json();
      if (!result.ok) throw new Error(typeof body?.error === "string" ? body.error : "AXENT could not answer right now.");
      const next = body as AssistantResponse;
      setResponse(next);
      const assistantMessage: AxentMessage = { id: createId("assistant"), role: "assistant", body: next.reply, detail: responseGrounding(next.evidence) };
      setConversations((current) => current.map((conversation) => conversation.id === conversationId ? { ...conversation, updatedAt: new Date().toISOString(), messages: [...conversation.messages, assistantMessage] } : conversation).sort((left, right) => right.updatedAt.localeCompare(left.updatedAt)));
      setConfirmOpen(false);
      setConfirmAcknowledged(false);
    } catch (cause) {
      setLastFailedMessage(value);
      setError(cause instanceof Error ? cause.message : "AXENT could not answer right now.");
    } finally {
      setPendingConversationId((current) => current === conversationId ? null : current);
      setIsSubmitting(false);
    }
  }

  function startNewChat(context: AxentContextSnapshot | null = null) {
    setActiveConversationId(null);
    setPendingContext(context);
    setDraft("");
    setError(null);
    setLastFailedMessage(null);
    setResponse(initialResponse(bootstrap));
    setConfirmOpen(false);
    setConfirmAcknowledged(false);
  }

  function selectConversation(conversationId: string) {
    setActiveConversationId(conversationId);
    setPendingContext(null);
    setDraft("");
    setError(null);
    setLastFailedMessage(null);
    setConfirmOpen(false);
    setConfirmAcknowledged(false);
  }

  function retryLastMessage() {
    if (!lastFailedMessage || isSubmitting) return;
    void submit(lastFailedMessage);
  }

  function useConversationAsContext(conversation: AxentConversation) {
    startNewChat({
      sourceConversationId: conversation.id,
      sourceTitle: conversation.title,
      messages: conversation.messages.slice(-8),
    });
  }

  function deleteConversation(conversation: AxentConversation) {
    if (isSubmitting || !window.confirm(`Delete “${conversation.title}”?`)) return;
    setConversations((current) => current.filter((item) => item.id !== conversation.id));
    if (activeConversationId === conversation.id) startNewChat();
  }

  function downloadConversation(conversation: AxentConversation) {
    downloadFile(`${safeFileName(conversation.title)}.txt`, conversationText(conversation), "text/plain;charset=utf-8");
  }

  function exportConversationPdf(conversation: AxentConversation) {
    downloadFile(`${safeFileName(conversation.title)}.pdf`, conversationPdf(conversation), "application/pdf");
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submit();
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submit();
  }

  function reviewWorkspace() {
    setConfirmOpen(true);
    setConfirmAcknowledged(false);
  }

  const isChat = Boolean(activeConversation);

  return <section className={styles.home} data-testid="axent-home">
    <div className={styles.homeGrid}>
      <main className={`${styles.content} ${isChat ? styles.chatContent : ""}`} data-mode={isChat ? "chat" : "welcome"}>
        {!isChat && <div className={styles.hero}>
          <AxentMark large />
          <span className={styles.brandWordmark}>AXENT</span>
          <h1>What are you investigating today?</h1>
          <p>Ask anything about opportunities, suppliers, entities, risk, or procurement.<br />AXENT responds using AXIGNAL knowledge and your context.</p>
        </div>}

        {isChat && <div className={styles.chatThread} role="log" aria-live="polite" aria-label="AXENT conversation">
          {activeMessages.map((message) => <article className={styles.chatMessage} key={message.id} data-role={message.role}><span>{message.role === "user" ? "You" : "AXENT"}</span><p>{message.body}</p>{message.detail ? <small>{message.detail}</small> : null}</article>)}
          {pendingConversationId === activeConversationId && <div className={styles.chatTyping} role="status"><span />AXENT is thinking…</div>}
        </div>}

        {!isChat && pendingContext && <div className={styles.contextChip} role="status">
          <BookOpenCheck size={15} />
          <span>Using context from <strong>{pendingContext.sourceTitle}</strong></span>
          <button type="button" aria-label="Clear reused context" onClick={() => setPendingContext(null)}>Clear</button>
        </div>}

        <form className={`${styles.composer} ${isChat ? styles.chatComposer : ""}`} onSubmit={handleSubmit}>
          <label className={styles.srOnly} htmlFor="axent-composer">Ask AXENT anything about AXIGNAL</label>
          <textarea id="axent-composer" value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={handleComposerKeyDown} placeholder="Ask AXENT anything…" disabled={isSubmitting || !historyReady} rows={3} />
          <div className={styles.composerFooter}><button className={styles.attach} type="button" aria-label="Attach context" onClick={onHelp} disabled={!historyReady}><Paperclip size={17} /></button><span>Shift + Enter for new line</span><button className={styles.send} type="submit" aria-label="Send message" disabled={isSubmitting || !historyReady || !draft.trim()}><Send size={17} /></button></div>
        </form>
        {error && <p className={styles.error} role="alert">{error} {lastFailedMessage ? <button type="button" onClick={retryLastMessage}>Retry</button> : null}</p>}

        {!isChat && <div className={styles.starterGrid} aria-label="Starter questions">
          {STARTERS.map((starter, index) => <button className={styles.starter} key={starter.title} type="button" onClick={() => void submit(starter.prompt)} disabled={isSubmitting || !historyReady}><span className={styles.starterIcon}>{index === 0 ? <ShieldCheck size={19} /> : index === 1 ? <Link2 size={19} /> : <BookOpen size={19} />}</span><span className={styles.starterCopy}><strong>{starter.title}</strong><small>{starter.prompt}</small></span><ArrowRight size={16} /></button>)}
        </div>}

        {!isChat && response.action && <section className={styles.nextStep}><div className={styles.nextStepIcon}><FolderOpen size={24} /></div><div><span>Next step (suggested)</span><strong>{response.action.title}</strong><small>{response.action.description}</small></div><button type="button" onClick={reviewWorkspace}>Open workspace <ArrowRight size={15} /></button>{confirmOpen && <div className={styles.confirmBox}><p>AXENT will only navigate to the selected Workspace. It will not approve requirements or submit anything.</p><label><input type="checkbox" checked={confirmAcknowledged} onChange={(event) => setConfirmAcknowledged(event.target.checked)} />I understand this is a navigation step and I remain the decision-maker.</label><button className={styles.confirmButton} type="button" disabled={!confirmAcknowledged} onClick={() => onOpenWorkspace(response.action!.workspaceId)}><Check size={14} />Confirm and open</button></div>}</section>}

        {!isChat && <footer className={styles.trust}><ShieldCheck size={16} /><strong>AXENT · grounded in AXIGNAL knowledge</strong><CircleHelp size={14} /><span>Responses are evidence-bounded and include sources.<br />They may be incomplete or reflect unknowns where evidence is insufficient.</span></footer>}
      </main>

      <ChatHistory conversations={conversations} activeConversationId={activeConversationId} onSelect={selectConversation} onNewChat={() => startNewChat()} onDelete={deleteConversation} onUseContext={useConversationAsContext} onDownload={downloadConversation} onExportPdf={exportConversationPdf} />
    </div>
  </section>;
}
