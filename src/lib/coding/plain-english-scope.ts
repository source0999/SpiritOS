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
  expectedChecks: string[];
  forbiddenFiles: string[];
  inspectionSummary: string;
  reasonCodes: string[];
  riskTier: PlainEnglishScopeRiskTier;
  rollbackHint: string;
  safeNextAction: "review_scope";
  status: PlainEnglishScopeStatus;
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
  const mentionedPaths = collectMentionedRepoPaths(task);
  const protectedMentions = collectProtectedPathMentions(task);
  const targetCandidates = normalizeUnique([...explicitTargets, ...mentionedPaths, ...protectedMentions]);
  const protectedCandidates = targetCandidates.filter(pathIsProtected);
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
  const checks = expectedChecksForTaskType(taskType);
  const status: PlainEnglishScopeStatus = reasonCodes.length > 0 ? "blocked" : "ready";
  const allowedFiles = status === "ready" && target ? [target] : [];
  return {
    allowedFiles,
    expectedChecks: checks,
    forbiddenFiles: forbiddenFilesForTaskType(taskType),
    inspectionSummary: inspectionSummary({
      explicitTargets,
      mentionedPaths,
      status,
      target,
      taskType,
    }),
    reasonCodes: normalizeUnique(reasonCodes),
    riskTier: riskTierForTaskType(taskType, protectedCandidates.length > 0),
    rollbackHint: allowedFiles.length > 0 ? `git restore ${allowedFiles.join(" ")}` : "No rollback command is available until scope is resolved.",
    safeNextAction: "review_scope",
    status,
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

function normalizeCandidate(raw: string): string {
  return normalizeRepoRelativePath(raw)
    .replace(/^["'`]+|["'`]+$/g, "")
    .replace(/[.,:;!?]+$/g, "");
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
  explicitTargets: string[];
  mentionedPaths: string[];
  status: PlainEnglishScopeStatus;
  target: string;
  taskType: PlainEnglishTaskType;
}): string {
  if (input.status === "blocked") {
    if (!input.target) {
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
