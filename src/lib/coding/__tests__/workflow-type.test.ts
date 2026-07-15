import { describe, expect, it } from "vitest";

import { derivePlainEnglishScopeDraft } from "@/lib/coding/plain-english-scope";
import { classifyCodingWorkflow } from "@/lib/coding/workflow-type";

function classify(task: string) {
  return classifyCodingWorkflow(task, derivePlainEnglishScopeDraft(task));
}

describe("coding workflow type contract", () => {
  it("classifies docs updates as write-capable scope-review workflows without apply authority", () => {
    const result = classify("Add a receipt note to docs/source-proxy-daily-use-runbook.md.");

    expect(result.workflowType).toBe("docs_update");
    expect(result.safeNextAction).toBe("scope_review");
    expect(result.authority.preview).toBe(true);
    expect(result.authority.writeCapable).toBe(true);
    expect(result.authority.approval).toBe(false);
    expect(result.authority.apply).toBe(false);
    expect(result.authority.commit).toBe(false);
    expect(result.authority.push).toBe(false);
  });

  it("classifies normal frontend work as a coding task", () => {
    const result = classify("Update labs/coding/CodingCommandCenterShell.tsx.");

    expect(result.workflowType).toBe("coding_task");
    expect(result.safeNextAction).toBe("scope_review");
  });

  it("classifies bugfix language separately", () => {
    const result = classify("Fix the failing preview state in labs/coding/CodingCommandCenterShell.tsx.");

    expect(result.workflowType).toBe("bugfix");
  });

  it("classifies test-writing language separately", () => {
    const result = classify("Add a regression test in src/lib/coding/__tests__/plain-english-scope.test.ts.");

    expect(result.workflowType).toBe("test_generation");
  });

  it("keeps review-only analysis non-write-capable", () => {
    const result = classify("Explain labs/coding/CodingCommandCenterShell.tsx.");

    expect(result.workflowType).toBe("review_only_analysis");
    expect(result.safeNextAction).toBe("review_only");
    expect(result.authority.preview).toBe(false);
    expect(result.authority.writeCapable).toBe(false);
  });

  it("keeps verification-only requests non-write-capable", () => {
    const result = classify("Run tests for src/lib/coding/__tests__/plain-english-scope.test.ts.");

    expect(result.workflowType).toBe("verification_only");
    expect(result.safeNextAction).toBe("verification");
    expect(result.authority.verification).toBe(true);
    expect(result.authority.writeCapable).toBe(false);
  });

  it("blocks ambiguous or unsafe prompts instead of defaulting to write-capable", () => {
    const ambiguous = classify(
      "Update docs/source-proxy-daily-use-runbook.md and docs/source-proxy-regression-matrix.md.",
    );
    const protectedTarget = classify("Update Target file: .env.local.");

    expect(ambiguous.workflowType).toBe("blocked_unsafe");
    expect(ambiguous.reasonCodes).toContain("multiple_targets");
    expect(ambiguous.authority.preview).toBe(false);
    expect(ambiguous.authority.writeCapable).toBe(false);
    expect(protectedTarget.workflowType).toBe("blocked_unsafe");
    expect(protectedTarget.reasonCodes).toContain("protected_path");
    expect(protectedTarget.authority.apply).toBe(false);
  });
});
