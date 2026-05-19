// ── Bounded proposal task handoff ───────────────────────────────────────────
// Proposal Creation drafts JSON; the lower workflow must not re-infer target
// from forbidden_files entries embedded in that JSON.

import { normalizeRepoRelativePath } from "@/lib/coding/explicit-task-target";

export type BoundedProposalDraft = {
  allowed_files: string[];
  expected_checks: string[];
  forbidden_files: string[];
  mode: "proposal" | "readonly";
  rollback_hint: string;
  target_file: string;
  task: string;
};

const PROPOSAL_FENCED_JSON_RE = /```json\s*\n([\s\S]*?)\n```/i;

export function parseBoundedProposalTask(text: string): BoundedProposalDraft | null {
  const trimmed = text.trim();
  if (!trimmed.toLowerCase().includes("proposal task:")) {
    return null;
  }
  const match = PROPOSAL_FENCED_JSON_RE.exec(trimmed);
  if (!match?.[1]) {
    return null;
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(match[1]) as unknown;
  } catch {
    return null;
  }
  if (!parsed || typeof parsed !== "object") {
    return null;
  }
  const record = parsed as Record<string, unknown>;
  const task = typeof record.task === "string" ? record.task.trim() : "";
  const targetRaw =
    typeof record.target_file === "string"
      ? record.target_file
      : record.target_file === null
        ? ""
        : "";
  const target_file = normalizeRepoRelativePath(targetRaw);
  const mode = record.mode === "readonly" ? "readonly" : "proposal";
  const allowed_files = normalizePathList(record.allowed_files);
  const forbidden_files = normalizePathList(record.forbidden_files);
  const expected_checks = normalizeStringList(record.expected_checks);
  const rollback_hint =
    typeof record.rollback_hint === "string" ? record.rollback_hint.trim() : "";
  if (!task && !target_file) {
    return null;
  }
  return {
    allowed_files,
    expected_checks,
    forbidden_files,
    mode,
    rollback_hint,
    target_file,
    task,
  };
}

export function proposalDraftResultToBounded(draft: {
  allowedFiles: string[];
  expectedChecks: string[];
  forbiddenFiles: string[];
  mode: "proposal" | "readonly";
  rollbackHint: string;
  targetFile: string;
  task: string;
}): BoundedProposalDraft {
  return {
    allowed_files: draft.allowedFiles,
    expected_checks: draft.expectedChecks,
    forbidden_files: draft.forbiddenFiles,
    mode: draft.mode,
    rollback_hint: draft.rollbackHint,
    target_file: normalizeRepoRelativePath(draft.targetFile),
    task: draft.task.trim(),
  };
}

/** Route/prompt task text: canonical Target file line + readable proposal body. */
export function buildWorkflowTaskFromProposal(proposal: BoundedProposalDraft): string {
  const lines: string[] = [];
  if (proposal.target_file) {
    lines.push(`Target file: ${proposal.target_file}`);
    lines.push("");
  }
  if (proposal.task) {
    lines.push(proposal.task);
    lines.push("");
  }
  lines.push(
    "Proposal task:",
    "",
    "```json",
    JSON.stringify(
      {
        allowed_files: proposal.allowed_files,
        expected_checks: proposal.expected_checks,
        forbidden_files: proposal.forbidden_files,
        mode: proposal.mode,
        rollback_hint: proposal.rollback_hint,
        target_file: proposal.target_file || null,
        task: proposal.task,
      },
      null,
      2,
    ),
    "```",
    "",
    "Safety: proposal draft only. Do not apply, commit, push, or edit files from this draft.",
  );
  return lines.join("\n").trim();
}

const PROPOSAL_TASK_MARKER_RE = /^\s*proposal\s+task\s*:\s*$/im;

function textBeforeProposalMarker(text: string): string {
  const match = PROPOSAL_TASK_MARKER_RE.exec(text);
  if (!match || match.index === undefined) {
    return text.trim();
  }
  return text.slice(0, match.index).trim();
}

/** Use proposal task body for diff/approval gates, not the fenced JSON envelope. */
export function effectivePlanningTaskText(text: string): string {
  const parsed = parseBoundedProposalTask(text);
  if (!parsed) {
    return text.trim();
  }
  if (parsed.task) {
    return parsed.task;
  }
  const before = textBeforeProposalMarker(text);
  if (before) {
    return before;
  }
  if (parsed.target_file) {
    return `Target file: ${parsed.target_file}`;
  }
  return "";
}

export function boundedProposalMatchesText(
  proposal: BoundedProposalDraft,
  textareaText: string,
): boolean {
  const parsed = parseBoundedProposalTask(textareaText);
  if (!parsed) {
    return false;
  }
  return (
    parsed.target_file === proposal.target_file &&
    parsed.task === proposal.task &&
    listsEqual(parsed.allowed_files, proposal.allowed_files) &&
    listsEqual(parsed.forbidden_files, proposal.forbidden_files)
  );
}

function normalizePathList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => (typeof item === "string" ? normalizeRepoRelativePath(item) : ""))
    .filter(Boolean);
}

function normalizeStringList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => (typeof item === "string" ? item.trim() : ""))
    .filter(Boolean);
}

function listsEqual(left: string[], right: string[]): boolean {
  if (left.length !== right.length) {
    return false;
  }
  return left.every((item, index) => item === right[index]);
}
