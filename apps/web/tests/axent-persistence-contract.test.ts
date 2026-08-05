import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const workingDirectory = process.cwd();
const repositoryRoot = workingDirectory.endsWith("/apps/web")
  ? `${workingDirectory}/../..`
  : workingDirectory;

const readRepositoryFile = (relativePath: string): string =>
  readFileSync(`${repositoryRoot}/${relativePath}`, "utf8");

test("AXENT client persists history only through the authenticated BFF", () => {
  const source = readRepositoryFile("apps/web/components/subscriber/axent-home.tsx");

  assert.match(
    source,
    /fetch\(`\/api\/subscriber-workspace\/axent\?\$\{query\.toString\(\)\}`/,
  );
  assert.match(source, /method:\s*"POST"/);
  assert.match(source, /method:\s*"PATCH"/);
  assert.match(source, /method:\s*"DELETE"/);
  assert.match(source, /credentials:\s*"same-origin"/);
  assert.doesNotMatch(source, /localStorage\.getItem/);
  assert.doesNotMatch(source, /localStorage\.setItem/);
  assert.doesNotMatch(source, /localStorage\.removeItem/);
  assert.doesNotMatch(source, /AXIGNAL_AXENT_HISTORY/);
});

test("AXENT API routes forward identity context through the persistent server boundary", () => {
  const collectionRoute = readRepositoryFile(
    "apps/web/app/api/subscriber-workspace/axent/route.ts",
  );
  const conversationRoute = readRepositoryFile(
    "apps/web/app/api/subscriber-workspace/axent/[conversationId]/route.ts",
  );
  const messagesRoute = readRepositoryFile(
    "apps/web/app/api/subscriber-workspace/axent/[conversationId]/messages/route.ts",
  );

  for (const source of [collectionRoute, conversationRoute, messagesRoute]) {
    assert.match(source, /resolveRequestIdentity/);
  }
  assert.match(collectionRoute, /listPersistentAxentConversations/);
  assert.match(collectionRoute, /createPersistentAxentConversation/);
  assert.match(conversationRoute, /updatePersistentAxentConversation/);
  assert.match(conversationRoute, /deletePersistentAxentConversation/);
  assert.match(messagesRoute, /appendPersistentAxentMessage/);
});
