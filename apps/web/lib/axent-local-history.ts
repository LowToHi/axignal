export const AXENT_LOCAL_HISTORY_SCHEMA =
  "axignal.axent-local-history/v1" as const;
export const AXENT_LOCAL_HISTORY_RETENTION_DAYS = 30;
export const AXENT_LOCAL_HISTORY_PREFIX =
  "axignal:axent:local-history:v1";
export const AXENT_LEGACY_HISTORY_PREFIX = "axignal:axent:history:v3";

export type AxentLocalHistoryState<T> = {
  conversations: T[];
  activeConversationId: string | null;
};

type AxentLocalHistoryEnvelope<T> = {
  schema_version: typeof AXENT_LOCAL_HISTORY_SCHEMA;
  tenant_id: string;
  identity_id: string;
  saved_at: string;
  expires_at: string;
  conversations: T[];
  active_conversation_id: string | null;
};

type StorageBoundary = Pick<
  Storage,
  "getItem" | "setItem" | "removeItem" | "key" | "length"
>;

function empty<T>(): AxentLocalHistoryState<T> {
  return { conversations: [], activeConversationId: null };
}

export function axentLocalHistoryKey(
  tenantId: string,
  identityId: string
): string {
  return `${AXENT_LOCAL_HISTORY_PREFIX}:${tenantId}:${identityId}`;
}

export function axentLegacyHistoryKey(tenantId: string): string {
  return `${AXENT_LEGACY_HISTORY_PREFIX}:${tenantId}`;
}

export function loadAxentLocalHistory<T>({
  storage,
  tenantId,
  identityId,
  isConversation,
  now = Date.now()
}: {
  storage: StorageBoundary;
  tenantId: string;
  identityId: string;
  isConversation: (value: unknown) => value is T;
  now?: number;
}): AxentLocalHistoryState<T> {
  const key = axentLocalHistoryKey(tenantId, identityId);
  storage.removeItem(axentLegacyHistoryKey(tenantId));
  const raw = storage.getItem(key);
  if (!raw) return empty();

  try {
    const parsed = JSON.parse(raw) as Partial<AxentLocalHistoryEnvelope<unknown>>;
    if (
      parsed.schema_version !== AXENT_LOCAL_HISTORY_SCHEMA ||
      parsed.tenant_id !== tenantId ||
      parsed.identity_id !== identityId ||
      typeof parsed.saved_at !== "string" ||
      typeof parsed.expires_at !== "string" ||
      !Number.isFinite(Date.parse(parsed.saved_at)) ||
      !Number.isFinite(Date.parse(parsed.expires_at)) ||
      Date.parse(parsed.expires_at) <= now ||
      !Array.isArray(parsed.conversations)
    ) {
      storage.removeItem(key);
      return empty();
    }

    const conversations = parsed.conversations
      .filter(isConversation)
      .slice(0, 50);
    const activeConversationId =
      typeof parsed.active_conversation_id === "string" &&
      conversations.some(
        (conversation) =>
          typeof conversation === "object" &&
          conversation !== null &&
          "id" in conversation &&
          conversation.id === parsed.active_conversation_id
      )
        ? parsed.active_conversation_id
        : null;
    return { conversations, activeConversationId };
  } catch {
    storage.removeItem(key);
    return empty();
  }
}

export function saveAxentLocalHistory<T>({
  storage,
  tenantId,
  identityId,
  conversations,
  activeConversationId,
  now = Date.now(),
  retentionDays = AXENT_LOCAL_HISTORY_RETENTION_DAYS
}: {
  storage: StorageBoundary;
  tenantId: string;
  identityId: string;
  conversations: T[];
  activeConversationId: string | null;
  now?: number;
  retentionDays?: number;
}): void {
  const safeRetentionDays = Math.min(Math.max(retentionDays, 1), 30);
  const savedAt = new Date(now);
  const envelope: AxentLocalHistoryEnvelope<T> = {
    schema_version: AXENT_LOCAL_HISTORY_SCHEMA,
    tenant_id: tenantId,
    identity_id: identityId,
    saved_at: savedAt.toISOString(),
    expires_at: new Date(
      savedAt.getTime() + safeRetentionDays * 24 * 60 * 60 * 1000
    ).toISOString(),
    conversations: conversations.slice(0, 50),
    active_conversation_id: activeConversationId
  };
  storage.setItem(
    axentLocalHistoryKey(tenantId, identityId),
    JSON.stringify(envelope)
  );
  storage.removeItem(axentLegacyHistoryKey(tenantId));
}

export function purgeAxentLocalHistory(storage: StorageBoundary): number {
  const keys: string[] = [];
  for (let index = 0; index < storage.length; index += 1) {
    const key = storage.key(index);
    if (
      key &&
      (key.startsWith(`${AXENT_LOCAL_HISTORY_PREFIX}:`) ||
        key.startsWith(`${AXENT_LEGACY_HISTORY_PREFIX}:`))
    ) {
      keys.push(key);
    }
  }
  keys.forEach((key) => storage.removeItem(key));
  return keys.length;
}
