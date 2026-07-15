export type CodingShellStatus = "active" | "legacy" | "experimental";
export type CodingApiRouteStatus = "canonical" | "supporting" | "dormant";

export type CodingShellRegistryEntry = {
  id: string;
  status: CodingShellStatus;
  route: string | null;
  component: string;
  ownerDecision: "canonical" | "alternate" | "undecided";
  rollback: string;
};

export type CodingApiRouteRegistryEntry = {
  id: string;
  status: CodingApiRouteStatus;
  route: string;
  sourceProxyRoute: string | null;
  ownerDecision: "canonical" | "supporting" | "dormant";
  operatorSurface: string;
  dormantReason: string | null;
};

// Owns the /coding shell decision record. Labs-only alternates cannot become
// production dependencies or navigation targets.
export const codingShellRegistry = [
  {
    id: "coding-cockpit-shell",
    status: "active",
    route: "/coding",
    component: "src/components/coding/CodingCockpitShell.tsx",
    ownerDecision: "canonical",
    rollback: "Revert /coding/page.tsx to direct CodingCockpitShell import only.",
  },
  {
    id: "coding-command-center-shell",
    status: "experimental",
    route: null,
    component: "labs/coding/CodingCommandCenterShell.tsx",
    ownerDecision: "alternate",
    rollback: "Restore only as an explicit labs comparison; never remount it in production.",
  },
  {
    id: "coding-agent-interface-lab",
    status: "experimental",
    route: null,
    component: "labs/coding/CodingAgentInterface.tsx",
    ownerDecision: "alternate",
    rollback: "Restore only as an explicit labs comparison; never issue or consume production approvals.",
  },
] as const satisfies readonly CodingShellRegistryEntry[];

export const activeCodingShell = codingShellRegistry.find(
  (shell) => shell.status === "active" && shell.route === "/coding",
) ?? codingShellRegistry[0];

export function codingShellById(id: string): CodingShellRegistryEntry | undefined {
  return codingShellRegistry.find((shell) => shell.id === id);
}

export function codingShellsByStatus(status: CodingShellStatus): CodingShellRegistryEntry[] {
  return codingShellRegistry.filter((shell) => shell.status === status);
}

export const codingApiRouteRegistry = [
  {
    id: "prompt-packet",
    status: "canonical",
    route: "/v1/decisions/prompt-packet",
    sourceProxyRoute: "/v1/decisions/prompt-packet",
    ownerDecision: "canonical",
    operatorSurface: "Task packet, repo research, provider truth, selected target, and allowed files.",
    dormantReason: null,
  },
  {
    id: "diff-preview",
    status: "canonical",
    route: "/v1/verification/diff-preview",
    sourceProxyRoute: "/v1/verification/diff-preview",
    ownerDecision: "canonical",
    operatorSurface: "Verifier result, changed files, checks, and approval gate.",
    dormantReason: null,
  },
  {
    id: "execute-approved",
    status: "canonical",
    route: "/v1/actions/execute-approved",
    sourceProxyRoute: "/v1/actions/execute-approved",
    ownerDecision: "canonical",
    operatorSurface: "Approved apply, fail-closed causal contract, reversal, and no hidden success.",
    dormantReason: null,
  },
  {
    id: "durable-runs",
    status: "supporting",
    route: "/v1/coding/runs",
    sourceProxyRoute: null,
    ownerDecision: "supporting",
    operatorSurface: "Route-backed trial persistence, stop, resume, and mobile sync state.",
    dormantReason: null,
  },
  {
    id: "codex-adapter",
    status: "dormant",
    route: "/v1/coding/codex",
    sourceProxyRoute: "/v1/coding/codex",
    ownerDecision: "dormant",
    operatorSurface: "Not used by canonical /coding manual apply flow.",
    dormantReason: "Legacy adapter; guarded by SPIRIT_CODING_USE_PROXY and not mounted as canonical.",
  },
  {
    id: "bounded-diff-preview",
    status: "dormant",
    route: "/v1/coding/bounded-diff-preview",
    sourceProxyRoute: "/v1/coding/bounded-diff-preview",
    ownerDecision: "dormant",
    operatorSurface: "Not used by canonical /coding manual apply flow.",
    dormantReason: "Legacy preview adapter; canonical preview runs through /v1/decisions/prompt-packet then /v1/verification/diff-preview.",
  },
  {
    id: "research-preview",
    status: "dormant",
    route: "/v1/coding/research-preview",
    sourceProxyRoute: null,
    ownerDecision: "dormant",
    operatorSurface: "Advisory/read-only route only.",
    dormantReason: "Research is advisory until consumed through the canonical prompt-packet route.",
  },
  {
    id: "helper-agents-preview",
    status: "dormant",
    route: "/v1/coding/helper-agents/preview",
    sourceProxyRoute: null,
    ownerDecision: "dormant",
    operatorSurface: "Advisory/read-only route only.",
    dormantReason: "Helper packets cannot dispatch, approve, apply, commit, or push.",
  },
] as const satisfies readonly CodingApiRouteRegistryEntry[];

export const activeCodingApiRouteSequence = codingApiRouteRegistry.filter(
  (route) => route.status === "canonical",
);

export function codingApiRoutesByStatus(status: CodingApiRouteStatus): CodingApiRouteRegistryEntry[] {
  return codingApiRouteRegistry.filter((route) => route.status === status);
}
