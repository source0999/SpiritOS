export const cartographerMapOperationalSections = [
  {
    id: "status-strip",
    label: "Top Status Strip",
    purpose:
      "Show Cartographer status, branch, short hash, dirty count, protected warnings, and next safe step.",
  },
  {
    id: "can-act",
    label: "Main Answer",
    purpose: "Give one large review-only answer in plain language.",
  },
  {
    id: "blockers",
    label: "Blockers",
    purpose:
      "Show dirty tree, protected lanes, approval state, queue/action state, and kill switch state.",
  },
  {
    id: "dirty-tree-groups",
    label: "Dirty Tree Groups",
    purpose: "Group docs-like, risky source, generated/cache, and decision-needed files.",
  },
  {
    id: "commit-push-readiness",
    label: "Commit And Push Readiness",
    purpose: "Show blocked/ready chips and missing proof without git action controls.",
  },
  {
    id: "project-tracker",
    label: "Project Tracker",
    purpose: "Show compressed project status and next step only.",
  },
  {
    id: "advisory-fleet",
    label: "Advisory Fleet",
    purpose: "Keep helper lanes compact, collapsed, and advisory-only.",
  },
  {
    id: "manual-check",
    label: "Manual Check",
    purpose: "Provide one clean copy-paste verification block.",
  },
  {
    id: "raw-diagnostics",
    label: "Raw Diagnostics Link",
    purpose: "Point deep diagnostics to /map/raw instead of crowding /map.",
  },
] as const;

export const cartographerRawMapDiagnosticSections = [
  {
    id: "read-only-sources",
    label: "Read-Only Sources",
    purpose: "Six approved endpoint diagnostics.",
  },
  {
    id: "approvals",
    label: "Approval And Token State",
    purpose: "Approval-token validation and consumption preview state for review only.",
  },
  {
    id: "queue-workflow",
    label: "Queue And Workflow State",
    purpose: "Queue, run-next, workflow, and step state without execution.",
  },
  {
    id: "stop-controls",
    label: "Kill Switch And Stop State",
    purpose: "Fail-closed kill switch and preview-only stop controls.",
  },
  {
    id: "review-readiness",
    label: "Review-Only Readiness",
    purpose: "Commit, push, merge, queue, approval, preflight, and stop readiness without execution.",
  },
  {
    id: "trust-audit",
    label: "Trust And Audit Summary",
    purpose: "Trust score and audit-trail signals without authority changes.",
  },
  {
    id: "receipts",
    label: "Evidence And Receipts",
    purpose: "Existing evidence Britton can review.",
  },
  {
    id: "authority-boundary",
    label: "Authority Boundary Audit",
    purpose: "Raw blocked action classes and manual diagnostics.",
  },
] as const;

export const cartographerMapAuthorityDenials = [
  "No approval minting",
  "No self-approval",
  "No broad full auto",
  "No source writes",
  "No command execution",
  "No commit, push, branch, checkout, reset, clean, or stash",
] as const;

export type CartographerPreviewControlKind =
  | "display-only-card"
  | "existing-get-link"
  | "copyable-manual-command-text"
  | "local-expand-collapse"
  | "safe-refresh"
  | "already-read-get-summary";

export type CartographerPreviewControlAuthority = {
  kind: CartographerPreviewControlKind;
  label: string;
  grantsAuthority: false;
  mayPost: false;
  mayMutate: false;
  mayExecute: false;
};

export const cartographerPreviewControlAuthority: CartographerPreviewControlAuthority[] = [
  {
    kind: "display-only-card",
    label: "Display-only card",
    grantsAuthority: false,
    mayPost: false,
    mayMutate: false,
    mayExecute: false,
  },
  {
    kind: "existing-get-link",
    label: "Link to an existing GET page",
    grantsAuthority: false,
    mayPost: false,
    mayMutate: false,
    mayExecute: false,
  },
  {
    kind: "copyable-manual-command-text",
    label: "Copyable manual command text",
    grantsAuthority: false,
    mayPost: false,
    mayMutate: false,
    mayExecute: false,
  },
  {
    kind: "local-expand-collapse",
    label: "Local expand/collapse UI",
    grantsAuthority: false,
    mayPost: false,
    mayMutate: false,
    mayExecute: false,
  },
  {
    kind: "safe-refresh",
    label: "Safe refresh",
    grantsAuthority: false,
    mayPost: false,
    mayMutate: false,
    mayExecute: false,
  },
  {
    kind: "already-read-get-summary",
    label: "Generated summary from already-read GET data",
    grantsAuthority: false,
    mayPost: false,
    mayMutate: false,
    mayExecute: false,
  },
];

export const cartographerForbiddenPreviewControlActions = [
  "POST",
  "approve",
  "stage",
  "clean",
  "write",
  "commit",
  "push",
  "merge",
  "checkout",
  "create branch",
  "switch branch",
  "start worker",
  "run queue",
  "run shell command",
  "mutate project state",
  "grant autonomy",
] as const;

export type CartographerDirtyTreePreviewInput = {
  trackedDirtyFiles: readonly string[];
  untrackedFiles: readonly string[];
  protectedLaneMatches: readonly { path: string; lane: string }[];
};

export type CartographerDirtyTreePreview = {
  totalDirtyFiles: number;
  trackedCount: number;
  untrackedCount: number;
  protectedLaneCount: number;
  likelySafeDocsFiles: string[];
  riskySourceFiles: string[];
  generatedCacheFiles: string[];
  unknownFiles: string[];
  protectedLaneFiles: { path: string; lane: string }[];
  cleanupPlanPreview: string[];
  authority: "preview-only";
};

export type CartographerCommitPreview = {
  suggestedCommitGroups: { label: string; files: string[]; recommendation: string }[];
  filesThatShouldNotBeCommittedYet: string[];
  missingVerification: string[];
  suggestedCommitMessageDraft: string;
  authority: "preview-only";
  canStage: false;
  canCommit: false;
};

export type CartographerBranchPushPreviewInput = {
  currentBranch: string | null;
  currentHead: string | null;
  ahead?: number | null;
  behind?: number | null;
  upstream?: string | null;
  dirtyTree: CartographerDirtyTreePreview;
};

export type CartographerBranchPushPreview = {
  currentBranch: string;
  headShortHash: string;
  aheadBehindSummary: string;
  changedAreas: string[];
  mergeRisk: "low" | "review-needed" | "blocked";
  pushReadiness: "blocked" | "proof-needed" | "not-needed";
  pushBlockers: string[];
  proofNeeded: string[];
  authority: "preview-only";
  canCheckout: false;
  canCreateBranch: false;
  canMerge: false;
  canPush: false;
};

export type CartographerProjectCardState =
  | "live"
  | "needs review"
  | "blocked"
  | "not wired yet"
  | "safe to inspect";

export type CartographerProjectCardPreview = {
  projectId: string;
  label: string;
  state: CartographerProjectCardState;
  visibleRepoSignals: string[];
  previewNextStep: string;
  authority: "preview-only";
  canMutateProject: false;
  canStartWorker: false;
};

export const cartographerDefaultProjectCardPreviews: CartographerProjectCardPreview[] = [
  {
    projectId: "spiritos",
    label: "SpiritOS",
    state: "live",
    visibleRepoSignals: ["package.json", "src/app", "source_proxy"],
    previewNextStep: "Review dirty tree and protected lanes before any operator action.",
    authority: "preview-only",
    canMutateProject: false,
    canStartWorker: false,
  },
  {
    projectId: "source-proxy",
    label: "Source Proxy",
    state: "needs review",
    visibleRepoSignals: ["source_proxy"],
    previewNextStep: "Inspect Source Proxy status without changing backend runtime.",
    authority: "preview-only",
    canMutateProject: false,
    canStartWorker: false,
  },
  {
    projectId: "cartographer",
    label: "Cartographer",
    state: "needs review",
    visibleRepoSignals: ["src/app/map", "src/app/v1/cartographer", "source_proxy/cartographer"],
    previewNextStep: "Keep preview-control work display-only until the next explicit approval.",
    authority: "preview-only",
    canMutateProject: false,
    canStartWorker: false,
  },
  {
    projectId: "scout",
    label: "Scout",
    state: "blocked",
    visibleRepoSignals: ["src/app/api/scout", "src/lib/scout-overview.ts"],
    previewNextStep: "Do not reopen Scout runtime; inspect only.",
    authority: "preview-only",
    canMutateProject: false,
    canStartWorker: false,
  },
  {
    projectId: "agent-factory",
    label: "Agent Factory",
    state: "safe to inspect",
    visibleRepoSignals: ["source_proxy/agent_factory"],
    previewNextStep: "Review status docs and tests without assigning workers.",
    authority: "preview-only",
    canMutateProject: false,
    canStartWorker: false,
  },
  {
    projectId: "media-app",
    label: "Media app",
    state: "safe to inspect",
    visibleRepoSignals: ["src/app/media", "src/components/media", "src/lib/media"],
    previewNextStep: "Inspect media state as a project card only.",
    authority: "preview-only",
    canMutateProject: false,
    canStartWorker: false,
  },
  {
    projectId: "oracle-chat",
    label: "Oracle / Chat",
    state: "safe to inspect",
    visibleRepoSignals: ["src/app/oracle", "src/app/chat", "src/components/chat"],
    previewNextStep: "Inspect visible Oracle and Chat surfaces without runtime mutation.",
    authority: "preview-only",
    canMutateProject: false,
    canStartWorker: false,
  },
];

export function buildCartographerDirtyTreePreview(
  input: CartographerDirtyTreePreviewInput,
): CartographerDirtyTreePreview {
  const allFiles = uniqueStrings([...input.trackedDirtyFiles, ...input.untrackedFiles]);
  const protectedLaneFiles = input.protectedLaneMatches.map((match) => ({
    path: match.path,
    lane: match.lane,
  }));
  const protectedPaths = new Set(protectedLaneFiles.map((match) => match.path));
  const likelySafeDocsFiles: string[] = [];
  const riskySourceFiles: string[] = [];
  const generatedCacheFiles: string[] = [];
  const unknownFiles: string[] = [];

  for (const file of allFiles) {
    if (isGeneratedCacheFile(file)) {
      generatedCacheFiles.push(file);
    } else if (isLikelySafeDocsFile(file)) {
      likelySafeDocsFiles.push(file);
    } else if (protectedPaths.has(file) || isRiskySourceFile(file)) {
      riskySourceFiles.push(file);
    } else {
      unknownFiles.push(file);
    }
  }

  return {
    totalDirtyFiles: allFiles.length,
    trackedCount: input.trackedDirtyFiles.length,
    untrackedCount: input.untrackedFiles.length,
    protectedLaneCount: protectedLaneFiles.length,
    likelySafeDocsFiles,
    riskySourceFiles,
    generatedCacheFiles,
    unknownFiles,
    protectedLaneFiles,
    cleanupPlanPreview: buildCleanupPlanPreview({
      likelySafeDocsFiles,
      riskySourceFiles,
      generatedCacheFiles,
      unknownFiles,
      protectedLaneFiles,
    }),
    authority: "preview-only",
  };
}

export function buildCartographerBranchPushPreview(
  input: CartographerBranchPushPreviewInput,
): CartographerBranchPushPreview {
  const changedAreas = branchChangedAreas(input.dirtyTree);
  const pushBlockers = branchPushBlockers(input);
  const hasDirtyFiles = input.dirtyTree.totalDirtyFiles > 0;
  const isBehind = (input.behind ?? 0) > 0;
  const mergeRisk =
    input.dirtyTree.protectedLaneCount > 0 || isBehind
      ? "blocked"
      : hasDirtyFiles
        ? "review-needed"
        : "low";
  const pushReadiness =
    pushBlockers.length > 0
      ? "blocked"
      : (input.ahead ?? 0) > 0
        ? "proof-needed"
        : "not-needed";

  return {
    currentBranch: input.currentBranch ?? "unknown",
    headShortHash: input.currentHead ? input.currentHead.slice(0, 12) : "unknown",
    aheadBehindSummary: aheadBehindSummary(input.ahead, input.behind, input.upstream),
    changedAreas,
    mergeRisk,
    pushReadiness,
    pushBlockers,
    proofNeeded: pushProofNeeded(input),
    authority: "preview-only",
    canCheckout: false,
    canCreateBranch: false,
    canMerge: false,
    canPush: false,
  };
}

export function buildCartographerCommitPreview(
  dirtyTree: CartographerDirtyTreePreview,
): CartographerCommitPreview {
  const suggestedCommitGroups = [
    dirtyTree.likelySafeDocsFiles.length > 0
      ? {
          label: "Docs review group",
          files: dirtyTree.likelySafeDocsFiles,
          recommendation: "Review as a possible docs-only commit after checks pass.",
        }
      : null,
    dirtyTree.riskySourceFiles.length > 0
      ? {
          label: "Source review group",
          files: dirtyTree.riskySourceFiles,
          recommendation: "Hold until scope, tests, and protected lanes are reviewed.",
        }
      : null,
  ].filter((group): group is { label: string; files: string[]; recommendation: string } =>
    group !== null,
  );
  const filesThatShouldNotBeCommittedYet = uniqueStrings([
    ...dirtyTree.generatedCacheFiles,
    ...dirtyTree.unknownFiles,
    ...dirtyTree.protectedLaneFiles.map((match) => match.path),
  ]);
  const missingVerification = [
    "git status --branch --short",
    "git diff --check",
    "npm test -- run src/app/map/__tests__/map-information-architecture.test.ts src/app/map/__tests__/map-display-shell.test.ts",
    "npm run typecheck",
    "npm run build",
  ];

  return {
    suggestedCommitGroups,
    filesThatShouldNotBeCommittedYet,
    missingVerification,
    suggestedCommitMessageDraft: suggestedCommitMessageFor(dirtyTree),
    authority: "preview-only",
    canStage: false,
    canCommit: false,
  };
}

export const cartographerMapOperatorQuestions = [
  "What is Cartographer's status?",
  "Can Cartographer act?",
  "What blocks action?",
  "How is the dirty tree grouped?",
  "Are commit and push ready?",
  "Which projects need attention?",
  "Which advisory helpers are watching only?",
  "What manual check should Britton run?",
  "Where are raw diagnostics?",
] as const;

export const cartographerMapReviewOnlyReadinessFields = [
  "Commit readiness",
  "Push readiness",
  "Merge readiness",
  "Queue readiness",
  "Approval readiness",
  "Preflight readiness",
  "Kill switch status",
] as const;

export const cartographerMapOperatorDecisionPacketFields = [
  "Decision default",
  "Current HEAD",
  "Dirty tree summary",
  "Protected lane summary",
  "Required proof",
  "Missing proof",
  "Blocked actions",
  "Kill switch state",
  "Manual decision",
] as const;

export const cartographerMapLiveStateFields = [
  "Branch",
  "HEAD",
  "Dirty state",
  "Protected-lane state",
  "Repo-map source",
  "Recommendation",
] as const;

export const cartographerMapReadOnlySourceFields = [
  "Live state",
  "Status",
  "Repo map",
  "Sub-cartographers",
  "Trust score",
  "Audit trail",
] as const;

export const cartographerMapSubCartographerFields = [
  "Roles observed",
  "Routes observed",
  "Outputs observed",
  "Maximum authority",
  "Forbidden actions",
] as const;

export const cartographerMapTrustAuditFields = [
  "Score",
  "Grade",
  "Authority granted",
  "Signals needing review",
  "Audit event count",
  "Audit result summary",
] as const;

export const cartographerMapApprovalTokenFields = [
  "Runtime status",
  "Validation status",
  "Consumption preview",
  "Blocked reasons",
  "Safe next action",
] as const;

export const cartographerMapQueuePanelFields = [
  "Queue status",
  "Run-next status",
  "One-task selection",
  "Execution blocked",
  "Safe next action",
] as const;

export const cartographerMapWorkflowPanelFields = [
  "Active runs",
  "Recent runs",
  "Workflow status",
  "Step status",
  "Blocked reasons",
] as const;

export const cartographerMapStopControlFields = [
  "Kill switch state",
  "Pause control",
  "Cancel control",
  "Timeout control",
  "Retry control",
] as const;

export const cartographerMapReceiptEvidenceFields = [
  "Receipt journal",
  "Evidence artifacts",
  "Approved docs paths",
  "Missing evidence",
  "Write blocked",
] as const;

function buildCleanupPlanPreview({
  likelySafeDocsFiles,
  riskySourceFiles,
  generatedCacheFiles,
  unknownFiles,
  protectedLaneFiles,
}: Pick<
  CartographerDirtyTreePreview,
  | "likelySafeDocsFiles"
  | "riskySourceFiles"
  | "generatedCacheFiles"
  | "unknownFiles"
  | "protectedLaneFiles"
>): string[] {
  const plan = [
    "Review the grouped dirty tree manually before any cleanup, staging, commit, or discard.",
  ];

  if (likelySafeDocsFiles.length > 0) {
    plan.push("Docs-like files may be easiest to review first.");
  }
  if (riskySourceFiles.length > 0 || protectedLaneFiles.length > 0) {
    plan.push("Source or protected-lane files need explicit human scope review.");
  }
  if (generatedCacheFiles.length > 0) {
    plan.push("Generated/cache files should be inspected manually; do not clean from /map.");
  }
  if (unknownFiles.length > 0) {
    plan.push("Unknown files stay blocked until Britton classifies them.");
  }

  return plan;
}

function suggestedCommitMessageFor(dirtyTree: CartographerDirtyTreePreview): string {
  if (dirtyTree.totalDirtyFiles === 0) {
    return "chore: confirm clean cartographer preview baseline";
  }

  if (
    dirtyTree.likelySafeDocsFiles.length > 0 &&
    dirtyTree.riskySourceFiles.length === 0 &&
    dirtyTree.unknownFiles.length === 0 &&
    dirtyTree.generatedCacheFiles.length === 0
  ) {
    return "docs: update cartographer preview planning";
  }

  return "chore: review cartographer preview model changes";
}

function branchChangedAreas(dirtyTree: CartographerDirtyTreePreview): string[] {
  const areas: string[] = [];
  if (dirtyTree.likelySafeDocsFiles.length > 0) {
    areas.push("docs");
  }
  if (dirtyTree.riskySourceFiles.length > 0) {
    areas.push("source");
  }
  if (dirtyTree.generatedCacheFiles.length > 0) {
    areas.push("generated/cache");
  }
  if (dirtyTree.unknownFiles.length > 0) {
    areas.push("unknown");
  }
  if (dirtyTree.protectedLaneFiles.length > 0) {
    areas.push("protected lanes");
  }
  return areas.length > 0 ? areas : ["none reported"];
}

function branchPushBlockers(input: CartographerBranchPushPreviewInput): string[] {
  const blockers: string[] = [];
  if (!input.currentBranch) {
    blockers.push("current branch unknown");
  }
  if (!input.currentHead) {
    blockers.push("HEAD unknown");
  }
  if (input.dirtyTree.totalDirtyFiles > 0) {
    blockers.push("dirty tree needs manual review");
  }
  if (input.dirtyTree.protectedLaneCount > 0) {
    blockers.push("protected-lane files need explicit review");
  }
  if ((input.behind ?? 0) > 0) {
    blockers.push("branch is behind upstream");
  }
  if (!input.upstream) {
    blockers.push("upstream unknown");
  }
  return blockers;
}

function pushProofNeeded(input: CartographerBranchPushPreviewInput): string[] {
  return [
    "manual branch check",
    "manual dirty-tree review",
    "manual verification results",
    (input.ahead ?? 0) > 0 ? "separate push approval" : "no local push proof needed",
  ];
}

function aheadBehindSummary(
  ahead: number | null | undefined,
  behind: number | null | undefined,
  upstream: string | null | undefined,
): string {
  const aheadText = typeof ahead === "number" ? ahead : "unknown";
  const behindText = typeof behind === "number" ? behind : "unknown";
  return `${aheadText} ahead, ${behindText} behind${upstream ? ` ${upstream}` : ""}`;
}

function isLikelySafeDocsFile(path: string): boolean {
  const normalized = normalizePreviewPath(path);
  return (
    normalized.startsWith("docs/") ||
    normalized.endsWith(".md") ||
    normalized.endsWith(".mdx")
  );
}

function isRiskySourceFile(path: string): boolean {
  const normalized = normalizePreviewPath(path);
  return (
    normalized.startsWith("src/") ||
    normalized.startsWith("source_proxy/") ||
    normalized.startsWith("config/") ||
    normalized === "package.json" ||
    normalized === "next.config.ts" ||
    normalized.startsWith(".env")
  );
}

function isGeneratedCacheFile(path: string): boolean {
  const normalized = normalizePreviewPath(path);
  return (
    normalized.startsWith(".next/") ||
    normalized.startsWith(".next.") ||
    normalized.includes("/__pycache__/") ||
    normalized.endsWith(".pyc") ||
    normalized.startsWith("repomix") ||
    normalized.includes("/repomix")
  );
}

function uniqueStrings(values: readonly string[]): string[] {
  return Array.from(new Set(values.filter((value) => value.trim().length > 0)));
}

function normalizePreviewPath(path: string): string {
  return path.trim().replaceAll("\\", "/");
}
