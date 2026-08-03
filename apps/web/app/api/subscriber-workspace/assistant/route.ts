import { NextResponse } from "next/server";

import type { SubscriberWorkspaceBootstrap } from "@/lib/subscriber-workspace-contract";
import { subscriberWorkspaceBootstrapResult, subscriberWorkspaceEnabled } from "@/lib/subscriber-workspace-server";

export const dynamic = "force-dynamic";

const MAX_MESSAGE_BYTES = 16 * 1024;
const MAX_MESSAGE_LENGTH = 4_000;
const IN_SCOPE_TERMS = [
  "axignal",
  "axent",
  "opportun",
  "workspace",
  "evidence",
  "investig",
  "methodolog",
  "source",
  "claim",
  "requirement",
  "alert",
  "report",
  "onboard",
  "help",
  "support",
  "how does"
];

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

type AssistantResponse = {
  reply: string;
  context: AssistantContext;
  evidence: EvidenceCard[];
  action: { workspaceId: string; title: string; description: string } | null;
  mode: "fixture" | "upstream";
};

type AssistantHistoryItem = {
  role: "user" | "assistant";
  content: string;
};

function jsonError(error: string, code: string, status: number) {
  return NextResponse.json({ error, code, state: "rejected", recoverable: status >= 500 }, { status, headers: { "cache-control": "no-store" } });
}

function contextFor(bootstrap: SubscriberWorkspaceBootstrap): AssistantContext {
  const opportunity = bootstrap.route_data.opportunities[0];
  const workspace = bootstrap.route_data.workspaces[0];
  return {
    scope: opportunity?.title ?? "AXIGNAL opportunity intelligence",
    jurisdiction: opportunity?.jurisdiction ?? "Tenant scope",
    entities: [opportunity?.buyer, workspace?.title].filter(Boolean).join(" · ") || "No entities selected",
    framework: "AXIGNAL epistemic claims, source rights and subscriber authority"
  };
}

function evidenceFor(bootstrap: SubscriberWorkspaceBootstrap): EvidenceCard[] {
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

function fixtureReply(message: string, bootstrap: SubscriberWorkspaceBootstrap): string {
  const lower = message.toLowerCase();
  if (lower.includes("evidence") || lower.includes("source") || lower.includes("claim")) {
    return "Start with the evidence rail. AXIGNAL keeps facts, inferences, contradictions and unknowns separate, so you can inspect the source and confidence before deciding what to do next.";
  }
  if (lower.includes("workspace") || lower.includes("onboard") || lower.includes("empez")) {
    return "I can take you into the prepared Workspace after you review the proposed context. Opening it is only navigation; requirements, approvals and external actions remain under subscriber authority.";
  }
  if (lower.includes("help") || lower.includes("how") || lower.includes("support")) {
    return "I can explain the Shell, help you find a destination, or show how AXIGNAL treats evidence and uncertainty. Ask in your own words and I will keep the answer grounded in the current tenant context.";
  }
  return `I have scoped your question to ${bootstrap.route_data.opportunities[0]?.title ?? "the current AXIGNAL context"}. I will use the available source-pinned context, show what is known and unknown, and suggest a reversible next step rather than making a decision for you.`;
}

function assistantResponse(message: string, bootstrap: SubscriberWorkspaceBootstrap, mode: "fixture" | "upstream", reply: string): AssistantResponse {
  const workspace = bootstrap.route_data.workspaces[0];
  return {
    reply,
    context: contextFor(bootstrap),
    evidence: evidenceFor(bootstrap),
    action: workspace ? {
      workspaceId: workspace.id,
      title: "Continue in your prepared Workspace",
      description: "Open the current evidence-governed context so you can review requirements and blockers."
    } : null,
    mode
  };
}

function deepSeekEnabled() {
  return ["1", "true", "yes", "on"].includes((process.env.AXIGNAL_AXENT_ASSISTANT_DEEPSEEK_ENABLED ?? "").trim().toLowerCase()) && Boolean(process.env.DEEPSEEK_API_KEY);
}

async function deepSeekReply(message: string, bootstrap: SubscriberWorkspaceBootstrap, history: AssistantHistoryItem[]): Promise<string | null> {
  if (!deepSeekEnabled()) return null;
  const baseUrl = process.env.AXIGNAL_DEEPSEEK_BASE_URL ?? "https://api.deepseek.com";
  const parsed = new URL(baseUrl);
  if (parsed.protocol !== "https:" || parsed.hostname !== "api.deepseek.com" || parsed.pathname !== "/") return null;
  const evidence = evidenceFor(bootstrap).map((item) => `${item.kind}: ${item.statement} (source: ${item.source}; confidence: ${item.confidence ?? "unknown"})`).join("\n");
  const system = [
    "You are AXENT, the bounded AXIGNAL subscriber assistant.",
    "Answer only about AXIGNAL investigations, evidence, opportunities, workspaces, methodology, onboarding and support.",
    "Use the supplied AXIGNAL context as retrieval-grounded evidence. Do not invent sources, scores, actions or external outcomes.",
    "Facts, inferences, contradictions and unknowns must remain distinct. Explain uncertainty when it matters.",
    "You may suggest navigation, but never approve, send, sign, submit or change anything.",
    `Retrieved AXIGNAL context:\n${evidence}`
  ].join("\n\n");
  try {
    const response = await fetch(`${baseUrl.replace(/\/$/, "")}/chat/completions`, {
      method: "POST",
      headers: { "content-type": "application/json", authorization: `Bearer ${process.env.DEEPSEEK_API_KEY}` },
      body: JSON.stringify({ model: process.env.AXIGNAL_DEEPSEEK_MODEL ?? "deepseek-v4-flash", temperature: 0.1, max_tokens: 700, messages: [{ role: "system", content: system }, ...history, { role: "user", content: message }] }),
      cache: "no-store",
      signal: AbortSignal.timeout(20_000)
    });
    const body = await response.json().catch(() => null) as { choices?: Array<{ message?: { content?: unknown } }> } | null;
    const content = body?.choices?.[0]?.message?.content;
    return response.ok && typeof content === "string" && content.trim() ? content.trim().slice(0, 4_000) : null;
  } catch {
    return null;
  }
}

export async function POST(request: Request) {
  if (!subscriberWorkspaceEnabled()) return jsonError("Subscriber workspace is disabled.", "not_found", 404);
  const contentLength = Number(request.headers.get("content-length") ?? "0");
  if (Number.isFinite(contentLength) && contentLength > MAX_MESSAGE_BYTES) return jsonError("Assistant request is too large.", "invalid_request", 413);
  const raw = await request.text();
  if (Buffer.byteLength(raw, "utf8") > MAX_MESSAGE_BYTES) return jsonError("Assistant request is too large.", "invalid_request", 413);
  let input: unknown;
  try { input = JSON.parse(raw); } catch { return jsonError("Invalid JSON assistant request.", "invalid_request", 400); }
  const message = typeof input === "object" && input !== null && "message" in input && typeof input.message === "string" ? input.message.trim() : "";
  if (!message || message.length > MAX_MESSAGE_LENGTH) return jsonError("Message must be between 1 and 4,000 characters.", "invalid_request", 400);
  if (!IN_SCOPE_TERMS.some((term) => message.toLowerCase().includes(term))) return jsonError("AXENT is limited to AXIGNAL product, research, evidence and support questions.", "out_of_scope", 422);

  const history = typeof input === "object" && input !== null && "history" in input && Array.isArray(input.history)
    ? input.history.filter((item): item is { role: string; content: string } => Boolean(item) && typeof item === "object" && typeof item.role === "string" && typeof item.content === "string").slice(-10).map((item) => ({ role: item.role === "assistant" ? "assistant" as const : "user" as const, content: item.content.trim().slice(0, 1_200) })).filter((item) => item.content)
    : [];

  const bootstrapResult = await subscriberWorkspaceBootstrapResult();
  if (bootstrapResult.status < 200 || bootstrapResult.status >= 300) return NextResponse.json(bootstrapResult.body, { status: bootstrapResult.status, headers: { "cache-control": "no-store" } });
  const bootstrap = bootstrapResult.body as SubscriberWorkspaceBootstrap;
  const liveReply = await deepSeekReply(message, bootstrap, history);
  const response = assistantResponse(message, bootstrap, liveReply ? "upstream" : "fixture", liveReply ?? fixtureReply(message, bootstrap));
  return NextResponse.json(response, { status: 200, headers: { "cache-control": "no-store", "x-axignal-ai-authority": "proposal-only" } });
}
