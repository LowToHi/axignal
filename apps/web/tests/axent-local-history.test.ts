import assert from "node:assert/strict";
import test from "node:test";

import {
  AXENT_LOCAL_HISTORY_SCHEMA,
  axentLegacyHistoryKey,
  axentLocalHistoryKey,
  loadAxentLocalHistory,
  purgeAxentLocalHistory,
  saveAxentLocalHistory
} from "../lib/axent-local-history";

type Conversation = { id: string; title: string };

class MemoryStorage {
  private readonly values = new Map<string, string>();

  get length() {
    return this.values.size;
  }

  getItem(key: string) {
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string) {
    this.values.set(key, value);
  }

  removeItem(key: string) {
    this.values.delete(key);
  }

  key(index: number) {
    return Array.from(this.values.keys())[index] ?? null;
  }
}

function isConversation(value: unknown): value is Conversation {
  return Boolean(
    value &&
      typeof value === "object" &&
      "id" in value &&
      typeof value.id === "string" &&
      "title" in value &&
      typeof value.title === "string"
  );
}

test("stores AXENT history per tenant and identity with a bounded expiry", () => {
  const storage = new MemoryStorage();
  const now = Date.parse("2026-08-04T00:00:00.000Z");
  saveAxentLocalHistory({
    storage,
    tenantId: "tenant-a",
    identityId: "user-a",
    conversations: [{ id: "chat-a", title: "Evidence review" }],
    activeConversationId: "chat-a",
    now
  });

  const key = axentLocalHistoryKey("tenant-a", "user-a");
  const envelope = JSON.parse(storage.getItem(key) ?? "null") as {
    schema_version: string;
    tenant_id: string;
    identity_id: string;
    expires_at: string;
  };
  assert.equal(envelope.schema_version, AXENT_LOCAL_HISTORY_SCHEMA);
  assert.equal(envelope.tenant_id, "tenant-a");
  assert.equal(envelope.identity_id, "user-a");
  assert.equal(
    envelope.expires_at,
    "2026-09-03T00:00:00.000Z"
  );

  assert.deepEqual(
    loadAxentLocalHistory({
      storage,
      tenantId: "tenant-a",
      identityId: "user-a",
      isConversation,
      now: now + 1
    }),
    {
      conversations: [{ id: "chat-a", title: "Evidence review" }],
      activeConversationId: "chat-a"
    }
  );
  assert.deepEqual(
    loadAxentLocalHistory({
      storage,
      tenantId: "tenant-a",
      identityId: "user-b",
      isConversation,
      now: now + 1
    }),
    { conversations: [], activeConversationId: null }
  );
});

test("purges legacy, malformed and expired history fail closed", () => {
  const storage = new MemoryStorage();
  storage.setItem(
    axentLegacyHistoryKey("tenant-a"),
    JSON.stringify({ conversations: [{ id: "legacy", title: "Legacy" }] })
  );
  storage.setItem(axentLocalHistoryKey("tenant-a", "user-a"), "not-json");

  assert.deepEqual(
    loadAxentLocalHistory({
      storage,
      tenantId: "tenant-a",
      identityId: "user-a",
      isConversation
    }),
    { conversations: [], activeConversationId: null }
  );
  assert.equal(storage.getItem(axentLegacyHistoryKey("tenant-a")), null);
  assert.equal(storage.getItem(axentLocalHistoryKey("tenant-a", "user-a")), null);

  saveAxentLocalHistory({
    storage,
    tenantId: "tenant-a",
    identityId: "user-a",
    conversations: [{ id: "expired", title: "Expired" }],
    activeConversationId: "expired",
    now: 0,
    retentionDays: 1
  });
  assert.deepEqual(
    loadAxentLocalHistory({
      storage,
      tenantId: "tenant-a",
      identityId: "user-a",
      isConversation,
      now: 2 * 24 * 60 * 60 * 1000
    }),
    { conversations: [], activeConversationId: null }
  );
});

test("logout purge removes only AXENT local history namespaces", () => {
  const storage = new MemoryStorage();
  storage.setItem(axentLegacyHistoryKey("tenant-a"), "legacy");
  storage.setItem(axentLocalHistoryKey("tenant-a", "user-a"), "current");
  storage.setItem("unrelated", "keep");

  assert.equal(purgeAxentLocalHistory(storage), 2);
  assert.equal(storage.getItem("unrelated"), "keep");
  assert.equal(storage.length, 1);
});
