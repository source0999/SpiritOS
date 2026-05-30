import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import CodingCockpitShell from "@/components/coding/CodingCockpitShell";

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

afterEach(() => {
  vi.restoreAllMocks();
  window.localStorage.clear();
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
    expect(within(trialRunner).getByText("Reversible trial runner")).toBeInTheDocument();
    expect(within(trialRunner).getByRole("group", { name: "Trial runner mode" })).toBeInTheDocument();
    expect(within(trialRunner).getByRole("button", { name: "Coder" })).toBeInTheDocument();
    expect(within(trialRunner).getByRole("button", { name: "Designer" })).toBeInTheDocument();
    expect(within(trialRunner).getByRole("button", { name: "Combined" })).toBeInTheDocument();
    expect(within(trialRunner).getByRole("group", { name: "Prompt count selector" })).toBeInTheDocument();
    expect(within(trialRunner).getByRole("button", { name: "25" })).toBeInTheDocument();
    expect(within(trialRunner).getByRole("button", { name: "50" })).toBeInTheDocument();
    expect(within(trialRunner).getByRole("button", { name: "100" })).toBeInTheDocument();
    expect(within(trialRunner).getByRole("button", { name: "Run reversible trial suite" })).toBeInTheDocument();
    expect(within(trialRunner).getByRole("button", { name: "Copy trial diagnostics" })).toBeDisabled();
    expect(screen.getByRole("heading", { name: "Live coding runner" })).toBeInTheDocument();
    expect(screen.getByText("Project")).toBeInTheDocument();
    expect(screen.getByText("Provider/model")).toBeInTheDocument();
    expect(screen.getByText("State")).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: "Task transcript" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Task Composer" })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Describe what you want SpiritOS to change.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start coding" })).toBeInTheDocument();

    const progress = screen.getByRole("region", { name: "Run progress" });
    [
      "Reading request",
      "Finding files",
      "Calling model",
      "Editing files",
      "Running checks",
      "Ready for review",
    ].forEach((step) => {
      expect(within(progress).getByText(step)).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: "Copy diagnostics" })).toBeDisabled();
    expect(screen.getAllByText("Advanced details").length).toBeGreaterThanOrEqual(2);

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
    expect(screen.getByText(/Checks run/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy diagnostics" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Revert this run" })).toBeInTheDocument();

    expect(calls.find((call) => call.url.includes("/v1/decisions/prompt-packet"))?.body)
      .toContain('"trial_mode":"live_apply"');
    expect(calls.some((call) => call.url.includes("/v1/actions/execute-approved"))).toBe(true);

    fireEvent.click(screen.getByRole("button", { name: "Copy diagnostics" }));
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

    fireEvent.click(screen.getByRole("button", { name: "Revert this run" }));
    expect(await screen.findByRole("heading", { name: "REVERTED" })).toBeInTheDocument();
    expect(screen.getAllByText(/Reverted this run/).length).toBeGreaterThan(0);

    const executeCalls = calls.filter((call) => call.url.includes("/v1/actions/execute-approved"));
    expect(executeCalls).toHaveLength(2);
    expect(executeCalls[1]?.body).toContain('"action":"Revert src/components/coding/CodingCockpitShell.tsx"');
    expect(executeCalls[1]?.body).toContain('"allowed_files":["src/components/coding/CodingCockpitShell.tsx"]');
  });
});
