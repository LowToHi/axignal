import { expect, test } from "@playwright/test";

type Bootstrap = {
  tenant: { revision: number };
  route_data: {
    workspaces: Array<{
      id: string;
      requirements: Array<{ id: string; evidence_ids: string[] }>;
    }>;
  };
};

async function bootstrap(page: Parameters<typeof test>[0] extends never ? never : any): Promise<Bootstrap> {
  const response = await page.request.get("/api/subscriber-workspace/bootstrap");
  expect(response.status()).toBe(200);
  return response.json() as Promise<Bootstrap>;
}

test("rejects requirement completion without linked verified evidence", async ({ page }) => {
  const state = await bootstrap(page);
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
  const state = await bootstrap(page);
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
