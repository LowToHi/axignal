import { expect, test } from "@playwright/test";

const workspaceId = "axfx_ws_eu_cloud_001";

test.describe("subscriber workspace contractual closure", () => {
  test("keeps continue review non-mutating and requires an explicit qualified decision", async ({ page }) => {
    await page.goto(`/workspaces/${workspaceId}/qualification`);

    await expect(page.getByRole("heading", { name: "Qualification" })).toBeVisible();

    const decision = page.getByLabel("Decision");
    const rationale = page.getByLabel("Rationale");
    const submit = page.getByTestId("qualification-decision-submit");

    await expect(decision).toHaveValue("review");
    await expect(submit).toBeDisabled();
    await expect(page.getByText("Continue review is intentionally non-mutating.")).toBeVisible();

    await decision.selectOption("pursue");
    await expect(submit).toBeDisabled();

    await rationale.fill("Pursuit decision supported by reviewed evidence.");
    await expect(submit).toBeEnabled();
  });

  test("does not expose document, approval or audit actions without persistent contracts", async ({ page }) => {
    await page.goto(`/workspaces/${workspaceId}/documents`);
    await expect(page.getByRole("button", { name: "Create draft unavailable" })).toBeDisabled();
    await expect(page.getByText(/persistent document contract/i)).toBeVisible();

    await page.goto(`/workspaces/${workspaceId}/team`);
    await expect(page.getByText(/Approval recording is unavailable/i).first()).toBeVisible();

    await page.goto(`/workspaces/${workspaceId}/audit`);
    await expect(page.getByRole("button", { name: "Create export unavailable" })).toBeDisabled();
    await expect(page.getByText(/Audit export remains disabled/i)).toBeVisible();
  });
});
