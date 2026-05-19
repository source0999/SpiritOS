import { expect, test } from "@playwright/test";

test.describe("/coding cockpit smoke", () => {
  test("loads the clean cockpit without diagnostic clutter", async ({ page }) => {
    await page.goto("/coding");

    await expect(page.getByRole("heading", { level: 1, name: "Coding" })).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Spirit workspace navigation" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Advanced diagnostics" })).toHaveAttribute(
      "href",
      "/proxy-backend",
    );
    await expect(page.getByText("Task Composer")).toBeVisible();
    await expect(page.getByText("No files changed")).toBeVisible();

    await expect(page.getByText("Debug JSON")).toHaveCount(0);
    await expect(page.getByText("Replayable logs")).toHaveCount(0);
    await expect(page.getByRole("button", { name: /apply approved diff/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /commit|push/i })).toHaveCount(0);
  });

  test("keeps the composer and mobile action surface usable", async ({ page, isMobile }) => {
    await page.goto("/coding");

    await expect(page.getByLabel("Task")).toBeVisible();
    await expect(page.getByLabel("Target file")).toBeVisible();
    await expect(page.getByLabel("Allowed files")).toBeVisible();
    await expect(page.getByRole("button", { name: "Preview safely" })).toBeDisabled();

    if (isMobile) {
      await expect(page.getByTestId("mobile-action-bar")).toBeVisible();
      await expect(page.getByRole("button", { name: "Preview" })).toBeDisabled();
    }
  });
});
