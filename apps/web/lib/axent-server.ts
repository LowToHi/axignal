import type { SubscriberWorkspaceError } from "./subscriber-workspace-contract";
import {
  resolveSubscriberWorkspaceActor,
  type SubscriberWorkspaceServerActor,
  type SubscriberWorkspaceServerResult
} from "./subscriber-workspace-server";
import { buildApiIdentityAssertion } from "./server-auth";

export type AxentConversationSummary = {
  conversation_id: string;
  title: string;
  retention_class: "EPHEMERAL_30D" | "STANDARD_90D";
  retention_until: string;
  state: "ACTIVE" | "DELETION_REQUESTED";
  message_count?: number;
  created_at: string;
  updated_at: string;
};

export type AxentMessage = {
  message_id: string;
  ordinal: number;
  role: "USER" | "ASSISTANT" | "SYSTEM";
  content: string;
  content_hash: string;
  created_at: string;
};

export type AxentConversationExport = {
  schema: "axignal.axent-conversation-export.v1";
  conversation_id: string;
  tenant_id: string;
  identity_subject: string;
  title: string;
  retention_class: "EPHEMERAL_30D" | "STANDARD_90D";
  retention_until: string;
  state: "ACTIVE" | "DELETION_REQUESTED";
  messages: AxentMessage[];
  exported_at: string;
};

export type AxentConversationList = {
  schema: "axignal.axent-conversation-list.v1";
  conversations: AxentConversationSummary[];
};

type AxentConversationCreate = {
  request_id: string;
  title: string;
  retention_class: "EPHEMERAL_30D" | "STANDARD_90D";
};

type AxentMessageCreate = {
  request_id: string;
  role: "USER" | "ASSISTANT" | "SYSTEM";
  content: string;
};

function upstreamBaseUrl(): string | null {
  const value =
    process.env.AXIGNAL_SUBSCRIBER_WORKSPACE_API_URL ?? process.env.AXIGNAL_API_URL;
  if (!value) return null;
  try {
    const parsed = new URL(value);
    if (!["http:", "https:"].includes(parsed.protocol)) return null;
    return parsed.toString().replace(/\/$/, "");
  } catch {
    return null;
  }
}

function errorResult(
  status: number,
  error: string,
  code: SubscriberWorkspaceError["code"]
): SubscriberWorkspaceServerResult<never> {
  return {
    status,
    body: {
      error,
      code,
      state: status === 401 ? "restricted" : "source_unavailable",
      recoverable: status >= 500
    }
  };
}

async function actorResult(): Promise<
  SubscriberWorkspaceServerActor | SubscriberWorkspaceServerResult<never>
> {
  try {
    const actor = await resolveSubscriberWorkspaceActor();
    if (!actor?.authenticatedIdentity) {
      return errorResult(401, "Authentication required.", "authentication_required");
    }
    return actor;
  } catch {
    return errorResult(
      503,
      "AXENT identity authority is unavailable.",
      "source_unavailable"
    );
  }
}

function isResult(
  value: SubscriberWorkspaceServerActor | SubscriberWorkspaceServerResult<never>
): value is SubscriberWorkspaceServerResult<never> {
  return "status" in value;
}

async function axentUpstreamRequest<T>(
  actor: SubscriberWorkspaceServerActor,
  pathName: string,
  init?: RequestInit
): Promise<SubscriberWorkspaceServerResult<T>> {
  const baseUrl = upstreamBaseUrl();
  if (!baseUrl || !actor.authenticatedIdentity) {
    return errorResult(
      503,
      "AXENT persistence authority is unavailable.",
      "source_unavailable"
    );
  }
  try {
    const headers = new Headers(init?.headers);
    headers.set("accept", "application/json");
    if (init?.body) headers.set("content-type", "application/json");
    headers.set(
      "X-AXIGNAL-Identity-Assertion",
      buildApiIdentityAssertion(actor.authenticatedIdentity)
    );
    const response = await fetch(
      `${baseUrl}/v1/subscriber-workspace/axent${pathName}`,
      {
        ...init,
        headers,
        cache: "no-store",
        signal: AbortSignal.timeout(10_000)
      }
    );
    const body = (await response.json().catch(() => ({
      error: "Invalid AXENT upstream response.",
      code: "upstream_error",
      state: "recoverable_error",
      recoverable: true
    }))) as T | SubscriberWorkspaceError;
    return { status: response.status, body };
  } catch {
    return errorResult(
      503,
      "AXENT persistence authority is unavailable.",
      "source_unavailable"
    );
  }
}

export async function axentListResult(): Promise<
  SubscriberWorkspaceServerResult<AxentConversationList>
> {
  const actor = await actorResult();
  if (isResult(actor)) return actor;
  return axentUpstreamRequest<AxentConversationList>(actor, "/conversations");
}

export async function axentCreateResult(
  command: AxentConversationCreate
): Promise<SubscriberWorkspaceServerResult<AxentConversationSummary>> {
  const actor = await actorResult();
  if (isResult(actor)) return actor;
  return axentUpstreamRequest<AxentConversationSummary>(actor, "/conversations", {
    method: "POST",
    body: JSON.stringify(command)
  });
}

export async function axentExportResult(
  conversationId: string
): Promise<SubscriberWorkspaceServerResult<AxentConversationExport>> {
  const actor = await actorResult();
  if (isResult(actor)) return actor;
  return axentUpstreamRequest<AxentConversationExport>(
    actor,
    `/conversations/${encodeURIComponent(conversationId)}`
  );
}

export async function axentAppendMessageResult(
  conversationId: string,
  command: AxentMessageCreate
): Promise<SubscriberWorkspaceServerResult<Record<string, unknown>>> {
  const actor = await actorResult();
  if (isResult(actor)) return actor;
  return axentUpstreamRequest<Record<string, unknown>>(
    actor,
    `/conversations/${encodeURIComponent(conversationId)}/messages`,
    { method: "POST", body: JSON.stringify(command) }
  );
}

export async function axentDeleteResult(
  conversationId: string,
  deleteAfter: string
): Promise<SubscriberWorkspaceServerResult<Record<string, unknown>>> {
  const actor = await actorResult();
  if (isResult(actor)) return actor;
  return axentUpstreamRequest<Record<string, unknown>>(
    actor,
    `/conversations/${encodeURIComponent(conversationId)}`,
    { method: "DELETE", body: JSON.stringify({ delete_after: deleteAfter }) }
  );
}
