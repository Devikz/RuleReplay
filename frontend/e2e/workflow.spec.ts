import { expect, test } from "@playwright/test";

test("offline verification, policy evidence, replay, generation and execution failure", async ({
  page,
}) => {
  await page.goto("/");
  const policies = await (await page.request.get("/api/policies")).json();
  await expect(
    page.getByText("Local demo uses reviewed fixture behavior.", {
      exact: false,
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Run current draft" }).click();
  await expect(page.getByLabel("Verification advisory")).toContainText("FAIL");
  await expect(page.getByLabel("Saved run context")).toContainText(
    "offline_boundary",
  );
  await expect(
    page.getByText("LATE-FEE-V1", { exact: true }).first(),
  ).toBeVisible();
  await expect(
    page
      .getByRole("complementary", { name: "Policy-backed evidence" })
      .getByText(policies.policies[0].provenance.clause, { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Release summary" }).click();
  await expect(page.getByLabel("Release advisory")).toContainText("FAIL");
  await page
    .getByRole("button", { name: "Replay evidence", exact: true })
    .click();
  await page.getByRole("button", { name: "Close release summary" }).click();
  await expect(page.getByText(/Evidence replay consistent/)).toBeVisible();
  await page.getByRole("button", { name: "Test generation" }).click();
  await page
    .getByRole("button", { name: /Generate/ })
    .last()
    .click();
  await expect(
    page.getByText("Deterministic boundary suite. No AI call was made."),
  ).toBeVisible();
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name: /^Verification/ })
    .click();
  await page
    .getByRole("combobox", { name: "Scenario", exact: true })
    .selectOption("execution_error");
  await page.getByRole("button", { name: "Run current draft" }).click();
  await expect(page.getByLabel("Verification advisory")).toContainText(
    "REVIEW",
  );
  await expect(
    page
      .getByRole("table")
      .getByText("Execution failure", { exact: true })
      .first(),
  ).toBeVisible();
});

test("successful offline cases remain UNVERIFIED in history, details, summary and replay", async ({
  page,
}) => {
  await page.goto("/");
  const response = await page.request.post("/api/verify", {
    data: {
      scenario: "corrected",
      mode: "simulator",
      cases: [
        { id: "green", due_date: "2026-11-01", payment_date: "2026-11-01" },
      ],
    },
  });
  expect(response.status()).toBe(201);
  const saved = await response.json();
  expect(saved.summary.decision).toBe("pass");
  expect(saved.release.outcome).toBe("UNVERIFIED");
  await page.getByRole("button", { name: "Run history" }).click();
  const row = page.getByRole("row").filter({ hasText: saved.id.slice(0, 8) });
  await expect(row.getByLabel("Historical release verdict")).toHaveText(
    "UNVERIFIED",
  );
  await expect(row.getByText("PASS", { exact: true })).toHaveCount(0);
  await row.getByRole("button", { name: "Open evidence" }).click();
  await expect(page.getByLabel("Verification advisory")).toContainText(
    "UNVERIFIED",
  );
  await expect(
    page.getByRole("heading", { name: "Compliant", exact: true }),
  ).toBeVisible();
  await page
    .locator("summary")
    .filter({ hasText: "Saved source and policy snapshot" })
    .click();
  await expect(page.getByLabel("Saved python source")).toBeVisible();
  await page.getByRole("button", { name: "Release summary" }).click();
  await expect(page.getByLabel("Release advisory")).toContainText("UNVERIFIED");
  await page
    .getByRole("button", { name: "Replay evidence", exact: true })
    .click();
  await expect(page.getByRole("dialog").getByRole("status")).toContainText(
    "Evidence replay consistent. Release verdict: UNVERIFIED.",
  );
  await expect(
    page.getByRole("dialog").getByText("PASS", { exact: true }),
  ).toHaveCount(0);
});
