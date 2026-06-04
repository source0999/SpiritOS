import { describe, expect, it } from "vitest";

import { normalizeAppliedRunReceiptFromJson } from "@/lib/coding/normalize-applied-run-receipt";

describe("normalizeAppliedRunReceiptFromJson", () => {
  it("preserves provider metadata and appliedAt from camelCase receipts", () => {
    const receipt = normalizeAppliedRunReceiptFromJson({
      allowedFiles: ["tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx"],
      appliedAt: "2026-05-31T01:31:33.895Z",
      changedFiles: ["tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx"],
      diff: "diff --git a/foo b/foo",
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
    });

    expect(receipt).toMatchObject({
      appliedAt: "2026-05-31T01:31:33.895Z",
      model: "qwen2.5-coder:7b",
      provider: "Local / Ollama",
    });
  });
});
