export type CodingTimelineStep =
  | "understand"
  | "inspect"
  | "scope"
  | "draft"
  | "preview"
  | "approval"
  | "apply"
  | "verify";

export type CodingTimelineAuthority = "none" | "preview" | "approval" | "apply" | "verification";

export type CodingTimelineEvent = {
  authority: CodingTimelineAuthority;
  evidence: string;
  source: "client" | "source_proxy" | "human" | "unavailable";
  status: "waiting" | "active" | "complete" | "blocked";
  step: CodingTimelineStep;
  timestamp: string;
  title: string;
};

export type CodingTimelineInput = {
  allowedFiles: string[];
  appliedAt: string | null;
  approvedAt: string | null;
  changedFiles: string[];
  draftText: string;
  previewMessage: string;
  previewStatus: "idle" | "loading" | "ready" | "blocked" | "error";
  previewTarget: string;
  receiptCommandsRun: string;
  taskId: string;
  taskSubmitted: boolean;
  verificationMessage: string;
  verificationStatus: "not_started" | "required" | "running" | "passed" | "failed" | "unavailable";
  verifiedAt: string | null;
};

const UNAVAILABLE_TIME = "unavailable";

export function deriveCodingTimelineEvents(input: CodingTimelineInput): CodingTimelineEvent[] {
  const hasDraft = input.draftText.trim().length > 0;
  const scoped = input.allowedFiles.length > 0 || input.previewTarget.trim().length > 0;
  const previewComplete = input.previewStatus === "ready";
  const previewBlocked = input.previewStatus === "blocked" || input.previewStatus === "error";
  const applied = Boolean(input.appliedAt);
  const verified = input.verificationStatus === "passed";

  return [
    event({
      evidence: hasDraft ? "Plain-English task text is present." : "No task text yet.",
      source: "client",
      status: hasDraft ? "complete" : "waiting",
      step: "understand",
      title: "Understand request",
    }),
    event({
      evidence: hasDraft
        ? "Repository inspection is represented by scoped task evidence when preview runs."
        : "Inspection waits for a task.",
      source: hasDraft ? "source_proxy" : "unavailable",
      status: hasDraft ? "active" : "waiting",
      step: "inspect",
      title: "Inspect repo context",
    }),
    event({
      evidence: scoped
        ? `Allowed files: ${input.allowedFiles.join(", ") || input.previewTarget}.`
        : "Scope is unavailable until bounded task data exists.",
      source: scoped ? "source_proxy" : "unavailable",
      status: scoped ? "complete" : "waiting",
      step: "scope",
      title: "Scope task",
    }),
    event({
      evidence: input.taskSubmitted
        ? "Task packet submitted locally; no files changed."
        : hasDraft
          ? "Draft exists but is not submitted."
          : "Draft not started.",
      source: "client",
      status: input.taskSubmitted ? "complete" : hasDraft ? "active" : "waiting",
      step: "draft",
      title: "Draft task packet",
    }),
    event({
      authority: "preview",
      evidence: previewComplete
        ? changedFilesEvidence(input.changedFiles, input.previewTarget)
        : input.previewMessage || "Preview has not run.",
      source: previewComplete || previewBlocked ? "source_proxy" : "unavailable",
      status: previewComplete ? "complete" : previewBlocked ? "blocked" : "waiting",
      step: "preview",
      title: "Preview diff evidence",
    }),
    event({
      authority: "approval",
      evidence: input.approvedAt
        ? `Human approval recorded at ${input.approvedAt}.`
        : "Approval waits for clean preview evidence.",
      source: input.approvedAt ? "human" : "unavailable",
      status: input.approvedAt ? "complete" : previewComplete ? "active" : "waiting",
      step: "approval",
      timestamp: input.approvedAt ?? UNAVAILABLE_TIME,
      title: "Approval gate",
    }),
    event({
      authority: "apply",
      evidence: applied
        ? `Apply evidence recorded at ${input.appliedAt}; commands: ${input.receiptCommandsRun || "unavailable"}.`
        : "Apply is locked until explicit approval.",
      source: applied ? "source_proxy" : "unavailable",
      status: applied ? "complete" : input.approvedAt ? "active" : "waiting",
      step: "apply",
      timestamp: input.appliedAt ?? UNAVAILABLE_TIME,
      title: "Apply approved diff",
    }),
    event({
      authority: "verification",
      evidence: verified
        ? `Verification recorded at ${input.verifiedAt}.`
        : input.verificationMessage || "Verification waits for apply evidence.",
      source: verified ? "source_proxy" : "unavailable",
      status: verified
        ? "complete"
        : input.verificationStatus === "failed"
          ? "blocked"
          : input.verificationStatus === "running" || input.verificationStatus === "required"
            ? "active"
            : "waiting",
      step: "verify",
      timestamp: input.verifiedAt ?? UNAVAILABLE_TIME,
      title: "Verify result",
    }),
  ];
}

function changedFilesEvidence(changedFiles: string[], previewTarget: string): string {
  if (changedFiles.length > 0) {
    return `Changed files: ${changedFiles.join(", ")}.`;
  }
  if (previewTarget.trim()) {
    return `Preview target: ${previewTarget}. Changed files unavailable.`;
  }
  return "Preview ready, but changed files are unavailable.";
}

function event(
  input: Omit<CodingTimelineEvent, "authority" | "timestamp"> &
    Partial<Pick<CodingTimelineEvent, "authority" | "timestamp">>,
): CodingTimelineEvent {
  return {
    authority: input.authority ?? "none",
    evidence: input.evidence,
    source: input.source,
    status: input.status,
    step: input.step,
    timestamp: input.timestamp ?? UNAVAILABLE_TIME,
    title: input.title,
  };
}
