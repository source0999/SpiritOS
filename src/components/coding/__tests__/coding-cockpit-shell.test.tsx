import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import CodingCockpitShell, {
  causalTraceFromPayload,
  changedFilesFromPayload,
  changedFileSnapshotsFromPayload,
  executeReadyReverseDiff,
  plan2SubsystemIntegrationsFromPayload,
  reverseUnifiedDiff,
  snapshotRestored,
  reversibleSuiteExceptionLabel,
  shouldClearStaleLocalTrialStateAfterCloudClear,
} from "@/components/coding/CodingCockpitShell";

const navMock = vi.hoisted(() => ({ path: "/coding" }));

vi.mock("next/navigation", () => ({
  usePathname: () => navMock.path,
}));

const targetFile = "src/components/coding/CodingCockpitShell.tsx";
const liveDiff = [
  `diff --git a/${targetFile} b/${targetFile}`,
  `--- a/${targetFile}`,
  `+++ b/${targetFile}`,
  "@@ -1 +1,2 @@",
  " export const value = true;",
  "+export const liveRunnerProof = true;",
  "",
].join("\n");

function jsonResponse(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), { status });
}

function installCommonFetchMock(extra?: (url: string, init?: RequestInit) => Response | null) {
  const calls: Array<{ body: string; url: string }> = [];
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    const body = typeof init?.body === "string" ? init.body : "";
    calls.push({ body, url });

    const handled = extra?.(url, init);
    if (handled) return handled;

    if (url.includes("/v1/self/status")) {
      return jsonResponse({
        model_routes: [
          {
            alias: "local",
            enabled: true,
            model: "ollama_chat/hermes4:latest",
            provider: "ollama",
            probe_ok: true,
            selected_via: "probe:fallback_default",
          },
        ],
      });
    }
    if (url.includes("/v1/coding/trial-fixture-baseline")) {
      return jsonResponse({
        component_trial: { excerpt: "", has_warning_tone: false, path: "unused" },
        backend_route_trial: { excerpt: "", has_ok_param: false, path: "unused" },
      });
    }
    if (url.includes("/v1/coding/agent-lab-baseline")) {
      return jsonResponse({
        baseline_agent_lab_files: [],
        baseline_checked_at: new Date().toISOString(),
        baseline_clean_for_fresh_suite: true,
        baseline_dirty_agent_lab_files: [],
        baseline_unreverted_receipts: [],
        visible_label: "BASELINE CLEAN",
      });
    }
    if (url.includes("/v1/coding/agent-lab-sweep")) {
      return jsonResponse({
        clean: true,
        failures: [],
        message: "Removed 0 agent-lab leftover file(s). Workspace is clean for a fresh Coder benchmark.",
        removed: 0,
        skipped: 0,
        snapshot: {
          baseline_agent_lab_files: [],
          baseline_checked_at: new Date().toISOString(),
          baseline_clean_for_fresh_suite: true,
          baseline_dirty_agent_lab_files: [],
          baseline_unreverted_receipts: [],
          visible_label: "BASELINE CLEAN",
        },
        targets: [],
      });
    }
    if (url.includes("/v1/coding/trial-receipt-reconcile")) {
      return jsonResponse({ ok: true, receipts: body ? JSON.parse(body).receipts ?? [] : [] });
    }
    if (url.includes("/v1/coding/workspace-read")) {
      return jsonResponse({ excerpt: "export default function Page() { return null; }\n" });
    }
    if (url.includes("/v1/coding/runs/active")) {
      return jsonResponse({ run: null });
    }
    if (url.includes("/v1/coding/runs/recent")) {
      return jsonResponse({ count: 0, runs: [] });
    }
    if (url.endsWith("/v1/coding/runs")) {
      const parsed = body ? JSON.parse(body) : {};
      return jsonResponse({
        run: {
          ...parsed,
          run_id: parsed.run_id ?? parsed.suite_id ?? "suite-test",
          suite_id: parsed.suite_id ?? parsed.run_id ?? "suite-test",
          status: parsed.status ?? "running",
        },
      }, init?.method === "POST" ? 201 : 200);
    }
    if (url.includes("/v1/coding/runs/")) {
      const parsed = body ? JSON.parse(body) : {};
      return jsonResponse({
        run: {
          ...parsed,
          run_id: "suite-test",
          suite_id: "suite-test",
          status: parsed.status ?? "running",
        },
      });
    }
    if (url.includes("/v1/tasks/long-running")) {
      const parsed = body ? JSON.parse(body) as Record<string, unknown> : {};
      if (parsed.diagnostic === true) {
        return jsonResponse({ detail: [{ msg: "Field required" }] }, 422);
      }
      return jsonResponse({ task_id: "task_test_123" });
    }
    if (url.includes("/v1/decisions/prompt-packet")) {
      const parsed = body ? JSON.parse(body) as Record<string, unknown> : {};
      if (parsed.diagnostic === true) {
        return jsonResponse({ detail: [{ msg: "Field required" }] }, 422);
      }
    }
    throw new Error(`Unexpected fetch: ${url}`);
  });
  return calls;
}

async function startLiveRun(prompt = "Make the coding result card easier to understand when a live apply run fails.") {
  fireEvent.change(screen.getByLabelText("Coding prompt"), {
    target: { value: prompt },
  });
  fireEvent.click(screen.getByRole("button", { name: "Start coding" }));
  return screen.findByText("Reverse diff stored");
}

beforeEach(() => {
  window.localStorage.clear();
  window.sessionStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
  window.localStorage.clear();
  window.sessionStorage.clear();
});

describe("CodingCockpitShell", () => {
  it("renders the simplified live runner without bank, preview, size, or manual file controls", () => {
    installCommonFetchMock();
    render(<CodingCockpitShell />);

    expect(screen.getByRole("complementary", { name: "Coding chats" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "New chat" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Coding session list" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Active task" })).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "Review pane" })).toBeInTheDocument();
    const trialRunner = screen.getByRole("region", { name: "Trial Runner" });
    expect(within(trialRunner).getByRole("heading", { name: "Trial Runner" })).toBeInTheDocument();
    expect(within(trialRunner).getByRole("combobox", { name: "Trial category" })).toBeInTheDocument();
    expect(within(trialRunner).getByRole("combobox", { name: "Trial count" })).toBeInTheDocument();
    expect(within(trialRunner).getByRole("combobox", { name: "Trial runner mode" })).toHaveValue("individual");
    ["Coder", "Designer", "Combined", "Messy Coder 10", "Messy Coder 25", "Messy Coder 50", "Messy Coder 100"].forEach((option) => {
      expect(within(trialRunner).getByRole("option", { name: option })).toBeInTheDocument();
    });
    expect(within(trialRunner).getByRole("button", { name: "Run selected prompt" })).toBeInTheDocument();
    expect(within(trialRunner).getByRole("button", { name: "Run all trials" })).toBeInTheDocument();
    expect(within(trialRunner).getByRole("button", { name: "Copy prompts" })).toBeInTheDocument();
    expect(within(trialRunner).getByRole("button", { name: "Copy trial diagnostics" })).toBeDisabled();
    expect(screen.getByRole("heading", { name: "Coding runner" })).toBeInTheDocument();
    expect(screen.getByText("Current task")).toBeInTheDocument();
    expect(screen.getByText("Model")).toBeInTheDocument();
    expect(screen.getByText("State")).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: "Background trial" })).toBeInTheDocument();
    expect(screen.getByText("Phone trial")).toBeInTheDocument();
    expect(screen.getByText("Browser online")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Task transcript" })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Task Composer" })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Describe what you want SpiritOS to change.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start coding" })).toBeInTheDocument();

    const progress = screen.getByRole("region", { name: "Run progress" });
    [
      "Reading request",
      "Finding files",
      "Calling model",
      "Editing files",
      "Checking",
      "Undoing trial edit",
      "Ready to review",
    ].forEach((step) => {
      expect(within(progress).getByText(step)).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: "Copy current task diagnostics" })).toBeDisabled();
    expect(screen.queryByText("Advanced details")).not.toBeInTheDocument();

    [
      "Trial Mode",
      "Live Apply Bank",
      "Preview-only Diagnostic Bank",
      "Active Bank",
      "Size",
      "View",
      "Actual Intelligence Bank",
      "Target file",
      "Allowed files",
      "Expected checks",
      "VOIDCORE SHELL",
      "Evidence packet for workflow replay",
    ].forEach((text) => {
      expect(screen.queryByText(text)).not.toBeInTheDocument();
    });
  });

  it("renders compact individual prompt mode inside Trial Runner", () => {
    installCommonFetchMock();
    render(<CodingCockpitShell />);

    const runner = screen.getByRole("region", { name: "Trial Runner" });
    expect(within(runner).getByRole("combobox", { name: "Dummy Coder prompt" })).toBeInTheDocument();
    expect(within(runner).getByText("Coder 001 - Init Dummy Product Site")).toBeInTheDocument();
    expect(within(runner).getByText("PASS_DUMMY_PROJECT_INIT")).toBeInTheDocument();
    expect(within(runner).getByText("dummy-product-site")).toBeInTheDocument();
    expect(within(runner).getByText("View prompt + boundaries")).toBeInTheDocument();
    expect(within(runner).queryByText(/make a tiny fake product website project/)).not.toBeInTheDocument();

    fireEvent.click(within(runner).getByText("View prompt + boundaries"));
    expect(within(runner).getByText("tests/ui-agent-trials/fixtures/dummy-product-site/")).toBeInTheDocument();
    expect(within(runner).getByText("tests/ui-agent-trials/fixtures/dummy-product-site/**")).toBeInTheDocument();
    expect(within(runner).getByText(/src\/app\/\*\*/)).toBeInTheDocument();

    fireEvent.change(within(runner).getByRole("combobox", { name: "Dummy Coder prompt" }), {
      target: { value: "coder-009-noop-category-proof" },
    });

    expect(within(runner).getByText("Coder 009 - No-Op / Already Satisfied Proof")).toBeInTheDocument();
    expect(within(runner).getByText("PASS_NOOP")).toBeInTheDocument();
    expect(within(runner).getByText("tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js")).toBeInTheDocument();
  });

  it("submits only one selected LumaCart prompt with dummy-root boundaries", async () => {
    const calls = installCommonFetchMock((url, init) => {
      if (url.includes("/v1/decisions/prompt-packet")) {
        const parsed = init?.body ? JSON.parse(String(init.body)) : {};
        return jsonResponse({
          changed_files: [],
          coder_diagnostics: {
            diff_source: "model_authored_diff",
            generation_source: "model",
            model_output_classification: "model_authored_diff",
            trial_result_trust_status: "model_authored",
          },
          provider_call_made: true,
          reason_code: "coder_no_changes_needed",
          recommended_next_action: "Inspect cited category evidence.",
          simple_reason: "category exists at tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js",
          status: "proposal_ready",
          taskEcho: parsed.task,
        });
      }
      return null;
    });
    render(<CodingCockpitShell />);

    const runner = screen.getByRole("region", { name: "Trial Runner" });
    fireEvent.change(within(runner).getByRole("combobox", { name: "Dummy Coder prompt" }), {
      target: { value: "coder-009-noop-category-proof" },
    });
    fireEvent.click(within(runner).getByRole("button", { name: "Run selected prompt" }));

    await waitFor(() => expect(within(runner).getByText("PASS_NOOP / score 10")).toBeInTheDocument());
    const promptPacketCalls = calls.filter((call) => call.url.includes("/v1/decisions/prompt-packet"));
    expect(promptPacketCalls).toHaveLength(1);
    const body = JSON.parse(promptPacketCalls[0].body);
    expect(body.selected_prompt_id).toBe("coder-009-noop-category-proof");
    expect(body.dummy_coder_10_packet.fixture_root).toBe("tests/ui-agent-trials/fixtures/dummy-product-site/");
    expect(body.dummy_coder_10_packet.allowed_write_root).toBe("tests/ui-agent-trials/fixtures/dummy-product-site/**");
    expect(body.dummy_coder_10_packet.forbidden_files).toEqual(
      expect.arrayContaining(["src/app/**", "source_proxy/**", "package.json", ".env*", ".git/**"]),
    );
    expect(JSON.stringify(body)).not.toMatch(/run_full_suite|25|50|100/i);
  });

  it("shows selected-prompt pending state immediately after click", async () => {
    const promptPacketGate: { release: () => void } = { release: () => undefined };
    installCommonFetchMock((url) => {
      if (url.includes("/v1/decisions/prompt-packet")) {
        return null;
      }
      return null;
    });
    vi.mocked(globalThis.fetch).mockImplementation(async (input, init) => {
      const url = String(input);
      const body = typeof init?.body === "string" ? init.body : "";
      if (url.includes("/v1/tasks/long-running")) {
        return jsonResponse({ task_id: "task_pending_001" });
      }
      if (url.includes("/v1/decisions/prompt-packet")) {
        await new Promise<void>((resolve) => {
          promptPacketGate.release = resolve;
        });
        return jsonResponse({ status: "blocked", reason_code: "coder_file_bundle_validation_failed" });
      }
      if (url.includes("/v1/self/status")) {
        return jsonResponse({ model_routes: [] });
      }
      if (url.includes("/v1/coding/agent-lab-baseline")) {
        return jsonResponse({
          baseline_agent_lab_files: [],
          baseline_checked_at: new Date().toISOString(),
          baseline_clean_for_fresh_suite: true,
          baseline_dirty_agent_lab_files: [],
          baseline_unreverted_receipts: [],
          visible_label: "BASELINE CLEAN",
        });
      }
      if (url.includes("/v1/coding/trial-receipt-reconcile")) {
        return jsonResponse({ ok: true, receipts: body ? JSON.parse(body).receipts ?? [] : [] });
      }
      if (url.includes("/v1/coding/runs/active")) return jsonResponse({ run: null });
      if (url.includes("/v1/coding/runs/recent")) return jsonResponse({ count: 0, runs: [] });
      throw new Error(`Unexpected fetch: ${url}`);
    });

    render(<CodingCockpitShell />);
    const runner = screen.getByRole("region", { name: "Trial Runner" });
    fireEvent.click(within(runner).getByRole("button", { name: "Run selected prompt" }));

    await waitFor(() => expect(within(runner).getByText(/Running task task_pending_001/)).toBeInTheDocument());
    expect(within(runner).getByRole("button", { name: "Run selected prompt" })).toBeDisabled();
    promptPacketGate.release();
  });

  it("clears selected-prompt blocked result with the Trial Runner reverse clear action", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    installCommonFetchMock((url) => {
      if (url.includes("/v1/decisions/prompt-packet")) {
        return jsonResponse({
          coder_diagnostics: {
            generation_source: "model",
            model_output_classification: "model_prose_only",
            trial_result_trust_status: "model_output_not_usable",
          },
          reason_code: "coder_file_bundle_validation_failed",
          status: "blocked",
        });
      }
      return null;
    });

    render(<CodingCockpitShell />);
    const runner = screen.getByRole("region", { name: "Trial Runner" });
    fireEvent.click(within(runner).getByRole("button", { name: "Run selected prompt" }));

    await waitFor(() => expect(within(runner).getByText("Needs fix")).toBeInTheDocument());
    fireEvent.click(within(runner).getByRole("button", { name: "Reverse trial edits and clear results" }));

    await waitFor(() => expect(within(runner).getByText("Cleared")).toBeInTheDocument());
    fireEvent.click(within(runner).getByRole("button", { name: "Copy diagnostics" }));
    await waitFor(() => expect(writeText).toHaveBeenCalled());
    expect(String(writeText.mock.calls.at(-1)?.[0] ?? "")).toContain("selected_prompt_result: none");
  });

  it("runs natural prompts as live apply, records proof, enables diagnostics, and offers run-only revert", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    const calls = installCommonFetchMock((url) => {
      if (url.includes("/v1/decisions/prompt-packet")) {
        return jsonResponse({
          coder_diagnostics: {
            litellm_model: "ollama_chat/hermes4:latest",
            model: "ollama_chat/hermes4:latest",
            provider: "ollama",
            router_call_attempted: true,
          },
          model: "ollama_chat/hermes4:latest",
          proposed_diff: liveDiff,
          provider: "ollama",
          provider_call_made: true,
          status: "proposal_ready",
          task_id: "task_test_123",
        });
      }
      if (url.includes("/v1/verification/diff-preview")) {
        return jsonResponse({
          changed_files: [{ path: targetFile }],
          git_apply_check_ok: true,
          requirement_coverage: { ok: true, summary: "Requirement coverage passed." },
          review_report: { passed: true },
          status: "preview_ready",
          task_spec_check: { ok: true },
          task_id: "task_test_123",
        });
      }
      if (url.includes("/v1/actions/execute-approved")) {
        return jsonResponse({
          changed_files: [{ path: targetFile }],
          disk_changed_files: [targetFile],
          message: "Applied approved diff.",
          reverse_diff: liveDiff,
          status: "applied",
        });
      }
      return null;
    });

    render(<CodingCockpitShell />);
    await startLiveRun();

    expect(screen.getAllByText(/Files changed/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(targetFile).length).toBeGreaterThan(0);
    expect(screen.getByText("Checks")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy current task diagnostics" })).toBeEnabled();
    expect(screen.getAllByRole("button", { name: "Undo last change" }).length).toBeGreaterThan(0);

    expect(calls.find((call) => call.url.includes("/v1/decisions/prompt-packet"))?.body)
      .toContain('"trial_mode":"live_apply"');
    expect(calls.some((call) => call.url.includes("/v1/actions/execute-approved"))).toBe(true);

    fireEvent.click(screen.getByRole("button", { name: "Copy current task diagnostics" }));
    await waitFor(() => expect(writeText).toHaveBeenCalled());
    const diagnostics = String(writeText.mock.calls.at(-1)?.[0] ?? "");
    [
      "run_id:",
      "provider_call_made: true",
      "model_called_for_generation: hermes4:latest",
      "generated_diff_present: true",
      `disk_changed_files: ${targetFile}`,
      "reversal_available: true",
      "visible_result_label: LIVE PASS",
    ].forEach((line) => {
      expect(diagnostics).toContain(line);
    });
  });

  it("copies the normal reversible prompt list without hidden grading metadata", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    installCommonFetchMock();

    render(<CodingCockpitShell />);
    fireEvent.click(screen.getByRole("button", { name: "Copy prompts" }));

    await waitFor(() => expect(writeText).toHaveBeenCalled());
    const copied = String(writeText.mock.calls.at(-1)?.[0] ?? "");
    expect(copied).toContain("category: Coder");
    expect(copied).toContain("count_requested: 10");
    expect(copied).toContain(
      "1. make a new isolated test area at `/agent-lab`. if it doesnt exist create the route and page files needed.",
    );
    expect(copied).toContain(
      "2. make a calculator page at `/agent-lab/calculator` and add a link to it from `/agent-lab`.",
    );
    [
      "tag:",
      "expected_outcome",
      "expectedOutcome",
      "quick_find_paths",
      "quick_find",
      "verify_instruction",
      "targetFile",
      "likelyTargets",
      "selected_target",
      "allowed_files",
      "endpoint_statuses",
      "quick_find_hints",
      "Target file:",
    ].forEach((hiddenField) => {
      expect(copied).not.toContain(hiddenField);
    });
    expect(copied).not.toMatch(/\d+\. coder-\d+ - /);
    expect(copied).not.toMatch(/\nprompt:/);
  });

  it("keeps trial prompt-packet timeout above the manual backend deadline and reports browser aborts", () => {
    const source = readFileSync("src/components/coding/CodingCockpitShell.tsx", "utf8");

    expect(source).toContain("const MANUAL_PROMPT_PACKET_TIMEOUT_MS = 180_000;");
    expect(source).toContain("const TRIAL_PROMPT_PACKET_TIMEOUT_BUFFER_MS = 180_000;");
    expect(source).toContain("const TRIAL_PROMPT_PACKET_TIMEOUT_MS = MANUAL_PROMPT_PACKET_TIMEOUT_MS + TRIAL_PROMPT_PACKET_TIMEOUT_BUFFER_MS;");
    expect(source).toContain("timeout_layer: ${timeoutLayer}");
    expect(source).toContain("browser_abort_timeout");
    expect(source).toContain("fetchPromptPacketWithRetry");
    expect(source).toContain("network_fetch_error");
    expect(source).toContain("promptPacketEndpointStatusForError(error)");
  });

  it("keeps already-satisfied, timeout, safety, and edit-applied suite counts separate", () => {
    const source = readFileSync("src/components/coding/CodingCockpitShell.tsx", "utf8");

    expect(source).toContain('visible_result_label: "ALREADY SATISFIED"');
    expect(source).toContain("edit_applied_count:");
    expect(source).toContain("already_satisfied_count:");
    expect(source).toContain("safety_block_count:");
    expect(source).toContain("timeout_count:");
    expect(source).not.toContain("edit_worked_count:");
    expect(source).toContain("NEEDS FIX: Live apply proof missing: ${noDiffClassification.reasonCode}.");
    expect(source).toContain("no_diff_reason_code: noDiffClassification.reasonCode");
    expect(source).toContain("A 200 route without diff preview proof must not count as PASS.");
  });

  it("runs Coder 10 with strict apply and reverse snapshot proof", async () => {
    const calls = installCommonFetchMock((url, init) => {
      const body = typeof init?.body === "string" ? JSON.parse(init.body) as Record<string, unknown> : {};
      const taskSpec = body.task_spec && typeof body.task_spec === "object" ? body.task_spec as Record<string, unknown> : {};
      const selectedTarget =
        typeof body.selected_target === "string"
          ? body.selected_target
          : typeof body.target === "string"
            ? body.target
            : typeof taskSpec.target === "string"
              ? taskSpec.target
              : targetFile;
      if (url.includes("/v1/decisions/prompt-packet")) {
        if (body.expected_outcome && body.expected_outcome !== "edit_reversible") {
          return jsonResponse({
            coder_diagnostics: {
              litellm_model: "ollama_chat/hermes4:latest",
              provider: "ollama",
              provider_call_made: true,
              router_call_attempted: true,
            },
            model: "ollama_chat/hermes4:latest",
            proposed_diff: "",
            provider: "ollama",
            provider_call_made: true,
            reason_code: body.expected_outcome,
            status: "blocked",
          });
        }
        return jsonResponse({
          coder_diagnostics: {
            litellm_model: "ollama_chat/hermes4:latest",
            provider: "ollama",
            provider_call_made: true,
            router_call_attempted: true,
          },
          model: "ollama_chat/hermes4:latest",
          proposed_diff: liveDiff.replaceAll(targetFile, selectedTarget),
          provider: "ollama",
          provider_call_made: true,
          status: "proposal_ready",
        });
      }
      if (url.includes("/v1/verification/diff-preview")) {
        return jsonResponse({
          changed_files: [{ path: selectedTarget }],
          git_apply_check_ok: true,
          status: "preview_ready",
        });
      }
      if (url.includes("/v1/actions/execute-approved")) {
        const isRevert = String(body.action ?? "").startsWith("Revert live trial");
        return jsonResponse({
          execution: {
            changed_file_snapshots: [
              {
                path: selectedTarget,
                sha256_after: isRevert ? `before-${selectedTarget}` : `after-${selectedTarget}`,
                sha256_before: isRevert ? `after-${selectedTarget}` : `before-${selectedTarget}`,
              },
            ],
            changed_files: [{ path: selectedTarget }],
            status: "applied_needs_verification",
          },
          changed_files: [{ path: selectedTarget }],
          disk_changed_files: [selectedTarget],
          status: "applied_needs_verification",
        });
      }
      return null;
    });

    render(<CodingCockpitShell />);
    const runButton = screen.getByRole("button", { name: "Run messy Coder benchmark" });
    await waitFor(() => expect(runButton).toBeEnabled());
    fireEvent.click(runButton);

    await waitFor(() => expect(screen.getAllByText("10/10").length).toBeGreaterThan(0), { timeout: 10000 });
    expect(screen.getAllByText("10").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("PASS").length).toBeGreaterThan(0);
    expect(screen.queryByText("NO EDIT EXPECTED")).not.toBeInTheDocument();
    expect(calls.some((call) => call.body.includes('"selected_target"'))).toBe(true);
    expect(calls.some((call) => call.body.includes('"Target file:'))).toBe(false);
    expect(calls.filter((call) => call.url.includes("/v1/actions/execute-approved")).length).toBeGreaterThan(0);

    expect(window.localStorage.getItem("spiritos:coding:applied-run-receipts:v1")).toContain("trial-suite:");
    fireEvent.click(screen.getAllByRole("button", { name: "Reverse trial edits and clear results" })[0]);

    await waitFor(() => {
      expect(screen.getAllByRole("button", { name: "Copy trial diagnostics" }).every((button) => button.hasAttribute("disabled"))).toBe(true);
      expect(window.localStorage.getItem("spiritos:coding:reversible-suite-state:v1")).toBeNull();
    });
    expect(screen.queryByLabelText("Trial run results")).not.toBeInTheDocument();
    expect(window.localStorage.getItem("spiritos:coding:applied-run-receipts:v1")).not.toContain("trial-suite:");
  }, 15000);

  it("rechecks Source Proxy health at suite start before blocking a stale mobile preflight", async () => {
    let selfStatusCalls = 0;
    const calls = installCommonFetchMock((url, init) => {
      const body = typeof init?.body === "string" ? JSON.parse(init.body) as Record<string, unknown> : {};
      if (url.includes("/v1/self/status")) {
        selfStatusCalls += 1;
        return jsonResponse({
          model_routes: [
            {
              alias: "coder",
              enabled: true,
              model: "ollama_chat/qwen2.5-coder:7b",
              provider: "ollama",
              probe_ok: true,
              selected_via: "probe:coder",
            },
          ],
        });
      }
      if (url.includes("/v1/decisions/prompt-packet")) {
        return jsonResponse({
          coder_diagnostics: {
            litellm_model: "ollama_chat/qwen2.5-coder:7b",
            provider: "ollama",
            provider_call_made: true,
            router_call_attempted: true,
          },
          model: "ollama_chat/qwen2.5-coder:7b",
          proposed_diff: "",
          provider: "ollama",
          provider_call_made: true,
          reason_code: "coder_no_changes_needed",
          status: "proposal_ready",
        });
      }
      if (url.includes("/v1/verification/diff-preview")) {
        return jsonResponse({ changed_files: [], git_apply_check_ok: true, status: "preview_ready" });
      }
      if (url.includes("/v1/actions/execute-approved")) {
        return jsonResponse({ changed_files: [], disk_changed_files: [], status: "applied_needs_verification" });
      }
      if (url.includes("/v1/coding/runs") && init?.method === "POST") {
        const parsed = body;
        return jsonResponse({
          run: {
            ...parsed,
            run_id: parsed.run_id ?? parsed.suite_id ?? "suite-mobile-recheck",
            suite_id: parsed.suite_id ?? parsed.run_id ?? "suite-mobile-recheck",
            status: parsed.status ?? "running",
          },
        }, url.endsWith("/v1/coding/runs") ? 201 : 200);
      }
      return null;
    });

    render(<CodingCockpitShell />);
    const runButton = screen.getByRole("button", { name: "Run messy Coder benchmark" });
    await waitFor(() => expect(runButton).toBeEnabled());
    fireEvent.click(runButton);

    await waitFor(() => expect(selfStatusCalls).toBeGreaterThanOrEqual(1));
    await waitFor(() => expect(calls.some((call) => call.url.includes("/v1/decisions/prompt-packet"))).toBe(true));
    expect(screen.queryByText("Blocked before model proof")).not.toBeInTheDocument();
  });

  it("classifies thrown preview route outages as needs-fix infra failures in reversible suites", () => {
    expect(reversibleSuiteExceptionLabel("Preview request returned status 404.")).toBe("NEEDS FIX");
    expect(reversibleSuiteExceptionLabel("Failed to fetch")).toBe("NEEDS FIX");
    expect(reversibleSuiteExceptionLabel("Coder exceeded the Source Proxy sync deadline")).toBe("NEEDS FIX");
    expect(reversibleSuiteExceptionLabel("Expected copy did not appear in target file.")).toBe("FAIL");
  });

  it("retries transient long-running task fetch failures before marking a coder prompt needs-fix", async () => {
    let longRunningPromptCalls = 0;
    const calls = installCommonFetchMock((url, init) => {
      const body = typeof init?.body === "string" ? JSON.parse(init.body) as Record<string, unknown> : {};
      if (url.includes("/v1/tasks/long-running") && body.diagnostic !== true) {
        longRunningPromptCalls += 1;
        if (longRunningPromptCalls === 1) {
          throw new Error("Failed to fetch");
        }
      }
      if (url.includes("/v1/decisions/prompt-packet")) {
        return jsonResponse({
          coder_diagnostics: {
            litellm_model: "ollama_chat/hermes4:latest",
            provider: "ollama",
            provider_call_made: true,
            router_call_attempted: true,
          },
          model: "ollama_chat/hermes4:latest",
          proposed_diff: liveDiff,
          provider: "ollama",
          provider_call_made: true,
          status: "proposal_ready",
        });
      }
      if (url.includes("/v1/verification/diff-preview")) {
        return jsonResponse({
          changed_files: [{ path: targetFile }],
          git_apply_check_ok: true,
          status: "preview_ready",
        });
      }
      if (url.includes("/v1/actions/execute-approved")) {
        return jsonResponse({
          changed_files: [{ path: targetFile }],
          disk_changed_files: [targetFile],
          status: "applied_needs_verification",
        });
      }
      return null;
    });

    render(<CodingCockpitShell />);
    const runButton = screen.getByRole("button", { name: "Run messy Coder benchmark" });
    await waitFor(() => expect(runButton).toBeEnabled());
    fireEvent.click(runButton);

    await waitFor(() => expect(longRunningPromptCalls).toBeGreaterThanOrEqual(2));
    expect(calls.some((call) => call.url.includes("/v1/decisions/prompt-packet"))).toBe(true);
    expect(calls.some((call) => call.body.includes("/v1/tasks/long-running(retry 1):fetch_error"))).toBe(true);
  });

  it("stops the suite on mid-run Next HTML 404 instead of cascading fake prompt failures", async () => {
    let longRunningPromptCalls = 0;
    const html404 = new Response(
      "<!DOCTYPE html><html><body>404: This page could not be found</body></html>",
      { status: 404, headers: { "content-type": "text/html; charset=utf-8" } },
    );
    const calls = installCommonFetchMock((url, init) => {
      const body = typeof init?.body === "string" ? JSON.parse(init.body) as Record<string, unknown> : {};
      if (url.includes("/v1/tasks/long-running") && body.diagnostic !== true) {
        longRunningPromptCalls += 1;
        if (longRunningPromptCalls >= 4) {
          return html404;
        }
      }
      if (url.includes("/v1/decisions/prompt-packet") && body.expected_outcome && body.expected_outcome !== "edit_reversible") {
        return jsonResponse({
          model: "ollama_chat/hermes4:latest",
          proposed_diff: "",
          provider: "ollama",
          provider_call_made: true,
          reason_code: body.expected_outcome,
          status: "blocked",
        });
      }
      if (url.includes("/v1/decisions/prompt-packet")) {
        return jsonResponse({
          coder_diagnostics: {
            litellm_model: "ollama_chat/hermes4:latest",
            provider: "ollama",
            provider_call_made: true,
            router_call_attempted: true,
          },
          model: "ollama_chat/hermes4:latest",
          proposed_diff: liveDiff,
          provider: "ollama",
          provider_call_made: true,
          status: "proposal_ready",
        });
      }
      if (url.includes("/v1/verification/diff-preview")) {
        return jsonResponse({
          changed_files: [{ path: targetFile }],
          git_apply_check_ok: true,
          status: "preview_ready",
        });
      }
      if (url.includes("/v1/actions/execute-approved")) {
        return jsonResponse({
          changed_files: [{ path: targetFile }],
          disk_changed_files: [targetFile],
          status: "applied_needs_verification",
        });
      }
      return null;
    });

    render(<CodingCockpitShell />);
    const runButton = screen.getByRole("button", { name: "Run messy Coder benchmark" });
    await waitFor(() => expect(runButton).toBeEnabled());
    fireEvent.click(runButton);

    await waitFor(
      () => {
        expect(screen.getAllByText(/SpiritOS API routes disappeared mid-run/i).length).toBeGreaterThan(0);
      },
      { timeout: 15000 },
    );
    expect(longRunningPromptCalls).toBe(4);
    expect(calls.filter((call) => call.url.includes("/v1/decisions/prompt-packet") && !call.body.includes('"diagnostic":true')).length).toBeLessThan(4);
    expect(screen.queryByText("10/10")).not.toBeInTheDocument();
  }, 20000);

  it("starts a live run for badge-component coding prompts instead of treating them as design handoff", async () => {
    const calls = installCommonFetchMock((url) => {
      if (url.includes("/v1/decisions/prompt-packet")) {
        return jsonResponse({
          model: "ollama_chat/qwen2.5-coder:7b",
          proposed_diff: liveDiff,
          provider: "ollama",
          provider_call_made: true,
          status: "proposal_ready",
        });
      }
      return null;
    });

    render(<CodingCockpitShell />);
    fireEvent.change(screen.getByLabelText("Coding prompt"), {
      target: {
        value:
          "Make the small badge component support a warning state for partial results while keeping the existing success and failure styles.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start coding" }));

    await waitFor(
      () => {
        expect(calls.some((call) => call.url.includes("/v1/decisions/prompt-packet"))).toBe(true);
      },
      { timeout: 8000 },
    );
    expect(screen.getAllByText("Calling model").length).toBeGreaterThan(0);
  });

  it("accepts deterministic already-satisfied badge responses without a live model call", async () => {
    installCommonFetchMock((url) => {
      if (url.includes("/v1/decisions/prompt-packet")) {
        return jsonResponse({
          already_satisfied: true,
          model: "qwen2.5-coder:7b",
          proposed_diff: "",
          provider: "ollama",
          provider_call_made: false,
          reason_code: "coder_no_changes_needed",
          status: "already_satisfied",
        });
      }
      return null;
    });

    render(<CodingCockpitShell />);
    fireEvent.change(screen.getByLabelText("Coding prompt"), {
      target: {
        value:
          "Make the small badge component support a warning state for partial results while keeping the existing success and failure styles.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start coding" }));

    await waitFor(() => {
      expect(screen.getAllByText(/ALREADY SATISFIED/i).length).toBeGreaterThan(0);
    });
    expect(screen.queryByText("FAIL: No model call")).not.toBeInTheDocument();
  });

  it("fails without provider generation proof and never applies preview-only output", async () => {
    const calls = installCommonFetchMock((url) => {
      if (url.includes("/v1/decisions/prompt-packet")) {
        return jsonResponse({
          model: "none",
          proposed_diff: liveDiff,
          provider: "none",
          provider_call_made: false,
          status: "proposal_ready",
        });
      }
      return null;
    });

    render(<CodingCockpitShell />);
    fireEvent.change(screen.getByLabelText("Coding prompt"), {
      target: { value: "Preview only: make the coding result card clearer and keep Copy diagnostics." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start coding" }));

    expect((await screen.findAllByText("Failed")).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/No model call/).length).toBeGreaterThan(0);
    expect(calls.some((call) => call.url.includes("/v1/actions/execute-approved"))).toBe(false);
  });

  it("reverts only the applied live run through execute-approved reverse diff", async () => {
    const calls = installCommonFetchMock((url) => {
      if (url.includes("/v1/decisions/prompt-packet")) {
        return jsonResponse({
          coder_diagnostics: {
            litellm_model: "ollama_chat/hermes4:latest",
            provider: "ollama",
            router_call_attempted: true,
          },
          model: "ollama_chat/hermes4:latest",
          proposed_diff: liveDiff,
          provider: "ollama",
          provider_call_made: true,
          status: "proposal_ready",
          task_id: "task_apply_456",
        });
      }
      if (url.includes("/v1/verification/diff-preview")) {
        return jsonResponse({
          changed_files: [{ path: targetFile }],
          git_apply_check_ok: true,
          requirement_coverage: { ok: true, summary: "Requirement coverage passed." },
          review_report: { passed: true },
          status: "preview_ready",
          task_spec_check: { ok: true },
          task_id: "task_apply_456",
        });
      }
      if (url.includes("/v1/actions/execute-approved")) {
        return jsonResponse({
          changed_files: [{ path: targetFile }],
          disk_changed_files: [targetFile],
          message: "Executed approved diff.",
          status: "applied",
        });
      }
      return null;
    });

    render(<CodingCockpitShell />);
    await startLiveRun();

    fireEvent.click(screen.getAllByRole("button", { name: "Undo last change" })[0]);
    expect(await screen.findByText("This run was reverted through execute-approved using the stored reverse diff.")).toBeInTheDocument();
    expect(screen.getAllByText(/Reverted this run/).length).toBeGreaterThan(0);

    const executeCalls = calls.filter((call) => call.url.includes("/v1/actions/execute-approved"));
    expect(executeCalls).toHaveLength(2);
    expect(executeCalls[1]?.body).toContain('"action":"Revert src/components/coding/CodingCockpitShell.tsx"');
    expect(executeCalls[1]?.body).toContain('"allowed_files":["src/components/coding/CodingCockpitShell.tsx"]');
  });

  it("builds reverse diffs and snapshot proof for modified and newly-created files", () => {
    const createDiff = [
      "diff --git a/src/app/agent-lab/revert-smoke/page.tsx b/src/app/agent-lab/revert-smoke/page.tsx",
      "new file mode 100644",
      "index 0000000..1111111",
      "--- /dev/null",
      "+++ b/src/app/agent-lab/revert-smoke/page.tsx",
      "@@ -0,0 +1 @@",
      "+export default function RevertSmoke() { return null; }",
      "",
    ].join("\n");

    expect(reverseUnifiedDiff(createDiff)).toContain("deleted file mode 100644");
    expect(reverseUnifiedDiff(createDiff)).toContain("--- b/src/app/agent-lab/revert-smoke/page.tsx");
    expect(reverseUnifiedDiff(createDiff)).toContain("+++ /dev/null");
    expect(reverseUnifiedDiff(createDiff)).toContain("-export default function RevertSmoke() { return null; }");
    expect(executeReadyReverseDiff(reverseUnifiedDiff(createDiff))).toContain("+++ /dev/null");

    const modifiedReverseDiff = [
      "--- b/src/app/agent-lab/page.tsx",
      "+++ a/src/app/agent-lab/page.tsx",
      "@@ -1,2 +1,2 @@",
      "-export default function AgentLabPage() {}",
      "+export default function AgentLabBaselinePage() {}",
      "",
    ].join("\n");
    expect(executeReadyReverseDiff(modifiedReverseDiff)).toContain("--- a/src/app/agent-lab/page.tsx");
    expect(executeReadyReverseDiff(modifiedReverseDiff)).toContain("+++ b/src/app/agent-lab/page.tsx");

    const modifiedApply = changedFileSnapshotsFromPayload({
      changed_file_snapshots: [
        {
          path: "src/app/agent-lab/page.tsx",
          sha256_after: "after-modified",
          sha256_before: "before-modified",
        },
      ],
    });
    const modifiedRevert = changedFileSnapshotsFromPayload({
      changed_file_snapshots: [
        {
          path: "src/app/agent-lab/page.tsx",
          sha256_after: "before-modified",
          sha256_before: "after-modified",
        },
      ],
    });
    expect(snapshotRestored(modifiedApply, modifiedRevert, "src/app/agent-lab/page.tsx")).toBe(true);

    const createdApply = changedFileSnapshotsFromPayload({
      changed_file_snapshots: [
        {
          missing_before_apply: true,
          path: "src/app/agent-lab/revert-smoke/page.tsx",
          sha256_after: "created-hash",
          sha256_before: null,
        },
      ],
    });
    const createdRevert = changedFileSnapshotsFromPayload({
      changed_file_snapshots: [
        {
          path: "src/app/agent-lab/revert-smoke/page.tsx",
          sha256_after: null,
          sha256_before: "created-hash",
        },
      ],
    });
    expect(snapshotRestored(createdApply, createdRevert, "src/app/agent-lab/revert-smoke/page.tsx")).toBe(true);
  });

  it("reads long-running execute-approved proof nested under the task audit snapshot", () => {
    const payload = {
      task: {
        ast_snapshot: {
          approved_execution_evidence: {
            audit: {
              changed_files: ["src/app/agent-lab/page.tsx"],
              changed_file_snapshots: [
                {
                  missing_before_apply: true,
                  path: "src/app/agent-lab/page.tsx",
                  sha256_after: "after",
                  sha256_before: null,
                },
              ],
            },
          },
        },
      },
      tool: "long_running_task_tracker",
    };

    expect(changedFilesFromPayload(payload)).toEqual(["src/app/agent-lab/page.tsx"]);
    expect(changedFileSnapshotsFromPayload(payload)).toEqual([
      {
        missingBeforeApply: true,
        path: "src/app/agent-lab/page.tsx",
        sha256After: "after",
        sha256Before: null,
      },
    ]);
  });

  it("reads long-running causal trace proof from execute-approved payloads", () => {
    const payload = {
      execution: {
        trace_id: "trace_123",
        invocation_event_id: "invocation_123",
        causal_trace: {
          consumer_event_id: "consumer_123",
          consumer_subsystem: "long_running_status_observer",
          status_after: "applied_needs_verification",
        },
      },
      task: {
        causal_trace: {
          trace_id: "trace_123",
        },
      },
    };

    expect(causalTraceFromPayload(payload)).toEqual({
      causalStatusAfter: "applied_needs_verification",
      consumerEventId: "consumer_123",
      consumerSubsystem: "long_running_status_observer",
      invocationEventId: "invocation_123",
      traceId: "trace_123",
    });
  });

  it("reads Plan 2 subsystem integration truth without a GO label", () => {
    const payload = {
      task: {
        ast_snapshot: {
          plan_2_subsystem_integrations: {
            cartographer_mac_assignment_consumer: {
              consumed_by: "cartographer_mac_assignment_consumer",
              consumer_event_id: "consumer_mac_123",
              invocation_event_id: "invocation_mac_123",
              output_hash: "sha256:mac",
              status: "INTEGRATED_LIVE",
              trace_id: "trace_mac_123",
            },
            specialist_synthesis_consumer: {
              status: "NOT_INTEGRATED_UNCONSUMED_OUTPUT",
            },
          },
        },
      },
    };

    expect(plan2SubsystemIntegrationsFromPayload(payload)).toEqual([
      {
        consumedBy: "cartographer_mac_assignment_consumer",
        consumerEventId: "consumer_mac_123",
        invocationEventId: "invocation_mac_123",
        outputHash: "sha256:mac",
        status: "INTEGRATED_LIVE",
        subsystem: "cartographer_mac_assignment_consumer",
        traceId: "trace_mac_123",
      },
      {
        consumedBy: null,
        consumerEventId: null,
        invocationEventId: null,
        outputHash: null,
        status: "NOT_INTEGRATED_UNCONSUMED_OUTPUT",
        subsystem: "specialist_synthesis_consumer",
        traceId: null,
      },
    ]);

    const shellSrc = readFileSync("src/components/coding/CodingCockpitShell.tsx", "utf8");
    expect(shellSrc).toContain("Plan 2 subsystem truth");
    expect(shellSrc).toContain("plan2SubsystemIntegrationsFromPayload");
    expect(shellSrc).not.toContain("Plan 2 GO");
    expect(shellSrc).not.toContain("Plan 2 PASS");
  });

  it("rehydrates a durable active Coder run on a second mount", async () => {
    const durableRun = {
      run_id: "suite-cross-device-1",
      suite_id: "suite-cross-device-1",
      created_at: "2026-06-06T12:00:00.000Z",
      updated_at: "2026-06-06T12:01:00.000Z",
      started_by_surface: "coding",
      lane: "coder",
      benchmark_name: "Messy Coder 10",
      requested_count: 10,
      completed_count: 1,
      status: "running",
      current_prompt_id: "coder-001",
      rows: [
        {
          prompt_id: "coder-001",
          run_id: "task-row-1",
          prompt_text: "make a new isolated test area at `/agent-lab`.",
          prompt_excerpt: "make a new isolated test area at `/agent-lab`.",
          status: "completed",
          started_at: "2026-06-06T12:00:00.000Z",
          updated_at: "2026-06-06T12:01:00.000Z",
          provider_call_made: true,
          model_called_for_generation: "ollama_chat/qwen2.5-coder:7b",
          reason_code: "",
          generated_diff_present: true,
          preview_changed_files: ["src/app/agent-lab/page.tsx"],
          applied_changed_files: ["src/app/agent-lab/page.tsx"],
          disk_changed_files: ["src/app/agent-lab/page.tsx"],
          checks_run: ["git diff --check"],
          checks_result: "git diff --check recorded",
          reversal_available: true,
          reversal_status: "available",
          result_label: "PASS",
          error_summary: "",
        },
      ],
      provider: "ollama",
      model: "ollama_chat/qwen2.5-coder:7b",
      provider_call_made: true,
      model_called_for_generation: "ollama_chat/qwen2.5-coder:7b",
      endpoint_statuses: ["/v1/decisions/prompt-packet:200"],
      generated_diff_present: true,
      preview_changed_files: ["src/app/agent-lab/page.tsx"],
      applied_changed_files: ["src/app/agent-lab/page.tsx"],
      disk_changed_files: ["src/app/agent-lab/page.tsx"],
      checks_run: ["git diff --check"],
      checks_result: "git diff --check recorded",
      reversal_available: true,
      reversal_status: "available",
      final_summary: "Ready to review",
      last_error: null,
      reason_code: null,
      frontend_url: "https://10.0.0.186:3000/coding",
      proxy_url: "https://10.0.0.186:8787",
    };
    installCommonFetchMock((url) => {
      if (url.includes("/v1/coding/runs/active") || url.includes("/v1/coding/runs/suite-cross-device-1")) {
        return jsonResponse({ run: durableRun });
      }
      return null;
    });

    const first = render(<CodingCockpitShell />);
    await screen.findByText("Active run attached");
    expect(screen.getByText("Run ID: suite-cross-device-1")).toBeInTheDocument();
    expect(screen.getAllByText("PASS").length).toBeGreaterThan(0);
    first.unmount();
    cleanup();

    render(<CodingCockpitShell />);
    await screen.findByText("Active run attached");
    expect(screen.getByText("Run ID: suite-cross-device-1")).toBeInTheDocument();
    expect(screen.getAllByText("PASS").length).toBeGreaterThan(0);
  });

  it("polls for newly-started backend runs while the page is idle", () => {
    const shellSrc = readFileSync("src/components/coding/CodingCockpitShell.tsx", "utf8");
    expect(shellSrc).toContain("async function pollActiveBackendRun()");
    expect(shellSrc).toContain('fetch("/v1/coding/runs/active", { cache: "no-store" })');
    expect(shellSrc).toContain("if (backendRunSync.runId) return;");
    expect(shellSrc).toContain("Other devices attach automatically while /coding stays open.");
  });

  it("does not rehydrate stale local results after another device clears the synced run", async () => {
    const storageKey = "spiritos:coding:reversible-suite-state:v1";
    window.localStorage.setItem(
      storageKey,
      JSON.stringify({
        completed: 1,
        count: 10,
        currentPrompt: "1/10: make a new isolated test",
        currentStep: "Needs fix",
        fail: 1,
        results: [],
        status: "failed",
        suiteId: "suite-cleared-cloud",
      }),
    );
    const clearedRun = {
      run_id: "suite-cleared-cloud",
      suite_id: "suite-cleared-cloud",
      created_at: "2026-06-06T12:00:00.000Z",
      updated_at: "2026-06-06T12:05:00.000Z",
      started_by_surface: "coding",
      lane: "coder",
      benchmark_name: "Messy Coder 10",
      requested_count: 10,
      completed_count: 1,
      status: "cleared",
      current_prompt_id: "coder-001",
      rows: [],
      provider: "ollama",
      model: "ollama_chat/qwen2.5-coder:7b",
      provider_call_made: false,
      model_called_for_generation: "ollama_chat/qwen2.5-coder:7b",
      endpoint_statuses: [],
      generated_diff_present: false,
      preview_changed_files: [],
      applied_changed_files: [],
      disk_changed_files: [],
      checks_run: [],
      checks_result: "",
      reversal_available: false,
      reversal_status: "none",
      final_summary: "Run cleared from synced coding cloud.",
      last_error: null,
      reason_code: "user_cleared_synced_run",
      frontend_url: "https://10.0.0.186:3000/coding",
      proxy_url: "https://10.0.0.186:8787",
    };
    installCommonFetchMock((url) => {
      if (url.includes("/v1/coding/runs/active")) return jsonResponse({ run: null });
      if (url.includes("/v1/coding/runs/recent")) return jsonResponse({ count: 1, runs: [clearedRun] });
      return null;
    });

    render(<CodingCockpitShell />);

    await screen.findByText("Run cleared from coding cloud");
    expect(screen.getByText("Run ID: none")).toBeInTheDocument();
    expect(window.localStorage.getItem(storageKey)).toBeNull();
    expect(screen.queryByText("1/10: make a new isolated test")).not.toBeInTheDocument();
  });

  it("classifies clean cloud plus active null as stale local trial state instead of cleanup blocker", () => {
    const baseState = {
      completed: 0,
      count: 10,
      currentPrompt: "",
      currentPromptElapsedMs: null,
      currentStep: "Idle",
      currentStepStartedAt: null,
      alreadySatisfied: 0,
      expectedNoEdit: 0,
      fail: 0,
      interruptionReason: null,
      interruptionSource: "none",
      pass: 0,
      provider: "Local / Ollama",
      model: "qwen2.5-coder:7b",
      results: [],
      reverted: 0,
      safetyBlock: 0,
      status: "idle",
      stopped: false,
      suiteFinishedAt: null,
      suiteId: "",
      suiteStartedAt: null,
      timeout: 0,
      baselineCheckedAt: null,
      baselineAgentLabFiles: [],
      baselineDirtyAgentLabFiles: [],
      baselineUnrevertedReceipts: [],
      baselineCleanForFreshSuite: true,
    } as Parameters<typeof shouldClearStaleLocalTrialStateAfterCloudClear>[0]["reversibleSuiteState"];
    const receipt = {
      allowedFiles: ["src/app/agent-lab/page.tsx"],
      appliedAt: "2026-06-07T18:00:00.000Z",
      changedFiles: ["src/app/agent-lab/page.tsx"],
      diff: "diff --git a/src/app/agent-lab/page.tsx b/src/app/agent-lab/page.tsx\n",
      id: "trial-suite:coder-001:task-one",
      model: "qwen2.5-coder:7b",
      prompt: "make a new isolated test area",
      provider: "Local / Ollama",
      providerModelSource: "runtime",
      providerModelStatus: "available",
      hermesUsedForThisRun: false,
      revertedAt: null,
      reversalModel: null,
      reversalProvider: null,
      reversalProviderModelSource: null,
      reverseDiff: "diff --git a/src/app/agent-lab/page.tsx b/src/app/agent-lab/page.tsx\n",
      target: "src/app/agent-lab/page.tsx",
      taskId: "task-one",
    };

    expect(
      shouldClearStaleLocalTrialStateAfterCloudClear({
        agentLabBaselineClean: true,
        agentLabBaselineLoadState: "ready",
        appliedRunReceipts: [receipt],
        backendRunSync: { runId: "", status: "synced" },
        localRunnerActive: false,
        reversibleSuiteState: {
          ...baseState,
          results: [{ prompt: { id: "coder-001" } }],
          status: "failed",
          suiteId: "suite-cleared-on-other-device",
        } as typeof baseState,
      }),
    ).toBe(true);
    expect(
      shouldClearStaleLocalTrialStateAfterCloudClear({
        agentLabBaselineClean: false,
        agentLabBaselineLoadState: "ready",
        appliedRunReceipts: [receipt],
        backendRunSync: { runId: "", status: "synced" },
        localRunnerActive: false,
        reversibleSuiteState: baseState,
      }),
    ).toBe(false);
    expect(
      shouldClearStaleLocalTrialStateAfterCloudClear({
        agentLabBaselineClean: true,
        agentLabBaselineLoadState: "ready",
        appliedRunReceipts: [receipt],
        backendRunSync: { runId: "", status: "synced" },
        localRunnerActive: true,
        reversibleSuiteState: {
          ...baseState,
          status: "running",
          suiteId: "suite-active-local-runner",
        },
      }),
    ).toBe(false);
  });

  it("surfaces backend failure instead of a stuck Calling model spinner", () => {
    const shellSrc = readFileSync("src/components/coding/CodingCockpitShell.tsx", "utf8");
    expect(shellSrc).toContain("function previewLoadingPhaseLabel(");
    expect(shellSrc).toContain("Source Proxy unreachable — backend failure");
    expect(shellSrc).toContain("previewLoadingSimpleResult(");
    expect(shellSrc).toContain('"/v1/decisions/prompt-packet:started"');
    expect(shellSrc).toContain("const promptPacketStartedStatuses =");
    expect(shellSrc).toContain('promptPacket: "Running prompt-packet"');
    expect(shellSrc).not.toContain("stayed on Calling model after prompt-packet start");
  });

  it("records prompt-packet:200 before already-satisfied retry and skips stale while local runner is active", () => {
    const shellSrc = readFileSync("src/components/coding/CodingCockpitShell.tsx", "utf8");
    const promptPacketStatusPush = shellSrc.indexOf('`/v1/decisions/prompt-packet:${proposalResponse.status}`');
    const immediateProgress = shellSrc.indexOf(
      'final_summary: providerCallMade ? "prompt-packet returned; calling model" : "prompt-packet returned; awaiting provider proof"',
    );
    const productRetry = shellSrc.indexOf("trial_recover_already_satisfied: true");
    expect(promptPacketStatusPush).toBeGreaterThan(-1);
    expect(immediateProgress).toBeGreaterThan(promptPacketStatusPush);
    expect(productRetry).toBeGreaterThan(immediateProgress);
    expect(shellSrc).toContain("Recovering prompt-packet route (already-satisfied retry)");
    expect(shellSrc).toContain("if (!localReversibleSuiteRunningRef.current) {");
    expect(shellSrc).toContain("failDurableRunIfPromptPacketStale(run);");
    expect(shellSrc).toContain("function reversibleSuiteRunnerLeaseKnown(");
    expect(shellSrc).toContain("if (!reversibleSuiteRunnerLeaseKnown(staleRun.run_id))");
    expect(shellSrc).toContain("stayed on prompt-packet:started without a recorded prompt-packet completion");
  });

  it("maps stale prompt-packet without provider proof to a resumable browser interruption", () => {
    const shellSrc = readFileSync("src/components/coding/CodingCockpitShell.tsx", "utf8");
    expect(shellSrc).toContain("function durableRunIsStaleStepInterruption(");
    expect(shellSrc).toContain('row.status === "completed"');
    expect(shellSrc).toContain('? "browser_refresh_or_dev_reload"');
    expect(shellSrc).toContain("function reversibleSuiteRunnerLeaseActive(");
    expect(shellSrc).toContain("function durableRunHasLocalRefreshInterruptedInFlightStep(");
    expect(shellSrc).toContain("localRefreshInterruptedInFlightStep");
    expect(shellSrc).toContain("Browser refreshed while the prompt was in flight; resume from the interrupted prompt.");
    expect(shellSrc).not.toContain("if (leaseActive && !staleExecuteApproved && !staleEditingFiles && !stalePostApplyVerification) return run ?? null;");
    expect(shellSrc).toContain("durableRunHasStalePostApplyVerification");
    expect(shellSrc).toContain("markDurableCodingRunPostApplyStale");
    expect(shellSrc).toContain("trialRunnerRunBlocked");
    expect(shellSrc).toContain("backgroundCleanupActive");
    expect(shellSrc).toContain("classifyEditReversibleAlreadySatisfied");
    expect(shellSrc).toContain("buildTrialPromptQuickLinks");
    expect(shellSrc).toContain("BASELINE DIRTY");
    expect(shellSrc).toContain("function durableRunHasStaleExecuteApproved(");
    expect(shellSrc).toContain("function durableRunHasStaleEditingFiles(");
    expect(shellSrc).toContain("function shouldAttachDurableRunToUi(");
    expect(shellSrc).toContain('run.status === "running" || run.status === "pending" || run.status === "completed"');
    expect(shellSrc).not.toContain('run.status === "running" || run.status === "pending" || run.status === "failed"');
    expect(shellSrc).toContain("await clearReversibleSuitePanel();");
    expect(shellSrc).toContain("UI cleared; reversing trial edits in background");
    expect(shellSrc).toContain("function durableRunPendingPromptId(");
    expect(shellSrc).toContain("function durableRunInFlightActiveRow(");
    expect(shellSrc).toContain("function releaseSyncedReversibleSuiteRun(");
    expect(shellSrc).toContain("bodyTimeoutMs: TRIAL_POST_MODEL_STAGE_TIMEOUT_MS");
    expect(shellSrc).toContain("TRIAL_PROMPT_PACKET_MAX_ATTEMPTS");
    expect(shellSrc).toContain("prompt_packet_total_budget_exceeded");
    expect(shellSrc).toContain("signal: promptPacketSignal");
    expect(shellSrc).toContain("function reversibleSuiteStateCanResume(");
    expect(shellSrc).toContain("function durableRunIsResumableUserStop(");
    expect(shellSrc).toContain("function durableRunBetweenPromptsStale(");
    expect(shellSrc).toContain("markDurableCodingRunBetweenPromptsStale");
    expect(shellSrc).toContain("between_prompts_runner_lost");
    expect(shellSrc).toContain("if (reversibleSuiteRunnerLeaseActive(run.run_id, nowMs)) {\n    return false;\n  }");
    expect(shellSrc).toContain("const autoResumeSuiteIdRef = useRef");
    expect(shellSrc).toContain("Auto-resuming suite");
    expect(shellSrc).toContain("void handleRunReversibleSuite(reversibleSuiteState, { forceResume: true });");
    expect(shellSrc).toContain("if (!reversibleSuiteStateCanResume(reversibleSuiteState)) return;");
    expect(shellSrc).toContain("if (!reversibleSuiteRunnerLeaseKnown(reversibleSuiteState.suiteId)) return;");
    expect(shellSrc).not.toContain("reversibleSuiteState.completed <= 0");
    expect(shellSrc).toContain("postDurableCodingRunRowWithTimeout");
    expect(shellSrc).toContain("classifyCurrentSuiteAgentLabFiles");
    expect(shellSrc).toContain("agentLabHasStaleLeftoversOutsideCurrentSuite");
    expect(shellSrc).toContain("reversibleSuiteResumeBlocked");
    expect(shellSrc).not.toContain("agentLabHasLeftovers\n                  }");
  });

  it("keeps Coder suite auto-continue and reason-codes durable row sync failures", () => {
    const shellSrc = readFileSync("src/components/coding/CodingCockpitShell.tsx", "utf8");
    const readyForReview = shellSrc.indexOf('"Ready for review"');
    const suiteContinue = shellSrc.indexOf('currentStep: bucketedSuccess ? "Continuing to next prompt..." : "Needs fix"');
    const syncFailure = shellSrc.indexOf("durable_row_sync_failed");
    expect(readyForReview).toBeGreaterThan(-1);
    expect(suiteContinue).toBeGreaterThan(readyForReview);
    expect(syncFailure).toBeGreaterThan(suiteContinue);
    expect(shellSrc).toContain("durableRowSyncFailed || nextState.fail > 0 || suiteAbort");
    expect(shellSrc).toContain("Stopped after prompt result: durable row sync timed out or failed.");
  });

  it("clears local suite state before bounded backend clear sync", () => {
    const shellSrc = readFileSync("src/components/coding/CodingCockpitShell.tsx", "utf8");
    const clearVersion = shellSrc.indexOf("reversibleSuiteClearVersionRef.current += 1");
    const backendClear = shellSrc.indexOf("const clearedRun = await markDurableCodingRunCleared(runId)");
    expect(clearVersion).toBeGreaterThan(-1);
    expect(backendClear).toBeGreaterThan(clearVersion);
    expect(shellSrc).toContain("fetchWithTimeout(\n      `/v1/coding/runs/${encodeURIComponent(runId)}`");
    expect(shellSrc).toContain("Backend clear timed out or failed");
  });

  it("drains agent-lab cleanup after reverse so one button click reaches clean baseline", () => {
    const shellSrc = readFileSync("src/components/coding/CodingCockpitShell.tsx", "utf8");
    expect(shellSrc).toContain("TRIAL_CLEANUP_DRAIN_MAX_PASSES = 3");
    expect(shellSrc).toContain("async function drainAgentLabCleanupToClean");
    expect(shellSrc).toContain("forceAgentLabSweep?: boolean");
    expect(shellSrc).toContain("const shouldSweepAgentLab = options.forceAgentLabSweep || reversibleTrialCategory === \"Coder\";");
    expect(shellSrc).toContain("waitForV1RoutesAfterHmr({\n        delayMs: 500");
    expect(shellSrc).toContain("Reverse completed; cleanup pass ${pass}/${TRIAL_CLEANUP_DRAIN_MAX_PASSES}");
    expect(shellSrc).toContain("await drainAgentLabCleanupToClean(note ?? \"\", { forceAgentLabSweep: true });");
    expect(shellSrc).toContain("await drainAgentLabCleanupToClean(note, { forceAgentLabSweep: true });");
    expect(shellSrc).toContain("Agent-lab cleanup finished. Workspace is clean for a fresh Coder benchmark.");
  });

  it("disables run while background cleanup/reverse is active", async () => {
    installCommonFetchMock();
    render(<CodingCockpitShell />);
    const runButton = screen.getByRole("button", { name: "Run messy Coder benchmark" });
    await waitFor(() => expect(runButton).toBeEnabled());
  });

  it("renders agent-lab quick links for page targets in result rows", () => {
    const shellSrc = readFileSync("src/components/coding/CodingCockpitShell.tsx", "utf8");
    const helperSrc = readFileSync("src/lib/coding/reversible-trial-runner.ts", "utf8");
    expect(shellSrc).toContain("buildTrialPromptQuickLinks");
    expect(helperSrc).toContain("Parent /agent-lab");
    expect(shellSrc).toContain("Copy target path");
    expect(shellSrc).toContain("Reverse agent-lab leftovers");
    expect(shellSrc).toContain("showTrialCleanupPanel");
    expect(shellSrc).toContain("agentLabHasLeftovers");
    expect(shellSrc).toContain("Reverse this prompt");
  });
});
