import { expect, test } from "@playwright/test";

type Bootstrap = {
  tenant: { revision: number };
  route_data: {
    workspaces: Array<{
      id: string;
      tasks: Array<{ id: string; owner_id: string | null }>;
    }>;
  };
};

test("renders a persisted workspace event from the append-only audit endpoint", async ({ page }) => {
  const bootstrapResponse = await page.request.get("/api/subscriber-workspace/bootstrap");
  expect(bootstrapResponse.status()).toBe(200);
  const bootstrap = await bootstrapResponse.json() as Bootstrap;
  const workspace = bootstrap.route_data.workspaces[0]!;
  const task = workspace.tasks[0]!;

  const actionResponse = await page.request.post("/api/subscriber-workspace/actions", {
    data: {
      action_id: `ax_action_${crypto.randomUUID().replaceAll("-", "")}`,
      action_type: "task.assign",
      tenant_revision: bootstrap.tenant.revision,
      payload: {
        workspace_id: workspace.id,
        task_id: task.id,
        owner_id: task.owner_id ?? "current_user"
      }
    }
  });
  expect(actionResponse.status()).toBe(200);

  await page.goto(`/workspaces/${workspace.id}/audit`);
  await expect(page.getByRole("heading", { name: "Audit" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "task assigned" }).first()).toBeVisible();
  await expect(page.getByText(`task:${task.id}`).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Create export unavailable" })).toBeDisabled();
});
