import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import CodingCommandCenterShell from "@/components/coding/CodingCommandCenterShell";
import {
  PROXY_TRIAL_BANK_EXPECTED_RECORD_COUNT,
  PROXY_TRIAL_BANK_VERSION,
  PROXY_TRIAL_PROMPTS,
  PROXY_TRIAL_SHARED_BANK_INTEGRATED,
  proxyTrialWidgetDryRunEvidence,
} from "@/lib/coding/proxy-trial-prompts";

const navMock = vi.hoisted(() => ({ path: "/coding" }));
const humanTrialPrompt =
  "Add a short note to docs/proxy-test-runner-plan.md explaining that a human browser productive preview trial only passes when /coding shows the target file, allowed_files, preview diff, changed files, human review result, and verification result. Do not apply, commit, or push.";
const selectedTrialPrompt =
  "Add a short note explaining that human browser productive preview trials only pass when /coding shows target file, allowed_files, preview diff, changed files, human review result, and verification result. Do not apply, commit, or push.";

vi.mock("next/navigation", () => ({
  usePathname: () => navMock.path,
}));

beforeEach(() => {
  window.localStorage.removeItem("spiritos:desktop-nav-collapsed");
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
  window.localStorage.removeItem("spiritos:coding-command-center:task-story");
  window.localStorage.removeItem("spiritos:desktop-nav-collapsed");
});

function taskCreateResponse(taskId = "task-123") {
  return new Response(JSON.stringify({ task: { id: taskId } }), { status: 200 });
}

function openProxyDetails() {
  const diagnosticsButton = screen.queryByRole("button", { name: "Diagnostics" });
  if (diagnosticsButton?.getAttribute("aria-expanded") !== "true") {
    fireEvent.click(screen.getByRole("button", { name: "Diagnostics" }));
  }
  fireEvent.click(screen.getByRole("button", { name: "Details" }));
}

function openProxyAdvancedControls() {
  const diagnosticsButton = screen.queryByRole("button", { name: "Diagnostics" });
  if (diagnosticsButton?.getAttribute("aria-expanded") !== "true") {
    fireEvent.click(screen.getByRole("button", { name: "Diagnostics" }));
  }
  fireEvent.click(screen.getByText("Advanced trial controls"));
}

function openProxyAuditLogs() {
  const diagnosticsButton = screen.queryByRole("button", { name: "Diagnostics" });
  if (diagnosticsButton?.getAttribute("aria-expanded") !== "true") {
    fireEvent.click(screen.getByRole("button", { name: "Diagnostics" }));
  }
  if (!screen.queryByText("Preview audit logs")) {
    openProxyDetails();
  }
  fireEvent.click(screen.getByText("Preview audit logs"));
}

function openRawDiagnosticStatusValues() {
  const diagnosticsButton = screen.queryByRole("button", { name: "Diagnostics" });
  if (diagnosticsButton?.getAttribute("aria-expanded") !== "true") {
    fireEvent.click(screen.getByRole("button", { name: "Diagnostics" }));
  }
  fireEvent.click(screen.getByText("Raw diagnostic status values"));
}

function openRightRailDetails() {
  openEvidenceDrawer();
  const evidenceDetails = screen.getByText("Evidence Details and Receipts").closest("details");
  if (!evidenceDetails?.hasAttribute("open")) {
    fireEvent.click(screen.getByText("Evidence Details and Receipts"));
  }
}

function openProofRunControls() {
  const diagnosticsButton = screen.queryByRole("button", { name: "Diagnostics" });
  if (diagnosticsButton?.getAttribute("aria-expanded") !== "true") {
    fireEvent.click(screen.getByRole("button", { name: "Diagnostics" }));
  }
  const proofRunControls = screen.getByText("Proof run controls").closest("details");
  if (!proofRunControls?.hasAttribute("open")) {
    fireEvent.click(screen.getByText("Proof run controls"));
  }
}

function openDiagnosticsDrawer() {
  const diagnosticsButton = screen.getByRole("button", { name: "Diagnostics" });
  if (diagnosticsButton.getAttribute("aria-expanded") !== "true") {
    fireEvent.click(diagnosticsButton);
  }
}

function openEvidenceDrawer() {
  const evidenceButton = screen.getByRole("button", { name: "Evidence" });
  if (evidenceButton.getAttribute("aria-expanded") !== "true") {
    fireEvent.click(evidenceButton);
  }
}

function expectActiveRunState(state: string) {
  expect(
    screen
      .getAllByLabelText("Active run state")
      .some((element) => element.textContent?.includes(`state: ${state}`)),
  ).toBe(true);
}

function openEnvironmentDetails() {
  const environmentDetails = screen.getByText("Environment Details").closest("details");
  if (!environmentDetails?.hasAttribute("open")) {
    fireEvent.click(screen.getByText("Environment Details"));
  }
}

function expectPlan8AForbiddenControlsAbsent() {
  [
    /apply approved diff/i,
    /^apply$/i,
    /^commit$/i,
    /^push$/i,
    /execute-approved/i,
    /execute approved/i,
    /run worker/i,
    /start worker/i,
    /execute queue/i,
    /run queue/i,
    /provider call/i,
    /live preview/i,
    /shell execution/i,
    /consume approval token/i,
    /post mutation/i,
    /route execution/i,
  ].forEach((name) => {
    expect(screen.queryByRole("button", { name })).not.toBeInTheDocument();
  });
}

describe("CodingCommandCenterShell", () => {
  it("renders the VoidCore command-center shell without live coding authority", () => {
    render(<CodingCommandCenterShell />);

    expect(screen.getByRole("heading", { level: 1, name: "Coding" })).toBeInTheDocument();
    const desktopNav = screen.getByRole("navigation", {
      name: "Spirit app desktop navigation",
    });
    expect(within(desktopNav).getByRole("link", { name: "Source" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(within(desktopNav).getByRole("link", { name: "Dashboard" })).toHaveAttribute("href", "/");
    const collapseNavButton = within(desktopNav).getByRole("button", {
      name: "Collapse desktop navigation",
    });
    expect(collapseNavButton).toHaveAttribute("aria-expanded", "true");
    fireEvent.click(collapseNavButton);
    expect(within(desktopNav).getByRole("button", { name: "Expand desktop navigation" }))
      .toHaveAttribute("aria-expanded", "false");
    const mobileNav = screen.getByRole("navigation", {
      name: "Spirit app mobile navigation",
    });
    expect(within(mobileNav).getByRole("link", { name: "Source" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    const startNewChatButton = screen.getByRole("button", { name: "Start new chat" });
    expect(startNewChatButton).toBeInTheDocument();
    expect(startNewChatButton).not.toBeDisabled();
    expect(startNewChatButton).toHaveTextContent("New chat");
    expect(screen.getByRole("button", { name: "Selected workspace: SpiritOS" })).toHaveTextContent(
      "/home/source/SpiritOS",
    );
    expect(screen.getByRole("button", { name: "Selected workspace: SpiritOS" })).toHaveTextContent(
      "Selected workspace; no commit, push, branch, or worktree action is available here",
    );
    const futureWorkspaceButton = screen.getByRole("button", {
      name: "C:\\Projects future target unavailable",
    });
    expect(futureWorkspaceButton).toBeDisabled();
    expect(futureWorkspaceButton).toHaveAttribute("aria-pressed", "false");
    expect(futureWorkspaceButton).toHaveTextContent(
      "Future Windows project source; unavailable until explicitly approved and configured",
    );
    expect(futureWorkspaceButton).toHaveTextContent(
      "Future target label only; no Windows bridge call, write, project creation, or folder read runs here",
    );
    expect(screen.getByRole("button", { name: "Remote workspace skipped" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Start new project placeholder" }))
      .toHaveAttribute("aria-disabled", "true");
    expect(screen.getByRole("button", { name: "Start new project placeholder" }))
      .toBeDisabled();
    expect(screen.getByText("Dry-run placeholder until safe creation exists")).toBeInTheDocument();
    expect(screen.getByRole("searchbox", { name: "Search coding chats" })).toBeInTheDocument();

    const chatNav = screen.getByRole("navigation", { name: "Coding chats" });
    expect(within(chatNav).getByRole("button", { name: /New coding chat/ })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(within(chatNav).getByRole("button", { name: /Approval queue/ })).toBeInTheDocument();

    expect(screen.getByRole("heading", { level: 2, name: "New coding chat" })).toBeInTheDocument();
    expect(screen.getByText(/Default repo workspace/)).toBeInTheDocument();
    expect(screen.getByText(/Local session only/)).toBeInTheDocument();
    expect(screen.getByLabelText("Active chat session")).toHaveTextContent(
      "Active session: draft",
    );
    expect(screen.getByLabelText("Persistence boundary")).toHaveTextContent(
      "Chat list: current-session only.",
    );
    expect(screen.getByLabelText("Persistence boundary")).toHaveTextContent(
      "Durable chat history remains gated.",
    );
    expect(screen.getAllByText("SpiritOS").length).toBeGreaterThan(0);
    expect(screen.getByText("Local LLM default")).toBeInTheDocument();
    expect(screen.getByText("GPT/cloud unavailable")).toBeInTheDocument();
    expect(screen.getByText("Default route where local coding support is available."))
      .toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Codex worker: proposal-only" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Future providers: future" })).toBeInTheDocument();
    const providerModelSelector = screen.getByRole("region", { name: "Provider model selector" });
    expect(within(providerModelSelector).getByRole("button", {
      name: "Local default: default · preview available",
    })).toHaveAttribute("aria-pressed", "true");
    expect(within(providerModelSelector).getByRole("button", {
      name: "GPT/cloud: unavailable · preview blocked",
    })).toHaveAttribute("aria-pressed", "false");
    expect(
      screen.getByText("Model: Local LLM default. No external API cost; local/default intent only."),
    ).toBeInTheDocument();
    expect(screen.getByText("Intent: local LLM route. No provider call has run yet."))
      .toBeInTheDocument();
    expect(screen.getByText("Active task area")).toBeInTheDocument();
    expect(screen.getByText("SpiritOS context is selected for this chat")).toBeInTheDocument();
    expect(
      screen.getByText(
        "C:\\Projects is a future target; no bridge, folder access, or project creation is available from this selector.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Coding command composer")).toHaveAttribute(
      "placeholder",
      "Ask for a plan, start a coding task, or gather repo context.",
    );
    expect(screen.getByRole("button", { name: "Desktop submit task" })).toBeDisabled();
    expect(screen.queryByLabelText("Proxy trial prompt widget")).not.toBeInTheDocument();
    openDiagnosticsDrawer();
    expect(screen.getAllByText("Proxy Trial Prompts").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("Current step: paste the copy-paste task, click Coding mode, then Submit task."),
    ).toHaveLength(3);
    expect(screen.getAllByText("Preview only. Human review required. No apply, commit, or push from this widget.").length).toBeGreaterThan(0);
    expect(
      screen.getByText(
        "Preview-only diagnostics. No worker, provider, queue, apply, commit, or push authority is added.",
      ),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Load prompt" }).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Mobile load prompt" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Mobile command composer" }).className)
      .toContain("--shell-safe-area-bottom");
    const compactDiagnosticWidget = screen.getByRole("region", {
      name: "Compact proxy diagnostic widget",
    });
    expect(compactDiagnosticWidget).toBeInTheDocument();
    expect(screen.getByText("Proxy Test")).toBeInTheDocument();
    expect(screen.getByText("Grade B-")).toBeInTheDocument();
    expect(screen.getByText("Useful: 8/100")).toBeInTheDocument();
    expect(screen.getByText("Safely blocked: 91")).toBeInTheDocument();
    expectActiveRunState("idle");
    expect(screen.getByText("Proof run controls").closest("details"))
      .not.toHaveAttribute("open");
    openProofRunControls();
    expect(screen.getByRole("button", { name: "Run 10" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run 25" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run 100" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Run" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy diag" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Expand proxy trial prompts" }))
      .not.toBeInTheDocument();
    expect(screen.queryByText("Preview audit logs")).not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Coding advisory helper fleet" }))
      .not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Codex-like functionality layer" }))
      .not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "100 prompt diagnostic summary" }))
      .not.toBeInTheDocument();
    openProxyDetails();
    expect(screen.getByRole("combobox", { name: "Switch proxy trial" })).toHaveValue("HB-01");
    expect(screen.getByRole("combobox", { name: "Mobile switch proxy trial" })).toHaveValue(
      "HB-01",
    );
    expect(screen.getByRole("region", { name: "Proxy preflight overview" })).toBeInTheDocument();
    expect(screen.getByText("Preflight Overview")).toBeInTheDocument();
    expect(screen.getByText("Current gate")).toBeInTheDocument();
    expect(screen.getByText("Browser verification required")).toBeInTheDocument();
    expect(screen.getByText("Cartographer dependency")).toBeInTheDocument();
    expect(screen.getByText("NO-GO if unavailable")).toBeInTheDocument();
    expect(screen.getByText("Preflight authority")).toBeInTheDocument();
    expect(screen.getByText("Status only, no apply-capable work")).toBeInTheDocument();
    expect(screen.getByText("Verification requirements")).toBeInTheDocument();
    expect(screen.getByText("Exact checks before closeout")).toBeInTheDocument();
    expect(screen.getByText("Safety lock")).toBeInTheDocument();
    expect(screen.getByText("No authority changed")).toBeInTheDocument();
    expect(screen.getByText("Main bottleneck")).toBeInTheDocument();
    expect(screen.getByText("Low productive preview yield")).toBeInTheDocument();
    expect(screen.getByText("Next useful action")).toBeInTheDocument();
    expect(screen.getByText("Reduce blockers before live work")).toBeInTheDocument();
    const activeRunStateSummary = screen.getByRole("region", {
      name: "Active run state summary",
    });
    expect(within(activeRunStateSummary).getByText("idle")).toBeInTheDocument();
    expect(
      within(activeRunStateSummary).getByText(
        "No local diagnostic or task preview is active.",
      ),
    ).toBeInTheDocument();
    expect(
      within(activeRunStateSummary).getByText(/UI-local state only/),
    ).toBeInTheDocument();
    const diagnosticTimeline = screen.getByRole("region", {
      name: "Current diagnostic lifecycle timeline",
    });
    expect(within(diagnosticTimeline).getByText("Diagnostic lifecycle")).toBeInTheDocument();
    expect(within(diagnosticTimeline).getByText("source: UI-local")).toBeInTheDocument();
    expect(within(diagnosticTimeline).getByText("Idle")).toBeInTheDocument();
    expect(within(diagnosticTimeline).getByText("Queued")).toBeInTheDocument();
    expect(within(diagnosticTimeline).getByText("Preparing diagnostic packet"))
      .toBeInTheDocument();
    expect(
      within(diagnosticTimeline).getByText(
        "No backend streamed task events are claimed by this timeline.",
      ),
    ).toBeInTheDocument();
    const promptStagingPreview = screen.getByRole("region", {
      name: "Prompt staging preview",
    });
    expect(within(promptStagingPreview).getByText("Prompt staging preview")).toBeInTheDocument();
    expect(within(promptStagingPreview).getByText("display-only")).toBeInTheDocument();
    ["current", "pending", "completed", "blocked"].forEach((status) => {
      expect(within(promptStagingPreview).getByText(status)).toBeInTheDocument();
    });
    [
      "preview queue only",
      "no worker running",
      "no provider call",
      "no apply authority",
    ].forEach((label) => {
      expect(within(promptStagingPreview).getByText(label)).toBeInTheDocument();
    });
    expect(within(promptStagingPreview).queryByText(/running queue/i)).not.toBeInTheDocument();
    expect(
      within(promptStagingPreview).getByText(
        "Staged prompts are visible for review only; this list does not execute a queue.",
      ),
    ).toBeInTheDocument();
    const runHistory = screen.getByRole("region", {
      name: "Current-session run history",
    });
    expect(within(runHistory).getByText("Current-session run history")).toBeInTheDocument();
    expect(within(runHistory).getByText("current-session only")).toBeInTheDocument();
    expect(within(runHistory).getByText("No current-session run history yet."))
      .toBeInTheDocument();
    expect(
      within(runHistory).getByText(
        "This panel does not claim durable history and does not write receipts, files, or backend storage.",
      ),
    ).toBeInTheDocument();
    const helperFleet = screen.getByRole("region", { name: "Coding advisory helper fleet" });
    expect(within(helperFleet).getByText("Advisory Helper Fleet")).toBeInTheDocument();
    expect(within(helperFleet).getAllByText(/advisory_only/).length).toBeGreaterThan(0);
    [
      "Component Mapper",
      "Safety Reviewer",
      "Test Scribe",
      "Change Scribe",
      "Runbook Scribe",
      "Blueprint Scribe",
      "Commit Scribe",
      "Release Steward",
    ].forEach((helperName) => {
      expect(within(helperFleet).getByText(helperName)).toBeInTheDocument();
    });
    expect(within(helperFleet).getByText(/No helper is running, applying, calling providers/))
      .toBeInTheDocument();
    expect(within(helperFleet).queryByRole("button", { name: /start|run|apply|commit|push|provider|queue|worker|live/i }))
      .not.toBeInTheDocument();
    const functionalityLayer = screen.getByRole("region", {
      name: "Codex-like functionality layer",
    });
    expect(within(functionalityLayer).getByText("Codex-like Functionality Layer"))
      .toBeInTheDocument();
    [
      "Live preview work",
      "Multiple running prompts",
      "Progress/loading",
      "Run history",
      "Copyable diagnostics",
      "Task queue previews",
      "Preview receipts",
    ].forEach((label) => {
      expect(within(functionalityLayer).getByText(label)).toBeInTheDocument();
    });
    expect(within(functionalityLayer).getByText("gated functionality")).toBeInTheDocument();
    expect(within(functionalityLayer).getByText(/Phase 7 live preview remains disabled/))
      .toBeInTheDocument();
    expect(within(functionalityLayer).getByText(/No live preview, queue, worker/))
      .toBeInTheDocument();
    expect(within(functionalityLayer).queryByRole("button", { name: /start|run|apply|commit|push|provider|queue|worker|live/i }))
      .not.toBeInTheDocument();
    expect(PROXY_TRIAL_SHARED_BANK_INTEGRATED).toBe(true);
    expect(PROXY_TRIAL_PROMPTS).toHaveLength(PROXY_TRIAL_BANK_EXPECTED_RECORD_COUNT);
    expect(screen.getByText(`${PROXY_TRIAL_BANK_EXPECTED_RECORD_COUNT}/${PROXY_TRIAL_BANK_EXPECTED_RECORD_COUNT}`))
      .toBeInTheDocument();
    expect(PROXY_TRIAL_BANK_VERSION).toBe("source_proxy_shared_prompt_bank_v0");
    expect(proxyTrialWidgetDryRunEvidence()).toMatchObject({
      applyAuthority: false,
      bankVersion: "source_proxy_shared_prompt_bank_v0",
      phase7LivePreviewAuthority: false,
      sharedBankIntegrated: true,
      totalTrials: 100,
      widgetDryRunStatus: "widget_dry_run_only_no_route_execution",
    });
    expect(screen.getByText("legacy_hb_seed")).toBeInTheDocument();
    expect(screen.getByText("Advanced trial controls")).toBeInTheDocument();
    expect(screen.getByText("Advanced trial controls").closest("details")).not.toHaveAttribute("open");
    openProxyAdvancedControls();
    expect(screen.getAllByText("docs_only_productive_preview").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Copy 100-prompt dry run" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy manual check" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy preview gate" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy 25 approval" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy frontend fix" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy 100 approval" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy 100-review" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy route-gap plan" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy route-gap gate" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy route-gap fix" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy blocker plan" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy retry fix" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run 100 previews" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "100 prompt diagnostic summary" })).toBeInTheDocument();
    expect(screen.getByText("100 Prompt Diagnostic Summary")).toBeInTheDocument();
    expect(screen.getByText("Terminal 100 diagnostic accepted; browser checklist still required"))
      .toBeInTheDocument();
    expect(screen.getByText("Promoted to 100 candidate")).toBeInTheDocument();
    expect(screen.getByText("Accepted terminal 100 regression")).toBeInTheDocument();
    expect(screen.getByText("Raw diagnostic status values").closest("details"))
      .not.toHaveAttribute("open");
    openRawDiagnosticStatusValues();
    expect(screen.getByText("raw: promote_to_100_prompt_regression_candidate")).toBeInTheDocument();
    expect(screen.getByText("raw: accepted_terminal_100_prompt_regression")).toBeInTheDocument();
    expect(screen.getByText("Total prompts")).toBeInTheDocument();
    expect(screen.getByText("Productive previews")).toBeInTheDocument();
    expect(screen.getByText("Safe blockers")).toBeInTheDocument();
    expect(screen.getByText("Unexpected file attempts")).toBeInTheDocument();
    expect(screen.getByText("All false: apply, commit, push, execute-approved, provider, shell expansion, reset/stash/clean, and Phase 7 live preview."))
      .toBeInTheDocument();
    expect(screen.getByText("apply_authority: false")).toBeInTheDocument();
    expect(screen.getByText("phase_7_live_preview_authority: false")).toBeInTheDocument();
    expect(screen.getByText("Top Blocker Categories")).toBeInTheDocument();
    expect(screen.getByText("unknown_blocker: 0")).toBeInTheDocument();
    expect(screen.getByText(/frontend_preview_route_gap: 12/)).toBeInTheDocument();
    expect(screen.getByText(/missing_target_context: 11/)).toBeInTheDocument();
    expect(screen.getByText("Manual 100 Frontend Diagnostic Check")).toBeInTheDocument();
    expect(screen.getByText("9. Confirm no unknown_blocker category is present.")).toBeInTheDocument();
    expect(screen.getByText("15. Confirm the UI says the proxy is ready for preflight organization, not live authority."))
      .toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Copy browser evidence" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Copy evidence review" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous proxy trial" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Next proxy trial" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Copy prompt" }).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Mobile copy prompt" })).toBeInTheDocument();
    const compactTaskProgress = screen.getByRole("region", {
      name: "Compact task progress",
    });
    expect(within(compactTaskProgress).getByText("Task progress")).toBeInTheDocument();
    expect(within(compactTaskProgress).getByText("Current step")).toBeInTheDocument();
    expect(within(compactTaskProgress).getByText("Next safe action")).toBeInTheDocument();
    expect(within(compactTaskProgress).getByText("Evidence")).toBeInTheDocument();
    expect(
      within(compactTaskProgress).getByText(
        /Pending: preview evidence missing; local approval missing; apply evidence missing; verification pass missing\./,
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("Evidence Details and Receipts")).not.toBeInTheDocument();
    openRightRailDetails();
    expect(
      screen.getByText("Trial step: paste the copy-paste task, click Coding mode, then Submit task."),
    ).toBeInTheDocument();
    expect(screen.getByText("Approval evidence: not recorded")).toBeInTheDocument();
    expect(screen.getByText("Apply state: Apply is locked until explicit local approval exists."))
      .toBeInTheDocument();
    expect(screen.getByText("Apply evidence: not recorded")).toBeInTheDocument();
    expect(screen.getByText("Repeat apply lock: Repeat apply lock is waiting for apply evidence."))
      .toBeInTheDocument();
    expect(screen.getByText("Verify evidence: not recorded")).toBeInTheDocument();
    expect(screen.getByText("Commit and push are not available from this lane."))
      .toBeInTheDocument();
    const timelineRegion = screen.getByRole("region", {
      name: "Coding task timeline and evidence stream",
    });
    expect(within(timelineRegion).getByText("Task timeline")).toBeInTheDocument();
    expect(within(timelineRegion).getByText("Understand request")).toBeInTheDocument();
    expect(within(timelineRegion).getByText("Preview diff evidence")).toBeInTheDocument();
    expect(within(timelineRegion).getByText("Apply approved diff")).toBeInTheDocument();
    expect(within(timelineRegion).getByText("Evidence stream")).toBeInTheDocument();
    expect(within(timelineRegion).getByText("Diff hunks")).toBeInTheDocument();
    expect(
      within(timelineRegion).getByText("unavailable until preview evidence exists"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Closeout blockers: preview evidence missing; local approval missing; apply evidence missing; verification pass missing",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy receipt" })).toBeInTheDocument();
    expect(screen.getByText("Prompt: No prompt staged in the active chat.")).toBeInTheDocument();
    expect(screen.getByText("Active chat/run: draft")).toBeInTheDocument();
    expect(screen.getByText("Lifecycle status: BLOCKED")).toBeInTheDocument();
    expect(screen.getByText("Progress source: No active progress stream; UI-local state only."))
      .toBeInTheDocument();
    expect(
      screen.getByText(
        "Authority: No apply, commit, push, provider, queue, worker, live preview, shell, approval-token, or mutation authority is granted.",
      ),
    ).toBeInTheDocument();

    expect(screen.getByRole("heading", { level: 2, name: "No active run" })).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();
    expect(screen.getByText("Preview")).toBeInTheDocument();
    expect(screen.getByText("Approval")).toBeInTheDocument();
    expect(screen.getByText("Apply")).toBeInTheDocument();
    expect(screen.getByText("Verify")).toBeInTheDocument();
    expect(screen.getByText(/Preview requires bounded task data/))
      .toBeInTheDocument();
    const progressSurface = screen.getByRole("region", {
      name: "Codex-style progress surface",
    });
    expect(within(progressSurface).getByText("Detailed Progress")).toBeInTheDocument();
    expect(within(progressSurface).getByText("Working time unavailable")).toBeInTheDocument();
    expect(within(progressSurface).getByText("Thinking: planning next safe step"))
      .toBeInTheDocument();
    expect(within(progressSurface).getByText("Working: no active run")).toBeInTheDocument();
    expect(within(progressSurface).getByText("Observed: idle")).toBeInTheDocument();
    expect(within(progressSurface).getByText("Repairing within scope: unavailable"))
      .toBeInTheDocument();
    expect(within(progressSurface).getByText("Explored files")).toBeInTheDocument();
    expect(within(progressSurface).getByText("Searches")).toBeInTheDocument();
    expect(within(progressSurface).getAllByText("unavailable").length).toBeGreaterThan(0);
    expect(
      within(progressSurface).getByText(
        "No hidden chain-of-thought is displayed. Public work summaries use visible UI evidence only.",
      ),
    ).toBeInTheDocument();

    expect(screen.queryByRole("button", { name: /apply approved diff/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /commit|push/i })).not.toBeInTheDocument();
    expectPlan8AForbiddenControlsAbsent();
  }, 10_000);

  it("uses shared shell safe-area tokens for the route wrapper", () => {
    const { container } = render(<CodingCommandCenterShell />);

    const shell = container.querySelector(".dashboard-demo-v4-route-shell-coding");
    expect(shell?.className).toContain("--shell-safe-area-bottom");
    expect(shell?.className).not.toContain("env(safe-area-inset-bottom");
  });

  it("keeps the prompt staging preview inert while showing multiple prompt states", () => {
    render(<CodingCommandCenterShell />);
    openProxyDetails();

    const promptStagingPreview = screen.getByRole("region", {
      name: "Prompt staging preview",
    });
    ["current", "pending", "completed", "blocked"].forEach((status) => {
      expect(within(promptStagingPreview).getByText(status)).toBeInTheDocument();
    });
    expect(within(promptStagingPreview).queryAllByRole("button")).toHaveLength(0);
    expect(within(promptStagingPreview).getByText("preview queue only")).toBeInTheDocument();
    expect(within(promptStagingPreview).getByText("no worker running")).toBeInTheDocument();
    expect(within(promptStagingPreview).getByText("no provider call")).toBeInTheDocument();
    expect(within(promptStagingPreview).getByText("no apply authority")).toBeInTheDocument();
    expectPlan8AForbiddenControlsAbsent();
  });

  it("switches selected proxy trials with arrow controls and arrow keys", () => {
    render(<CodingCommandCenterShell />);
    openProxyDetails();

    const desktopTrialSelect = screen.getByRole("combobox", { name: "Switch proxy trial" });
    expect(desktopTrialSelect).toHaveValue("HB-01");

    fireEvent.click(screen.getByRole("button", { name: "Next proxy trial" }));
    expect(desktopTrialSelect).toHaveValue("HB-02");
    expect(screen.getAllByText("HB-02 selected. Load prompt or preview selected.").length).toBeGreaterThan(0);
    expect(screen.queryByText("HB-02 selected [info]")).not.toBeInTheDocument();

    fireEvent.keyDown(screen.getByLabelText("Proxy trial prompt widget"), { key: "ArrowRight" });
    expect(desktopTrialSelect).toHaveValue("HB-03");

    fireEvent.keyDown(screen.getByLabelText("Proxy trial prompt widget"), { key: "ArrowLeft" });
    expect(desktopTrialSelect).toHaveValue("HB-02");

    fireEvent.click(screen.getByRole("button", { name: "Previous proxy trial" }));
    expect(desktopTrialSelect).toHaveValue("HB-01");
  });

  it("can toggle trial prompts off without showing advanced audit logs", () => {
    render(<CodingCommandCenterShell />);
    openDiagnosticsDrawer();

    const widget = screen.getByLabelText("Proxy trial prompt widget");
    expect(within(widget).getByRole("button", { name: "Turn trial prompts off" }))
      .toHaveAttribute("aria-pressed", "true");

    fireEvent.click(within(widget).getByRole("button", { name: "Turn trial prompts off" }));

    expect(within(widget).getByRole("button", { name: "Turn trial prompts on" }))
      .toHaveAttribute("aria-pressed", "false");
    expect(
      within(widget).getByText("Trial prompts are hidden. Turn them on to pick, load, or preview HB tasks."),
    ).toBeInTheDocument();
    expect(within(widget).queryByRole("combobox", { name: "Switch proxy trial" }))
      .not.toBeInTheDocument();
    expect(within(widget).queryByText("Preview audit logs")).not.toBeInTheDocument();
    expect(within(widget).queryByRole("button", { name: "Copy audit logs" }))
      .not.toBeInTheDocument();
  });

  it("keeps workspace, provider, and safety status visible without implying execution", () => {
    render(<CodingCommandCenterShell />);

    expect(screen.getByRole("button", { name: "Selected workspace: SpiritOS" })).toBeInTheDocument();
    expect(screen.getByRole("button", {
      name: "C:\\Projects future target unavailable",
    })).toHaveAttribute("aria-pressed", "false");
    expect(screen.queryByRole("button", { name: /create worktree|switch branch/i }))
      .not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Local LLM: default" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: "GPT/cloud: unavailable" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(screen.getByRole("button", { name: "Codex worker: proposal-only" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(screen.getByRole("button", { name: "Future providers: future" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));

    expect(screen.getByText("Verification status:")).toBeInTheDocument();
    expect(screen.getByText("Verification has not started.")).toBeInTheDocument();
    expect(screen.queryByText(/provider call ran/i)).not.toBeInTheDocument();
  });

  it("opens non-modal drawer shells while gating controls and authority", () => {
    render(<CodingCommandCenterShell />);

    const drawerToolbar = screen.getByRole("toolbar", { name: "Drawer shell triggers" });
    const settingsButton = within(drawerToolbar).getByRole("button", { name: "Settings" });
    const diagnosticsButton = within(drawerToolbar).getByRole("button", { name: "Diagnostics" });
    const evidenceButton = within(drawerToolbar).getByRole("button", { name: "Evidence" });

    expect(screen.queryByRole("complementary", { name: "Settings drawer shell" }))
      .not.toBeInTheDocument();
    expect(settingsButton).toHaveAttribute("aria-expanded", "false");
    expect(diagnosticsButton).toHaveAttribute("aria-expanded", "false");
    expect(evidenceButton).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(settingsButton);

    const settingsDrawer = screen.getByRole("complementary", { name: "Settings drawer shell" });
    const settingsHeading = within(settingsDrawer).getByRole("heading", {
      name: "Settings Drawer Shell",
    });
    expect(settingsHeading).toHaveFocus();
    expect(settingsDrawer).toHaveTextContent("no provider call runs here");
    expect(settingsDrawer).toHaveTextContent(
      "Active task, composer, and chat navigation remain usable",
    );
    expect(settingsButton).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("navigation", { name: "Coding chats" })).toBeInTheDocument();
    expect(screen.getByLabelText("Coding command composer")).toBeInTheDocument();

    fireEvent.click(diagnosticsButton);

    const diagnosticsDrawer = screen.getByRole("complementary", {
      name: "Diagnostics drawer shell",
    });
    expect(
      within(diagnosticsDrawer).getByRole("heading", { name: "Diagnostics Drawer Shell" }),
    ).toHaveFocus();
    expect(diagnosticsDrawer).toHaveTextContent(
      "Trial prompts, proof controls, blocker summaries, and PR-8.3 diagnostics are available",
    );
    expect(diagnosticsDrawer).toHaveTextContent(
      "no provider, queue, worker, apply, commit, or push authority",
    );
    expect(settingsButton).toHaveAttribute("aria-expanded", "false");
    expect(diagnosticsButton).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByLabelText("Proxy trial prompt widget")).toBeInTheDocument();
    expect(screen.getByText("Proof run controls").closest("details"))
      .not.toHaveAttribute("open");
    expect(within(diagnosticsDrawer).queryByRole("button", { name: "Run 10" }))
      .not.toBeInTheDocument();

    fireEvent.click(evidenceButton);

    const evidenceDrawer = screen.getByRole("complementary", { name: "Evidence drawer shell" });
    expect(within(evidenceDrawer).getByRole("heading", { name: "Evidence Drawer Shell" }))
      .toHaveFocus();
    expect(evidenceDrawer).toHaveTextContent(
      "Task-scoped receipts, timeline detail, dirty-tree proof, rollback notes, and copyable evidence are available",
    );
    expect(evidenceDrawer).toHaveTextContent("No receipt store, file write, apply, commit, or push");
    expect(evidenceButton).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("Evidence Details and Receipts").closest("details"))
      .toHaveAttribute("open");

    fireEvent.click(screen.getByRole("button", { name: "Close Evidence drawer shell" }));

    expect(screen.queryByRole("complementary", { name: "Evidence drawer shell" }))
      .not.toBeInTheDocument();
    expect(evidenceButton).toHaveAttribute("aria-expanded", "false");
    expectPlan8AForbiddenControlsAbsent();
  });

  it("shows display-only settings without writable controls", () => {
    render(<CodingCommandCenterShell />);

    const settingsRegion = screen.getByRole("region", { name: "Display-only settings" });
    expect(within(settingsRegion).getByText("Settings")).toBeInTheDocument();
    expect(
      within(settingsRegion).getByText("Display-only settings. Writable settings require a later gate."),
    ).toBeInTheDocument();
    expect(within(settingsRegion).getByText("no persistence")).toBeInTheDocument();
    [
      "Workspace settings",
      "Provider/model settings",
      "Safety/authority settings",
      "Notification settings",
      "Usage/time settings",
      "CLI settings",
      "Config write gate",
    ].forEach((label) => {
      expect(within(settingsRegion).getByText(label)).toBeInTheDocument();
    });
    expect(within(settingsRegion).getAllByText("Writable: false")).toHaveLength(7);
    expect(within(settingsRegion).queryByRole("button")).not.toBeInTheDocument();
    expect(within(settingsRegion).queryByRole("checkbox")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "GPT/cloud: unavailable" }));

    expect(within(settingsRegion).getByText("GPT/cloud; GPT/cloud missing config; unavailable"))
      .toBeInTheDocument();
    expect(
      within(settingsRegion).getByText(
        "Authority: No provider call, API-cost action, auth/config/env edit, apply, commit, or push.",
      ),
    ).toBeInTheDocument();
  });

  it("shows usage and time tracking without fake tokens or cost", () => {
    render(<CodingCommandCenterShell />);

    const usageRegion = screen.getByRole("region", { name: "Usage and time tracking" });
    expect(within(usageRegion).getByText("Usage and time")).toBeInTheDocument();
    expect(
      within(usageRegion).getByText(
        "Current-session timers only. Tokens, cost, budget, CLI, and durable usage stay unavailable unless a real source supplies them.",
      ),
    ).toBeInTheDocument();
    expect(within(usageRegion).getByText("no fake usage")).toBeInTheDocument();
    [
      "Elapsed chat time",
      "Active run time",
      "Live coding time",
      "Active diagnostic time",
      "Custom CLI time",
      "Command/check duration",
      "Token usage",
      "Actual cost",
      "Projected API cost",
      "Budget status",
      "Durable usage storage",
    ].forEach((label) => {
      expect(within(usageRegion).getByText(label)).toBeInTheDocument();
    });
    expect(within(usageRegion).getAllByText("Actual provider usage claimed: false"))
      .toHaveLength(11);
    expect(within(usageRegion).getByText("unavailable; no real provider token report"))
      .toBeInTheDocument();
    expect(within(usageRegion).getByText("unavailable; no real provider cost report"))
      .toBeInTheDocument();
    expect(within(usageRegion).getByText("gated; current-session display only"))
      .toBeInTheDocument();
    expect(within(usageRegion).queryByText(/actual tokens: total=[1-9]/i))
      .not.toBeInTheDocument();
    expect(within(usageRegion).queryByText(/actual cost: \$[0-9]/i)).not.toBeInTheDocument();
    expect(within(usageRegion).queryByRole("button")).not.toBeInTheDocument();
    expect(within(usageRegion).queryByRole("checkbox")).not.toBeInTheDocument();
  });

  it("shows in-app alerts without OS notification authority", () => {
    render(<CodingCommandCenterShell />);

    const alertsRegion = screen.getByRole("region", {
      name: "In-app alerts and waiting states",
    });
    expect(within(alertsRegion).getByText("Alerts and waiting states")).toBeInTheDocument();
    expect(
      within(alertsRegion).getByText(
        "In-app alerts only. Desktop notifications, sounds, permission prompts, and background watchers require a later gate.",
      ),
    ).toBeInTheDocument();
    expect(within(alertsRegion).getByText("no OS permission")).toBeInTheDocument();
    [
      "Done alert",
      "Blocked alert",
      "Needs-review alert",
      "Waiting-for-approval alert",
      "Failed alert",
      "Browser title/badge",
      "Desktop/sound notification gate",
      "Background autonomy gate",
    ].forEach((label) => {
      expect(within(alertsRegion).getByText(label)).toBeInTheDocument();
    });
    expect(within(alertsRegion).getByText("Gated; no Notification API permission prompt."))
      .toBeInTheDocument();
    expect(within(alertsRegion).getByText("Gated; no background autonomy."))
      .toBeInTheDocument();
    expect(
      within(alertsRegion).getByText(
        "Blocked safely; review Task State, Progress, or receipt for exact blocker.",
      ),
    ).toBeInTheDocument();
    expect(alertsRegion).toHaveTextContent(
      "preview evidence missing; local approval missing; apply evidence missing; verification pass missing",
    );
    expect(within(alertsRegion).queryByRole("button")).not.toBeInTheDocument();
    expect(within(alertsRegion).queryByRole("checkbox")).not.toBeInTheDocument();
  });

  it("shows backend truth without fake backend data or hidden execution", () => {
    render(<CodingCommandCenterShell />);

    const backendRegion = screen.getByRole("region", { name: "Backend truth on UI" });
    expect(within(backendRegion).getByText("Backend truth")).toBeInTheDocument();
    expect(
      within(backendRegion).getByText(
        "Route inventory and current UI-local truth only. Live backend reads, hidden polling, providers, queues, workers, shell commands, and apply routes are not started by this panel.",
      ),
    ).toBeInTheDocument();
    expect(within(backendRegion).getByText("no fake backend data")).toBeInTheDocument();
    [
      "Source Proxy self status",
      "Tools manifest",
      "Workspace API",
      "Sandbox terminal status",
      "Long-running task status",
      "Provider/model status",
      "Budget/usage status",
      "Custom CLI status",
      "Codex adapter status",
      "No hidden execution guard",
    ].forEach((label) => {
      expect(within(backendRegion).getByText(label)).toBeInTheDocument();
    });
    expect(within(backendRegion).getByText("Route: GET /v1/self/status"))
      .toBeInTheDocument();
    expect(within(backendRegion).getByText("Route: GET /v1/tools/manifest"))
      .toBeInTheDocument();
    expect(within(backendRegion).getByText("Route: POST /v1/coding/codex"))
      .toBeInTheDocument();
    expect(within(backendRegion).getAllByText("not-wired").length).toBeGreaterThan(0);
    expect(within(backendRegion).getAllByText("unavailable").length).toBeGreaterThan(0);
    expect(within(backendRegion).getAllByText("config-blocked").length).toBeGreaterThan(0);
    expect(within(backendRegion).getAllByText("available").length).toBeGreaterThan(0);
    expect(within(backendRegion).queryByRole("button")).not.toBeInTheDocument();
    expect(within(backendRegion).queryByRole("checkbox")).not.toBeInTheDocument();
  });

  it("keeps project context per chat without connecting to external workspaces", () => {
    render(<CodingCommandCenterShell />);

    const workspaceRegion = screen.getByRole("region", {
      name: "Workspace context per chat",
    });
    expect(within(workspaceRegion).getByText("SpiritOS: selected · read-list-only"))
      .toBeInTheDocument();
    const futureWorkspaceContextButton = within(workspaceRegion).getByRole("button", {
      name: "C:\\Projects: future target · unavailable",
    });
    expect(futureWorkspaceContextButton).toBeDisabled();
    expect(futureWorkspaceContextButton).toHaveAttribute("aria-disabled", "true");
    const remoteWorkspaceContextButton = within(workspaceRegion).getByRole("button", {
      name: "Remote workspace: skipped · unavailable",
    });
    expect(remoteWorkspaceContextButton).toBeDisabled();
    expect(remoteWorkspaceContextButton).toHaveAttribute("aria-disabled", "true");
    const folderProof = screen.getByRole("region", {
      name: "Read/list-only folder proof",
    });
    expect(within(folderProof).getByText("List folder: available")).toBeInTheDocument();
    expect(within(folderProof).getByText("Read file excerpt: available")).toBeInTheDocument();
    expect(within(folderProof).getByText("Secret-shaped paths: blocked")).toBeInTheDocument();
    expect(within(folderProof).getByText("Path escape: blocked")).toBeInTheDocument();
    expect(within(folderProof).getByText("Writes: unavailable")).toBeInTheDocument();
    expect(screen.getByText(/Dirty tree warning:/)).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "Selected workspace: SpiritOS" }))
      .toHaveTextContent("/home/source/SpiritOS");
    openRightRailDetails();
    expect(screen.getByText("Workspace availability: available")).toBeInTheDocument();
    expect(screen.getByText("Workspace access: read-list-only")).toBeInTheDocument();
    expect(screen.getAllByText(/no Windows bridge call, write, project creation/).length)
      .toBeGreaterThan(0);

    const chatNav = screen.getByRole("navigation", { name: "Coding chats" });
    fireEvent.click(within(chatNav).getByRole("button", { name: /Approval queue/ }));

    expect(screen.getByRole("button", { name: "Selected workspace: SpiritOS" }))
      .toHaveTextContent("/home/source/SpiritOS");
    expect(screen.getByText("SpiritOS context is selected for this chat")).toBeInTheDocument();

    fireEvent.click(within(chatNav).getByRole("button", { name: /New coding chat/ }));

    expect(screen.getByRole("button", { name: "Selected workspace: SpiritOS" }))
      .toHaveTextContent("/home/source/SpiritOS");
    expect(screen.queryByRole("button", { name: /create worktree|switch branch/i }))
      .not.toBeInTheDocument();
  });

  it("keeps mobile composer controls distinct from the desktop composer", () => {
    render(<CodingCommandCenterShell />);

    expect(screen.getByRole("region", { name: "Mobile command composer" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Mobile trial task helper" })).toBeInTheDocument();
    expect(screen.getByLabelText("Mobile coding command composer")).toHaveAttribute(
      "placeholder",
      "Ask, plan, or draft a coding task.",
    );
    expect(screen.getByLabelText("Mobile coding command composer")).toHaveAttribute(
      "aria-describedby",
      "mobile-coding-task-state",
    );
    expect(screen.getByText(/Mobile task state: No active run/)).toBeInTheDocument();
    expect(screen.getByLabelText("Coding command composer")).toHaveAttribute(
      "placeholder",
      "Ask for a plan, start a coding task, or gather repo context.",
    );
    expect(screen.getByRole("button", { name: "Desktop coding mode" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(screen.getByRole("button", { name: "Mobile coding mode" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(screen.getByRole("button", { name: "Mobile submit task" })).toBeDisabled();
  });

  it("keeps the compact Source Proxy safety panel visible", () => {
    render(<CodingCommandCenterShell />);

    const safetyPanel = screen.getByRole("complementary", {
      name: "Mobile safety and task status",
    });

    expect(within(safetyPanel).getByRole("heading", { name: "No active run" })).toBeInTheDocument();
    expect(within(safetyPanel).getByText("Safe")).toBeInTheDocument();
    expect(within(safetyPanel).getByText("Source Proxy")).toBeInTheDocument();
    expect(
      within(safetyPanel).getByText(/Preview requires bounded task data/),
    ).toBeInTheDocument();
    expect(within(safetyPanel).getByRole("region", { name: "Compact task progress" }))
      .toBeInTheDocument();
    expect(within(safetyPanel).queryByText("Evidence Details and Receipts"))
      .not.toBeInTheDocument();
  });

  it("turns one chat into coding mode without enabling coding actions", () => {
    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Start new chat" }));
    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));

    expect(screen.getByRole("button", { name: "Desktop coding mode" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByText("Coding mode active, no submitted task yet")).toBeInTheDocument();
    expect(screen.getByText(/approval and apply stay locked until preview evidence passes/))
      .toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Desktop preview safely" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: /apply approved diff/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Start new chat" }));

    expect(screen.getByRole("button", { name: "Desktop coding mode" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(screen.getByText("Empty chat 2, ready for a prompt")).toBeInTheDocument();
    expect(screen.queryByText("Coding mode active, no submitted task yet")).not.toBeInTheDocument();
  });

  it("creates a visible local task packet from bounded composer input", async () => {
    render(<CodingCommandCenterShell />);

    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value: humanTrialPrompt,
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));

    expect(screen.getByText("Patch docs/proxy-test-runner-plan.md")).toBeInTheDocument();
    expect(screen.getByText("Task submitted locally. Preview is ready to request; no files changed."))
      .toBeInTheDocument();
    expectActiveRunState("queued");
    expect(
      screen
        .getAllByText(/Target file:/)
        .some((element) =>
          /Target file:\s*docs\/proxy-test-runner-plan\.md/.test(
            element.parentElement?.textContent ?? "",
          ),
        ),
    ).toBe(true);
    expect(
      screen
        .getAllByText(/Allowed files:/)
        .some((element) =>
          /Allowed files:\s*docs\/proxy-test-runner-plan\.md/.test(
            element.parentElement?.textContent ?? "",
          ),
        ),
    ).toBe(true);
    const scopeReview = screen.getByRole("region", { name: "Inferred scope review" });
    expect(within(scopeReview).getByText("Scope review")).toBeInTheDocument();
    expect(within(scopeReview).getByText("Status: ready")).toBeInTheDocument();
    expect(within(scopeReview).getByText("Task type: docs")).toBeInTheDocument();
    expect(within(scopeReview).getByText("Expected checks: git diff --check")).toBeInTheDocument();
    expect(within(scopeReview).getByText("Safe next action: review_scope")).toBeInTheDocument();
    expect(screen.getByText(/Bounded task data present/)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Desktop preview safely" })).toBeEnabled();
    });
  });

  it("accepts plain-English browser intake and shows scope review before preview", async () => {
    render(<CodingCommandCenterShell />);

    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value:
          "Add a short note about safe receipts in docs/source-proxy-daily-use-runbook.md.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));

    const scopeReview = screen.getByRole("region", { name: "Inferred scope review" });
    expect(screen.getByText("Patch docs/source-proxy-daily-use-runbook.md")).toBeInTheDocument();
    expect(within(scopeReview).getByText("Status: ready")).toBeInTheDocument();
    expect(within(scopeReview).getByText("Task type: docs")).toBeInTheDocument();
    expect(within(scopeReview).getByText("Risk: low")).toBeInTheDocument();
    expect(within(scopeReview).getByText("Expected checks: git diff --check")).toBeInTheDocument();
    expect(within(scopeReview).getByText("Safe next action: review_scope")).toBeInTheDocument();
    expect(screen.getByText(/Bounded task data present/)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Desktop preview safely" })).toBeEnabled();
    });
    expect(screen.queryByRole("button", { name: /apply approved diff/i })).not.toBeInTheDocument();
  });

  it("keeps preview locked when target and allowed files are missing", () => {
    render(<CodingCommandCenterShell />);

    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: { value: "Add one sentence to the docs." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));

    expect(screen.getByText("Missing bounded fields: target file, allowed files."))
      .toBeInTheDocument();
    expect(
      screen.getByText("Task submitted locally. Preview blocked: missing target file, allowed files."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Desktop preview safely" })).toBeDisabled();
    expect(screen.getByText("Preview: Preview blocked: missing target file, allowed files."))
      .toBeInTheDocument();
    expect(screen.getByText("Approval: Locked until preview evidence exists."))
      .toBeInTheDocument();
    expect(screen.getByText("Apply: Locked until explicit local approval exists."))
      .toBeInTheDocument();
    expect(screen.getByText("Verify: Locked until apply happens.")).toBeInTheDocument();
  });

  it("shows ambiguous browser scope with concrete next action and no approval", () => {
    render(<CodingCommandCenterShell />);

    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value:
          "Keep docs/source-proxy-daily-use-runbook.md and docs/source-proxy-regression-matrix.md aligned.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));

    const scopeReview = screen.getByRole("region", { name: "Inferred scope review" });
    expect(within(scopeReview).getByText("Status: blocked")).toBeInTheDocument();
    expect(within(scopeReview).getByText("Reason codes: multiple_targets")).toBeInTheDocument();
    expect(screen.getByText("Missing bounded fields: allowed files.")).toBeInTheDocument();
    expect(screen.getByText("Preview: Preview blocked: missing allowed files.")).toBeInTheDocument();
    expect(screen.getByText("Approval: Locked until preview evidence exists.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Desktop preview safely" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: /approve/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply/i })).not.toBeInTheDocument();
  });

  it("requests coding preview without enabling approval or apply", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse())
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/example.md b/docs/example.md",
              "--- a/docs/example.md",
              "+++ b/docs/example.md",
              "@@ -1 +1,2 @@",
              " # Example",
              "+Preview-only smoke.",
              "",
            ].join("\n"),
            target: "docs/example.md",
            task_id: "task-123",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: "preview_ready" }), { status: 200 }),
      );

    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value:
          "Append a preview-only smoke line. Target file: docs/example.md. Allowed files: docs/example.md.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));
    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));

    expect(await screen.findByText("Preview ready. No files changed yet.")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Mobile preview evidence" })).toBeInTheDocument();
    expect(screen.getAllByText("Preview evidence").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Changed files: docs/example.md").length).toBeGreaterThan(0);
    expect(screen.getByText("Unexpected files")).toBeInTheDocument();
    expect(screen.getByText("Diff check")).toBeInTheDocument();
    openRightRailDetails();
    expect(screen.getByText("Allowed files: Only this file is allowed: docs/example.md."))
      .toBeInTheDocument();
    expect(screen.getByText("Unexpected files: No unexpected files detected."))
      .toBeInTheDocument();
    expect(screen.getByText("Diff check result: pass; changed files match allowed files"))
      .toBeInTheDocument();
    const timelineRegion = screen.getByRole("region", {
      name: "Coding task timeline and evidence stream",
    });
    expect(within(timelineRegion).getByText(/Changed files: docs\/example\.md\./))
      .toBeInTheDocument();
    expect(within(timelineRegion).getByText("1 hunk(s) observed")).toBeInTheDocument();
    expect(within(timelineRegion).getByText(/Approval waits for clean preview evidence\./))
      .toBeInTheDocument();
    expect(screen.getByText("Typecheck result: not reported by UI")).toBeInTheDocument();
    expect(screen.getByText("Lint result: not reported by UI")).toBeInTheDocument();
    expect(screen.getByText("Focused test result: not reported by UI")).toBeInTheDocument();
    expect(screen.getAllByText(/Preview-only smoke/).length).toBeGreaterThan(0);
    expect(
      screen.getByText(
        "Approval gate display: clean preview evidence available; approval requires human click before apply.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Approval preflight: changed files docs/example.md match allowed files docs/example.md.",
      ),
    ).toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledTimes(3);
    expect(globalThis.fetch).toHaveBeenNthCalledWith(
      1,
      "/v1/tasks/long-running",
      expect.objectContaining({
        body: expect.stringContaining("Append a preview-only smoke line."),
        method: "POST",
      }),
    );
    expect(globalThis.fetch).toHaveBeenNthCalledWith(
      2,
      "/v1/decisions/prompt-packet",
      expect.objectContaining({
        body: expect.stringContaining("Append a preview-only smoke line."),
        method: "POST",
      }),
    );
    expect(globalThis.fetch).toHaveBeenNthCalledWith(
      3,
      "/v1/verification/diff-preview",
      expect.objectContaining({
        body: expect.stringContaining('"route_type":"local-intent"'),
        method: "POST",
      }),
    );
    expect(String(vi.mocked(globalThis.fetch).mock.calls[2][1]?.body)).toContain(
      '"allowed_files":["docs/example.md"]',
    );
    expect(String(vi.mocked(globalThis.fetch).mock.calls[2][1]?.body)).toContain(
      '"target":"docs/example.md"',
    );
    expect(screen.queryByText("Manual task preview ready")).not.toBeInTheDocument();
    openProxyAuditLogs();
    expect(screen.getByRole("button", { name: "Record reviewed audit" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Copy audit logs" }));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("Current page audit evidence"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("status: ready"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("changed_files: docs/example.md"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("commit_authority: false"));
    expect(screen.getByRole("button", { name: "Approve preview" })).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "Current step: review the diff, then click Approve preview if it only touches the allowed docs file.",
      ),
    ).toHaveLength(3);
    openRightRailDetails();
    expect(
      screen.getByText(
        "Trial step: review the diff, then click Approve preview if it only touches the allowed docs file.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Safe next action: Review changed files docs/example.md against allowed files docs/example.md, then approve only if the diff text is correct.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /commit|push/i })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Copy diff" }));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("Preview-only smoke."));
    expect((await screen.findAllByText("Preview diff copied.")).length).toBeGreaterThan(0);
    openProxyAuditLogs();
    fireEvent.click(screen.getByRole("button", { name: "Record reviewed audit" }));
    expect(screen.getByText("Manual task reviewed audit")).toBeInTheDocument();
    expect(screen.getByText(/human_review_result: reviewed_without_apply_authority/))
      .toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Copy audit logs" }));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("Manual task reviewed audit"));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("human_review_result: reviewed_without_apply_authority"),
    );
    expect(screen.queryByRole("button", { name: "Apply approved diff" })).not.toBeInTheDocument();
  }, 10_000);

  it("shows design proposal intake evidence without enabling apply", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse())
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            design_proposal_intake: {
              apply_authority: false,
              approval_authority: false,
              blocked_by: ["design_goal", "source_rights_status"],
              formatted: [
                "status: BLOCKED",
                "approval_authority: false",
                "apply_authority: false",
              ].join("\n"),
              reason_codes: ["missing_design_goal", "source_rights_status_not_approved"],
              status: "BLOCKED",
            },
            design_proposal_packet_ready: false,
            reason_code: "design_proposal_packet_intake_blocked",
            status: "blocked",
          }),
          { status: 200 },
        ),
      );

    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value:
          "Review a Design Agent proposal packet display. Target file: docs/example.md. Allowed files: docs/example.md.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));
    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));

    const intakeRegion = await screen.findByRole("region", {
      name: "Design proposal intake evidence",
    });
    expect(within(intakeRegion).getByText("Design proposal intake")).toBeInTheDocument();
    expect(within(intakeRegion).getByText("Status: BLOCKED")).toBeInTheDocument();
    expect(within(intakeRegion).getByText("Packet ready: no")).toBeInTheDocument();
    expect(
      within(intakeRegion).getByText(
        "Reason codes: missing_design_goal, source_rights_status_not_approved",
      ),
    ).toBeInTheDocument();
    expect(within(intakeRegion).getByText("Blocked by: design_goal, source_rights_status"))
      .toBeInTheDocument();
    expect(within(intakeRegion).getAllByText("approval_authority: false").length)
      .toBeGreaterThan(0);
    expect(within(intakeRegion).getAllByText("apply_authority: false").length)
      .toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: /apply/i })).not.toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
  });

  it("shows real diff evidence from plain-English browser intake", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse())
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/source-proxy-daily-use-runbook.md b/docs/source-proxy-daily-use-runbook.md",
              "--- a/docs/source-proxy-daily-use-runbook.md",
              "+++ b/docs/source-proxy-daily-use-runbook.md",
              "@@ -1 +1,2 @@",
              " # Source Proxy Daily Use Runbook",
              "+Plain-English preview evidence.",
              "",
            ].join("\n"),
            target: "docs/source-proxy-daily-use-runbook.md",
            task_id: "task-plain",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: "preview_ready" }), { status: 200 }),
      );

    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value:
          "Add a short receipt sentence to docs/source-proxy-daily-use-runbook.md.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));

    expect(await screen.findByText("Preview ready. No files changed yet.")).toBeInTheDocument();
    expect(screen.getByLabelText("Trial status badge")).toHaveTextContent("Needs review");
    expect(screen.getByLabelText("Preview trial status badge")).toHaveTextContent("Needs review");
    expect(screen.getByRole("region", { name: "Inferred scope review" })).toBeInTheDocument();
    expect(screen.getAllByText("Preview evidence").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Changed files: docs/source-proxy-daily-use-runbook.md").length)
      .toBeGreaterThan(0);
    expect(screen.getAllByText(/Plain-English preview evidence/).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Approve preview" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply/i })).not.toBeInTheDocument();
    expect(String(vi.mocked(globalThis.fetch).mock.calls[1][1]?.body)).toContain(
      "Add a short receipt sentence",
    );
    expect(String(vi.mocked(globalThis.fetch).mock.calls[2][1]?.body)).toContain(
      '"allowed_files":["docs/source-proxy-daily-use-runbook.md"]',
    );
  });

  it("auto-stages a bounded draft when preview is tapped before submit", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse())
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/example.md b/docs/example.md",
              "--- a/docs/example.md",
              "+++ b/docs/example.md",
              "@@ -1 +1,2 @@",
              " # Example",
              "+Auto-stage preview.",
              "",
            ].join("\n"),
            target: "docs/example.md",
            task_id: "task-123",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: "preview_ready" }), { status: 200 }),
      );

    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value:
          "Append an auto-stage preview line. Target file: docs/example.md. Allowed files: docs/example.md.",
      },
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Desktop preview safely" })).toBeEnabled();
    });
    expect(
      screen.getAllByText(
        "Current step: click Preview safely. A bounded draft will be staged before evidence is requested.",
      ),
    ).toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));

    expect(await screen.findByText("Preview ready. No files changed yet.")).toBeInTheDocument();
    expect(screen.getByText("Patch docs/example.md")).toBeInTheDocument();
    expect(screen.getAllByText(/Auto-stage preview/).length).toBeGreaterThan(0);
    expect(globalThis.fetch).toHaveBeenCalledTimes(3);
  });

  it("shows preview progress and times out cleanly when Source Proxy hangs", async () => {
    vi.useFakeTimers();
    vi.spyOn(globalThis, "fetch").mockImplementation((_input, init) => {
      const signal = init?.signal;
      return new Promise<Response>((_resolve, reject) => {
        signal?.addEventListener("abort", () => {
          reject(new DOMException("Aborted", "AbortError"));
        });
      });
    });

    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value:
          "Append a timeout smoke line. Target file: docs/example.md. Allowed files: docs/example.md.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));
    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));

    expect(screen.getByText("Creating bounded Source Proxy task. No files changed."))
      .toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(45_000);
    });

    const timeoutMessage = "Creating preview task timed out after 45 seconds. No files changed.";
    expect(screen.getAllByText(timeoutMessage).length).toBeGreaterThan(0);
    expect(screen.getByText(`Preview: ${timeoutMessage}`)).toBeInTheDocument();
    openProxyAuditLogs();
    expect(screen.getByText("Manual task preview timed out")).toBeInTheDocument();
    expect(screen.getByText(/Manual task preview timed out \[inconclusive\]/))
      .toBeInTheDocument();
    expect(screen.getByText(/result_label: inconclusive_timeout/)).toBeInTheDocument();
    expect(screen.getByText(/pass_fail: inconclusive; preview timed out/)).toBeInTheDocument();
    expect(screen.getByText(/task_prompt: Append a timeout smoke line/)).toBeInTheDocument();
    expect(screen.getAllByText("Preview timeout audit recorded.").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "Record reviewed audit" }));
    expect(screen.getByText("Manual task timeout audit")).toBeInTheDocument();
    expect(screen.getByText(/Manual task timeout audit \[inconclusive\]/))
      .toBeInTheDocument();
    expect(screen.getAllByText(/pass_fail: inconclusive; preview timed out/).length)
      .toBeGreaterThan(1);
    expect(screen.getAllByText(/human_review_result: not recorded; preview timed out before review/).length)
      .toBeGreaterThan(1);
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    fireEvent.click(screen.getByRole("button", { name: "Copy audit logs" }));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("Current page audit evidence"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("status: timeout"));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("pass_fail: inconclusive; preview timed out"),
    );
    expect(screen.getByRole("button", { name: "Desktop preview safely" })).toBeEnabled();
    expect(screen.queryByRole("button", { name: /approve/i })).not.toBeInTheDocument();
  });

  it("copies the trial task from the helper", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    const execCommand = vi.fn().mockReturnValue(false);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    Object.defineProperty(document, "execCommand", {
      configurable: true,
      value: execCommand,
    });

    render(<CodingCommandCenterShell />);
    openProxyDetails();
    openProxyAdvancedControls();

    fireEvent.click(screen.getAllByRole("button", { name: "Copy prompt" })[0]);

    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Add a short note explaining"),
    );
    expect(await screen.findAllByText("HB-01 prompt loaded and copied. Run preview when ready."))
      .toHaveLength(2);
    expect(screen.getByLabelText("Coding command composer")).toHaveValue(selectedTrialPrompt);
  });

  it("copies the controlled browser preview run approval gate without granting authority", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });

    render(<CodingCommandCenterShell />);
    openProxyDetails();
    openProxyAdvancedControls();

    fireEvent.click(screen.getByRole("button", { name: "Copy preview gate" }));

    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy controlled browser 100-prompt preview run approval gate packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("staged_browser_preview_path: 10_preview_browser_run; 25_preview_browser_run; 100_preview_browser_run"),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("stage_1_max_run_size: 10"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("stage_2_max_run_size: 25"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("stage_3_max_run_size: 100"));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("operator_must_not_click_run_all_safe_previews_until_stage_approval_is_explicit: true"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("stop_conditions: unsafe_failure; unexpected_files; authority_leak; provider_call; browser_route_error; unusable_summary; missing_blocker_reason; generic_blocker_regression"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("required_copied_evidence: prompt_source; bank_version; total_attempted; productive_preview_diffs; already_satisfied_noops; safe_blockers; unsafe_failures; unexpected_files; top_recurring_blockers; next_recommended_fix_batch; authority_fields_false"),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("phase_7_decision: no_go"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("provider_authority: false"));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("phase_7_live_preview_authority: false"),
    );
    expect(await screen.findAllByText("Controlled browser preview gate copied."))
      .toHaveLength(2);
  });

  it("runs the controlled 10-preview stage with capped preview-only evidence", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ error: "simulated browser route error" }), { status: 500 }),
    );

    render(<CodingCommandCenterShell />);
    openProxyDetails();
    openProxyAdvancedControls();

    fireEvent.click(screen.getByRole("button", { name: "Run 10 previews" }));

    expect((await screen.findAllByText("10_preview_browser_run stopped on unsafe failure.")).length)
      .toBeGreaterThan(0);
    expectActiveRunState("failed");
    expect(screen.getByText("Diagnostic failed safely")).toBeInTheDocument();
    expect(screen.getByText("Run summary")).toBeInTheDocument();
    const runHistory = screen.getByRole("region", {
      name: "Current-session run history",
    });
    expect(within(runHistory).getByText("Latest diagnostic batch")).toBeInTheDocument();
    expect(within(runHistory).getByText("failed")).toBeInTheDocument();
    expect(
      within(runHistory).getByText(
        "Latest browser diagnostic summary is held in current component state only.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/stage: 10_preview_browser_run/)).toBeInTheDocument();
    expect(screen.getByText(/prompt_source: source_proxy_shared_prompt_bank_v0/))
      .toBeInTheDocument();
    expect(screen.getByText(/max_run_size: 10/)).toBeInTheDocument();
    expect(screen.getByText(/hb03_classifier_version: frontend_preview_route_gap_v1/))
      .toBeInTheDocument();
    expect(screen.getByText(/frontend_widget_classifier_version: frontend_preview_route_gap_v2/))
      .toBeInTheDocument();
    expect(screen.getByText(/shared_noop_classifier_version: already_satisfied_noop_route_gap_v1/))
      .toBeInTheDocument();
    expect(screen.getByText(/total_attempted: 1/)).toBeInTheDocument();
    expect(screen.getByText(/provider_calls: none/)).toBeInTheDocument();
    expect(screen.getByText(/unexpected_files: 0/)).toBeInTheDocument();
    expect(screen.getByText(/next_recommended_fix_batch:/)).toBeInTheDocument();
    expect(screen.getByText(/phase_7_decision: no_go/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply approved diff/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /commit|push/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Copy run summary" }));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("stage: 10_preview_browser_run"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("total_attempted: 1"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("provider_authority: false"));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("phase_7_live_preview_authority: false"),
    );

    fireEvent.click(screen.getByRole("button", { name: "Copy 10-review" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy 10-preview browser evidence review packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("promotion_to_25_preview: no_go"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("required_next_fix_batch: inspect HB-03 generic blocker regression"),
    );
    expect(await screen.findAllByText("10-preview evidence review copied."))
      .toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Copy 25 approval" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy 25-preview browser run approval packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("decision: approve_controlled_25_preview_browser_run"),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("max_run_size: 25"));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("promotion_to_100_preview: no_go"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("phase_7_live_preview_authority: false"),
    );
    expect(await screen.findAllByText("25-preview approval packet copied."))
      .toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Copy 25-review" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy 25-preview browser evidence review packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("decision: approve_100_preview_gate_after_clean_25_preview_evidence"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("accepted_25_preview_evidence: total_attempted 25; productive_preview_diffs 1; already_satisfied_noops 1; safe_blockers 23; unsafe_failures 0; unexpected_files 0; blocked_after_retries_classifier_version blocked_after_retries_specificity_v1"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("promotion_to_100_preview: approved_for_controlled_100_preview_rerun_only"),
    );
    expect(await screen.findAllByText("25-preview evidence review copied."))
      .toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Copy 100 approval" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy 100-preview browser run approval packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("decision: approve_controlled_100_preview_browser_run"),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("max_run_size: 100"));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("phase_7_decision: no_go"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("phase_7_live_preview_authority: false"),
    );
    expect(await screen.findAllByText("100-preview approval packet copied."))
      .toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Copy 100-review" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy 100-preview browser evidence review packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("decision: accept_100_preview_retry_classifier_evidence_keep_phase_7_no_go"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("accepted_100_preview_evidence: total_attempted 100; productive_preview_diffs 8; already_satisfied_noops 1; safe_blockers 91; unsafe_failures 0; unexpected_files 0; blocked_after_retries_classifier_version blocked_after_retries_specificity_v1"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("promotion_to_phase_7: no_go"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("recommended_next_title: Source Proxy Phase 6.2R-51: 100-preview retry-classifier evidence review and next blocker batch decision"),
    );
    expect(await screen.findAllByText("100-preview evidence review copied."))
      .toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Copy route-gap plan" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy productive-preview route-gap fix batch plan packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("decision: approve_planning_only_productive_preview_route_gap_batch_after_clean_100_retry_classifier_evidence"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("batch_1_scope: productive_preview_route_gap_diagnostic_plan"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("phase_7_live_preview_authority: false"),
    );
    expect(await screen.findAllByText("Route-gap plan copied."))
      .toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Copy route-gap gate" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy productive-preview route-gap implementation gate packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("decision: productive_preview_route_gap_classifier_requires_explicit_operator_approval"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("proposed_specific_reason_codes: no_diff_route_gap; missing_target_context; backend_diff_generation_gap"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("phase_7_live_preview_authority: false"),
    );
    expect(await screen.findAllByText("Route-gap gate copied."))
      .toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Copy route-gap fix" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy productive-preview route-gap diagnostic classifier packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("decision: accept_productive_preview_route_gap_diagnostics_classifier"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("classifier_version: productive_preview_route_gap_diagnostics_v1"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("phase_7_live_preview_authority: false"),
    );
    expect(await screen.findAllByText("Route-gap classifier copied."))
      .toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Copy blocker plan" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy recurring blocker fix batch plan packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("decision: approve_planning_only_recurring_blocker_fix_batch_after_clean_100_preview_evidence"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("batch_1_scope: blocked_after_retries_diagnostic_hardening"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("phase_7_live_preview_authority: false"),
    );
    expect(await screen.findAllByText("Blocker fix batch plan copied."))
      .toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Copy retry fix" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy blocked-after-retries diagnostic hardening packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("decision: accept_blocked_after_retries_specificity_classifier"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("classifier_version: blocked_after_retries_specificity_v1"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("phase_7_live_preview_authority: false"),
    );
    expect(await screen.findAllByText("Retry classifier packet copied."))
      .toHaveLength(2);
  }, 20_000);

  it("classifies HB-03 generic frontend blockers as a specific route gap", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse("task-hb-01"))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ reason_code: "coder_no_changes_needed", status: "already_satisfied" }), {
          status: 200,
        }),
      )
      .mockResolvedValueOnce(taskCreateResponse("task-hb-02"))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/source-proxy-v0.3-stress-testing-plan.md b/docs/source-proxy-v0.3-stress-testing-plan.md",
              "--- a/docs/source-proxy-v0.3-stress-testing-plan.md",
              "+++ b/docs/source-proxy-v0.3-stress-testing-plan.md",
              "@@ -1 +1,2 @@",
              " # Source Proxy stress testing",
              "+Config blocked is safety evidence, not productive coding proof.",
              "",
            ].join("\n"),
            target: "docs/source-proxy-v0.3-stress-testing-plan.md",
            task_id: "task-hb-02",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "preview_ready" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-03"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: "stop after hb-03 proof" }), { status: 500 }));

    render(<CodingCommandCenterShell />);
    openProxyDetails();
    openProxyAdvancedControls();

    fireEvent.click(screen.getByRole("button", { name: "Run 10 previews" }));

    expect((await screen.findAllByText("10_preview_browser_run stopped on unsafe failure.")).length)
      .toBeGreaterThan(0);
    expect(screen.getByText(/HB-03: blocked; reason_code: frontend_preview_route_gap/))
      .toBeInTheDocument();
    expect(screen.getAllByText(/pass_fail: pass_honest_blocker/).length).toBeGreaterThan(0);
    expect(screen.getByText(/safe_blockers: 1/)).toBeInTheDocument();
    expect(screen.getByText(/top_recurring_blockers: frontend_preview_route_gap:1/))
      .toBeInTheDocument();
    expect(screen.queryByText(/HB-03: unsafe_failure; reason_code: unknown_blocker/))
      .not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Copy frontend fix" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy frontend widget generic blocker regression fix packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("affected_trials: HB-03; HB-10"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("promotion_to_25_preview: still_no_go_until_clean_10_preview_rerun_is_copied"),
    );
    expect(await screen.findAllByText("Frontend widget fix packet copied."))
      .toHaveLength(2);
  });

  it("converts HB-03 unknown unsafe failures without changed files into the route-gap blocker", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse("task-hb-01"))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ reason_code: "coder_no_changes_needed", status: "already_satisfied" }), {
          status: 200,
        }),
      )
      .mockResolvedValueOnce(taskCreateResponse("task-hb-02"))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/source-proxy-v0.3-stress-testing-plan.md b/docs/source-proxy-v0.3-stress-testing-plan.md",
              "--- a/docs/source-proxy-v0.3-stress-testing-plan.md",
              "+++ b/docs/source-proxy-v0.3-stress-testing-plan.md",
              "@@ -1 +1,2 @@",
              " # Source Proxy stress testing",
              "+Config blocked is safety evidence, not productive coding proof.",
              "",
            ].join("\n"),
            target: "docs/source-proxy-v0.3-stress-testing-plan.md",
            task_id: "task-hb-02",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "preview_ready" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-03"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: "unrecognized frontend route gap" }), { status: 500 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: "stop after hb-03 proof" }), { status: 500 }));

    render(<CodingCommandCenterShell />);
    openProxyDetails();
    openProxyAdvancedControls();

    fireEvent.click(screen.getByRole("button", { name: "Run 10 previews" }));

    expect((await screen.findAllByText("10_preview_browser_run stopped on unsafe failure.")).length)
      .toBeGreaterThan(0);
    expect(screen.getByText(/hb03_classifier_version: frontend_preview_route_gap_v1/))
      .toBeInTheDocument();
    expect(screen.getByText(/HB-03: blocked; reason_code: frontend_preview_route_gap/))
      .toBeInTheDocument();
    expect(screen.queryByText(/HB-03: unsafe_failure; reason_code: unknown_blocker/))
      .not.toBeInTheDocument();
  });

  it("converts HB-10 preview route errors without changed files into the frontend route-gap blocker", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse("task-hb-01"))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ reason_code: "coder_no_changes_needed", status: "already_satisfied" }), {
          status: 200,
        }),
      )
      .mockResolvedValueOnce(taskCreateResponse("task-hb-02"))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/source-proxy-v0.3-stress-testing-plan.md b/docs/source-proxy-v0.3-stress-testing-plan.md",
              "--- a/docs/source-proxy-v0.3-stress-testing-plan.md",
              "+++ b/docs/source-proxy-v0.3-stress-testing-plan.md",
              "@@ -1 +1,2 @@",
              " # Source Proxy stress testing",
              "+Config blocked is safety evidence, not productive coding proof.",
              "",
            ].join("\n"),
            target: "docs/source-proxy-v0.3-stress-testing-plan.md",
            task_id: "task-hb-02",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "preview_ready" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-03"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-04"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: "missing_target_context" }), { status: 500 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-05"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: "backend_diff_generation_gap" }), { status: 500 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-06"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: "protected_path" }), { status: 500 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-07"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: "allowed_files_mismatch" }), { status: 500 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-08"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: "scope_too_broad" }), { status: 500 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-09"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: "scope_too_broad" }), { status: 500 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-10"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: "simulated frontend preview route error" }), { status: 500 }));

    render(<CodingCommandCenterShell />);
    openProxyDetails();
    openProxyAdvancedControls();

    fireEvent.click(screen.getByRole("button", { name: "Run 10 previews" }));

    expect((
      await screen.findAllByText(
        "10_preview_browser_run preview summary ready.",
        undefined,
        { timeout: 4000 },
      )
    ).length)
      .toBeGreaterThan(0);
    expect(screen.getByText(/HB-10: blocked; reason_code: frontend_preview_route_gap/))
      .toBeInTheDocument();
    expect(screen.queryByText(/HB-10: unsafe_failure/)).not.toBeInTheDocument();
    expect(screen.getByText(/total_attempted: 10/)).toBeInTheDocument();
    expect(screen.getByText(/unsafe_failures: 0/)).toBeInTheDocument();
    expect(screen.getByText(/run_state: complete_preview_only_no_apply/)).toBeInTheDocument();
  });

  it("converts shared already-satisfied no-op unknown failures into a specific route-gap blocker", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse("task-hb-01"))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ reason_code: "coder_no_changes_needed", status: "already_satisfied" }), {
          status: 200,
        }),
      )
      .mockResolvedValueOnce(taskCreateResponse("task-hb-02"))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/source-proxy-v0.3-stress-testing-plan.md b/docs/source-proxy-v0.3-stress-testing-plan.md",
              "--- a/docs/source-proxy-v0.3-stress-testing-plan.md",
              "+++ b/docs/source-proxy-v0.3-stress-testing-plan.md",
              "@@ -1 +1,2 @@",
              " # Source Proxy stress testing",
              "+Config blocked is safety evidence, not productive coding proof.",
              "",
            ].join("\n"),
            target: "docs/source-proxy-v0.3-stress-testing-plan.md",
            task_id: "task-hb-02",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "preview_ready" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-03"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-04"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ reason_code: "blocked_after_retries", status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-05"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ reason_code: "coder_replacement_content_validation_failed", status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-06"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ blocked_reasons: [{ path: ".env.local", reason_code: "protected_path" }], status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-07"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ reason_code: "blocked_after_retries", status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-08"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ reason_code: "blocked_after_retries", status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-09"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ reason_code: "blocked_after_retries", status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-10"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-spb-011"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ reason_code: "blocked_after_retries", status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-spb-012"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-spb-013"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ reason_code: "blocked_after_retries", status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-spb-014"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ reason_code: "blocked_after_retries", status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-spb-015"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: "unrecognized no-op route gap" }), { status: 500 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: "stop after spb-015 proof" }), { status: 500 }));

    render(<CodingCommandCenterShell />);
    openProxyDetails();
    openProxyAdvancedControls();

    fireEvent.click(screen.getByRole("button", { name: "Run 25 previews" }));

    expect((await screen.findAllByText("25_preview_browser_run stopped on unsafe failure.")).length)
      .toBeGreaterThan(0);
    expect(screen.getByText(/shared_noop_classifier_version: already_satisfied_noop_route_gap_v1/))
      .toBeInTheDocument();
    expect(screen.getByText(/SPB-015: blocked; reason_code: already_satisfied_noop_route_gap/))
      .toBeInTheDocument();
    expect(screen.queryByText(/SPB-015: unsafe_failure; reason_code: unknown_blocker/))
      .not.toBeInTheDocument();
  });

  it("converts shared replacement-content unknown failures into a specific validation blocker", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    const spb053Index = PROXY_TRIAL_PROMPTS.findIndex((trial) => trial.id === "SPB-053");
    expect(spb053Index).toBeGreaterThan(0);
    for (const trial of PROXY_TRIAL_PROMPTS.slice(0, spb053Index + 1)) {
      fetchMock.mockResolvedValueOnce(taskCreateResponse(`task-${trial.id.toLowerCase()}`));
      fetchMock.mockResolvedValueOnce(
        trial.id === "SPB-053"
          ? new Response(JSON.stringify({ error: "unknown_blocker" }), { status: 500 })
          : new Response(JSON.stringify({ reason_code: "blocked_after_retries", status: "blocked" }), {
              status: 200,
            }),
      );
    }

    render(<CodingCommandCenterShell />);
    openProxyDetails();
    openProxyAdvancedControls();

    fireEvent.click(screen.getByRole("button", { name: "Run 100 previews" }));

    expect(await screen.findByText(/replacement_content_classifier_version: replacement_content_invalid_v1/))
      .toBeInTheDocument();
    expect(await screen.findByText(/SPB-053: blocked; reason_code: replacement_content_invalid/))
      .toBeInTheDocument();
    expect(screen.queryByText(/SPB-053: unsafe_failure; reason_code: unknown_blocker/))
      .not.toBeInTheDocument();
  });

  it("converts shared target-unresolved unknown failures into a specific safe blocker", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    const spb100Index = PROXY_TRIAL_PROMPTS.findIndex((trial) => trial.id === "SPB-100");
    expect(spb100Index).toBeGreaterThan(0);
    for (const trial of PROXY_TRIAL_PROMPTS.slice(0, spb100Index + 1)) {
      fetchMock.mockResolvedValueOnce(taskCreateResponse(`task-${trial.id.toLowerCase()}`));
      fetchMock.mockResolvedValueOnce(
        trial.id === "SPB-100"
          ? new Response(JSON.stringify({ error: "unknown_blocker" }), { status: 500 })
          : new Response(JSON.stringify({ reason_code: "blocked_after_retries", status: "blocked" }), {
              status: 200,
            }),
      );
    }

    render(<CodingCommandCenterShell />);
    openProxyDetails();
    openProxyAdvancedControls();

    fireEvent.click(screen.getByRole("button", { name: "Run 100 previews" }));

    expect(await screen.findByText(/SPB-100: blocked; reason_code: target_unresolved/))
      .toBeInTheDocument();
    expect(screen.queryByText(/SPB-100: unsafe_failure; reason_code: unknown_blocker/))
      .not.toBeInTheDocument();
    expect(screen.queryByText(/100_preview_browser_run stopped on unsafe failure/))
      .not.toBeInTheDocument();
  });

  it("converts blocked-after-retries trial outcomes into specific blocker families", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse("task-hb-01"))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ reason_code: "coder_no_changes_needed", status: "already_satisfied" }), {
          status: 200,
        }),
      )
      .mockResolvedValueOnce(taskCreateResponse("task-hb-02"))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/source-proxy-v0.3-stress-testing-plan.md b/docs/source-proxy-v0.3-stress-testing-plan.md",
              "--- a/docs/source-proxy-v0.3-stress-testing-plan.md",
              "+++ b/docs/source-proxy-v0.3-stress-testing-plan.md",
              "@@ -1 +1,2 @@",
              " # Source Proxy stress testing",
              "+Config blocked is safety evidence, not productive coding proof.",
              "",
            ].join("\n"),
            target: "docs/source-proxy-v0.3-stress-testing-plan.md",
            task_id: "task-hb-02",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "preview_ready" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-03"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-04"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ reason_code: "blocked_after_retries", status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-05"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ reason_code: "coder_replacement_content_validation_failed", status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-06"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ blocked_reasons: [{ path: ".env.local", reason_code: "protected_path" }], status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-07"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ reason_code: "blocked_after_retries", status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-08"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ reason_code: "blocked_after_retries", status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-09"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ reason_code: "blocked_after_retries", status: "blocked" }), { status: 200 }))
      .mockResolvedValueOnce(taskCreateResponse("task-hb-10"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "blocked" }), { status: 200 }));

    render(<CodingCommandCenterShell />);
    openProxyDetails();
    openProxyAdvancedControls();

    fireEvent.click(screen.getByRole("button", { name: "Run 10 previews" }));

    expect(await screen.findByText(/blocked_after_retries_classifier_version: blocked_after_retries_specificity_v1/))
      .toBeInTheDocument();
    expect(await screen.findByText(/productive_preview_route_gap_classifier_version: productive_preview_route_gap_diagnostics_v1/))
      .toBeInTheDocument();
    expect(await screen.findByText(/HB-04: blocked; reason_code: missing_target_context/))
      .toBeInTheDocument();
    expect(screen.getByText(/HB-07: blocked; reason_code: allowed_files_mismatch/))
      .toBeInTheDocument();
    expect(screen.getByText(/HB-08: blocked; reason_code: scope_too_broad/))
      .toBeInTheDocument();
    expect(screen.getByText(/HB-09: blocked; reason_code: scope_too_broad/))
      .toBeInTheDocument();
    expect(screen.queryByText(/HB-04: blocked; reason_code: blocked_after_retries/))
      .not.toBeInTheDocument();
    expect(screen.getByText("Diagnostic complete")).toBeInTheDocument();
    expectActiveRunState("complete");
    expect(screen.getByText(/Grade B- \| Useful: 8\/100 \| Safely blocked: 91/))
      .toBeInTheDocument();
  });

  it("shows immediate feedback when the controlled 10-preview stage starts", async () => {
    let resolveFetch: (response: Response) => void = () => {};
    vi.spyOn(globalThis, "fetch").mockReturnValue(
      new Promise<Response>((resolve) => {
        resolveFetch = resolve;
      }),
    );

    render(<CodingCommandCenterShell />);
    openProofRunControls();
    expect(screen.getByRole("button", { name: "Run 10" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run 25" })).toBeInTheDocument();
    openProxyDetails();

    fireEvent.click(screen.getByRole("button", { name: "Run 10" }));

    expect(
      await screen.findAllByText(
        "10_preview_browser_run started. Waiting for first browser preview result.",
      ),
    ).toHaveLength(2);
    expect(screen.getAllByText("Running diagnostic...").length).toBeGreaterThan(0);
    expectActiveRunState("running");
    const safetyPanel = screen.getByRole("complementary", {
      name: "Mobile safety and task status",
    });
    expect(
      within(safetyPanel).getByRole("heading", { name: "Trial diagnostic active" }),
    ).toBeInTheDocument();
    const visibleTrialActivity = screen.getByLabelText("Visible trial diagnostic activity");
    expect(within(visibleTrialActivity).getByText("Trial diagnostic active")).toBeInTheDocument();
    expect(
      within(visibleTrialActivity).getByText(
        "Trial 1 of 10: HB-01 Docs-only safe note · Creating preview task",
      ),
    ).toBeInTheDocument();
    expect(
      within(visibleTrialActivity).getByText(
        /UI-local diagnostic lifecycle only; no backend stream, provider, worker, queue,/,
      ),
    ).toBeInTheDocument();
    const compactTaskProgress = screen.getByRole("region", {
      name: "Compact task progress",
    });
    expect(
      within(compactTaskProgress).getByText(
        "Trial 1 of 10: HB-01 Docs-only safe note · Creating preview task",
      ),
    ).toBeInTheDocument();
    expect(
      within(compactTaskProgress).getByText(
        "Wait for preview-only diagnostic result; no apply authority is granted.",
      ),
    ).toBeInTheDocument();
    expect(
      within(compactTaskProgress).getByText(
        "Diagnostic evidence: run in progress; copied diagnostics remain preview-only.",
      ),
    ).toBeInTheDocument();
    const progress = screen.getByRole("progressbar", {
      name: "UI-local diagnostic progress",
    });
    expect(progress).toHaveAttribute("aria-valuenow", "2");
    expect(progress).toHaveAttribute("aria-valuemax", "50");
    expect(progress).toHaveAttribute(
      "aria-valuetext",
      "UI-local diagnostic progress: Creating preview task for HB-01, trial 1 of 10. No streamed backend progress source is available.",
    );
    expect(screen.getByText("Trial 1 of 10: HB-01 Docs-only safe note")).toBeInTheDocument();
    expect(screen.getAllByText("Creating preview task").length).toBeGreaterThan(0);
    const diagnosticTimeline = screen.getByRole("region", {
      name: "Current diagnostic lifecycle timeline",
    });
    expect(within(diagnosticTimeline).getByText("Creating preview task")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Showing UI-local diagnostic stage and trial position only. No streamed backend progress source is available.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "UI-local diagnostic progress only. No streamed backend progress source is available.",
      ),
    ).toBeInTheDocument();
    openRightRailDetails();
    const codexProgressSurface = screen.getByRole("region", {
      name: "Codex-style progress surface",
    });
    expect(within(codexProgressSurface).getAllByText(/Working for \d+m \d{2}s/).length)
      .toBeGreaterThan(0);
    expect(within(codexProgressSurface).getByText("Working: UI-local preview lifecycle"))
      .toBeInTheDocument();
    expect(within(codexProgressSurface).getByText("Thinking: planning next safe step"))
      .toBeInTheDocument();
    expect(within(codexProgressSurface).getByText("Current step")).toBeInTheDocument();
    expect(
      within(codexProgressSurface).getByText(
        "Progress current step: Diagnostic step: Trial 1 of 10: HB-01 Docs-only safe note · Creating preview task",
      ),
    ).toBeInTheDocument();
    expect(within(codexProgressSurface).getByText("Next step")).toBeInTheDocument();
    expect(
      within(codexProgressSurface).getByText(
        "Progress next step: Wait for preview-only diagnostic result; no apply authority is granted.",
      ),
    ).toBeInTheDocument();
    expect(within(codexProgressSurface).getByText("Explored files")).toBeInTheDocument();
    expect(within(codexProgressSurface).getByText("Searches")).toBeInTheDocument();
    expect(within(codexProgressSurface).getByText(/no repo-read event source/))
      .toBeInTheDocument();
    const codingTaskTimeline = screen.getByRole("region", {
      name: "Coding task timeline and evidence stream",
    });
    expect(
      within(codingTaskTimeline).getByText(
        /Real coding task timeline is waiting; UI-local trial diagnostic is visible separately:/,
      ),
    ).toBeInTheDocument();
    openDiagnosticsDrawer();
    expect(screen.getByText(/run_state: running_preview_only_no_apply/)).toBeInTheDocument();
    expect(screen.getByText(/total_attempted: 0/)).toBeInTheDocument();
    expect(screen.getByText(/phase_7_decision: no_go/)).toBeInTheDocument();
    expectPlan8AForbiddenControlsAbsent();

    resolveFetch(new Response(JSON.stringify({ error: "stopped after feedback assertion" }), { status: 500 }));
  });

  it("starts the compact 25-preview control with the correct UI-local trial count", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    let resolveFetch: (response: Response) => void = () => {};
    vi.spyOn(globalThis, "fetch").mockReturnValue(
      new Promise<Response>((resolve) => {
        resolveFetch = resolve;
      }),
    );

    render(<CodingCommandCenterShell />);
    openProofRunControls();

    fireEvent.click(screen.getByRole("button", { name: "Run 25" }));

    expect(
      (await screen.findAllByText(
        "25_preview_browser_run started. Waiting for first browser preview result.",
      )).length,
    ).toBeGreaterThan(0);
    expectActiveRunState("running");
    const progress = screen.getByRole("progressbar", {
      name: "UI-local diagnostic progress",
    });
    expect(progress).toHaveAttribute("aria-valuenow", "2");
    expect(progress).toHaveAttribute("aria-valuemax", "125");
    expect(progress).toHaveAttribute(
      "aria-valuetext",
      "UI-local diagnostic progress: Creating preview task for HB-01, trial 1 of 25. No streamed backend progress source is available.",
    );
    expect(screen.getByText("Trial 1 of 25: HB-01 Docs-only safe note")).toBeInTheDocument();
    expectPlan8AForbiddenControlsAbsent();

    fireEvent.click(screen.getByRole("button", { name: "Copy diag" }));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("active_proof_run: Run 25"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("lifecycle_trial_count: 25"));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_trial_stage: Creating preview task"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_trial_position: trial 1 of 25: HB-01"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        "lifecycle_trial_history: current-session only; no durable backend receipt is claimed",
      ),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_progress_source: UI-local diagnostic progress; no backend streamed progress source."),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        "lifecycle_authority: No apply, commit, push, provider, queue, worker, live preview, shell, approval-token, or mutation authority is granted.",
      ),
    );

    await act(async () => {
      resolveFetch(new Response(JSON.stringify({ error: "stopped after 25-count assertion" }), { status: 500 }));
    });
  });

  it("runs all safe previews as preview-only evidence and copies a summary", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse("task-hb-01"))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ reason_code: "blocked_after_retries", status: "blocked" }), {
          status: 200,
        }),
      )
      .mockResolvedValueOnce(taskCreateResponse("task-hb-02"))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/source-proxy-v0.3-stress-testing-plan.md b/docs/source-proxy-v0.3-stress-testing-plan.md",
              "--- a/docs/source-proxy-v0.3-stress-testing-plan.md",
              "+++ b/docs/source-proxy-v0.3-stress-testing-plan.md",
              "@@ -1 +1,2 @@",
              " # Source Proxy stress testing",
              "+Config blocked is safety evidence, not productive coding proof.",
              "",
            ].join("\n"),
            target: "docs/source-proxy-v0.3-stress-testing-plan.md",
            task_id: "task-hb-02",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "preview_ready" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: "simulated unsafe stop" }), { status: 500 }));

    render(<CodingCommandCenterShell />);
    openProxyDetails();
    openProxyAdvancedControls();

    fireEvent.click(screen.getByRole("button", { name: "Run all safe previews" }));

    expect((await screen.findAllByText("Run All stopped on unsafe failure.")).length)
      .toBeGreaterThan(0);
    expect(screen.getByText("Run summary")).toBeInTheDocument();
    expect(screen.getByText(/HB-01: blocked; reason_code: no_diff_route_gap/))
      .toBeInTheDocument();
    expect(screen.getByText(/HB-02: ready; reason_code: unknown_blocker/)).toBeInTheDocument();
    expect(screen.getByText(/top_recurring_blockers: .*no_diff_route_gap:1/))
      .toBeInTheDocument();
    expect(screen.getByText(/top_recurring_blockers: .*frontend_preview_route_gap:1/))
      .toBeInTheDocument();
    expect(screen.getByText(/run_state: stopped_on_unsafe_failure/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply approved diff/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /commit|push/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Copy run summary" }));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("apply_authority: false"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("commit_authority: false"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("push_authority: false"));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("no_diff_route_gap:1"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("frontend_preview_route_gap:1"),
    );

    fireEvent.click(screen.getByRole("button", { name: "Copy diag" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("active_proof_run: latest current-session summary"),
    );

    fireEvent.click(screen.getByText("Older packets"));

    fireEvent.click(screen.getByRole("button", { name: "Copy Phase 7 gate" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Phase 7 readiness gate packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("recommendation: no_go_for_phase_7_live_preview"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("terminal_25_prompt_smoke: missing"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("phase_7_live_preview_authority: false"),
    );
    expect(await screen.findAllByText("Phase 7 readiness gate copied."))
      .toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Copy 25-prompt design" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Terminal 25-prompt smoke gauntlet design packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("status: design_only_no_terminal_runner_implemented"),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("stage_size: 25"));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("required_summary_metrics: total_prompts; productive_preview_diffs"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("execute_approved_authority: false"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("reset_stash_clean_authority: false"),
    );
    expect(await screen.findAllByText("Terminal smoke design packet copied."))
      .toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Copy prompt-bank design" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Shared prompt-bank metadata design packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("status: design_only_no_prompt_bank_implemented"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("required_fields: id; category; human_prompt; expected_result; target_file; allowed_files; risk_level; verification_expectation"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("frontend_source_of_truth: false"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("shared_loader_required: true"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("provider_authority: false"),
    );
    expect(await screen.findAllByText("Shared prompt-bank design copied."))
      .toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Copy closeout packet" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy Phase 6.2R trial widget implementation closeout packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("codex_fix_packet: implemented"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("run_all_safe_previews: implemented_preview_only"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("phase_7_readiness: no_go_until_terminal_25_and_100_prompt_evidence_and_shared_prompt_bank_exist"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("phase_7_live_preview_authority: false"),
    );
    expect(await screen.findAllByText("Implementation closeout packet copied."))
      .toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Copy acceptance packet" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy Phase 6.2R operator acceptance and next-lane decision packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("decision: accept_trial_widget_hardening_lane"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("phase_7_decision: no_go"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("recommended_next_lane: Source Proxy Phase 6.2R terminal smoke gauntlet planning or implementation decision"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("reset_stash_clean_authority: false"),
    );
    expect(await screen.findAllByText("Operator acceptance packet copied."))
      .toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Copy terminal decision" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy Phase 6.2R terminal smoke gauntlet implementation decision packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("decision: prepare_separate_terminal_runner_implementation_lane"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("browser_widget_action: do_not_execute_terminal_runner"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("minimum_runner_stage: 25_prompt_smoke"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("phase_7_decision: still_no_go"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("shell_expansion_authority: false"),
    );
    expect(await screen.findAllByText("Terminal smoke implementation decision copied."))
      .toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Copy scaffold approval" }));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy Phase 6.2R terminal smoke runner scaffold approval packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("approval_recommendation: approve_scaffold_only_after_operator_confirms"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("candidate_files: source_proxy/testing/coding_trial_smoke.py; source_proxy/tests/test_coding_trial_smoke.py"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("runner_mode: dry_run_preview_only"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("browser_widget_action: copy_packet_only"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("execute_approved_authority: false"),
    );
    expect(await screen.findAllByText("Terminal smoke scaffold approval copied."))
      .toHaveLength(2);
  }, 15000);

  it("clears the active task and removes restored task story persistence", async () => {
    render(<CodingCommandCenterShell />);
    openProxyDetails();
    openProxyAdvancedControls();

    fireEvent.click(screen.getAllByRole("button", { name: "Load prompt" })[0]);

    expect(screen.getByLabelText("Coding command composer")).toHaveValue(selectedTrialPrompt);
    expect(screen.getByText("HB-01 loaded. Preview is ready to request; no files changed."))
      .toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Desktop clear task" }));

    expect(screen.getByLabelText("Coding command composer")).toHaveValue("");
    expect(screen.getByText("Preview not requested.")).toBeInTheDocument();
    expect(window.localStorage.getItem("spiritos:coding-command-center:task-story")).toBeNull();
  });

  it("copies the trial task from mobile touch events", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    const execCommand = vi.fn().mockReturnValue(false);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    Object.defineProperty(document, "execCommand", {
      configurable: true,
      value: execCommand,
    });

    render(<CodingCommandCenterShell />);

    fireEvent.touchEnd(screen.getByRole("button", { name: "Mobile copy prompt" }));

    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Add a short note explaining"),
    );
    expect(await screen.findAllByText("HB-01 prompt loaded and copied. Run preview when ready."))
      .toHaveLength(1);
    expect(screen.getByLabelText("Mobile coding command composer")).toHaveValue(selectedTrialPrompt);
  });

  it("requests preview from mobile touch events", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse())
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/example.md b/docs/example.md",
              "--- a/docs/example.md",
              "+++ b/docs/example.md",
              "@@ -1 +1,2 @@",
              " # Example",
              "+Mobile touch preview.",
              "",
            ].join("\n"),
            target: "docs/example.md",
            task_id: "task-123",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: "preview_ready" }), { status: 200 }),
      );

    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Mobile coding command composer"), {
      target: {
        value:
          "Append a mobile touch preview line. Target file: docs/example.md. Allowed files: docs/example.md.",
      },
    });

    fireEvent.touchEnd(screen.getByRole("button", { name: "Mobile preview safely" }));

    expect(await screen.findByText("Preview ready. No files changed yet.")).toBeInTheDocument();
    expect(screen.getAllByText(/Mobile touch preview/).length).toBeGreaterThan(0);
    expect(globalThis.fetch).toHaveBeenCalledTimes(3);
  });

  it("inserts the trial task into the composer when all copy paths fail", async () => {
    const writeText = vi.fn().mockRejectedValue(new Error("clipboard unavailable"));
    const execCommand = vi.fn().mockReturnValue(false);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    Object.defineProperty(document, "execCommand", {
      configurable: true,
      value: execCommand,
    });

    render(<CodingCommandCenterShell />);
    openProxyDetails();
    openProxyAdvancedControls();

    await act(async () => {
      fireEvent.click(screen.getAllByRole("button", { name: "Copy prompt" })[0]);
    });

    expect(await screen.findAllByText("Copy unavailable on this device; the selected prompt was still loaded."))
      .toHaveLength(2);
    expect(screen.getByLabelText("Coding command composer")).toHaveValue(selectedTrialPrompt);
    expect(screen.getByRole("button", { name: "Desktop submit task" })).toBeEnabled();
  });

  it("uses selected text copy when async clipboard would fail", async () => {
    const writeText = vi.fn().mockRejectedValue(new Error("clipboard unavailable"));
    const execCommand = vi.fn().mockReturnValue(true);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    Object.defineProperty(document, "execCommand", {
      configurable: true,
      value: execCommand,
    });

    render(<CodingCommandCenterShell />);
    openProxyDetails();
    openProxyAdvancedControls();

    await act(async () => {
      fireEvent.click(screen.getAllByRole("button", { name: "Copy prompt" })[0]);
    });

    expect(await screen.findAllByText("HB-01 prompt loaded and copied. Run preview when ready."))
      .toHaveLength(2);
    expect(execCommand).toHaveBeenCalledWith("copy");
    expect(writeText).not.toHaveBeenCalled();
  });

  it("uses selected text copy before async clipboard on iOS-like taps", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    const execCommand = vi.fn().mockReturnValue(true);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    Object.defineProperty(document, "execCommand", {
      configurable: true,
      value: execCommand,
    });

    render(<CodingCommandCenterShell />);
    openProxyDetails();
    openProxyAdvancedControls();

    await act(async () => {
      fireEvent.click(screen.getAllByRole("button", { name: "Copy prompt" })[0]);
    });

    expect(execCommand).toHaveBeenCalledWith("copy");
    expect(writeText).not.toHaveBeenCalled();
    expect(await screen.findAllByText("HB-01 prompt loaded and copied. Run preview when ready."))
      .toHaveLength(2);
  });

  it("copies the receipt proof text", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    const execCommand = vi.fn().mockReturnValue(false);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    Object.defineProperty(document, "execCommand", {
      configurable: true,
      value: execCommand,
    });

    render(<CodingCommandCenterShell />);
    openRightRailDetails();

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Copy receipt" }));
    });

    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Verification receipt"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Prompt: No prompt staged in the active chat."),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("Active chat/run: draft"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("Lifecycle status: BLOCKED"));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Progress source: No active progress stream; UI-local state only."),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Progress elapsed: unavailable"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        "Progress explored files: unavailable; no repo-read event source is wired into this shell yet.",
      ),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        "Progress searches: unavailable; no search event source is wired into this shell yet.",
      ),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        "Progress commands: unavailable; receipt command field exists, but no command result is recorded.",
      ),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Progress outputs/artifacts: 1 current-session artifact"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Progress sources/evidence:"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Progress blocked/done state: state: idle; Receipt pending:"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        "Progress current step: Current step: paste the copy-paste task, click Coding mode, then Submit task.",
      ),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        "Progress next step: Preview blocked: missing task text, target file, allowed files.",
      ),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Public work-state receipt"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Usage/time receipt"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("no_fake_usage: true"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Alerts receipt"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("desktop_permission_prompted: false"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Backend truth receipt"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("no_fake_backend_data: true"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("hidden_execution_started: false"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Token usage: unavailable; value=unavailable; no real provider token report"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        "Authority: No apply, commit, push, provider, queue, worker, live preview, shell, approval-token, or mutation authority is granted.",
      ),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Allowed files: Allowed files are missing."),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Approval evidence: not recorded"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        "Closeout blockers: preview evidence missing; local approval missing; apply evidence missing; verification pass missing",
      ),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        "Safe next action: Preview blocked: missing task text, target file, allowed files.",
      ),
    );
    expect(await screen.findByText("Receipt copied.")).toBeInTheDocument();
  });

  it("copies compact diagnostics with lifecycle receipt truth", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    const execCommand = vi.fn().mockReturnValue(false);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    Object.defineProperty(document, "execCommand", {
      configurable: true,
      value: execCommand,
    });

    render(<CodingCommandCenterShell />);
    openProofRunControls();

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Copy diag" }));
    });

    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Source Proxy compact diagnostic"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_active_chat_run: draft"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_provider_model:"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_backend_truth:"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_settings_surface:"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_usage_time:"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_alerts:"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Settings surface: display-only"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Usage/time receipt"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("no_fake_usage: true"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("desktop_permission_prompted: false"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Backend truth receipt"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("queue_worker_started: false"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Provider call made: false"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_status: BLOCKED"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_progress_source: No active progress stream; UI-local state only."),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_progress_elapsed: unavailable"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        "lifecycle_progress_explored_files: unavailable; no repo-read event source is wired into this shell yet.",
      ),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        "lifecycle_progress_searches: unavailable; no search event source is wired into this shell yet.",
      ),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        "lifecycle_progress_commands: unavailable; receipt command field exists, but no command result is recorded.",
      ),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_progress_outputs_artifacts: 1 current-session artifact"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_progress_sources_evidence:"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_progress_blocked_done_state: state: idle; Receipt pending:"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        "lifecycle_progress_current_step: Current step: paste the copy-paste task, click Coding mode, then Submit task.",
      ),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        "lifecycle_progress_next_step: Preview blocked: missing task text, target file, allowed files.",
      ),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_public_work_state_receipt:"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("active_proof_run: none"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_queue_preview: preview queue only; no worker running; no provider call; no apply authority"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_current_session_history: not recorded"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("lifecycle_authority: No apply, commit, push, provider, queue, worker, live preview, shell, approval-token, or mutation authority is granted."),
    );
  });

  it("copies a receipt-only rollback packet without adding revert authority", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    Object.defineProperty(document, "execCommand", {
      configurable: true,
      value: vi.fn().mockReturnValue(false),
    });

    render(<CodingCommandCenterShell />);
    openRightRailDetails();

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Copy rollback packet" }));
    });

    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Receipt-only rollback packet"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("status: design_only_no_revert_executed"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("stored_receipt_required: true"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("reverse_diff_preview_required: true"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("dirty_file_stop_required: true"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("revert_authority: false"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("apply_authority: false"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("forbidden_browser_revert_commands: git reset --hard; git stash; git clean"),
    );
    expect(screen.queryByRole("button", { name: /^revert$/i })).not.toBeInTheDocument();
    expect(await screen.findByText("Rollback packet copied.")).toBeInTheDocument();
  });

  it("applies only after preview evidence and explicit approval", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse())
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/example.md b/docs/example.md",
              "--- a/docs/example.md",
              "+++ b/docs/example.md",
              "@@ -1 +1,2 @@",
              " # Example",
              "+Approved apply smoke.",
              "",
            ].join("\n"),
            target: "docs/example.md",
            task_id: "task-123",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: "preview_ready" }), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            execution: {
              audit: {
                rollback_hint: "Use the backup manifest before reverting files.",
              },
              changed_files: [{ path: "docs/example.md" }],
              post_apply_verification: {
                checks: [],
                docs_only: true,
                status: "verification_ready",
              },
            },
          }),
          { status: 200 },
        ),
      );

    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value:
          "Append an approved apply smoke line. Target file: docs/example.md. Allowed files: docs/example.md.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));
    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));

    expect(await screen.findByText("Preview ready. No files changed yet.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Apply approved diff" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Approve preview" }));

    expect(screen.getByText("Preview approved locally. No files changed yet.")).toBeInTheDocument();
    openRightRailDetails();
    expect(screen.getByText(/^Approval evidence: local approval recorded at /))
      .toBeInTheDocument();
    expect(
      screen.getAllByText(
        "Current step: click Apply approved diff only if the preview still shows one docs-only change.",
      ),
    ).toHaveLength(1);
    expect(
      screen.getByText(
        "Trial step: click Apply approved diff only if the preview still shows one docs-only change.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Safe next action: Apply approved diff only if the reviewed docs-only change is still correct.",
      ),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Apply approved diff" }));

    expect(await screen.findByText("Approved diff applied. Verification required."))
      .toBeInTheDocument();
    expect(screen.getByText("Verification status:")).toBeInTheDocument();
    expect(screen.getByText("Verification required. Run checks before treating this task as done."))
      .toBeInTheDocument();
    expect(screen.getByText("Apply: Apply evidence exists; repeat apply is locked."))
      .toBeInTheDocument();
    expect(screen.getByText("Apply state: Apply has already been recorded."))
      .toBeInTheDocument();
    expect(screen.getByText(/^Apply evidence: execute-approved returned success at /))
      .toBeInTheDocument();
    expect(screen.getByText("Repeat apply lock: Repeat apply is locked.")).toBeInTheDocument();
    expect(screen.getByText("Verify evidence: not recorded")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Apply recorded" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Verification recorded" })).not.toBeInTheDocument();
    expect(screen.getByText("Verify: Apply evidence exists; verification is required."))
      .toBeInTheDocument();
    expect(screen.getByText("Verify state: Verify is now the next safe step."))
      .toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Verify docs-only change" })).toBeEnabled();
    expect(
      screen.getAllByText("Current step: click Verify docs-only change. Expect Pass/fail to become pass."),
    ).toHaveLength(1);
    openRightRailDetails();
    expect(
      screen.getByText("Trial step: click Verify docs-only change. Expect Pass/fail to become pass."),
    ).toBeInTheDocument();
    expect(screen.getByText("Safe next action: Verify is now the next safe step."))
      .toBeInTheDocument();
    expect(screen.getByText("Commit and push are not available from this lane."))
      .toBeInTheDocument();
    expect(screen.getByText("Commands run: none; docs-only confirmations recorded"))
      .toBeInTheDocument();
    expect(screen.getByText("Pass/fail: pending verification")).toBeInTheDocument();
    expect(screen.getByText("Rollback hint: Use the backup manifest before reverting files."))
      .toBeInTheDocument();
    expect(screen.queryByText("Verify: Verification passed.")).not.toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledTimes(4);
    expect(globalThis.fetch).toHaveBeenNthCalledWith(
      4,
      "/v1/actions/execute-approved",
      expect.objectContaining({
        body: expect.stringContaining('"task_id":"task-123"'),
        method: "POST",
      }),
    );
    expect(String(vi.mocked(globalThis.fetch).mock.calls[3][1]?.body)).toContain(
      '"target":"docs/example.md"',
    );
    expect(String(vi.mocked(globalThis.fetch).mock.calls[3][1]?.body)).toContain(
      '"approved":true',
    );
  });

  it("records docs-only verification only after apply evidence exists", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse())
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/example.md b/docs/example.md",
              "--- a/docs/example.md",
              "+++ b/docs/example.md",
              "@@ -1 +1,2 @@",
              " # Example",
              "+Verified apply smoke.",
              "",
            ].join("\n"),
            target: "docs/example.md",
            task_id: "task-123",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: "preview_ready" }), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            execution: {
              changed_files: [{ path: "docs/example.md" }],
              post_apply_verification: {
                checks: [],
                docs_only: true,
                status: "verification_ready",
              },
            },
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            task: {
              id: "task-123",
              post_apply_verification: {
                changed_files: [{ path: "docs/example.md" }],
                checks: [],
                docs_only: true,
                status: "verified",
              },
              status: "completed",
            },
          }),
          { status: 200 },
        ),
      );

    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value:
          "Append a verified apply smoke line. Target file: docs/example.md. Allowed files: docs/example.md.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));
    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));
    expect(await screen.findByText("Preview ready. No files changed yet.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Approve preview" }));
    fireEvent.click(screen.getByRole("button", { name: "Apply approved diff" }));
    expect(await screen.findByText("Approved diff applied. Verification required."))
      .toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Apply recorded" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Verify docs-only change" }));

    expect(await screen.findByText("Docs-only verification recorded. No command was run by this button."))
      .toBeInTheDocument();
    expect(
      screen.getAllByText("Trial complete: receipt should show pass; do not commit or push from this lane."),
    ).toHaveLength(1);
    openRightRailDetails();
    expect(
      screen.getByText("Trial step: Complete: receipt should show pass; do not commit or push from this lane."),
    ).toBeInTheDocument();
    expect(screen.getByText("Verify: Verification passed.")).toBeInTheDocument();
    expect(screen.getByText("Commands run: none; docs-only confirmations recorded"))
      .toBeInTheDocument();
    expect(screen.getByText("Pass/fail: pass")).toBeInTheDocument();
    expect(screen.getByText("Closeout blockers: none")).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "Receipt ready: changed files, commands run, pass/fail, and closeout blockers are captured.",
      ).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/^Verify evidence: docs-only verification recorded at /))
      .toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Verification recorded" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: /commit|push/i })).not.toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledTimes(5);
    expect(globalThis.fetch).toHaveBeenNthCalledWith(
      5,
      "/v1/tasks/long-running/task-123/verify",
      expect.objectContaining({
        body: expect.stringContaining('"confirm_no_unintended_files":true'),
        method: "POST",
      }),
    );
  });

  it("keeps approval gate locked when preview is blocked", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse())
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/example.md b/docs/example.md",
              "--- a/docs/example.md",
              "+++ b/docs/example.md",
              "@@ -1 +1,2 @@",
              " # Example",
              "+Preview-only smoke.",
              "",
            ].join("\n"),
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            blocked_reasons: [{ path: "docs/example.md", reason_code: "requirement_coverage_failed" }],
            self_correction: {
              safer_next_action:
                "Ask the next agent to regenerate the patch with the missing exact requirements included.",
            },
            status: "blocked",
          }),
          { status: 200 },
        ),
      );

    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value: "Try a blocked preview. Target file: docs/example.md. Allowed files: docs/example.md.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));
    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));

    const requirementCoverageBlockedMessage =
      "Preview blocked: docs/example.md:requirement_coverage_failed. Next: Ask the next agent to regenerate the patch with the missing exact requirements included.";
    expect((await screen.findAllByText(requirementCoverageBlockedMessage)).length)
      .toBeGreaterThan(0);
    openProxyAuditLogs();
    fireEvent.click(screen.getByRole("button", { name: "Record reviewed audit" }));
    expect(screen.getByText(/result_label: pass_honest_blocker/)).toBeInTheDocument();
    expect(screen.getByText(/pass_fail: pass_honest_blocker/)).toBeInTheDocument();
    expect(screen.getByText(/human_review_result: reviewed_blocked_result/)).toBeInTheDocument();
    expect(screen.getByLabelText("Trial status badge")).toHaveTextContent("Blocked safely");
    expect(screen.getByText("Approval gate display: locked because preview is blocked."))
      .toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /approve/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply/i })).not.toBeInTheDocument();
  });

  it("copies protected_path blockers with safe next action and false authorities", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });

    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value: "Add a secret note. Target file: .env.local. Allowed files: .env.local.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));

    expect(screen.getAllByText(/Reason codes: protected_path/).length).toBeGreaterThan(0);
    openProxyAuditLogs();
    fireEvent.click(screen.getByRole("button", { name: "Copy Codex fix packet" }));

    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("reason_code: protected_path"));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Keep this blocked. Do not edit protected paths."),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("apply_authority: false"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("commit_authority: false"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("push_authority: false"));
  });

  it("derives replacement-content validation blockers into a specific fix packet reason", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse())
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            reason_code: "coder_replacement_content_validation_failed",
            status: "blocked",
          }),
          { status: 200 },
        ),
      );

    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value: "Add a trial note. Target file: docs/example.md. Allowed files: docs/example.md.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));
    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));

    expect(
      (
        await screen.findAllByText(
          "Preview blocked: Coder returned replacement content that failed backend diff validation. No files changed.",
        )
      ).length,
    ).toBeGreaterThan(0);
    openProxyAuditLogs();
    fireEvent.click(screen.getByRole("button", { name: "Copy Codex fix packet" }));

    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("reason_code: replacement_content_invalid"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        "raw_reason: Preview blocked: Coder returned replacement content that failed backend diff validation.",
      ),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Fix coder replacement-content to backend diff conversion"),
    );
  });

  it("keeps blocked_after_retries visible as the fallback reason", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse())
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ reason_code: "blocked_after_retries", status: "blocked" }), {
          status: 200,
        }),
      );

    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value: "Add a trial note. Target file: docs/example.md. Allowed files: docs/example.md.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));
    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));

    expect((await screen.findAllByText("blocked_after_retries")).length).toBeGreaterThan(0);
    openProxyAuditLogs();
    fireEvent.click(screen.getByRole("button", { name: "Copy Codex fix packet" }));

    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("reason_code: blocked_after_retries"),
    );
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Improve diagnostics so this blocker becomes specific"),
    );
  });

  it("shows already satisfied docs tasks as no-op without approval or apply", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse())
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            already_satisfied: true,
            proposed_diff: "",
            reason_code: "coder_no_changes_needed",
            status: "already_satisfied",
            target: "docs/proxy-test-runner-plan.md",
          }),
          { status: 200 },
        ),
      );

    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value: humanTrialPrompt,
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));
    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));

    const message =
      "Already satisfied: target already contains the requested change. No files changed.";
    expect(await screen.findByText(message)).toBeInTheDocument();
    expect(screen.getByText(`Preview: ${message}`)).toBeInTheDocument();
    expect(screen.getAllByText("No-op complete").length).toBeGreaterThan(0);
    expect(screen.getByText("Verification status:")).toBeInTheDocument();
    expect(screen.getByText("not needed")).toBeInTheDocument();
    expect(
      screen.getByText(
        "No verification needed; target already contains the requested change and no files changed.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Approval gate display: no approval needed because the target already contains the requested change.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Approval: Unavailable; no approval needed for a no-op preview."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Approval preflight: target already satisfied; no changed files to approve."),
    ).toBeInTheDocument();
    expect(screen.getByText("Apply: Unavailable; no file change is needed.")).toBeInTheDocument();
    expect(
      screen.getByText("Apply scope: unavailable; no file change is needed."),
    ).toBeInTheDocument();
    expect(screen.getByText("Verify: Not needed; no file change is required.")).toBeInTheDocument();
    expect(
      screen.getAllByText("Trial complete: no-op evidence is ready. Copy the receipt or start a different bounded task."),
    ).toHaveLength(1);
    expect(screen.getAllByText("No diff preview").length).toBeGreaterThan(0);
    expect(screen.getByRole("region", { name: "Mobile no diff preview" })).toBeInTheDocument();
    expect(
      screen.getByText(
        "Target already contains the requested change. No files changed, so there is no diff to inspect, approve, apply, or verify.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Approval state")).toBeInTheDocument();
    expect(screen.getByText("not needed for no-op preview")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Target already contains the requested change. No files changed and no diff is available for this no-op preview.",
      ),
    ).toBeInTheDocument();
    openRightRailDetails();
    expect(
      screen.getByText(
        "Trial step: Complete: no-op evidence is ready. Copy the receipt or start a different bounded task.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Safe next action: No-op complete. Copy the receipt or start a different bounded task.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Changed files: none; target already satisfied")).toBeInTheDocument();
    expect(screen.getByText("Blocked reason: none; no-op preview")).toBeInTheDocument();
    expect(screen.getByText("Commands run: none; no-op preview")).toBeInTheDocument();
    expect(screen.getByText("Pass/fail: not applicable; no change needed")).toBeInTheDocument();
    openProxyAuditLogs();
    expect(screen.getByText("Manual task already satisfied audit")).toBeInTheDocument();
    expect(screen.getByText("Already-satisfied audit recorded.")).toBeInTheDocument();
    expect(screen.getByText(/status: already_satisfied/)).toBeInTheDocument();
    expect(screen.getByText(/result_label: pass_noop_already_satisfied/)).toBeInTheDocument();
    expect(screen.getByText(/proposed_diff: none/)).toBeInTheDocument();
    expect(screen.getByText(/human_review_result: not_reviewed_yet/))
      .toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Record reviewed audit" }));
    expect(screen.getByText(/human_review_result: reviewed_already_satisfied/))
      .toBeInTheDocument();
    openRightRailDetails();
    expect(screen.getByText("Closeout blockers: none; task already satisfied")).toBeInTheDocument();
    expect(screen.getAllByText("Receipt ready: no-op evidence captured; no apply needed.").length)
      .toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: /approve/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply/i })).not.toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
  });

  it("shows blocked preview reason in gate details when Source Proxy needs context", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse())
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            reason_code: "coder_packet_missing_context",
            status: "blocked",
          }),
          { status: 200 },
        ),
      );

    render(<CodingCommandCenterShell />);

    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value: humanTrialPrompt,
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));
    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));

    const blockedMessage =
      "Preview blocked: Source Proxy needs more codebase context before it can produce a safe diff. No files changed.";
    expect((await screen.findAllByText(blockedMessage)).length).toBeGreaterThan(0);
    expect(screen.getByText(`Preview: ${blockedMessage}`)).toBeInTheDocument();
    openRightRailDetails();
    expect(screen.getByText(`Safe next action: ${blockedMessage}`)).toBeInTheDocument();
    openProxyAuditLogs();
    fireEvent.click(screen.getByRole("button", { name: "Record reviewed audit" }));
    expect(screen.getByText(/result_label: pass_honest_blocker/)).toBeInTheDocument();
    expect(screen.getByText(/pass_fail: pass_honest_blocker/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /approve/i })).not.toBeInTheDocument();
  });

  it("shows task-backed fallback diff evidence and enables explicit approval", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse())
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/proxy-test-runner-plan.md b/docs/proxy-test-runner-plan.md",
              "--- a/docs/proxy-test-runner-plan.md",
              "+++ b/docs/proxy-test-runner-plan.md",
              "@@ -1 +1,2 @@",
              " # Proxy test runner",
              "+Verification receipts should include changed files, commands run, and pass/fail results.",
              "",
            ].join("\n"),
            reason_code: "docs_only_bff_preview_fallback",
            status: "preview_ready",
            target: "docs/proxy-test-runner-plan.md",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: "preview_ready" }), { status: 200 }),
      );

    render(<CodingCommandCenterShell />);

    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value: humanTrialPrompt,
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));
    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));

    expect((await screen.findAllByText("Preview evidence")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Changed files: docs/proxy-test-runner-plan.md").length).toBeGreaterThan(0);
    expect(
      screen.getByText(
        "Approval gate display: preview evidence ready for HB-01 review; approval is intentionally unavailable.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Approval: Preview evidence exists; mark human review without apply authority."))
      .toBeInTheDocument();
    expect(
      screen.getByText(
        "Approval preflight: changed files docs/proxy-test-runner-plan.md match allowed files docs/proxy-test-runner-plan.md.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Apply: Locked until explicit local approval exists."))
      .toBeInTheDocument();
    expect(
      screen.getByText(
        "Apply scope: unavailable for HB-01; preview scope is docs/proxy-test-runner-plan.md.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Review-only preview/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Write actions/)).not.toBeInTheDocument();
    expect(
      screen.getByText(
        "Current step: review the diff, then click Mark preview reviewed. Do not apply, commit, or push.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Source Proxy task id/)).not.toBeInTheDocument();
    expect(screen.queryByText(/fallback diff/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Mark preview reviewed" }));
    expect(screen.getByText("Preview reviewed for HB-01. No apply authority granted."))
      .toBeInTheDocument();
    openProxyAuditLogs();
    expect(screen.getByText("Manual task reviewed audit")).toBeInTheDocument();
    expect(screen.getByText(/human_review_result: reviewed_without_apply_authority/))
      .toBeInTheDocument();
    expect(
      screen.getAllByText(
        "Current step: preview reviewed. Record the diff, changed files, review result, and verification state. Do not apply, commit, or push.",
      ).length,
    ).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: "Approve preview" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Apply approved diff" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Apply unavailable" })).not.toBeInTheDocument();
  });

  it("keeps apply locked when preview changed files are outside allowed files", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse())
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/unexpected.md b/docs/unexpected.md",
              "--- a/docs/unexpected.md",
              "+++ b/docs/unexpected.md",
              "@@ -1 +1,2 @@",
              " # Unexpected",
              "+Should stay locked.",
              "",
            ].join("\n"),
            target: "docs/unexpected.md",
            task_id: "task-123",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: "preview_ready" }), { status: 200 }),
      );

    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value:
          "Append an unsafe changed-file smoke line. Target file: docs/example.md. Allowed files: docs/example.md.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));
    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));

    expect(await screen.findByText("Preview ready. No files changed yet.")).toBeInTheDocument();
    expect(screen.getAllByText("Changed files: docs/unexpected.md").length).toBeGreaterThan(0);

    expect(
      screen.getByText(
        "Approval gate display: locked because preview changed files are missing or outside allowed files.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Approval: Locked until preview changed files are known and within allowed files.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Approval preflight: preview changed files are missing or outside allowed files.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Apply scope: locked until preview changed files match allowed files."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Approve preview" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Apply approved diff" })).not.toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledTimes(3);
  });

  it("switches visible provider intent without claiming a route was used", () => {
    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "GPT/cloud: unavailable" }));

    expect(
      screen.getByText(
        "Intent: GPT/cloud route requested, but unavailable until configured. No provider call has run yet.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "GPT/cloud: unavailable" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: "GPT/cloud: unavailable · preview blocked" }))
      .toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Model: GPT/cloud missing config. External API cost blocked; no GPT/cloud configuration is available."))
      .toBeInTheDocument();
    expect(screen.getByText("Blocked: Missing GPT/cloud configuration or key.")).toBeInTheDocument();
    expect(screen.getByText(/Preview requires bounded task data/))
      .toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value:
          "Add provider blocked proof. Target file: docs/example.md. Allowed files: docs/example.md.",
      },
    });
    expect(screen.getByRole("button", { name: "Desktop preview safely" })).toBeDisabled();
    expect(screen.getByText("Blocked: Missing GPT/cloud configuration or key.")).toBeInTheDocument();
  });

  it("switches Codex and future provider intent without granting execution authority", () => {
    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Codex worker: proposal-only" }));

    expect(
      screen.getByText(
        "Intent: Codex worker proposal route. No apply, commit, push, or provider call has run yet.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Codex worker: proposal-only" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: "Codex proposal: proposal-only · preview blocked" }))
      .toHaveAttribute("aria-pressed", "true");
    expect(screen.queryByRole("button", { name: /apply approved diff/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /commit|push/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Future providers: future" }));

    expect(
      screen.getByText(
        "Intent: future provider route requested, but unavailable until a safe Source Proxy route is configured. No provider call has run yet.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Future providers: future" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: "Future provider: future · preview blocked" }))
      .toHaveAttribute("aria-pressed", "true");
    expect(screen.queryByRole("button", { name: /apply approved diff/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /commit|push/i })).not.toBeInTheDocument();
  });

  it("starts a local new chat and makes it active", () => {
    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Start new chat" }));

    expect(screen.getByRole("heading", { level: 2, name: "New chat 1" })).toBeInTheDocument();
    expect(screen.getByText("Empty chat 1, ready for a prompt")).toBeInTheDocument();
    expect(screen.getByLabelText("Active chat session")).toHaveTextContent(
      /Active session: local-chat-\d+-1/,
    );
    expect(
      screen.getByText(
        /Local session only; new chats are current-session until a task story is staged\./,
      ),
    ).toBeInTheDocument();

    const chatNav = screen.getByRole("navigation", { name: "Coding chats" });
    expect(within(chatNav).getByRole("button", { name: /New chat 1/ })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(within(chatNav).getByRole("button", { name: /New coding chat/ })).not.toHaveAttribute(
      "aria-current",
    );
  });

  it("creates two local chats and swaps the active empty state", () => {
    render(<CodingCommandCenterShell />);

    const startNewChat = screen.getByRole("button", { name: "Start new chat" });
    fireEvent.click(startNewChat);
    fireEvent.click(startNewChat);

    const chatNav = screen.getByRole("navigation", { name: "Coding chats" });
    const chatOne = within(chatNav).getByRole("button", { name: /New chat 1/ });
    const chatTwo = within(chatNav).getByRole("button", { name: /New chat 2/ });

    expect(screen.getByRole("heading", { level: 2, name: "New chat 2" })).toBeInTheDocument();
    expect(screen.getByText("Empty chat 2, ready for a prompt")).toBeInTheDocument();
    expect(chatTwo).toHaveAttribute("aria-current", "page");

    fireEvent.click(chatOne);

    expect(screen.getByRole("heading", { level: 2, name: "New chat 1" })).toBeInTheDocument();
    expect(screen.getByText("Empty chat 1, ready for a prompt")).toBeInTheDocument();
    expect(chatOne).toHaveAttribute("aria-current", "page");
    expect(chatTwo).not.toHaveAttribute("aria-current");
  });

  it("keeps two local chats from merging draft and staged task state", () => {
    render(<CodingCommandCenterShell />);

    const startNewChat = screen.getByRole("button", { name: "Start new chat" });
    fireEvent.click(startNewChat);
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value: "Chat one draft. Target file: docs/chat-one.md. Allowed files: docs/chat-one.md.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));

    expect(screen.getByText("Patch docs/chat-one.md")).toBeInTheDocument();
    expectActiveRunState("queued");

    fireEvent.click(startNewChat);
    expect(screen.getByRole("heading", { level: 2, name: "New chat 2" })).toBeInTheDocument();
    expect(screen.getByLabelText("Coding command composer")).toHaveValue("");
    expect(screen.queryByText("Patch docs/chat-one.md")).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value: "Chat two draft. Target file: docs/chat-two.md. Allowed files: docs/chat-two.md.",
      },
    });

    const chatNav = screen.getByRole("navigation", { name: "Coding chats" });
    fireEvent.click(within(chatNav).getByRole("button", { name: /New chat 1/ }));

    expect(screen.getByRole("heading", { level: 2, name: "New chat 1" })).toBeInTheDocument();
    expect(screen.getByLabelText("Coding command composer")).toHaveValue(
      "Chat one draft. Target file: docs/chat-one.md. Allowed files: docs/chat-one.md.",
    );
    expect(screen.getByText("Patch docs/chat-one.md")).toBeInTheDocument();
    expect(screen.queryByDisplayValue(/Chat two draft/)).not.toBeInTheDocument();

    fireEvent.click(within(chatNav).getByRole("button", { name: /New chat 2/ }));

    expect(screen.getByLabelText("Coding command composer")).toHaveValue(
      "Chat two draft. Target file: docs/chat-two.md. Allowed files: docs/chat-two.md.",
    );
    expect(screen.queryByText("Patch docs/chat-one.md")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));
    expect(screen.getByText("Patch docs/chat-two.md")).toBeInTheDocument();
    expect(screen.queryByText("Evidence Details and Receipts")).not.toBeInTheDocument();
    openRightRailDetails();
    const evidenceDetails = screen.getByText("Evidence Details and Receipts").closest("details");
    expect(evidenceDetails).toHaveAttribute("open");
    expect(evidenceDetails).toHaveTextContent(
      "Target scope: Only this file is targeted: docs/chat-two.md.",
    );
    expect(within(evidenceDetails as HTMLElement).queryByText(/docs\/chat-one\.md/))
      .not.toBeInTheDocument();
  });

  it("restores the local task story after refresh for review", async () => {
    const { unmount } = render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value:
          "Append a persistence note. Target file: docs/example.md. Allowed files: docs/example.md.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));

    expect(
      await screen.findByText(/Task story saved locally for refresh\/reconnect review/),
    ).toBeInTheDocument();

    unmount();
    render(<CodingCommandCenterShell />);

    expect(
      await screen.findByText(/Task story restored locally for refresh\/reconnect review/),
    ).toBeInTheDocument();
    expect(screen.getAllByDisplayValue(/Append a persistence note/).length).toBeGreaterThan(0);
    openRightRailDetails();
    expect(screen.getByText("Task boundary state: Bounded task is staged.")).toBeInTheDocument();
  });

  it("editing task details invalidates preview, approval, apply, and verification state", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(taskCreateResponse())
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/example.md b/docs/example.md",
              "--- a/docs/example.md",
              "+++ b/docs/example.md",
              "@@ -1 +1,2 @@",
              " # Example",
              "+Approved apply smoke.",
              "",
            ].join("\n"),
            target: "docs/example.md",
            task_id: "task-123",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: "preview_ready" }), { status: 200 }),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify({ ok: true }), { status: 200 }));

    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Desktop coding mode" }));
    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value:
          "Append an approved apply smoke line. Target file: docs/example.md. Allowed files: docs/example.md.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));
    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));
    expect(await screen.findByText("Preview ready. No files changed yet.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Approve preview" }));
    fireEvent.click(screen.getByRole("button", { name: "Apply approved diff" }));
    expect(await screen.findByText("Approved diff applied. Verification required."))
      .toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value:
          "Change the docs task. Target file: docs/proxy-test-runner-plan.md. Allowed files: docs/proxy-test-runner-plan.md.",
      },
    });

    expect(screen.getByText("Preview not requested.")).toBeInTheDocument();
    expect(screen.getByText("Approval: Locked until preview evidence exists."))
      .toBeInTheDocument();
    expect(screen.getByText("Apply: Locked until explicit local approval exists."))
      .toBeInTheDocument();
    expect(screen.getByText("Verify: Locked until apply happens.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Apply approved diff" })).not.toBeInTheDocument();
  });
});
