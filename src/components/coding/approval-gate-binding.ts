import { collectPathsFromUnifiedDiff, diffTouchesExplicitTarget } from "@/lib/coding/unified-diff-paths";

const SUBJECTIVE_IMPROVEMENT_REQUIRES_DIFF_REASON_CODE =
  "coder_subjective_improvement_requires_diff_or_review";
const VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE =
  "coder_visual_improvement_diff_too_shallow";

export type ApprovalGateBindingDecision = {
  next_prompt_action?: string;
  reason_codes?: string[];
  recommended_route?: string;
  resolved_target?: {
    exists?: boolean;
    path?: string;
    source?: string;
  };
  resolvedTarget?: {
    exists?: boolean;
    path?: string;
    source?: string;
  };
  task_classification?: string;
};

export type ApprovalGateBindingPromptPacket = {
  prompt_text?: string;
  requested_output?: string[];
  /** Coder Agent / proxy returns the backend-generated patch here while `prompt_text` stays a stub. */
  proposed_diff?: string;
  proposedDiff?: string;
  target?: string;
  already_satisfied?: boolean;
  alreadySatisfied?: boolean;
  reason_code?: string;
  reasonCode?: string;
  coder_blocked?: boolean;
  coderBlocked?: boolean;
  coder_diagnostics?: Record<string, unknown>;
  coderDiagnostics?: Record<string, unknown>;
};

export type ApprovalGateProposal = {
  action: string;
  content?: string;
  proposedDiff?: string;
  target: string;
};

const FILE_PATH_PATTERN =
  /(?:^|[\s`"'])((?:docs|_blueprints|src|source_proxy|app|components|lib|scripts|public|tests|styles)\/[A-Za-z0-9._/@()[\]-]+\.(?:tsx?|jsx?|py|css|html|json|md|xml|yml|yaml|toml))(?:$|[\s`"',.:;])/gm;

export function deriveApprovalGateProposal(
  decision: ApprovalGateBindingDecision,
  promptPacket: ApprovalGateBindingPromptPacket,
  options?: { currentTaskText?: string; resolvedTargetPath?: string },
): ApprovalGateProposal | null {
  if (
    promptPacket.already_satisfied === true ||
    promptPacket.alreadySatisfied === true ||
    promptPacket.reason_code === "coder_no_changes_needed" ||
    promptPacket.reasonCode === "coder_no_changes_needed"
  ) {
    return null;
  }
  if (
    promptPacket.reason_code === SUBJECTIVE_IMPROVEMENT_REQUIRES_DIFF_REASON_CODE ||
    promptPacket.reasonCode === SUBJECTIVE_IMPROVEMENT_REQUIRES_DIFF_REASON_CODE ||
    promptPacket.reason_code === VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE ||
    promptPacket.reasonCode === VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE
  ) {
    return null;
  }
  if (
    promptPacket.reason_code === "coder_model_not_configured" ||
    promptPacket.reasonCode === "coder_model_not_configured"
  ) {
    return null;
  }
  if (
    decision.reason_codes?.includes("target_missing") ||
    decision.reason_codes?.includes("target_unresolved") ||
    promptPacket.reason_code === "target_missing" ||
    promptPacket.reasonCode === "target_missing" ||
    promptPacket.reason_code === "target_unresolved" ||
    promptPacket.reasonCode === "target_unresolved"
  ) {
    return null;
  }
  const coderBlocked = promptPacket.coder_blocked === true || promptPacket.coderBlocked === true;
  const packetUnifiedDiff = unifiedDiffFromPromptPacketFields(promptPacket);
  if (coderBlocked && !packetUnifiedDiff) {
    return null;
  }
  const promptText = promptPacket.prompt_text ?? "";
  const userTask = options?.currentTaskText ?? "";
  const userExplicitTarget =
    normalizeRepoRelativePath(options?.resolvedTargetPath ?? "") ||
    resolvedTargetPathFromDecision(decision);
  if (userExplicitTarget) {
    let proposed =
      (coderBlocked ? packetUnifiedDiff || undefined : packetUnifiedDiff) || undefined;
    if (proposed && !diffTouchesExplicitTarget(proposed, userExplicitTarget)) {
      proposed = undefined;
    }
    const content = codeBlockForTarget(promptText, userExplicitTarget);
    if (!proposed && !content) {
      return null;
    }
    return proposalWithOptionalContent({
      action: actionForTarget(userTask || promptText, userExplicitTarget),
      content,
      proposedDiff: proposed,
      target: userExplicitTarget,
    });
  }

  const explicit = explicitProposalFromPrompt(promptText);
  if (explicit) {
    const proposedDiff = coderBlocked
      ? packetUnifiedDiff || undefined
      : packetUnifiedDiff || undefined;
    if (coderBlocked && !proposedDiff) {
      return null;
    }
    return proposalWithOptionalContent({
      action: explicit.action,
      content: explicit.content ?? "",
      proposedDiff: proposedDiff || undefined,
      target: explicit.target,
    });
  }

  if (!isImplementationRun(decision)) {
    return null;
  }

  const fromUserTask = firstFilePath(userTask);
  const fromPrompt = firstFilePath(promptText);
  const fromPromptSafe =
    fromPrompt &&
    (!normalizeRepoRelativePath(userTask) || pathMentionedInUserTask(fromPrompt, userTask))
      ? fromPrompt
      : "";
  const packetT = typeof promptPacket.target === "string" ? promptPacket.target.trim() : "";
  const packetSafe = packetT && isTrustworthyPacketTarget(packetT, userTask, decision) ? packetT : "";

  const target = packetSafe || fromUserTask || fromPromptSafe;
  if (!target) {
    return null;
  }

  let proposed =
    (coderBlocked ? packetUnifiedDiff || undefined : packetUnifiedDiff) || undefined;
  if (proposed) {
    const touched = collectPathsFromUnifiedDiff(proposed);
    if (touched.length > 0 && !diffTouchesExplicitTarget(proposed, target)) {
      proposed = undefined;
    }
  }
  const content = codeBlockForTarget(promptText, target);
  if (!proposed && !content) {
    const hadDiffHint = Boolean(packetUnifiedDiff);
    if (hadDiffHint) {
      return null;
    }
  }

  return proposalWithOptionalContent({
    action: actionForTarget(promptText, target),
    content,
    proposedDiff: proposed,
    target,
  });
}

export function resolvedTargetPathFromDecision(
  decision: ApprovalGateBindingDecision | null | undefined,
): string {
  const snake = decision?.resolved_target?.path;
  const camel = decision?.resolvedTarget?.path;
  return normalizeRepoRelativePath(
    (typeof snake === "string" && snake) ||
      (typeof camel === "string" && camel) ||
      "",
  );
}

function pathMentionedInUserTask(path: string, userTask: string): boolean {
  const p = normalizeRepoRelativePath(path);
  const t = normalizeRepoRelativePath(userTask);
  return Boolean(p && t && t.includes(p));
}

function isTrustworthyPacketTarget(
  packetTarget: string,
  userTask: string,
  decision: ApprovalGateBindingDecision,
): boolean {
  const norm = normalizeRepoRelativePath(packetTarget);
  if (!norm) {
    return false;
  }
  if (!normalizeRepoRelativePath(userTask)) {
    return true;
  }
  if (pathMentionedInUserTask(norm, userTask)) {
    return true;
  }
  if (normalizeRepoRelativePath(resolvedTargetPathFromDecision(decision)) === norm) {
    return true;
  }
  return false;
}

export function isImplementationRun(decision: ApprovalGateBindingDecision) {
  return (
    decision.task_classification === "implementation" ||
    decision.reason_codes?.includes("implementation_requested") === true
  );
}

function explicitProposalFromPrompt(promptText: string): ApprovalGateProposal | null {
  const action = matchNamedValue(promptText, ["proposed_action", "proposed action", "action"]);
  const target = matchNamedValue(promptText, ["target file", "target", "file", "path"]);
  if (!action || !target) {
    return null;
  }
  return proposalWithOptionalContent({
    action,
    content: codeBlockForTarget(promptText, target),
    proposedDiff: extractUnifiedDiff(promptText),
    target,
  });
}

function matchNamedValue(promptText: string, names: string[]) {
  for (const name of names) {
    const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const match = promptText.match(new RegExp(`^\\s*${escaped}\\s*:\\s*(.+)`, "im"));
    const value = match?.[1]?.trim().replace(/^["'`]|["'`]$/g, "");
    if (value) {
      return value;
    }
  }
  return "";
}

function firstFilePath(promptText: string) {
  const matches = [...promptText.matchAll(FILE_PATH_PATTERN)];
  return matches[0]?.[1] ?? "";
}

function normalizeRepoRelativePath(path: string): string {
  return path.replace(/\\/g, "/").replace(/^\.\/+/, "").trim();
}

function finalizeUnifiedDiffBody(raw: string): string {
  // Never `String.trim()` the whole patch — that eats the terminal `\n` `git apply` expects.
  const core = raw.replace(/^[\r\n]+/, "").replace(/[\r\n]+$/, "");
  if (!core.includes("@@")) {
    return "";
  }
  return core.endsWith("\n") ? core : `${core}\n`;
}

export function unifiedDiffFromPromptPacketFields(packet: ApprovalGateBindingPromptPacket): string {
  const snake = typeof packet.proposed_diff === "string" ? packet.proposed_diff : "";
  const camel = typeof packet.proposedDiff === "string" ? packet.proposedDiff : "";
  for (const raw of [snake, camel]) {
    if (!raw.trim()) {
      continue;
    }
    const finalized = finalizeUnifiedDiffBody(raw);
    if (finalized) {
      return finalized;
    }
  }
  return "";
}

export function extractUnifiedDiff(promptText: string) {
  const fenced = promptText.match(/```(?:diff|patch)\s*\n([\s\S]*?)```/i);
  if (fenced?.[1]?.includes("@@")) {
    return finalizeUnifiedDiffBody(fenced[1]);
  }

  const diffStart = promptText.search(/^diff --git /m);
  if (diffStart !== -1) {
    return finalizeUnifiedDiffBody(promptText.slice(diffStart));
  }

  return "";
}

function actionForTarget(promptText: string, target: string) {
  const targetLine = promptText
    .split(/\r?\n/)
    .find((line) => line.includes(target))
    ?.toLowerCase();
  if (targetLine?.includes("create") || targetLine?.includes("add")) {
    return "create file";
  }
  if (targetLine?.includes("modify") || targetLine?.includes("update")) {
    return "modify file";
  }
  return "implement proposed file change";
}

function codeBlockForTarget(promptText: string, target: string) {
  const normalizedTarget = target.replace(/\\/g, "/");
  const fences = [
    ...promptText.matchAll(/```([^\n`]*)\n([\s\S]*?)```/g),
  ].filter((match) => !/^(?:diff|patch)\b/i.test(match[1]?.trim() ?? ""));
  if (fences.length === 0) {
    return "";
  }

  const targetIndex = promptText.replace(/\\/g, "/").indexOf(normalizedTarget);
  if (targetIndex >= 0) {
    const afterTarget = fences.find((match) => (match.index ?? 0) > targetIndex);
    if (afterTarget?.[2]?.trim()) {
      return stripTrailingBlankLine(afterTarget[2]);
    }
  }

  const first = fences[0]?.[2];
  return first?.trim() ? stripTrailingBlankLine(first) : "";
}

function stripTrailingBlankLine(value: string) {
  return value.replace(/\s+$/, "") + "\n";
}

function proposalWithOptionalContent({
  action,
  content,
  proposedDiff,
  target,
}: {
  action: string;
  content: string;
  proposedDiff?: string;
  target: string;
}): ApprovalGateProposal {
  return {
    action,
    ...(content ? { content } : {}),
    ...(proposedDiff ? { proposedDiff } : {}),
    target,
  };
}
