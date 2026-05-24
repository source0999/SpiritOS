import { describe, expect, it } from "vitest";

import { derivePlainEnglishScopeDraft } from "@/lib/coding/plain-english-scope";

describe("plain-English scope draft", () => {
  it("turns a plain docs prompt with one path into a review-only scope packet", () => {
    const draft = derivePlainEnglishScopeDraft(
      "Add a short runbook note about changed files in docs/source-proxy-daily-use-runbook.md.",
    );

    expect(draft.status).toBe("ready");
    expect(draft.taskType).toBe("docs");
    expect(draft.targetFiles).toEqual(["docs/source-proxy-daily-use-runbook.md"]);
    expect(draft.allowedFiles).toEqual(["docs/source-proxy-daily-use-runbook.md"]);
    expect(draft.expectedChecks).toEqual(["git diff --check"]);
    expect(draft.rollbackHint).toBe("git restore docs/source-proxy-daily-use-runbook.md");
    expect(draft.safeNextAction).toBe("review_scope");
    expect(draft.reasonCodes).toEqual([]);
  });

  it("blocks normal language when no single target can be inferred", () => {
    const draft = derivePlainEnglishScopeDraft(
      "Add a short runbook note about changed files in verification receipts.",
    );

    expect(draft.status).toBe("blocked");
    expect(draft.allowedFiles).toEqual([]);
    expect(draft.reasonCodes).toContain("target_unresolved");
    expect(draft.safeNextAction).toBe("review_scope");
  });

  it("blocks multiple mentioned targets instead of guessing", () => {
    const draft = derivePlainEnglishScopeDraft(
      "Keep docs/source-proxy-daily-use-runbook.md and docs/source-proxy-regression-matrix.md aligned.",
    );

    expect(draft.status).toBe("blocked");
    expect(draft.reasonCodes).toContain("multiple_targets");
    expect(draft.allowedFiles).toEqual([]);
  });

  it("classifies frontend targets without adding apply authority", () => {
    const draft = derivePlainEnglishScopeDraft(
      "Fix the disabled state in src/components/coding/CodingCommandCenterShell.tsx.",
    );

    expect(draft.status).toBe("ready");
    expect(draft.taskType).toBe("frontend");
    expect(draft.riskTier).toBe("medium");
    expect(draft.expectedChecks).toContain("npm run typecheck");
    expect(draft.safeNextAction).toBe("review_scope");
  });

  it("blocks protected targets", () => {
    const draft = derivePlainEnglishScopeDraft("Update Target file: .env.local with a new model key.");

    expect(draft.status).toBe("blocked");
    expect(draft.reasonCodes).toContain("protected_path");
    expect(draft.riskTier).toBe("high");
    expect(draft.allowedFiles).toEqual([]);
  });

  it("uses known path evidence to block missing targets", () => {
    const draft = derivePlainEnglishScopeDraft(
      "Update docs/missing-runbook.md.",
      { knownExistingPaths: ["docs/source-proxy-daily-use-runbook.md"] },
    );

    expect(draft.status).toBe("blocked");
    expect(draft.reasonCodes).toContain("target_missing");
    expect(draft.allowedFiles).toEqual([]);
  });
});
