import { expect, test, type Page } from "@playwright/test";

type Bootstrap = {
  tenant: { revision: number };
  route_data: {
    summary: { deadlines_next_30_days: number };
    workspaces: Array<{
      id: string;
      deadline: string;
      requirements: Array<{ id: string; evidence_ids: string[] }>;
    }>;
  };
};

async function loadBootstrap(page: Page): Promise<Bootstrap> {
  const response = await page.request.get("/api/subscriber-workspace/bootstrap");
  expect(response.status()).toBe(200);
  return response.json() as Promise<Bootstrap>;
}

test("derives the thirty-day deadline summary from actual workspace deadlines", async ({ page }) => {
  const state = await loadBootstrap(page);
  const now = Date.now();
  const horizon = now + 30 * 24 * 60 * 60 * 1_000;
  const expected = state.route_data.workspaces.filter((workspace) => {
    const deadline = Date.parse(workspace.deadline);
    return Number.isFinite(deadline) && deadline >= now && deadline <= horizon;
  }).length;

  expect(state.route_data.summary.deadlines_next_30_days).toBe(expected);
});

test("rejects requirement completion without linked verified evidence", async ({ page }) => {
  const state = await loadBootstrap(page);
  const workspace = state.route_data.workspaces[0]!;
  const requirement = workspace.requirements.find((item) => item.evidence_ids.length === 0)!;

  const response = await page.request.post("/api/subscriber-workspace/actions", {
    data: {
      action_id: `ax_action_${crypto.randomUUID().replaceAll("-", "")}`,
      action_type: "requirement.update",
      tenant_revision: state.tenant.revision,
      payload: {
        workspace_id: workspace.id,
        requirement_id: requirement.id,
        status: "met"
      }
    }
  });

  expect(response.status()).toBe(409);
  await expect(response.json()).resolves.toMatchObject({
    code: "state_conflict",
    state: "rejected",
    recoverable: false
  });
});

test("rejects submission preparation while readiness blockers remain", async ({ page }) => {
  const state = await loadBootstrap(page);
  const workspace = state.route_data.workspaces[0]!;

  const response = await page.request.post("/api/subscriber-workspace/actions", {
    data: {
      action_id: `ax_action_${crypto.randomUUID().replaceAll("-", "")}`,
      action_type: "submission.prepare",
      tenant_revision: state.tenant.revision,
      payload: { workspace_id: workspace.id }
    }
  });

  expect(response.status()).toBe(409);
  await expect(response.json()).resolves.toMatchObject({
    code: "state_conflict",
    state: "rejected",
    recoverable: false
  });
});
