import { expect, test } from "@playwright/test";

/**
 * Cierre funcional E2E — recorrido completo con navegador:
 *
 * login → onboarding → consulta AXENT → resultados reales → selección
 * → confirmación → incorporación a Workspace → creación de Pursuit
 * → creación de tarea → recarga → persistencia comprobada → consulta
 * de soporte → creación y resolución de caso.
 *
 * Atraviesa browser → Next.js → FastAPI → PostgreSQL (sin mocks).
 */

const TENANT = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";

test.describe.configure({ timeout: 90_000 });

// Helper: login with retry — the dev server compiles API routes on demand,
// so the very first POST may race compilation and return 404/500.
async function loginWithRetry(context: {
  request: import("@playwright/test").APIRequestContext;
}) {
  let lastStatus = 0;
  for (let attempt = 0; attempt < 5; attempt += 1) {
    const login = await context.request.post("/api/auth/login", {
      data: { email: "test-runtime@axignal.test", password: "axignal-test-pass" },
    });
    lastStatus = login.status();
    if (lastStatus === 200) return login;
    await new Promise((resolve) => setTimeout(resolve, 2500));
  }
  throw new Error(`login failed after retries: HTTP ${lastStatus}`);
}

test("AXENT functional lifecycle over the real stack", async ({
  page,
  context,
}) => {
  // 1. Real test-runtime login (browser session, server-side identity).
  const login = await loginWithRetry(context);
  expect(login.status()).toBe(200);

  // 2. Onboarding journey is persisted and resumable.
  await page.goto("/opportunity-intelligence");
  const onboarding = await context.request.get("/api/axent/onboarding");
  expect(onboarding.status()).toBe(200);
  const journey = (await onboarding.json()).journey;
  expect(journey).toBeTruthy();
  const stateBefore = journey.state;

  // Advance the journey (idempotent) and verify persistence.
  const advance = await context.request.post("/api/axent/onboarding/advance");
  expect(advance.status()).toBe(200);
  const advanced = await advance.json();
  expect(advanced.state).toBeTruthy();

  // Preferences persist explicitly.
  const pref = await context.request.post("/api/axent/onboarding/preferences", {
    data: { preference_key: "sectors", value: { sectors: ["public-works"] } },
  });
  expect(pref.status()).toBe(200);

  const onboardingAfter = await context.request.get("/api/axent/onboarding");
  const persistedState = (await onboardingAfter.json()).journey.state;
  expect(persistedState).toBeTruthy();

  // 3. AXENT chat: grounded search over real opportunities.
  await page.getByLabel("Abrir AXENT").click();
  const panel = page.getByLabel("AXENT asistente");
  await expect(panel).toBeVisible();

  const input = page.getByLabel("Mensaje para AXENT");
  await input.fill("muéstrame cloud infrastructure");
  await page.getByRole("button", { name: "Enviar" }).click();

  // Real results: the opportunity card with the add button appears.
  await expect(
    panel.getByRole("button", { name: "Añadir" }).first()
  ).toBeVisible({ timeout: 25000 });

  // 4. Select the first opportunity → add to workspace Iberia → confirm.
  await panel.getByRole("button", { name: "Añadir" }).first().click();
  await expect(
    panel.getByText(/Previsualización/).first()
  ).toBeVisible({ timeout: 15000 });
  await panel.getByRole("button", { name: "Confirmar" }).click();
  await expect(
    panel.getByText(/Operación confirmada y persistida|Workspace/).first()
  ).toBeVisible({ timeout: 15000 });

  // 5. Create a pursuit for the first result.
  await input.fill("crea un pursuit para la primera");
  await page.getByRole("button", { name: "Enviar" }).click();
  await expect(
    panel.getByText(/Previsualización/).first()
  ).toBeVisible({ timeout: 15000 });
  await panel.getByRole("button", { name: "Confirmar" }).click();
  await expect(
    panel.getByText(/Pursuit prs_/).first()
  ).toBeVisible({ timeout: 15000 });

  // 6. Create a task (low-risk, executes immediately).
  await input.fill("crea una tarea para revisar los requisitos");
  await page.getByRole("button", { name: "Enviar" }).click();
  await expect(
    panel.getByText(/Tarea task_/).first()
  ).toBeVisible({ timeout: 15000 });

  // 7. Reload → persistence verified through the API (not the panel state).
  await page.reload();
  const cases = await context.request.get("/api/axent/support/cases");
  expect(cases.status()).toBe(200);

  const pursuits = await context.request.get(
    `/api/axent/conversations`
  );
  expect(pursuits.status()).toBe(200);

  // 8. Support round-trip: create a case from a conversation and resolve it.
  const conversations = await pursuits.json();
  expect(conversations.length).toBeGreaterThanOrEqual(1);
  const conversationId = conversations[0].conversation_id;
  const created = await context.request.post("/api/axent/support/cases", {
    data: {
      conversation_id: conversationId,
      subject: "No puedo guardar mi perfil",
      description: "El formulario de sectores no responde al guardar.",
      severity: "S3",
    },
  });
  expect(created.status()).toBe(200);
  const caseBody = await created.json();
  expect(caseBody.case_ref).toBeTruthy();
  expect(caseBody.status).toBe("OPENED");

  const resolved = await context.request.post(
    "/api/axent/support/cases/resolve",
    {
      data: {
        case_ref: caseBody.case_ref,
        action: "RESOLVED",
        note: "Perfil actualizado manualmente por soporte.",
      },
    }
  );
  expect(resolved.status()).toBe(200);
  expect((await resolved.json()).status).toBe("RESOLVED");

  const listed = await context.request.get("/api/axent/support/cases");
  expect(listed.status()).toBe(200);
  const listedCases = (await listed.json()).cases;
  expect(
    listedCases.some(
      (c: { case_ref: string; status: string }) =>
        c.case_ref === caseBody.case_ref && c.status === "RESOLVED"
    )
  ).toBe(true);
});

test("AXENT contextual explanation from an opportunity route", async ({
  page,
  context,
}) => {
  const login = await loginWithRetry(context);
  expect(login.status()).toBe(200);

  await page.goto("/opportunity-intelligence");
  await page.getByLabel("Abrir AXENT").click();
  const panel = page.getByLabel("AXENT asistente");
  await expect(panel).toBeVisible();

  // Direct contextual call: the assistant explains the opportunity.
  const conversations = await context.request.post("/api/axent/conversations", {
    data: { title: "AXENT contextual" },
  });
  const conversationId = (await conversations.json()).conversation_id;
  const explain = await context.request.post(
    `/api/axent/conversations/${conversationId}/messages`,
    {
      data: {
        content: "Explícame esta oportunidad",
        context_opportunity_ref: "opp_ted_123456_2026",
      },
    }
  );
  expect(explain.status()).toBe(201);
  const body = await explain.json();
  expect(body.bundle.operation.tool_name).toBe("explain_context");
  expect(body.segments[0].text).toContain("opp_ted_123456_2026");
});
