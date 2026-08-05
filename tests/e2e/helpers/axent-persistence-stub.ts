import type { Page, Route } from "@playwright/test";

type StubMessage = {
  message_id: string;
  ordinal: number;
  role: "USER" | "ASSISTANT" | "SYSTEM";
  content: string;
  content_hash: string;
  created_at: string;
};

type StubConversation = {
  conversation_id: string;
  title: string;
  retention_class: "EPHEMERAL_30D" | "STANDARD_90D";
  retention_until: string;
  state: "ACTIVE" | "DELETION_REQUESTED";
  created_at: string;
  updated_at: string;
  messages: StubMessage[];
};

type AssistantRequest = Record<string, unknown>;

type AxentPersistenceStub = {
  assistantRequests: AssistantRequest[];
  createRequests: Array<Record<string, unknown>>;
  deleteRequests: string[];
  conversations: () => StubConversation[];
};

const COLLECTION_PATH = "/api/subscriber-workspace/axent";
const CONVERSATION_PATH = /^\/api\/subscriber-workspace\/axent\/([^/]+)$/;
const MESSAGES_PATH = /^\/api\/subscriber-workspace\/axent\/([^/]+)\/messages$/;
const AXENT_API_PATH = /\/api\/subscriber-workspace\/axent(?:\/.*)?(?:\?.*)?$/;

function timestamp(sequence: number): string {
  return new Date(Date.UTC(2026, 7, 5, 9, sequence, 0)).toISOString();
}

function conversationId(sequence: number): string {
  return `00000000-0000-4000-8000-${String(sequence).padStart(12, "0")}`;
}

function summary(conversation: StubConversation) {
  return {
    conversation_id: conversation.conversation_id,
    title: conversation.title,
    retention_class: conversation.retention_class,
    retention_until: conversation.retention_until,
    state: conversation.state,
    message_count: conversation.messages.length,
    created_at: conversation.created_at,
    updated_at: conversation.updated_at,
  };
}

async function fulfillJson(
  route: Route,
  body: unknown,
  status = 200,
  headers: Record<string, string> = {},
): Promise<void> {
  await route.fulfill({
    status,
    contentType: "application/json",
    headers: { "cache-control": "no-store", ...headers },
    body: JSON.stringify(body),
  });
}

export async function installAxentPersistenceStub(
  page: Page,
): Promise<AxentPersistenceStub> {
  const conversations = new Map<string, StubConversation>();
  const assistantRequests: AssistantRequest[] = [];
  const createRequests: Array<Record<string, unknown>> = [];
  const deleteRequests: string[] = [];
  let sequence = 0;

  await page.route(AXENT_API_PATH, async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;

    if (path === COLLECTION_PATH) {
      if (request.method() === "GET") {
        const summaries = [...conversations.values()]
          .sort((left, right) => right.updated_at.localeCompare(left.updated_at))
          .map(summary);
        await fulfillJson(route, {
          schema: "axignal.axent-conversation-list.v1",
          conversations: summaries,
        });
        return;
      }

      if (request.method() === "POST") {
        const body = request.postDataJSON() as Record<string, unknown>;
        createRequests.push(body);
        sequence += 1;
        const now = timestamp(sequence);
        const id = conversationId(sequence);
        const conversation: StubConversation = {
          conversation_id: id,
          title: String(body.title),
          retention_class: body.retention_class === "EPHEMERAL_30D"
            ? "EPHEMERAL_30D"
            : "STANDARD_90D",
          retention_until: "2026-11-03T09:00:00.000Z",
          state: "ACTIVE",
          created_at: now,
          updated_at: now,
          messages: [],
        };
        conversations.set(id, conversation);
        await fulfillJson(route, summary(conversation), 201);
        return;
      }
    }

    const messagesMatch = path.match(MESSAGES_PATH);
    if (messagesMatch && request.method() === "POST") {
      const conversation = conversations.get(messagesMatch[1]);
      if (!conversation) {
        await fulfillJson(route, { error: "Conversation not found." }, 404);
        return;
      }
      const body = request.postDataJSON() as Record<string, unknown>;
      sequence += 1;
      const message: StubMessage = {
        message_id: conversationId(sequence),
        ordinal: conversation.messages.length + 1,
        role: body.role === "ASSISTANT" ? "ASSISTANT" : body.role === "SYSTEM" ? "SYSTEM" : "USER",
        content: String(body.content),
        content_hash: `sha256:${sequence}`,
        created_at: timestamp(sequence),
      };
      conversation.messages.push(message);
      conversation.updated_at = message.created_at;
      await fulfillJson(route, {
        conversation_id: conversation.conversation_id,
        message_id: message.message_id,
        ordinal: message.ordinal,
      }, 201);
      return;
    }

    const conversationMatch = path.match(CONVERSATION_PATH);
    if (conversationMatch) {
      const conversation = conversations.get(conversationMatch[1]);
      if (!conversation) {
        await fulfillJson(route, { error: "Conversation not found." }, 404);
        return;
      }
      if (request.method() === "GET") {
        await fulfillJson(route, {
          schema: "axignal.axent-conversation-export.v1",
          conversation_id: conversation.conversation_id,
          tenant_id: "11111111-1111-4111-8111-111111111111",
          identity_subject: "usr_pilot_ci",
          title: conversation.title,
          retention_class: conversation.retention_class,
          retention_until: conversation.retention_until,
          state: conversation.state,
          messages: conversation.messages,
          exported_at: timestamp(sequence + 1),
        });
        return;
      }
      if (request.method() === "DELETE") {
        deleteRequests.push(conversation.conversation_id);
        conversations.delete(conversation.conversation_id);
        await fulfillJson(route, {
          conversation_id: conversation.conversation_id,
          state: "DELETION_REQUESTED",
        });
        return;
      }
    }

    await fulfillJson(route, { error: "Unhandled AXENT persistence request." }, 501);
  });

  await page.route("**/api/subscriber-workspace/assistant", async (route) => {
    const body = route.request().postDataJSON() as AssistantRequest;
    assistantRequests.push(body);
    await fulfillJson(
      route,
      {
        reply: "Start with the evidence rail. Deterministic guidance mode — no live model response was used.",
        context: {
          scope: "AXIGNAL workspace",
          jurisdiction: "Tenant scope",
          entities: "Subscriber",
          framework: "Evidence governed",
        },
        evidence: [],
        action: null,
        mode: "fixture",
      },
      200,
      {
        "x-axignal-ai-authority": "proposal-only",
        "x-axignal-assistant-mode": "fixture",
      },
    );
  });

  return {
    assistantRequests,
    createRequests,
    deleteRequests,
    conversations: () => [...conversations.values()],
  };
}
