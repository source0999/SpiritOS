import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import CodingCockpitShell, {
  reversibleSuiteExceptionLabel,
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
    if (url.includes("/v1/coding/trial-receipt-reconcile")) {
      return jsonResponse({ ok: true });
    }
    if (url.includes("/v1/tasks/long-running")) {
      return jsonResponse({ task_id: "task_test_123" });
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
  return screen.findByRole("heading", { name: "PASS" });
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
    const trialRunner = screen.getByRole("region", { name: "Reversible trial runner" });
    expect(within(trialRunner).getByText("Trial runner")).toBeInTheDocument();
    expect(within(trialRunner).getByRole("combobox", { name: "Trial category" })).toBeInTheDocument();
    expect(within(trialRunner).getByRole("combobox", { name: "Trial count" })).toBeInTheDocument();
    ["Coder", "Designer", "Combined", "10", "25", "50", "100"].forEach((option) => {
      expect(within(trialRunner).getByRole("option", { name: option })).toBeInTheDocument();
    });
    expect(within(trialRunner).getByRole("button", { name: "Run reversible trial suite" })).toBeInTheDocument();
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
      "1. Make the small badge component support a warning state for partial results while keeping the existing success and failure styles.",
    );
    expect(copied).toContain(
      "2. The fake backend route helper always returns a happy response. Add a failure path so tests can cover non-200 responses.",
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
    const runButton = screen.getByRole("button", { name: "Run reversible trial suite" });
    await waitFor(() => expect(runButton).toBeEnabled());
    fireEvent.click(runButton);

    await waitFor(() => expect(screen.getByText("10/10")).toBeInTheDocument(), { timeout: 10000 });
    expect(screen.getAllByText("7").length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText("0").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Applied and reversed.").length).toBeGreaterThan(0);
    expect(screen.getAllByText("PASS").length).toBeGreaterThan(0);
    expect(screen.getAllByText("NO EDIT EXPECTED").length).toBeGreaterThan(0);
    expect(calls.some((call) => call.body.includes('"selected_target"'))).toBe(true);
    expect(calls.some((call) => call.body.includes('"Target file:'))).toBe(false);
  });

  it("classifies thrown preview route outages as needs-fix infra failures in reversible suites", () => {
    expect(reversibleSuiteExceptionLabel("Preview request returned status 404.")).toBe("NEEDS FIX");
    expect(reversibleSuiteExceptionLabel("Failed to fetch")).toBe("NEEDS FIX");
    expect(reversibleSuiteExceptionLabel("Coder exceeded the Source Proxy sync deadline")).toBe("NEEDS FIX");
    expect(reversibleSuiteExceptionLabel("Expected copy did not appear in target file.")).toBe("FAIL");
  });

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
    expect(screen.getByText("Calling model")).toBeInTheDocument();
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
    expect(screen.getByRole("button", { name: "Copy path to verify" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Reset trial fixture" })).toBeEnabled();
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

    expect(await screen.findByRole("heading", { name: "FAIL" })).toBeInTheDocument();
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
    expect(await screen.findByRole("heading", { name: "REVERTED" })).toBeInTheDocument();
    expect(screen.getAllByText(/Reverted this run/).length).toBeGreaterThan(0);

    const executeCalls = calls.filter((call) => call.url.includes("/v1/actions/execute-approved"));
    expect(executeCalls).toHaveLength(2);
    expect(executeCalls[1]?.body).toContain('"action":"Revert src/components/coding/CodingCockpitShell.tsx"');
    expect(executeCalls[1]?.body).toContain('"allowed_files":["src/components/coding/CodingCockpitShell.tsx"]');
  });

  it("surfaces backend failure instead of a stuck Calling model spinner", () => {
    const shellSrc = readFileSync("src/components/coding/CodingCockpitShell.tsx", "utf8");
    expect(shellSrc).toContain("function previewLoadingPhaseLabel(");
    expect(shellSrc).toContain("Source Proxy unreachable — backend failure");
    expect(shellSrc).toContain("previewLoadingSimpleResult(");
  });
});
