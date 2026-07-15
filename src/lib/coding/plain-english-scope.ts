import { normalizeRepoRelativePath } from "@/lib/coding/explicit-task-target";

export type PlainEnglishTaskType =
  | "docs"
  | "frontend"
  | "backend_api"
  | "test"
  | "config"
  | "unknown";

export type PlainEnglishScopeStatus = "ready" | "blocked";

export type PlainEnglishScopeRiskTier = "low" | "medium" | "high";

export type PlainEnglishScopeDraft = {
  allowedFiles: string[];
  candidateFiles: string[];
  clarificationPrompt: string;
  expectedChecks: string[];
  forbiddenFiles: string[];
  inspectionSummary: string;
  reasonCodes: string[];
  restrictions: {
    apply: boolean;
    commit: boolean;
    permanentChanges: boolean;
    providerCalls: boolean;
    push: boolean;
  };
  riskTier: PlainEnglishScopeRiskTier;
  rollbackHint: string;
  safeNextAction: "review_scope";
  status: PlainEnglishScopeStatus;
  taskGoal: string;
  targetFiles: string[];
  taskType: PlainEnglishTaskType;
};

type DerivePlainEnglishScopeOptions = {
  knownExistingPaths?: string[];
};

const REPO_PATH_RE =
  /\b((?:docs|src|source_proxy|tests|scripts|public|styles)\/[A-Za-z0-9._/@()[\]\-]+(?:\.(?:tsx?|jsx?|py|css|html|json|md|xml|ya?ml|toml)))\b/g;

const EXPLICIT_TARGET_RE = /^\s*target\s+file\s*:\s*(.+?)\s*$/gim;
const INLINE_TARGET_RE = /\btarget\s+file\s*:\s*([^\s,;]+)/gi;
const EXPLICIT_ALLOWED_RE = /^\s*allowed\s+files?\s*:\s*(.+?)\s*$/gim;
const EXPLICIT_FORBIDDEN_RE = /^\s*forbidden(?:\s+(?:files?|scope))?\s*:\s*(.+?)\s*$/gim;
const MANUAL_CHECK_RE = /^\s*manual\s+checks?\s*:\s*(.+?)\s*$/gim;
const PROTECTED_TOKEN_RE = /\b(\.env(?:\.[A-Za-z0-9_-]+)?|[A-Za-z0-9._/@()[\]\-]+\.(?:pem|key|crt|p12|pfx))\b/g;

const PROTECTED_PATH_PATTERNS = [
  /^\.env(?:\.|$)/,
  /(^|\/)(?:id_rsa|id_dsa|id_ecdsa|id_ed25519)$/,
  /(^|\/).*\.(?:pem|key|crt|p12|pfx)$/,
  /(^|\/)(?:secrets?|tokens?|credentials?)(?:\.|\/|$)/i,
];

export function derivePlainEnglishScopeDraft(
  taskText: string,
  options: DerivePlainEnglishScopeOptions = {},
): PlainEnglishScopeDraft {
  const task = taskText.trim();
  const knownExistingPaths = normalizeUnique(options.knownExistingPaths ?? []);
  const explicitTargets = collectExplicitTargets(task);
  const explicitAllowedFiles = collectLabeledPaths(task, EXPLICIT_ALLOWED_RE);
  const explicitForbiddenFiles = normalizeUnique([
    ...collectLabeledPaths(task, EXPLICIT_FORBIDDEN_RE),
    ...collectNegatedPaths(task),
    ...collectProtectedPathMentions(task),
  ]);
  const mentionedPaths = collectMentionedRepoPaths(task);
  const targetCandidates = normalizeUnique([
    ...explicitTargets,
    ...explicitAllowedFiles,
    ...mentionedPaths.filter((path) => !explicitForbiddenFiles.includes(path) && !pathIsProtected(path)),
  ]);
  const protectedCandidates = targetCandidates.filter(pathIsProtected);
  const candidateFiles = candidateFilesForTask(task);
  const existingTargetCandidates =
    knownExistingPaths.length > 0
      ? targetCandidates.filter((path) => knownExistingPaths.includes(path))
      : targetCandidates;
  const reasonCodes: string[] = [];
  if (!task) {
    reasonCodes.push("missing_task_text");
  }
  if (protectedCandidates.length > 0) {
    reasonCodes.push("protected_path");
  }
  if (targetCandidates.length === 0) {
    reasonCodes.push("target_unresolved");
  }
  if (targetCandidates.length > 1) {
    reasonCodes.push("multiple_targets");
  }
  if (knownExistingPaths.length > 0 && targetCandidates.length > 0 && existingTargetCandidates.length === 0) {
    reasonCodes.push("target_missing");
  }

  const target = protectedCandidates[0] ?? existingTargetCandidates[0] ?? targetCandidates[0] ?? "";
  const taskType = classifyTaskType(task, target);
  const checks = uniqueStrings([...collectManualChecks(task), ...expectedChecksForTaskType(taskType)]);
  const status: PlainEnglishScopeStatus = reasonCodes.length > 0 ? "blocked" : "ready";
  const allowedFiles =
    status === "ready" && target
      ? explicitAllowedFiles.length > 0
        ? normalizeUnique(explicitAllowedFiles)
        : [target]
      : [];
  const restrictions = restrictionFlags(task);
  return {
    allowedFiles,
    candidateFiles,
    clarificationPrompt:
      status === "blocked"
        ? clarificationPromptFor({ candidateFiles, reasonCodes, target })
        : "Scope is ready for preview; review the target and allowed files before requesting evidence.",
    expectedChecks: checks,
    forbiddenFiles: normalizeUnique([...forbiddenFilesForTaskType(taskType), ...explicitForbiddenFiles]),
    inspectionSummary: inspectionSummary({
      candidateFiles,
      explicitTargets,
      mentionedPaths,
      status,
      target,
      taskType,
    }),
    reasonCodes: normalizeUnique(reasonCodes),
    restrictions,
    riskTier: riskTierForTaskType(taskType, protectedCandidates.length > 0),
    rollbackHint: allowedFiles.length > 0 ? `git restore ${allowedFiles.join(" ")}` : "No rollback command is available until scope is resolved.",
    safeNextAction: "review_scope",
    status,
    taskGoal: taskGoalFromText(task),
    targetFiles: target ? [target] : [],
    taskType,
  };
}

function collectExplicitTargets(task: string): string[] {
  EXPLICIT_TARGET_RE.lastIndex = 0;
  const paths: string[] = [];
  let match: RegExpExecArray | null;
  while ((match = EXPLICIT_TARGET_RE.exec(task)) !== null) {
    const normalized = normalizeCandidate(match[1] ?? "");
    if (normalized) {
      paths.push(normalized);
    }
  }
  INLINE_TARGET_RE.lastIndex = 0;
  while ((match = INLINE_TARGET_RE.exec(task)) !== null) {
    const normalized = normalizeCandidate(match[1] ?? "");
    if (normalized) {
      paths.push(normalized);
    }
  }
  return normalizeUnique(paths);
}

function collectMentionedRepoPaths(task: string): string[] {
  REPO_PATH_RE.lastIndex = 0;
  const paths: string[] = [];
  let match: RegExpExecArray | null;
  while ((match = REPO_PATH_RE.exec(task)) !== null) {
    const normalized = normalizeCandidate(match[1] ?? "");
    if (normalized) {
      paths.push(normalized);
    }
  }
  return normalizeUnique(paths);
}

function collectLabeledPaths(task: string, pattern: RegExp): string[] {
  pattern.lastIndex = 0;
  const paths: string[] = [];
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(task)) !== null) {
    paths.push(...splitPathList(match[1] ?? ""));
  }
  return normalizeUnique(paths);
}

function collectManualChecks(task: string): string[] {
  MANUAL_CHECK_RE.lastIndex = 0;
  const checks: string[] = [];
  let match: RegExpExecArray | null;
  while ((match = MANUAL_CHECK_RE.exec(task)) !== null) {
    checks.push(
      ...(match[1] ?? "")
        .split(/[;\n]+/)
        .map((value) => value.trim())
        .filter(Boolean),
    );
  }
  return normalizeUnique(checks);
}

function collectNegatedPaths(task: string): string[] {
  const paths: string[] = [];
  const negatedPattern =
    /\b(?:do\s+not|don't|never|no)\s+(?:touch|edit|mutate|change|write|inspect)\s+([^.\n]+)/gi;
  let match: RegExpExecArray | null;
  while ((match = negatedPattern.exec(task)) !== null) {
    paths.push(...splitPathList(match[1] ?? ""));
  }
  return normalizeUnique(paths);
}

function collectProtectedPathMentions(task: string): string[] {
  PROTECTED_TOKEN_RE.lastIndex = 0;
  const paths: string[] = [];
  let match: RegExpExecArray | null;
  while ((match = PROTECTED_TOKEN_RE.exec(task)) !== null) {
    const normalized = normalizeCandidate(match[1] ?? "");
    if (normalized) {
      paths.push(normalized);
    }
  }
  return normalizeUnique(paths);
}

function splitPathList(raw: string): string[] {
  return raw
    .split(/[,;\n]+|\s+and\s+/i)
    .map((value) => normalizeCandidate(value))
    .filter(looksLikeScopeToken)
    .filter(Boolean);
}

function normalizeCandidate(raw: string): string {
  return normalizeRepoRelativePath(raw)
    .replace(/^["'`]+|["'`]+$/g, "")
    .replace(/[.,:;!?]+$/g, "");
}

function taskGoalFromText(task: string): string {
  const taskLine = task.match(/^\s*task\s*:\s*(.+?)\s*$/im)?.[1];
  if (taskLine) return taskLine.trim();
  return task.split(/\n+/)[0]?.trim().slice(0, 220) || "No task goal supplied.";
}

function restrictionFlags(task: string) {
  const normalized = task.toLowerCase();
  return {
    apply: /\bno\s+apply|do\s+not[^.\n]*\bapply|without\s+apply/.test(normalized),
    commit: /\bno\s+commit|do\s+not[^.\n]*\bcommit|without\s+commit/.test(normalized),
    permanentChanges:
      /\bno\s+permanent\s+changes|preview[-\s]only|do\s+not[^.\n]*\b(?:mutate|permanent\s+changes|make\s+permanent)/.test(
        normalized,
      ),
    providerCalls:
      /\bno\s+provider|no\s+model\s+call|do\s+not[^.\n]*\b(?:provider|call\s+providers?|model\s+call)/.test(
        normalized,
      ),
    push: /\bno\s+push|do\s+not[^.\n]*\bpush|without\s+push/.test(normalized),
  };
}

function candidateFilesForTask(task: string): string[] {
  const normalized = task.toLowerCase();
  const candidates: string[] = [];
  if (normalized.includes("/coding") || normalized.includes("coding agent") || normalized.includes("command center")) {
    candidates.push(
      "src/components/coding/CodingCockpitShell.tsx",
      "src/components/coding/CodingCockpitShell.tsx",
      "src/lib/coding/plain-english-scope.ts",
    );
  }
  if (normalized.includes("taskspec") || normalized.includes("task spec") || normalized.includes("scope")) {
    candidates.push("src/lib/coding/plain-english-scope.ts");
  }
  if (normalized.includes("trial") || normalized.includes("harness")) {
    candidates.push(
      "scripts/agent-trials/run-ui-agent-trials.mjs",
      "tests/ui-agent-trials/coding-ui-trial.spec.ts",
    );
  }
  if (normalized.includes("design")) {
    candidates.push("src/app/coding/design-demo/page.tsx");
  }
  return normalizeUnique(candidates);
}

function clarificationPromptFor(input: { candidateFiles: string[]; reasonCodes: string[]; target: string }) {
  if (input.reasonCodes.includes("protected_path")) {
    return "That target touches protected scope. Pick one non-secret repo file or approve a safer allowed-file scope before preview.";
  }
  if (input.reasonCodes.includes("multiple_targets")) {
    return "I found more than one possible target. Pick one target file and allowed-file scope before preview.";
  }
  if (input.candidateFiles.length > 0) {
    return `I need one target file or allowed-file scope before preview. Suggested candidates: ${input.candidateFiles.join(", ")}.`;
  }
  if (input.target) {
    return `I inferred ${input.target}, but need Britton to approve or edit the allowed-file scope before preview.`;
  }
  return "I need one target file or allowed-file scope before preview.";
}

function normalizeUnique(values: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const value of values) {
    const normalized = normalizeCandidate(value);
    if (!normalized || seen.has(normalized)) {
      continue;
    }
    seen.add(normalized);
    out.push(normalized);
  }
  return out;
}

function uniqueStrings(values: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const value of values) {
    const normalized = value.trim();
    if (!normalized || seen.has(normalized)) continue;
    seen.add(normalized);
    out.push(normalized);
  }
  return out;
}

function looksLikeScopeToken(value: string): boolean {
  return (
    value === ".env" ||
    value.startsWith(".env.") ||
    value.includes("/") ||
    value.includes("*") ||
    /\.(?:tsx?|jsx?|py|css|html|json|md|xml|ya?ml|toml|pem|key|crt|p12|pfx)$/.test(value)
  );
}

function pathIsProtected(path: string): boolean {
  const normalized = normalizeCandidate(path);
  if (!normalized || normalized.includes("..")) {
    return true;
  }
  return PROTECTED_PATH_PATTERNS.some((pattern) => pattern.test(normalized));
}

function classifyTaskType(task: string, target: string): PlainEnglishTaskType {
  const combined = `${task} ${target}`.toLowerCase();
  if (target.startsWith("docs/") || /\.md$/.test(target)) {
    return "docs";
  }
  if (target.includes("__tests__") || target.startsWith("tests/") || /test|spec/.test(target)) {
    return "test";
  }
  if (target.startsWith("source_proxy/") || target.includes("/api/")) {
    return "backend_api";
  }
  if (target.startsWith("src/") || /\.(?:tsx|jsx|css)$/.test(target)) {
    return "frontend";
  }
  if (/package\.json|next\.config|tsconfig|eslint|tailwind|config/.test(combined)) {
    return "config";
  }
  return "unknown";
}

function expectedChecksForTaskType(taskType: PlainEnglishTaskType): string[] {
  switch (taskType) {
    case "docs":
      return ["git diff --check"];
    case "frontend":
      return ["npm run typecheck", "git diff --check"];
    case "backend_api":
      return ["PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests", "git diff --check"];
    case "test":
      return ["npm run typecheck", "git diff --check"];
    case "config":
      return ["npm run typecheck", "git diff --check"];
    default:
      return ["git diff --check"];
  }
}

function forbiddenFilesForTaskType(taskType: PlainEnglishTaskType): string[] {
  const base = [".env", ".env.*", "*.pem", "*.key", "certificates/*", "package-lock.json"];
  if (taskType === "docs") {
    return [...base, "src/*", "source_proxy/*"];
  }
  return base;
}

function riskTierForTaskType(
  taskType: PlainEnglishTaskType,
  protectedPath: boolean,
): PlainEnglishScopeRiskTier {
  if (protectedPath || taskType === "config") {
    return "high";
  }
  if (taskType === "backend_api" || taskType === "frontend" || taskType === "test") {
    return "medium";
  }
  return "low";
}

function inspectionSummary(input: {
  candidateFiles: string[];
  explicitTargets: string[];
  mentionedPaths: string[];
  status: PlainEnglishScopeStatus;
  target: string;
  taskType: PlainEnglishTaskType;
}): string {
  if (input.status === "blocked") {
    if (!input.target) {
      if (input.candidateFiles.length > 0) {
        return `No single repo-relative target path was approved yet. Candidate files: ${input.candidateFiles.join(", ")}.`;
      }
      return "No single repo-relative target path could be inferred from the prompt.";
    }
    return `Scope needs review before preview: inferred ${input.target} as ${input.taskType}.`;
  }
  const source =
    input.explicitTargets.length > 0
      ? "an explicit Target file line"
      : "one repo-relative path in the prompt";
  return `Ready for scope review: inferred ${input.target} from ${source}; task type ${input.taskType}.`;
}
