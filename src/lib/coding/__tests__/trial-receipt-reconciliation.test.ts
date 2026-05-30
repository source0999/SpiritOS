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
});
