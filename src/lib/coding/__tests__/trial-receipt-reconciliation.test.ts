import { describe, expect, it } from "vitest";

import {
  applyTrialReceiptReconciliation,
  countActiveUnrevertedTrialReceipts,
  reconcileTrialReceiptWithContent,
  type TrialRunReceipt,
} from "@/lib/coding/trial-receipt-reconciliation";

const componentFixturePath = "tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx";

describe("trial receipt reconciliation", () => {
  it("marks receipts stale when applied diff markers are no longer on disk", () => {
    const receipt = {
      changedFiles: [componentFixturePath],
      diff: [
        `diff --git a/${componentFixturePath} b/${componentFixturePath}`,
        `--- a/${componentFixturePath}`,
        `+++ b/${componentFixturePath}`,
        "@@ -1,6 +1,6 @@",
        ' export type TrialBadgeProps = {',
        '   label: string;',
        '-  tone: "neutral" | "success";',
        '+  tone: "neutral" | "success" | "warning";',
        " };",
      ].join("\n"),
      id: "trial-1",
      revertedAt: null,
      target: componentFixturePath,
    };

    expect(
      reconcileTrialReceiptWithContent(
        receipt,
        [
          'export type TrialBadgeProps = {',
          '  label: string;',
          '  tone: "neutral" | "success";',
          "};",
        ].join("\n"),
      ),
    ).toBe("stale_resolved");
  });

  it("marks receipts stale when only unchanged context lines still match disk", () => {
    const receipt = {
      changedFiles: [
        "tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.test.tsx",
      ],
      diff: [
        "diff --git a/tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.test.tsx b/tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.test.tsx",
        "--- a/tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.test.tsx",
        "+++ b/tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.test.tsx",
        "@@ -3,3 +3,11 @@",
        " export function assertTrialBadgeSuccessState() {",
        "   const badge = TrialBadge({ label: \"Done\", tone: \"success\" });",
        "   return badge.tone === \"success\" && badge.label === \"Done\";",
        " }",
        "+",
        "+export function assertTrialBadgeWarningState() {",
        '+  const badge = TrialBadge({ label: "Partial", tone: "warning" as const });',
        '+  return badge.tone === "warning" && badge.label === "Partial";',
        "+}",
      ].join("\n"),
      id: "trial-warning-test",
      revertedAt: null,
      target: "tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.test.tsx",
    };

    expect(
      reconcileTrialReceiptWithContent(
        receipt,
        [
          "import { TrialBadge } from \"./component-trial\";",
          "",
          "export function assertTrialBadgeSuccessState() {",
          "  const badge = TrialBadge({ label: \"Done\", tone: \"success\" });",
          "  return badge.tone === \"success\" && badge.label === \"Done\";",
          "}",
        ].join("\n"),
      ),
    ).toBe("stale_resolved");
  });

  it("keeps active receipts when applied diff markers still exist", () => {
    const receipt = {
      changedFiles: [componentFixturePath],
      diff: [
        `diff --git a/${componentFixturePath} b/${componentFixturePath}`,
        `--- a/${componentFixturePath}`,
        `+++ b/${componentFixturePath}`,
        "@@ -1,6 +1,6 @@",
        ' export type TrialBadgeProps = {',
        '   label: string;',
        '-  tone: "neutral" | "success";',
        '+  tone: "neutral" | "success" | "warning";',
        " };",
      ].join("\n"),
      id: "trial-1",
      revertedAt: null,
      target: componentFixturePath,
    };

    expect(
      reconcileTrialReceiptWithContent(
        receipt,
        [
          'export type TrialBadgeProps = {',
          '  label: string;',
          '  tone: "neutral" | "success" | "warning";',
          "};",
        ].join("\n"),
      ),
    ).toBe("active");
  });

  it("auto-resolves stale receipts and excludes them from active unreverted counts", () => {
    const receipts = applyTrialReceiptReconciliation<TrialRunReceipt & { allowedFiles: string[] }>(
      [
        {
          allowedFiles: [componentFixturePath],
          changedFiles: [componentFixturePath],
          diff: [
            `diff --git a/${componentFixturePath} b/${componentFixturePath}`,
            `--- a/${componentFixturePath}`,
            `+++ b/${componentFixturePath}`,
            "@@ -1 +1,2 @@",
            " export const value = true;",
            "+export const verificationTargetSmoke = true;",
          ].join("\n"),
          id: "trial-1",
          revertedAt: null,
          target: componentFixturePath,
        },
      ],
      {
        [componentFixturePath]: "export const value = true;\n",
      },
    );

    expect(receipts[0]?.staleResolvedAt).toBeTruthy();
    expect(countActiveUnrevertedTrialReceipts(receipts as Array<TrialRunReceipt & { allowedFiles: string[] }>)).toBe(0);
  });

  it("marks route-summary receipts stale after the fixture is already back at baseline", () => {
    const routeSummaryPath =
      "tests/ui-agent-trials/fixtures/dummy-coding-targets/route-summary-trial.ts";
    const receipt = {
      changedFiles: [routeSummaryPath],
      diff: [
        `diff --git a/${routeSummaryPath} b/${routeSummaryPath}`,
        `--- a/${routeSummaryPath}`,
        `+++ b/${routeSummaryPath}`,
        "@@ -9,9 +9,12 @@",
        '     return "Request completed.";',
        "   }",
        " ",
        "-  return typeof input.message === \"string\" && input.message.trim()",
        "-    ? input.message.trim()",
        "-    : \"Request failed.\";",
        "+  const safeMessage =",
        "+    typeof input.message === \"string\" && input.message.trim()",
        "+      ? input.message.trim().slice(0, 120)",
        "+      : \"Request failed.\";",
        "+",
        "+  return `Status: ${input.status} - ${safeMessage}`;",
      ].join("\n"),
      id: "trial-suite:coder-013:task_0",
      revertedAt: null,
      target: routeSummaryPath,
    };
    const baselineFixture = [
      'export function summarizeTrialRouteResponse(input: TrialRouteSummaryInput): string {',
      '  if (input.status >= 200 && input.status < 300) {',
      '    return "Request completed.";',
      "  }",
      "",
      '  return typeof input.message === "string" && input.message.trim()',
      "    ? input.message.trim()",
      '    : "Request failed.";',
      "}",
    ].join("\n");

    expect(reconcileTrialReceiptWithContent(receipt, baselineFixture)).toBe("stale_resolved");
  });
});
