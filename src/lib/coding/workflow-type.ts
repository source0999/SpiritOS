import type { PlainEnglishScopeDraft } from "@/lib/coding/plain-english-scope";

export type CodingWorkflowType =
  | "coding_task"
  | "bugfix"
  | "test_generation"
  | "docs_update"
  | "review_only_analysis"
  | "verification_only"
  | "blocked_unsafe";

export type CodingWorkflowAuthority = {
  approval: boolean;
  apply: boolean;
  commit: boolean;
  push: boolean;
  preview: boolean;
  verification: boolean;
  writeCapable: boolean;
};

export type CodingWorkflowClassification = {
  authority: CodingWorkflowAuthority;
  reasonCodes: string[];
  safeNextAction: "scope_review" | "review_only" | "verification" | "blocked";
  workflowType: CodingWorkflowType;
};

const BLOCKED_REASON_CODES = new Set([
  "missing_task_text",
  "multiple_targets",
  "protected_path",
  "target_missing",
  "target_unresolved",
]);

export function classifyCodingWorkflow(
  taskText: string,
  scopeDraft: Pick<PlainEnglishScopeDraft, "reasonCodes" | "status" | "taskType">,
): CodingWorkflowClassification {
  const normalized = taskText.toLowerCase();
  const reasonCodes = [...scopeDraft.reasonCodes];
  if (
    scopeDraft.status === "blocked" ||
    reasonCodes.some((reason) => BLOCKED_REASON_CODES.has(reason))
  ) {
    return workflow("blocked_unsafe", reasonCodes, "blocked", {
      preview: false,
      verification: false,
      writeCapable: false,
    });
  }
  if (looksReviewOnly(normalized)) {
    return workflow("review_only_analysis", reasonCodes, "review_only", {
      preview: false,
      verification: false,
      writeCapable: false,
    });
  }
  if (looksVerificationOnly(normalized)) {
    return workflow("verification_only", reasonCodes, "verification", {
      preview: false,
      verification: true,
      writeCapable: false,
    });
  }
  if (scopeDraft.taskType === "docs") {
    return workflow("docs_update", reasonCodes, "scope_review");
  }
  if (scopeDraft.taskType === "test" || looksTestGeneration(normalized)) {
    return workflow("test_generation", reasonCodes, "scope_review");
  }
  if (looksBugfix(normalized)) {
    return workflow("bugfix", reasonCodes, "scope_review");
  }
  return workflow("coding_task", reasonCodes, "scope_review");
}

function workflow(
  workflowType: CodingWorkflowType,
  reasonCodes: string[],
  safeNextAction: CodingWorkflowClassification["safeNextAction"],
  overrides: Partial<CodingWorkflowAuthority> = {},
): CodingWorkflowClassification {
  const writeCapable = overrides.writeCapable ?? safeNextAction === "scope_review";
  return {
    authority: {
      approval: false,
      apply: false,
      commit: false,
      preview: writeCapable,
      push: false,
      verification: false,
      writeCapable,
      ...overrides,
    },
    reasonCodes,
    safeNextAction,
    workflowType,
  };
}

function looksReviewOnly(task: string): boolean {
  return /\b(explain|inspect|review|summarize|analy[sz]e|read)\b/.test(task) &&
    !/\b(add|change|create|edit|fix|implement|update|write)\b/.test(task);
}

function looksVerificationOnly(task: string): boolean {
  return /\b(verify|check|run tests?|validate)\b/.test(task) &&
    !/\b(add|change|create|edit|fix|implement|update|write)\b/.test(task);
}

function looksTestGeneration(task: string): boolean {
  return /\b(add|create|write)\b.*\b(test|spec|coverage)\b/.test(task);
}

function looksBugfix(task: string): boolean {
  return /\b(fix|bug|regression|broken|failing)\b/.test(task);
}
