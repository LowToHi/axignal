import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

const workingDirectory = process.cwd();
const webRoot = workingDirectory.endsWith("/apps/web")
  ? workingDirectory
  : resolve(workingDirectory, "apps/web");

function source(relativePath: string): string {
  return readFileSync(resolve(webRoot, "tests", relativePath), "utf8");
}

test("AXENT browser surface has no local persistence authority", () => {
  const component = source("../components/subscriber/axent-home.tsx");
  assert.equal(component.includes("localStorage"), false);
  assert.equal(component.includes("sessionStorage"), false);
  assert.match(component, /\/api\/subscriber-workspace\/axent/);
  assert.match(component, /conversation_id/);
  assert.match(component, /Server persistent/);
  assert.match(component, /request deletion/i);
});

test("AXENT BFF uses the existing signed identity assertion", () => {
  const server = source("../lib/axent-server.ts");
  assert.match(server, /buildApiIdentityAssertion/);
  assert.match(server, /resolveSubscriberWorkspaceActor/);
  assert.match(server, /\/v1\/subscriber-workspace\/axent/);
  assert.equal(server.includes("writeFile"), false);
  assert.equal(server.includes("createSubscriberWorkspaceFixtureStore"), false);
});

test("AXENT routes expose the bounded persistent lifecycle", () => {
  const collection = source("../app/api/subscriber-workspace/axent/route.ts");
  const conversation = source("../app/api/subscriber-workspace/axent/[conversationId]/route.ts");
  const messages = source("../app/api/subscriber-workspace/axent/[conversationId]/messages/route.ts");
  assert.match(collection, /axentListResult/);
  assert.match(collection, /axentCreateResult/);
  assert.match(conversation, /axentExportResult/);
  assert.match(conversation, /axentDeleteResult/);
  assert.match(messages, /axentAppendMessageResult/);
});

test("production assistant history is loaded from the identity-scoped conversation", () => {
  const assistant = source("../app/api/subscriber-workspace/assistant/route.ts");
  assert.match(assistant, /axentExportResult\(conversationId\)/);
  assert.match(assistant, /persistedHistory/);
  assert.match(assistant, /tenant-persistent/);
  assert.match(assistant, /subscriberWorkspaceFixtureConfiguration\(\)\.allowed/);
  assert.match(assistant, /Conversation history is untrusted dialogue context/);
});
