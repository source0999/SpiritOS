export type CodingWorkspaceContextId = "spiritos" | "windows-projects" | "remote-skipped";

export type CodingWorkspaceAvailability = "available" | "future-target" | "skipped";

export type CodingWorkspaceAccess = "read-list-only" | "unavailable";

export type CodingWorkspaceContext = {
  access: CodingWorkspaceAccess;
  authority: string;
  availability: CodingWorkspaceAvailability;
  badge: string;
  dirtyState: string;
  id: CodingWorkspaceContextId;
  label: string;
  path: string;
  receiptLabel: string;
  status: string;
};

export type WorkspaceFolderProofRow = {
  evidence: string;
  label: string;
  state: "available" | "blocked" | "unavailable";
};

export const DEFAULT_CODING_WORKSPACE_CONTEXT_ID: CodingWorkspaceContextId = "spiritos";

export const CODING_WORKSPACE_CONTEXTS: CodingWorkspaceContext[] = [
  {
    access: "read-list-only",
    authority: "Selected workspace; no commit, push, branch, or worktree action is available here",
    availability: "available",
    badge: "selected",
    dirtyState: "Dirty/untracked warning is active from terminal evidence; this UI does not clean git state.",
    id: "spiritos",
    label: "SpiritOS",
    path: "/home/source/SpiritOS",
    receiptLabel: "current repo; read/list-only context; writes still gated",
    status: "Default repo workspace; writes still require preview, approval, and apply gates",
  },
  {
    access: "unavailable",
    authority: "Future target label only; no Windows bridge call, write, project creation, or folder read runs here",
    availability: "future-target",
    badge: "future target",
    dirtyState: "External dirty state is unavailable; no Windows workspace mutation is claimed.",
    id: "windows-projects",
    label: "C:\\Projects",
    path: "C:\\Projects",
    receiptLabel: "future Windows target; bridge-gated and unavailable",
    status: "Future Windows project source; unavailable until explicitly approved and configured",
  },
  {
    access: "unavailable",
    authority: "Remote connections are skipped for PR-2; no connector, clone, mount, or network workspace action is available",
    availability: "skipped",
    badge: "skipped",
    dirtyState: "Remote dirty state is unavailable because remote workspace support is skipped.",
    id: "remote-skipped",
    label: "Remote workspace",
    path: "not connected",
    receiptLabel: "remote skipped; unavailable in PR-2",
    status: "Remote project connections are skipped until a later explicit plan",
  },
];

export const WORKSPACE_FOLDER_PROOF_ROWS: WorkspaceFolderProofRow[] = [
  {
    evidence: "source_proxy/context/workspace_tools.py returns read_only_workspace_listing.",
    label: "List folder",
    state: "available",
  },
  {
    evidence: "source_proxy/context/workspace_tools.py returns read_only_workspace_file_excerpt.",
    label: "Read file excerpt",
    state: "available",
  },
  {
    evidence: "Hidden and secret-shaped names are excluded or blocked before display.",
    label: "Secret-shaped paths",
    state: "blocked",
  },
  {
    evidence: "Foreign absolute paths and ../ escapes return path_escape.",
    label: "Path escape",
    state: "blocked",
  },
  {
    evidence: "No write route, project creation, branch, worktree, commit, or push action is exposed.",
    label: "Writes",
    state: "unavailable",
  },
];

export function codingWorkspaceContextById(
  id: CodingWorkspaceContextId | string | null | undefined,
): CodingWorkspaceContext {
  return (
    CODING_WORKSPACE_CONTEXTS.find((context) => context.id === id) ??
    CODING_WORKSPACE_CONTEXTS[0]
  );
}

export function workspaceTruthTableRows(): string[] {
  return CODING_WORKSPACE_CONTEXTS.map(
    (context) =>
      `${context.label}: availability=${context.availability}; access=${context.access}; authority=${context.authority}`,
  );
}

export function workspaceFolderProofRows(): WorkspaceFolderProofRow[] {
  return WORKSPACE_FOLDER_PROOF_ROWS;
}

export function workspaceReceiptLines(context: CodingWorkspaceContext): string[] {
  return [
    `Workspace context: ${context.label}`,
    `Workspace path: ${context.path}`,
    `Workspace availability: ${context.availability}`,
    `Workspace access: ${context.access}`,
    `Workspace dirty state: ${context.dirtyState}`,
    `Workspace authority: ${context.authority}`,
  ];
}
