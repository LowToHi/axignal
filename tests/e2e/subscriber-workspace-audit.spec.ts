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

type ActionResult = {
  tenant_revision: number;
  event: {
    type: string;
    object_type: string;
    object_id: string;
  } | null;
};

test("renders precise persisted workspace events from the append-only audit endpoint", async ({
  page
}) => {
  const bootstrapResponse = await page.request.get(
    "/api/subscriber-workspace/bootstrap"
  );
  expect(bootstrapResponse.status()).toBe(200);
  const bootstrap = (await bootstrapResponse.json()) as Bootstrap;
  const workspace = bootstrap.route_data.workspaces[0]!;
  const task = workspace.tasks[0]!;

  const taskResponse = await page.request.post(
    "/api/subscriber-workspace/actions",
    {
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
    }
  );
  expect(taskResponse.status()).toBe(200);
  const taskResult = (await taskResponse.json()) as ActionResult;
  expect(taskResult.event?.type).toBe("task.assigned");

  const clarificationResponse = await page.request.post(
    "/api/subscriber-workspace/actions",
    {
      data: {
        action_id: `ax_action_${crypto.randomUUID().replaceAll("-", "")}`,
        action_type: "clarification.draft",
        tenant_revision: taskResult.tenant_revision,
        payload: {
          workspace_id: workspace.id,
          question: "Which assurance evidence is mandatory?",
          rationale: "The requirement must be resolved before qualification."
        }
      }
    }
  );
  expect(clarificationResponse.status()).toBe(200);
  const clarificationResult =
    (await clarificationResponse.json()) as ActionResult;
  expect(clarificationResult.event).toMatchObject({
    type: "clarification.drafted",
    object_type: "clarification"
  });

  await page.goto(`/workspaces/${workspace.id}/audit`);
  await expect(page.getByRole("heading", { name: "Audit" })).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "task.assigned" }).first()
  ).toBeVisible();
  await expect(
    page.getByText(`task:${task.id}`).first()
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "clarification.drafted" }).first()
  ).toBeVisible();
  await expect(
    page
      .getByText(
        `clarification:${clarificationResult.event?.object_id ?? "missing"}`
      )
      .first()
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Create export unavailable" })
  ).toBeDisabled();
});
