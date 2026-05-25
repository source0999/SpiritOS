import type { CodingProviderModelOption, CodingProviderStatus } from "@/lib/coding/model-provider-status";
import type { CodingWorkspaceContext } from "@/lib/coding/workspace-context";

export type CodingSettingsState = "current-session" | "display-only" | "gated" | "unavailable";

export type CodingSettingsRow = {
  authority: string;
  id:
    | "workspace"
    | "provider-model"
    | "safety-authority"
    | "notifications"
    | "usage-time"
    | "cli"
    | "config-write-gate";
  label: string;
  source: string;
  state: CodingSettingsState;
  value: string;
  writable: false;
};

export function buildCodingSettingsRows(input: {
  model: CodingProviderModelOption;
  provider: CodingProviderStatus;
  workspace: CodingWorkspaceContext;
}): CodingSettingsRow[] {
  return [
    {
      authority: "No project creation, Windows write, branch, worktree, commit, or push action.",
      id: "workspace",
      label: "Workspace settings",
      source: "Workspace context helper and dirty-tree terminal evidence.",
      state: "display-only",
      value: `${input.workspace.label}; ${input.workspace.access}; ${input.workspace.availability}`,
      writable: false,
    },
    {
      authority: "No provider call, API-cost action, auth/config/env edit, apply, commit, or push.",
      id: "provider-model",
      label: "Provider/model settings",
      source: "Provider/model status helper; selected per chat.",
      state: input.model.previewAvailable ? "display-only" : "unavailable",
      value: `${input.provider.label}; ${input.model.modelLabel}; ${input.model.status}`,
      writable: false,
    },
    {
      authority: "No apply, execute-approved, commit, push, queue, worker, provider, or shell authority.",
      id: "safety-authority",
      label: "Safety/authority settings",
      source: "Source Proxy gate state and receipt authority statement.",
      state: "display-only",
      value: "Safe preview/apply wiring remains gated.",
      writable: false,
    },
    {
      authority: "No OS notification permission prompt, sound, desktop notification, or background watcher.",
      id: "notifications",
      label: "Notification settings",
      source: "PR-6 future alert plan; current shell status surfaces only.",
      state: "gated",
      value: "In-app status only; OS notifications gated.",
      writable: false,
    },
    {
      authority: "No fake tokens, fake cost, provider call, budget write, or durable usage store.",
      id: "usage-time",
      label: "Usage/time settings",
      source: "UI-local progress timer and future PR-5 usage/time plan.",
      state: "current-session",
      value: "Current-session progress time or unavailable; token/cost require real provider reports.",
      writable: false,
    },
    {
      authority: "No shell mutation, command execution, queue, worker, or terminal write from settings.",
      id: "cli",
      label: "CLI settings",
      source: "Sandbox terminal evidence is read-only; command result source is not wired into this shell.",
      state: "unavailable",
      value: "CLI timing/status unavailable here; read-only terminal proof remains future/gated.",
      writable: false,
    },
    {
      authority: "No config/env/auth writes, secret writes, provider routing changes, or durable preferences.",
      id: "config-write-gate",
      label: "Config write gate",
      source: "PR-4.3 future config write gate.",
      state: "gated",
      value: "Writable settings require separate Britton approval.",
      writable: false,
    },
  ];
}

export function settingsReceiptLines(rows: CodingSettingsRow[]): string[] {
  return [
    "Settings surface: display-only",
    ...rows.map(
      (row) =>
        `${row.label}: ${row.state}; value=${row.value}; source=${row.source}; writable=${row.writable}; authority=${row.authority}`,
    ),
  ];
}
