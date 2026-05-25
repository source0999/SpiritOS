export type CodingProgressRunState = "idle" | "queued" | "running" | "blocked" | "complete" | "failed";

export type PublicCodingWorkLabel =
  | "Thinking"
  | "Working"
  | "Observed"
  | "Repairing within scope";

export type PublicCodingWorkItem = {
  evidence: string;
  evidence_unavailable: boolean;
  label: PublicCodingWorkLabel;
  source: "ui-local" | "receipt" | "timeline" | "unavailable";
  summary: string;
  timestamp: string;
};

export type PublicCodingWorkInput = {
  blockerText?: string;
  currentStep: string;
  nextStep: string;
  progressSource: string;
  receiptCommandsRun?: string;
  runState: CodingProgressRunState;
  timestamp: string;
};

const UNAVAILABLE = "unavailable";

export function formatCodingProgressElapsed(startedAtMs: number | null, nowMs: number): string {
  if (
    startedAtMs === null ||
    !Number.isFinite(startedAtMs) ||
    !Number.isFinite(nowMs) ||
    nowMs < startedAtMs
  ) {
    return UNAVAILABLE;
  }

  const totalSeconds = Math.floor((nowMs - startedAtMs) / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  return `Working for ${minutes}m ${seconds.toString().padStart(2, "0")}s`;
}

export function buildPublicCodingWorkItems(input: PublicCodingWorkInput): PublicCodingWorkItem[] {
  const timestamp = input.timestamp || UNAVAILABLE;
  const currentStep = input.currentStep.trim();
  const nextStep = input.nextStep.trim();
  const progressSource = input.progressSource.trim();
  const blockerText = input.blockerText?.trim() || "";
  const commandsRun = input.receiptCommandsRun?.trim() || "";

  return [
    {
      evidence: currentStep || "Current step evidence unavailable.",
      evidence_unavailable: !currentStep,
      label: "Thinking",
      source: currentStep ? "ui-local" : "unavailable",
      summary: "Thinking: planning next safe step",
      timestamp,
    },
    {
      evidence:
        input.runState === "running"
          ? progressSource || "Progress source unavailable."
          : "No active work loop is running.",
      evidence_unavailable: input.runState !== "running" || !progressSource,
      label: "Working",
      source: input.runState === "running" && progressSource ? "ui-local" : "unavailable",
      summary:
        input.runState === "running"
          ? "Working: UI-local preview lifecycle"
          : "Working: no active run",
      timestamp,
    },
    {
      evidence:
        blockerText ||
        commandsRun ||
        progressSource ||
        "Observed evidence unavailable until preview or receipt data exists.",
      evidence_unavailable: !blockerText && !commandsRun && !progressSource,
      label: "Observed",
      source: blockerText || commandsRun ? "receipt" : progressSource ? "ui-local" : "unavailable",
      summary: `Observed: ${publicRunStateSummary(input.runState)}`,
      timestamp,
    },
    {
      evidence:
        input.runState === "blocked" && blockerText
          ? `Scoped repair can use blocker evidence: ${blockerText}`
          : "Repair evidence unavailable until a scoped blocker is selected.",
      evidence_unavailable: input.runState !== "blocked" || !blockerText,
      label: "Repairing within scope",
      source: input.runState === "blocked" && blockerText ? "receipt" : "unavailable",
      summary:
        input.runState === "blocked" && blockerText
          ? "Repairing within scope: blocker evidence ready"
          : "Repairing within scope: unavailable",
      timestamp,
    },
  ];
}

export function publicCodingWorkReceipt(items: PublicCodingWorkItem[]): string {
  return [
    "Public work-state receipt",
    "hidden_chain_of_thought_displayed: false",
    "private_reasoning_displayed: false",
    ...items.map((item) =>
      [
        `${item.label}: ${item.summary}`,
        `source=${item.source}`,
        `timestamp=${item.timestamp}`,
        `evidence_unavailable=${item.evidence_unavailable ? "true" : "false"}`,
        `evidence=${item.evidence}`,
      ].join("; "),
    ),
  ].join("\n");
}

function publicRunStateSummary(runState: CodingProgressRunState): string {
  switch (runState) {
    case "blocked":
      return "blocked safely";
    case "complete":
      return "done";
    case "failed":
      return "failed safely";
    case "queued":
      return "waiting for preview";
    case "running":
      return "work in progress";
    case "idle":
    default:
      return "idle";
  }
}
