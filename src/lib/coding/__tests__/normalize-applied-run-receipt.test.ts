import { describe, expect, it } from "vitest";

import { normalizeAppliedRunReceiptFromJson } from "@/lib/coding/normalize-applied-run-receipt";

describe("normalizeAppliedRunReceiptFromJson", () => {
  it("preserves provider metadata and appliedAt from camelCase receipts", () => {
    const receipt = normalizeAppliedRunReceiptFromJson({
      allowedFiles: ["tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx"],
      appliedAt: "2026-05-31T01:31:33.895Z",
      backupManifest: ".spirit-backups/task-1/manifest.json",
      changedFiles: ["tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx"],
      diff: "diff --git a/foo b/foo",
      finalTruthStatus: "GO",
      hermesUsedForThisRun: false,
      id: "receipt-1",
      model: "qwen2.5-coder:7b",
      prompt: "badge warning",
      provider: "Local / Ollama",
      providerModelSource: "runtime",
      providerModelStatus: "available",
      revertedAt: null,
      reversalModel: null,
      reversalProvider: null,
      reversalProviderModelSource: null,
      reverseDiff: "diff --git b/foo a/foo",
      target: "tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx",
      taskId: "task-1",
      undoReceiptId: null,
      undoReceiptPath: null,
      postApplyVerificationStatus: "verified",
    });

    expect(receipt).toMatchObject({
      appliedAt: "2026-05-31T01:31:33.895Z",
      backupManifest: ".spirit-backups/task-1/manifest.json",
      finalTruthStatus: "GO",
      model: "qwen2.5-coder:7b",
      postApplyVerificationStatus: "verified",
      provider: "Local / Ollama",
      undoReceiptId: null,
      undoReceiptPath: null,
    });
  });

  it("preserves manifest Undo fields from snake_case receipts", () => {
    const receipt = normalizeAppliedRunReceiptFromJson({
      allowed_files: ["tests/ui-agent-trials/fixtures/dummy-product-site/**"],
      applied_at: "2026-07-11T22:48:03.747Z",
      backup_manifest: ".spirit-backups/approved-diff/manifest.json",
      changed_files: ["tests/ui-agent-trials/fixtures/dummy-product-site/index.html"],
      diff: "diff --git a/index.html b/index.html",
      final_truth_status: "GO",
      id: "selected-prompt:prompt-1:task-1",
      post_apply_verification_status: "verified",
      reverse_diff: "diff --git b/index.html a/index.html",
      target: "tests/ui-agent-trials/fixtures/dummy-product-site/",
      task_id: "task-1",
      undo_receipt_id: "undo-task-1",
      undo_receipt_path: ".spirit-backups/task-1/undo.json",
    });

    expect(receipt).toMatchObject({
      backupManifest: ".spirit-backups/approved-diff/manifest.json",
      finalTruthStatus: "GO",
      postApplyVerificationStatus: "verified",
      undoReceiptId: "undo-task-1",
      undoReceiptPath: ".spirit-backups/task-1/undo.json",
    });
  });
});
