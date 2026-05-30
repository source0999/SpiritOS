import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import CodingCockpitShell from "@/components/coding/CodingCockpitShell";

const navMock = vi.hoisted(() => ({ path: "/coding" }));

vi.mock("next/navigation", () => ({
  usePathname: () => navMock.path,
}));

afterEach(() => {
  vi.restoreAllMocks();
  window.localStorage.clear();
});

function diffForFile(path: string): string {
  return [
    `diff --git a/${path} b/${path}`,
    `--- a/${path}`,
    `+++ b/${path}`,
    "@@ -1 +1,2 @@",
    " export const value = true;",
    "+export const verificationTargetSmoke = true;",
    "",
  ].join("\n");
}

const componentTrialPath = "tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx";
const backendRouteTrialPath = "tests/ui-agent-trials/fixtures/dummy-coding-targets/backend-route-trial.ts";

function trialBaselineFetchResponse(options?: {
  backendHasOkParam?: boolean;
  componentHasWarning?: boolean;
}) {
  const componentHasWarning = options?.componentHasWarning ?? false;
  const backendHasOkParam = options?.backendHasOkParam ?? true;
  const componentExcerpt = componentHasWarning
    ? 'tone: "neutral" | "success" | "warning";'
    : 'tone: "neutral" | "success";';
  const backendExcerpt = backendHasOkParam
    ? "export function buildTrialRouteResponse(message: string, ok = true): TrialRouteResponse {"
    : "export function buildTrialRouteResponse(message: string): TrialRouteResponse {";
  return new Response(
    JSON.stringify({
      backend_route_trial: {
        excerpt: backendExcerpt,
        has_ok_param: backendHasOkParam,
        path: backendRouteTrialPath,
      },
      component_trial: {
        excerpt: componentExcerpt,
        has_warning_tone: componentHasWarning,
        path: componentTrialPath,
      },
      excerpt: componentExcerpt,
      has_warning_tone: componentHasWarning,
      path: componentTrialPath,
    }),
    { status: 200 },
  );
}

function mockPreviewRun(changedFile: string, baselineOptions?: Parameters<typeof trialBaselineFetchResponse>[0]) {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    if (url.includes("/v1/coding/trial-fixture-baseline")) {
      return trialBaselineFetchResponse(baselineOptions);
    }
    if (url.includes("/v1/decisions/prompt-packet")) {
      return new Response(
        JSON.stringify({
          proposed_diff: diffForFile(changedFile),
          status: "proposal_ready",
        }),
        { status: 200 },
      );
    }
    if (url.includes("/v1/verification/diff-preview")) {
      return new Response(
        JSON.stringify({
          changed_files: [{ path: changedFile }],
          git_apply_check_ok: true,
          requirement_coverage: { ok: true, summary: "Requirement coverage passed." },
          review_report: { passed: true },
          status: "preview_ready",
          task_spec_check: { ok: true },
        }),
        { status: 200 },
      );
    }
    if (url.includes("/v1/self/status")) {
      return new Response(
        JSON.stringify({
          model_routes: [
            {
              alias: "local",
              enabled: true,
              model: "ollama_chat/hermes4",
              provider: "ollama",
              probe_ok: true,
              selected_via: "probe:fallback_default",
            },
          ],
        }),
        { status: 200 },
      );
    }
    if (url.includes("/v1/coding/trial-receipt-reconcile")) {
      return new Response(JSON.stringify({ ok: true }), { status: 200 });
    }
    throw new Error(`Unexpected fetch in mockPreviewRun: ${url}`);
  });
}

async function startPreviewForFile(changedFile: string) {
  mockPreviewRun(changedFile);
  render(<CodingCockpitShell />);

  fireEvent.change(screen.getByLabelText("Task"), {
    target: { value: `Patch a focused verification target smoke change in ${changedFile}.` },
  });
  fireEvent.change(screen.getByLabelText("Target file"), {
    target: { value: changedFile },
  });
  fireEvent.change(screen.getByLabelText("Allowed files"), {
    target: { value: changedFile },
  });
  fireEvent.click(screen.getByRole("button", { name: "Start task" }));

  expect(await screen.findByText(/Preview ready. No files changed yet/)).toBeInTheDocument();
}

describe("CodingCockpitShell", () => {
  it("renders a clean cockpit shell without diagnostic console clutter", async () => {
    render(<CodingCockpitShell />);

    expect(screen.getByRole("heading", { level: 1, name: "Coding" })).toBeInTheDocument();
    const desktopNav = screen.getByRole("navigation", {
      name: "Spirit app desktop navigation",
    });
    expect(screen.getByRole("navigation", { name: "Spirit app mobile navigation" })).toBeInTheDocument();
    expect(within(desktopNav).getByRole("link", { name: "Source" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(within(desktopNav).getByRole("link", { name: "Dashboard" })).toHaveAttribute("href", "/");
    expect(screen.queryByText("Source Proxy cockpit")).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /advanced diagnostics/i })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Diagnostics" })).toHaveAttribute(
      "href",
      "/proxy-backend",
    );
    expect(screen.getByRole("complementary", { name: "Project task rail" })).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "Review pane" })).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "Project task rail" })).toHaveTextContent(
      "Ready",
    );
    expect(screen.getByRole("navigation", { name: "Task queues" })).not.toHaveTextContent(
      "Needs input",
    );
    expect(screen.getByRole("navigation", { name: "Task queues" })).not.toHaveTextContent("Failed");
    expect(screen.getByRole("navigation", { name: "Task queues" })).not.toHaveTextContent(
      "Recent tasks",
    );
    expect(screen.getByRole("navigation", { name: "Task queues" })).not.toHaveTextContent("Empty");
    const runner = screen.getByRole("region", { name: "Agent trials runner" });
    expect(within(runner).getByText("Runner")).toBeInTheDocument();
    expect(within(runner).getByRole("button", { name: "Coder" })).toHaveAttribute("aria-pressed", "true");
    expect(within(runner).getByRole("button", { name: "Designer" })).toBeInTheDocument();
    expect(within(runner).getByRole("button", { name: "Combined" })).toBeInTheDocument();
    expect(within(runner).getByLabelText("Size")).toHaveValue("10");
    expect(within(runner).getByLabelText("View")).toHaveValue("desktop");
    expect(within(runner).getByRole("button", { name: "Run trial" })).toBeInTheDocument();
    expect(within(runner).getByRole("button", { name: "Revert all trial runs" })).toBeDisabled();
    expect(within(runner).getByText("Status")).toBeInTheDocument();
    expect(within(runner).getByText("Score")).toBeInTheDocument();
    expect(within(runner).getByText("Result")).toBeInTheDocument();
    expect(within(runner).getByText("Category")).toBeInTheDocument();
    expect(within(runner).getByText("Run a trial to see the latest result.")).toBeInTheDocument();
    expect(within(runner).queryByText(/final-grade-report|latest evidence|artifact|grep|backend proof/i))
      .not.toBeInTheDocument();
    expect(within(runner).queryByRole("button", { name: "Copy report" })).not.toBeInTheDocument();
    fireEvent.click(within(runner).getByRole("button", { name: "Run trial" }));
    expect(await within(runner).findByRole("button", { name: "Copy report" })).toBeInTheDocument();
    expect(within(runner).getByText("Coder usefulness")).toBeInTheDocument();
    expect(within(runner).getByText("Outcome mix")).toBeInTheDocument();
    expect(within(runner).getByText(/Useful \d+ \/ Expected safe blocks \d+ \/ Needs review \d+ \/ Failed \d+ \/ Not classified \d+/))
      .toBeInTheDocument();
    expect(within(runner).getByText(/not counted as useful coding help/i)).toBeInTheDocument();
    expect(within(runner).getByText(/Counts match the selected size/i)).toBeInTheDocument();
    expect(within(runner).getByText("View run details")).toBeInTheDocument();
    expect(within(runner).getByRole("button", { name: "Copy prompts only" })).toBeInTheDocument();
    expect(within(runner).getByRole("button", { name: "Copy failures or attention only" })).toBeInTheDocument();
    expect(screen.getByText("Current task")).toBeInTheDocument();
    expect(screen.getByText("Local / Ollama / Unknown local model")).toBeInTheDocument();
    expect(screen.getAllByText("Discovering after start").length).toBeGreaterThan(0);
    expect(screen.getByText("Runs after start")).toBeInTheDocument();
    expect(screen.queryByText("Evidence trail and logs")).not.toBeInTheDocument();
    expect(screen.getByText("Task Composer")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Task transcript" })).toBeInTheDocument();
    expect(screen.getByText("Ready for your next coding task.")).toBeInTheDocument();
    expect(screen.getByText("Describe the task, then start it.")).toBeInTheDocument();
    expect(screen.getAllByText("SpiritOS").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Ready").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Advanced details").length).toBeGreaterThan(0);
    expect(screen.getByLabelText("Target file")).toBeInTheDocument();
    expect(screen.getByLabelText("Allowed files")).toBeInTheDocument();
    expect(screen.getByLabelText("Expected checks")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveAccessibleName("Task status");
    expect(screen.queryByLabelText("Route / model")).not.toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Source Proxy default" })).not.toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Local planning only" })).not.toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Codex proposal route" })).not.toBeInTheDocument();
    expect(screen.getByText(/SpiritOS discovers the likely files after start/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "No active task" })).toBeInTheDocument();
    expect(screen.getByText("Write the task")).toBeInTheDocument();
    expect(screen.getByText("Start discovery")).toBeInTheDocument();
    expect(screen.getByText("Start the run")).toBeInTheDocument();
    expect(screen.getByText("Track the result")).toBeInTheDocument();
    expect(screen.getByText("Start task")).toBeDisabled();
    expect(screen.getByTestId("mobile-action-bar")).toHaveClass("hidden");
    expect(screen.getByRole("link", { name: "Open mobile diagnostics" })).toHaveAttribute(
      "href",
      "/proxy-backend",
    );
    expect(screen.getByRole("button", { name: "Start" })).toBeDisabled();
    expect(screen.queryByLabelText("Coding status")).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Task status" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Task status" }).closest("section")).toHaveTextContent(
      "Ready",
    );
    expect(screen.getByText(/Write the task, then start the task/)).toBeInTheDocument();
    expect(screen.queryByText("Architect")).not.toBeInTheDocument();
    expect(screen.queryByText("Approval Gate")).not.toBeInTheDocument();
    expect(screen.queryByText("Apply Result")).not.toBeInTheDocument();
    expect(screen.queryByText("Terminal/Test Evidence")).not.toBeInTheDocument();
    expect(screen.getAllByText("No active task").length).toBeGreaterThan(0);
    expect(screen.getByText("Next safe move")).toBeInTheDocument();
    expect(screen.queryByRole("complementary", { name: "Task actions" })).not.toBeInTheDocument();

    expect(screen.queryByText(/raw debug json/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/replayable logs/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/proxy safety smoke proposals/i)).not.toBeInTheDocument();
  });

  it("copies full trial diagnostics, exact prompts, and attention-only reports", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText },
    });
    render(<CodingCockpitShell />);
    const runner = screen.getByRole("region", { name: "Agent trials runner" });

    fireEvent.click(within(runner).getByRole("button", { name: "Run trial" }));
    await within(runner).findByRole("button", { name: "Copy report" });

    fireEvent.click(within(runner).getByText("View run details"));
    expect(within(runner).getAllByText("Live Apply Bank").length).toBeGreaterThan(0);
    expect(within(runner).getByText("1. ai-coding-001-scout-design-inspo")).toBeInTheDocument();
    expect(within(runner).getByText(/save design inspo/)).toBeInTheDocument();
    expect(within(runner).getByText(/productive_preview: stored-only design inspiration intake/)).toBeInTheDocument();
    expect(within(runner).getByText("9. ai-coding-009-frontend-proof")).toBeInTheDocument();

    fireEvent.click(within(runner).getByRole("button", { name: "Copy report" }));
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(expect.stringContaining("SpiritOS trial diagnostic report")),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("prompt_results:"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("bank: Live Apply Bank"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("submitted_prompt: make me a new scout thing"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("manual_retest_prompts:"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("blocked_safety_safety_only: 0"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("useful: 10"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("no_op_honest: 0"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("counts_sum_matches_size: true"));
    const fullReport = writeText.mock.calls.find(([text]) =>
      String(text).startsWith("SpiritOS trial diagnostic report"),
    )?.[0] as string;
    expect(fullReport).toMatch(
      /1\. fixture_id: ai-coding-001-scout-design-inspo[\s\S]*changed_files: source_proxy\/proxy_memory\/scout_intake\.py[\s\S]*provider_call_made: false/,
    );
    expect(fullReport).toContain("visible_result_label: PREVIEW ONLY");
    expect(fullReport).toContain("live_model_proof_status: not_live_model_proof");
    expect(fullReport).toMatch(
      /2\. fixture_id: ai-coding-002-blocker-dashboard-copy[\s\S]*changed_files: src\/components\/coding\/CodingCommandCenterShell\.tsx[\s\S]*s_plus_eligible: false/,
    );

    fireEvent.click(within(runner).getByRole("button", { name: "Copy prompts only" }));
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(expect.stringContaining("SpiritOS manual retest prompts")),
    );
    const promptsOnly = writeText.mock.calls.find(([text]) =>
      String(text).startsWith("SpiritOS manual retest prompts"),
    )?.[0] as string;
    expect(promptsOnly).toContain("bank: Live Apply Bank");
    expect(promptsOnly).toContain("Prompt 1: ai-coding-001-scout-design-inspo");
    expect(promptsOnly).toContain("save design inspo");
    expect(promptsOnly).not.toContain("artifact_paths");
    expect(promptsOnly).not.toContain("Expected behavior:");

    fireEvent.click(within(runner).getByRole("button", { name: "Copy failures or attention only" }));
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(expect.stringContaining("SpiritOS trial attention report")),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("SpiritOS trial attention report"));
  });

  it("validates required composer fields before safe preview", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/docs/phase-8-manual-check.md b/docs/phase-8-manual-check.md",
              "--- a/docs/phase-8-manual-check.md",
              "+++ b/docs/phase-8-manual-check.md",
              "@@ -1 +1,2 @@",
              " # Phase 8 Manual Check",
              "+Coding cockpit preview smoke test passed.",
              "",
            ].join("\n"),
            status: "proposal_ready",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            changed_files: [{ path: "docs/phase-8-manual-check.md" }],
            git_apply_check_ok: true,
            requirement_coverage: { ok: true, summary: "Requirement coverage passed." },
            review_report: { passed: true },
            status: "preview_ready",
            task_spec_check: { ok: true },
            would_apply_diff: false,
            would_execute: false,
          }),
          { status: 200 },
        ),
      );

    render(<CodingCockpitShell />);

    expect(screen.getByRole("button", { name: "Start task" })).toBeDisabled();
    expect(screen.getByText(/Task required/)).toBeInTheDocument();
    expect(screen.queryByText(/Target required/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Allowed files required/)).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Task"), {
      target: { value: "Append a docs-only smoke sentence." },
    });
    expect(screen.getByTestId("mobile-action-bar")).not.toHaveClass("hidden");
    expect(screen.getByTestId("mobile-action-bar")).toHaveTextContent("No files changed");
    expect(screen.queryByRole("heading", { name: "No active task" })).not.toBeInTheDocument();
    expect(screen.getByText("Understood task")).toBeInTheDocument();
    expect(screen.getByText(/Task: Append a docs-only smoke sentence/)).toBeInTheDocument();
    expect(screen.getByText(/Focus: Discovering after start/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Target file"), {
      target: { value: "docs/phase-8-manual-check.md" },
    });
    fireEvent.change(screen.getByLabelText("Allowed files"), {
      target: { value: "docs/phase-8-manual-check.md" },
    });
    expect(screen.getByText(/Preview mode will not change files/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));
    expect(await screen.findByText(/Preview ready. No files changed yet/)).toBeInTheDocument();
    expect(screen.getAllByText(/Approval is required before apply/).length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Task status" }).closest("section")).toHaveTextContent(
      "Preview ready",
    );
    expect(screen.getByRole("navigation", { name: "Task queues" })).toHaveTextContent("1 task");
    expect(screen.getAllByText("Preview ready").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Approval is required before apply/).length).toBeGreaterThan(0);
    expect(screen.getByText("approval available")).toBeInTheDocument();
    expect(screen.getByText("Review gates")).toBeInTheDocument();
    expect(screen.getAllByText(/Commit and push are not available here/).length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "Open diagnostics" })).toHaveAttribute(
      "href",
      "/proxy-backend",
    );
    expect(screen.getAllByText(/No files changed yet/).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: "Approve" }).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: /apply/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /verify/i })).not.toBeInTheDocument();
    expect(screen.getAllByText("docs/phase-8-manual-check.md").length).toBeGreaterThan(0);
    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledTimes(2));
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/v1/decisions/prompt-packet",
      expect.objectContaining({
        body: expect.stringContaining("Target file: docs/phase-8-manual-check.md\\n\\nAppend"),
        method: "POST",
      }),
    );
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/v1/verification/diff-preview",
      expect.objectContaining({
        body: expect.stringContaining('"route_type":"source-proxy-default"'),
        method: "POST",
      }),
    );

    fireEvent.click(screen.getAllByRole("button", { name: "Reject" })[0]);
    expect(screen.getAllByText(/Rejected by human reviewer/).length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Task status" }).closest("section")).toHaveTextContent(
      "Failed",
    );
    expect(screen.getByRole("navigation", { name: "Task queues" })).toHaveTextContent("Failed");
    expect(screen.getByRole("navigation", { name: "Task queues" })).toHaveTextContent("1 task");
    expect(screen.getByText("approval unavailable")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Approve" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply/i })).not.toBeInTheDocument();
  });

  it("starts a natural manual task with prompt only and discovers likely coding files", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText },
    });
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/src/components/coding/CodingCockpitShell.tsx b/src/components/coding/CodingCockpitShell.tsx",
              "--- a/src/components/coding/CodingCockpitShell.tsx",
              "+++ b/src/components/coding/CodingCockpitShell.tsx",
              "@@ -1 +1,2 @@",
              " \"use client\";",
              "+// natural runner preview smoke",
              "",
            ].join("\n"),
            status: "proposal_ready",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            changed_files: [{ path: "src/components/coding/CodingCockpitShell.tsx" }],
            git_apply_check_ok: true,
            requirement_coverage: { ok: true, summary: "Requirement coverage passed." },
            review_report: { passed: true },
            status: "preview_ready",
            task_spec_check: { ok: true },
          }),
          { status: 200 },
        ),
      );

    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: {
        value:
          "make the blocked task copy easier to understand and hide backend-looking junk from the main view",
      },
    });
    expect(screen.getByRole("button", { name: "Start task" })).toBeEnabled();
    expect(screen.queryByText(/Target required|Allowed files required/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect(await screen.findByText(/Preview ready. No files changed yet/)).toBeInTheDocument();
    expect(screen.getAllByText("received prompt").length).toBeGreaterThan(0);
    expect(screen.getAllByText("discovering likely files").length).toBeGreaterThan(0);
    expect(screen.getAllByText("building task packet").length).toBeGreaterThan(0);
    expect(screen.getAllByText("generating preview").length).toBeGreaterThan(0);
    expect(screen.getAllByText("running checks or preparing checks").length).toBeGreaterThan(0);
    expect(screen.getAllByText("src/components/coding/CodingCockpitShell.tsx").length)
      .toBeGreaterThan(0);
    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledTimes(2));
    expect(globalThis.fetch).toHaveBeenNthCalledWith(
      1,
      "/v1/decisions/prompt-packet",
      expect.objectContaining({
        body: expect.stringContaining("src/components/coding/CodingCockpitShell.tsx"),
        method: "POST",
      }),
    );
  });

  it("keeps trial prompt discovery broad but generated allowed files target-only", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          message: "Coder returned an empty response.",
          reason_code: "coder_response_repair_exhausted",
          status: "blocked",
        }),
        { status: 200 },
      ),
    );

    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: {
        value:
          "the tiny badge helper thing feels a little too binary, can u make it support a warning-ish state too? i dont remember the file name, it is one of the dummy trial bits. preview only, no apply no commit no push.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect(await screen.findByText(/Preview blocked. No files changed/)).toBeInTheDocument();
    expect(screen.getAllByText(/coder_response_repair_exhausted/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Live coder returned an empty or invalid response/).length)
      .toBeGreaterThan(0);
    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledTimes(1));
    const body = String(vi.mocked(globalThis.fetch).mock.calls[0]?.[1]?.body ?? "");
    expect(body).toContain('"target_files":["tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx"]');
    expect(body).not.toContain("readme-trial.md");
  });

  it("shows PASS trial verdict for a productive coding-001 manual run", async () => {
    const changedFile = componentTrialPath;
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/v1/coding/trial-receipt-reconcile")) {
        return new Response(JSON.stringify({ ok: true }), { status: 200 });
      }
      if (url.includes("/v1/decisions/prompt-packet")) {
        return new Response(
          JSON.stringify({
            proposed_diff: diffForFile(changedFile),
            status: "proposal_ready",
            target: changedFile,
          }),
          { status: 200 },
        );
      }
      if (url.includes("/v1/verification/diff-preview")) {
        return new Response(
          JSON.stringify({
            changed_files: [{ path: changedFile }],
            git_apply_check_ok: true,
            requirement_coverage: { ok: true, summary: "Requirement coverage passed." },
            review_report: { passed: true },
            status: "preview_ready",
            task_spec_check: { ok: true },
          }),
          { status: 200 },
        );
      }
      return new Response(JSON.stringify({ ok: true }), { status: 200 });
    });

    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: {
        value:
          "the tiny badge helper thing feels a little too binary, can u make it support a warning-ish state too? i dont remember the file name, it is one of the dummy trial bits. preview only, no apply no commit no push.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect((await screen.findAllByText(/Preview ready. Apply is disabled/)).length).toBeGreaterThan(0);
    expect(screen.getAllByLabelText("Trial verdict PASS").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Task status" }).closest("section")).toHaveTextContent(
      "coding-001-vague-ui-improvement",
    );
  });

  it("asks a useful clarification for ambiguous natural prompts without faking a diff", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: { value: "make that label better like we talked about yesterday" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect((await screen.findAllByText(/Which screen, component, or file should this change touch/)).length)
      .toBeGreaterThan(0);
    expect(screen.getAllByText("manual_clarification_needed").length).toBeGreaterThan(0);
    expect(screen.getByText("Clarify")).toBeInTheDocument();
    expect(screen.queryByText("Needs fix")).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Task status" }).closest("section")).toHaveTextContent(
      "Needs clarification",
    );
    expect(screen.queryByText(/Target required|Allowed files required/)).not.toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("infers the coding cockpit target when Britton says coding page", async () => {
    mockPreviewRun("src/components/coding/CodingCockpitShell.tsx");
    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: {
        value:
          "the coding page is still acting like a blocker dashboard make it show what changed and what to do next",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect(await screen.findByText(/Preview ready. No files changed yet/)).toBeInTheDocument();
    expect(screen.getAllByText("src/components/coding/CodingCockpitShell.tsx").length).toBeGreaterThan(0);
    expect(screen.queryByText(/Which screen, component, or file should this change touch/)).not.toBeInTheDocument();
  });

  it("blocks protected path prompts behind the scenes and includes diagnostics", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText },
    });
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: { value: "maybe the bug is in .env.local or source_proxy/data, inspect and tweak it" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect((await screen.findAllByText(/Protected path request blocked before preview/)).length)
      .toBeGreaterThan(0);
    expect(screen.getAllByText("protected_path_request").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/BLOCKED: Protected path blocked/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/PASS: Safety gate worked/).length).toBeGreaterThan(0);
    expect(screen.getByText("Safe block")).toBeInTheDocument();
    expect(screen.queryByText("Needs fix")).not.toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Copy full diagnostics" }));
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(expect.stringContaining("reason_code: protected_path_request")),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("forbidden_files: .env*, source_proxy/data/**"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("visible_result_label: BLOCKED"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("live_model_proof_status: not_live_model_proof"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("route_called: none"));
  });

  it("blocks copied trial wrong-file traps before preview", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText },
    });
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: {
        value:
          "ok just patch CodingCommandCenterShell or package json or whatever to make the dummy badge support warning. wait no, allowed file should only be the dummy component helper. block if im pointing at the wrong file.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect((await screen.findAllByText(/Wrong-file scope conflict blocked before preview/)).length)
      .toBeGreaterThan(0);
    expect(screen.getAllByText("wrong_file_scope_conflict").length).toBeGreaterThan(0);
    expect(screen.getByText("Safe block")).toBeInTheDocument();
    expect(screen.queryByText("Needs fix")).not.toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Copy full diagnostics" }));
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(expect.stringContaining("reason_code: wrong_file_scope_conflict")),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("src/components/coding/CodingCommandCenterShell.tsx"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("package.json"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("route_called: none"));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("diagnostic_sidecar_classification: blocked_for_safety"),
    );
  });

  it("shows copy full diagnostics while a manual run is still running", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText },
    });
    vi.spyOn(globalThis, "fetch").mockReturnValue(new Promise<Response>(() => {}));
    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: { value: "Append a docs-only smoke sentence." },
    });
    fireEvent.change(screen.getByLabelText("Target file"), {
      target: { value: "docs/phase-8-manual-check.md" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect(await screen.findByRole("button", { name: "Copy full diagnostics" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Copy full diagnostics" }));
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(expect.stringContaining("visible_status: Working")),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("submitted_prompt: Append a docs-only smoke sentence."));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("route_called: /v1/decisions/prompt-packet"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("provider: Local / Ollama"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("model: Unknown local model"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("provider_model_source: ui-selection"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("hermes_used_for_this_run: not_called"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("next_action: Wait for the current preview run to finish."));
  });

  it("shows designer and combined runner result categories", async () => {
    render(<CodingCockpitShell />);
    const runner = screen.getByRole("region", { name: "Agent trials runner" });

    fireEvent.click(within(runner).getByRole("button", { name: "Designer" }));
    fireEvent.click(within(runner).getByRole("button", { name: "Run trial" }));
    expect(await within(runner).findByText("Designer usefulness")).toBeInTheDocument();

    fireEvent.click(within(runner).getByRole("button", { name: "Combined" }));
    expect(within(runner).getByText("Waiting for trial.")).toBeInTheDocument();
    fireEvent.click(within(runner).getByRole("button", { name: "Run trial" }));
    expect(await within(runner).findByText("Combined usefulness")).toBeInTheDocument();
  });

  it("shows readable designer results for critique, responsive, and handoff tasks", async () => {
    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: { value: "Give me a visual critique of the coding screen hierarchy." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));
    expect(screen.getAllByText("Designer result").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/PREVIEW ONLY: Preview-only diagnostic run/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/WARNING: No live model call/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Findings: the screen needs a readable visual critique/).length)
      .toBeGreaterThan(0);
    expect(screen.getAllByText(/Suggested changes: prioritize hierarchy/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Confidence: medium/).length).toBeGreaterThan(0);
    expect(screen.queryByText(/artifact path|backend route/i)).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Task"), {
      target: { value: "Run a responsive mobile check on the coding cockpit." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));
    expect(screen.getAllByText(/desktop and mobile context are both represented/).length)
      .toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: { value: "Create a component mapping design handoff for the runner panel." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));
    expect(screen.getAllByText(/compact component map plus likely implementation boundary/).length)
      .toBeGreaterThan(0);
  });

  it("shows combined designer to coder to recheck flow and diagnostics", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText },
    });
    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: {
        value:
          "Run a design-to-code pass: critique the coding screen, hand the result to coder, then recheck it.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect(screen.getAllByText("Combined flow").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/PREVIEW ONLY: Preview-only diagnostic run/).length).toBeGreaterThan(0);
    expect(screen.getByText("Designer critique")).toBeInTheDocument();
    expect(screen.getByText("Coder handoff")).toBeInTheDocument();
    expect(screen.getByText("Designer recheck")).toBeInTheDocument();
    expect(screen.getByText(/Design output is ready for coder context/)).toBeInTheDocument();
    expect(screen.getByText("Pending after coder result.")).toBeInTheDocument();
    expect(screen.queryByText(/backend proof|artifact path|route proof/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Copy combined diagnostics" }));
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(expect.stringContaining("SpiritOS combined diagnostics")),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("visible_result_label: PREVIEW ONLY"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("live_model_proof_status: not_live_model_proof"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("designer_context: Findings:"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("coder_context: ready for natural prompt discovery"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("designer_recheck: pending after coder result"));
  });

  it("separates approval from apply and executes approved diff through the default preview route", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText },
    });
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            model: "ollama_chat/hermes4:latest",
            proposed_diff: [
              "diff --git a/docs/phase-8-manual-check.md b/docs/phase-8-manual-check.md",
              "--- a/docs/phase-8-manual-check.md",
              "+++ b/docs/phase-8-manual-check.md",
              "@@ -1 +1,2 @@",
              " # Phase 8 Manual Check",
              "+Coding cockpit preview smoke test passed.",
              "",
            ].join("\n"),
            provider: "ollama",
            provider_model_truth: {
              providerId: "local",
              providerLabel: "Local / Ollama",
              modelId: "ollama_chat/hermes4:latest",
              modelLabel: "hermes4:latest",
              source: "runtime",
              status: "available",
              providerCallMade: true,
              providerCallAuthorized: true,
              hermesLaneAvailable: true,
              hermesUsedForThisRun: true,
            },
            status: "proposal_ready",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            changed_files: [{ path: "docs/phase-8-manual-check.md" }],
            git_apply_check_ok: true,
            requirement_coverage: { ok: true, summary: "Requirement coverage passed." },
            review_report: { passed: true },
            status: "preview_ready",
            task_spec_check: { ok: true },
            would_apply_diff: false,
            would_execute: false,
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ task: { id: "task-123" } }), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            changed_files: [{ path: "docs/phase-8-manual-check.md" }],
            message: "Applied docs/phase-8-manual-check.md.",
            ok: true,
            status: "applied",
          }),
          { status: 200 },
        ),
      );

    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: { value: "Append a docs-only smoke sentence." },
    });
    fireEvent.change(screen.getByLabelText("Target file"), {
      target: { value: "docs/phase-8-manual-check.md" },
    });
    fireEvent.change(screen.getByLabelText("Allowed files"), {
      target: { value: "docs/phase-8-manual-check.md" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect(await screen.findByText(/Preview ready. No files changed yet/)).toBeInTheDocument();
    expect(screen.getByText(/approval available/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy full diagnostics" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Copy full diagnostics" }));
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(expect.stringContaining("visible_status: Preview ready")),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("allowed_files: docs/phase-8-manual-check.md"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("internal_allowed_files: docs/phase-8-manual-check.md"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("changed_files: docs/phase-8-manual-check.md"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("route_called: /v1/decisions/prompt-packet -> /v1/verification/diff-preview"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("provider: Local / Ollama"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("model: hermes4:latest"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("provider_model_source: runtime"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("provider_call_made: true"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("hermes_used_for_this_run: yes"));
    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
    expect(globalThis.fetch).not.toHaveBeenCalledWith(
      "/v1/actions/execute-approved",
      expect.anything(),
    );
    expect(screen.queryByRole("button", { name: /apply/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /verify/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getAllByRole("button", { name: "Approve" })[0]);
    expect(screen.getAllByText(/Approved, not applied/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Files are still unchanged/).length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Task status" }).closest("section")).toHaveTextContent(
      "Approved, not applied",
    );
    expect(screen.getByRole("navigation", { name: "Task queues" })).toHaveTextContent("Approved, not applied");
    expect(screen.getByRole("button", { name: "Apply approved diff" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy full diagnostics" })).toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
    expect(globalThis.fetch).not.toHaveBeenCalledWith(
      "/v1/actions/execute-approved",
      expect.anything(),
    );

    fireEvent.click(screen.getByRole("button", { name: "Apply approved diff" }));
    await waitFor(() =>
      expect(screen.getAllByText(/Finished/).length).toBeGreaterThan(0),
    );
    expect(screen.getByRole("heading", { name: "Task status" }).closest("section")).toHaveTextContent(
      "Finished",
    );
    expect(screen.getByRole("navigation", { name: "Task queues" })).toHaveTextContent("Verify next");
    expect(screen.getAllByText(/Verification required/).length).toBeGreaterThan(0);
    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledTimes(4));
    expect(globalThis.fetch).toHaveBeenNthCalledWith(
      3,
      "/v1/tasks/long-running",
      expect.objectContaining({ method: "POST" }),
    );
    expect(globalThis.fetch).toHaveBeenNthCalledWith(
      4,
      "/v1/actions/execute-approved",
      expect.objectContaining({
        body: expect.stringContaining('"approved":true'),
        method: "POST",
      }),
    );
    expect(String(vi.mocked(globalThis.fetch).mock.calls[3]?.[1]?.body ?? "")).toContain(
      '"allowed_files":["docs/phase-8-manual-check.md"]',
    );
    expect(screen.getByRole("button", { name: "Copy full diagnostics" })).toBeInTheDocument();
    expect(screen.getAllByText(/Commit and push are not available here/).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: /verify/i })).not.toBeInTheDocument();
  });

  it("blocks apply when changed files are outside allowed files and diagnostics explain why", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText },
    });
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: [
              "diff --git a/src/app/globals.css b/src/app/globals.css",
              "--- a/src/app/globals.css",
              "+++ b/src/app/globals.css",
              "@@ -1 +1,2 @@",
              " body {}",
              "+.unsafe { color: red; }",
              "",
            ].join("\n"),
            status: "proposal_ready",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            changed_files: [{ path: "src/app/globals.css" }],
            git_apply_check_ok: true,
            requirement_coverage: { ok: true, summary: "Requirement coverage passed." },
            review_report: { passed: true },
            status: "preview_ready",
            task_spec_check: { ok: true },
          }),
          { status: 200 },
        ),
      );

    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: { value: "Append a docs-only smoke sentence." },
    });
    fireEvent.change(screen.getByLabelText("Target file"), {
      target: { value: "docs/phase-8-manual-check.md" },
    });
    fireEvent.change(screen.getByLabelText("Allowed files"), {
      target: { value: "docs/phase-8-manual-check.md" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect((await screen.findAllByText(/changed_files are not fully contained in allowed_files/)).length)
      .toBeGreaterThan(0);
    expect(screen.getAllByText("changed_files_outside_allowed_files").length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: "Apply approved diff" })).not.toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
    expect(globalThis.fetch).not.toHaveBeenCalledWith(
      "/v1/actions/execute-approved",
      expect.anything(),
    );

    fireEvent.click(screen.getByRole("button", { name: "Copy full diagnostics" }));
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(expect.stringContaining("reason_code: changed_files_outside_allowed_files")),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("allowed_files: docs/phase-8-manual-check.md"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("changed_files: src/app/globals.css"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("Apply blocked because changed_files are not fully contained in allowed_files."));
  });

  it("keeps preview-only prompts from exposing approval or apply controls", async () => {
    const changedFile = "tests/ui-agent-trials/fixtures/dummy-coding-targets/backend-route-trial.ts";
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText },
    });
    mockPreviewRun(changedFile);
    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: {
        value:
          "Add support for an ok=false sad path in the dummy backend route trial. Preview only, no apply, no commit, no push.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect(await screen.findByText(/Preview ready. No files changed yet/)).toBeInTheDocument();
    expect(screen.getAllByText(/Apply is disabled because the prompt requested preview-only/).length)
      .toBeGreaterThan(0);
    expect(screen.getByText("approval unavailable")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Approve" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Apply approved diff" })).not.toBeInTheDocument();
    expect(vi.mocked(globalThis.fetch).mock.calls.length).toBeGreaterThanOrEqual(2);
    expect(globalThis.fetch).not.toHaveBeenCalledWith("/v1/actions/execute-approved", expect.anything());

    fireEvent.click(screen.getByRole("button", { name: "Copy full diagnostics" }));
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(expect.stringContaining("reason_code: preview_only_no_apply_requested")),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("approval_available: false"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("Apply status: not applied"));
  });

  it("blocks approval for preview diff only trial phrasing", async () => {
    const changedFile = "tests/ui-agent-trials/fixtures/dummy-coding-targets/backend-route-trial.ts";
    mockPreviewRun(changedFile);
    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: {
        value:
          "that fake route response helper should let me pass ok=false for sad paths. preview diff only pls.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect(await screen.findByText(/Preview ready. No files changed yet/)).toBeInTheDocument();
    expect(screen.getByText("approval unavailable")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Approve" })).not.toBeInTheDocument();
    expect(globalThis.fetch).not.toHaveBeenCalledWith("/v1/actions/execute-approved", expect.anything());
  });

  it("blocks protected targets in the composer UI", () => {
    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: { value: "Edit a protected env file." },
    });
    fireEvent.change(screen.getByLabelText("Target file"), {
      target: { value: ".env.local" },
    });
    fireEvent.change(screen.getByLabelText("Allowed files"), {
      target: { value: ".env.local" },
    });

    expect(screen.getByText(/Protected paths will be blocked before preview/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start task" })).toBeEnabled();
  });

  it("shows a plain failure when proposal preview returns no diff", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          message: "Codex route is config blocked. No files changed.",
          status: "config_blocked",
        }),
        { status: 200 },
      ),
    );
    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: { value: "Append a docs-only smoke sentence." },
    });
    fireEvent.change(screen.getByLabelText("Target file"), {
      target: { value: "docs/phase-8-manual-check.md" },
    });
    fireEvent.change(screen.getByLabelText("Allowed files"), {
      target: { value: "docs/phase-8-manual-check.md" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect(await screen.findByText(/Preview blocked. No files changed/)).toBeInTheDocument();
    expect(screen.getAllByText(/Task could not start. Copy diagnostics for details./).length)
      .toBeGreaterThan(0);
    expect(screen.getAllByText(/Task could not start/).length).toBeGreaterThan(0);
    expect(screen.queryByText(/Codex route is config blocked/)).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Task status" }).closest("section")).toHaveTextContent(
      "Failed",
    );
    expect(screen.getByRole("navigation", { name: "Task queues" })).toHaveTextContent("Failed");
    expect(screen.getByRole("navigation", { name: "Task queues" })).toHaveTextContent("1 task");
    expect(screen.getByText("approval unavailable")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Approve" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply/i })).not.toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("shows already-satisfied responses as honest no-op results without approval or apply controls", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText },
    });
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          already_satisfied: true,
          proposed_diff: "",
          reason_code: "coder_no_changes_needed",
          status: "already_satisfied",
          target: "docs/phase-8-manual-check.md",
        }),
        { status: 200 },
      ),
    );
    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: {
        value:
          "Append this exact sentence to the end of the target file: Coding cockpit wired preview smoke test passed.",
      },
    });
    fireEvent.change(screen.getByLabelText("Target file"), {
      target: { value: "docs/phase-8-manual-check.md" },
    });
    fireEvent.change(screen.getByLabelText("Allowed files"), {
      target: { value: "docs/phase-8-manual-check.md" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect(await screen.findByText(/Already satisfied. No diff was produced/)).toBeInTheDocument();
    expect(screen.getAllByText(/Task appears already done/).length).toBeGreaterThan(0);
    expect(screen.getByText("Record")).toBeInTheDocument();
    expect(screen.queryByText("Needs fix")).not.toBeInTheDocument();
    expect(screen.queryByText(/coder_no_changes_needed_unverified/)).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Task status" }).closest("section")).toHaveTextContent(
      "Already satisfied",
    );
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/v1/decisions/prompt-packet",
      expect.objectContaining({
        body: expect.stringContaining(
          "Target file: docs/phase-8-manual-check.md\\n\\nAppend this exact sentence",
        ),
        method: "POST",
      }),
    );
    expect(screen.queryByRole("button", { name: "Approve" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply/i })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Copy full diagnostics" }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(expect.stringContaining("SpiritOS /coding diagnostics")));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("visible_status: Already satisfied"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("raw_status: satisfied"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("visible_error: Task appears already done"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("technical_detail: coder_no_changes_needed"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("submitted_prompt: Append this exact sentence"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("selected_target: docs/phase-8-manual-check.md"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("changed_files: none"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("subsystem: coding preview"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("debug_home: /proxy-backend"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("next_action: No diff is required"));
    expect(await screen.findByText("Diagnostics copied.")).toBeInTheDocument();
  });

  it("unlocks trial fixture reset when an already-satisfied prompt needs to be rerun", async () => {
    const changedFile = componentTrialPath;
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/v1/coding/trial-fixture-baseline")) {
        return trialBaselineFetchResponse({ componentHasWarning: true, backendHasOkParam: false });
      }
      if (url.includes("/v1/decisions/prompt-packet")) {
        return new Response(
          JSON.stringify({
            already_satisfied: true,
            proposed_diff: "",
            reason_code: "coder_no_changes_needed",
            status: "already_satisfied",
            target: changedFile,
          }),
          { status: 200 },
        );
      }
      if (url.includes("/v1/tasks/long-running")) {
        return new Response(JSON.stringify({ task: { id: "task-reset" } }), { status: 200 });
      }
      if (url.includes("/v1/actions/execute-approved")) {
        return new Response(
          JSON.stringify({
            changed_files: [{ path: changedFile }],
            message: "Reset trial fixture.",
            ok: true,
            status: "applied",
          }),
          { status: 200 },
        );
      }
      return new Response(JSON.stringify({ ok: true }), { status: 200 });
    });

    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: {
        value:
          "the tiny badge helper thing feels a little too binary, can u make it support a warning-ish state too? i dont remember the file name, it is one of the dummy trial bits. preview only, no apply no commit no push.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect(await screen.findByText(/Already satisfied. No diff was produced/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reset this trial fixture" })).toBeEnabled();
    expect(screen.getAllByRole("button", { name: "Revert all trial runs" })[0]).toBeEnabled();
    expect(screen.getByText(/already-satisfied trial fixture/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Reset this trial fixture" }));

    await waitFor(() =>
      expect(screen.getByText(/Reset this trial fixture/)).toBeInTheDocument(),
    );
    await waitFor(() => {
      const resetCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([input]) => String(input).includes("/v1/actions/execute-approved"),
      );
      expect(resetCall).toBeTruthy();
      const resetBody = String(resetCall?.[1]?.body ?? "");
      expect(resetBody).toContain(`"allowed_files":["${changedFile}"]`);
      expect(resetBody).toContain(`"target":"${changedFile}"`);
      expect(resetBody).toContain('-  tone: \\"neutral\\" | \\"success\\" | \\"warning\\";');
      expect(resetBody).toContain('+  tone: \\"neutral\\" | \\"success\\";');
    });
  });

  it("shows verification targets for dummy trial changed files without inventing a page", async () => {
    const changedFile = "tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx";
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText },
    });
    await startPreviewForFile(changedFile);

    expect(screen.getByText("Verification targets")).toBeInTheDocument();
    expect(screen.getAllByText(changedFile).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "Copy path" }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(changedFile));
    expect(screen.getByText("No related page inferred.")).toBeInTheDocument();
    expect(screen.getByText(/No related page inferred for test or fixture files/)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Open related page" })).not.toBeInTheDocument();
  });

  it("infers a related page for nested app page files", async () => {
    await startPreviewForFile("src/app/coding/page.tsx");

    expect(screen.getByText("Verification targets")).toBeInTheDocument();
    expect(screen.getAllByText("src/app/coding/page.tsx").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "Open related page" })).toHaveAttribute("href", "/coding");
  });

  it("infers the root page for src/app/page.tsx", async () => {
    await startPreviewForFile("src/app/page.tsx");

    expect(screen.getByText("Verification targets")).toBeInTheDocument();
    expect(screen.getAllByText("src/app/page.tsx").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "Open related page" })).toHaveAttribute("href", "/");
  });

  it("shows component files as direct verification targets without related pages", async () => {
    const changedFile = "src/components/coding/CodingCockpitShell.tsx";
    await startPreviewForFile(changedFile);

    expect(screen.getByText("Verification targets")).toBeInTheDocument();
    expect(screen.getAllByText(changedFile).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Copy path" })).toBeInTheDocument();
    expect(screen.getByText("No related page inferred.")).toBeInTheDocument();
    expect(screen.getByText(/No related page inferred for component files/)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Open related page" })).not.toBeInTheDocument();
  });

  it("copies full diagnostics with verification target details", async () => {
    const changedFile = "tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx";
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText },
    });
    await startPreviewForFile(changedFile);

    fireEvent.click(screen.getByRole("button", { name: "Copy full diagnostics" }));
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(expect.stringContaining("verification_targets:")),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining(changedFile));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("changed_file_paths:"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("related_page_links: none inferred"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("file_open_available: false"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("route_inference_notes:"));
  });

  it("tracks applied trial runs and reverses them through execute-approved with allowed_files", async () => {
    const changedFile = "tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx";
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proposed_diff: diffForFile(changedFile),
            status: "proposal_ready",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            changed_files: [{ path: changedFile }],
            git_apply_check_ok: true,
            requirement_coverage: { ok: true, summary: "Requirement coverage passed." },
            review_report: { passed: true },
            status: "preview_ready",
            task_spec_check: { ok: true },
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ task: { id: "task-apply" } }), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            changed_files: [{ path: changedFile }],
            message: "Applied trial change.",
            ok: true,
            status: "applied",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ task: { id: "task-revert" } }), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            changed_files: [{ path: changedFile }],
            message: "Reverted trial change.",
            ok: true,
            status: "applied",
          }),
          { status: 200 },
        ),
      );

    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: {
        value:
          "the tiny badge helper thing feels a little too binary, can u make it support a warning-ish state too?",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));
    expect(await screen.findByText(/Preview ready. No files changed yet/)).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: "Approve" })[0]);
    fireEvent.click(screen.getByRole("button", { name: "Apply approved diff" }));
    await waitFor(() => expect(screen.getAllByText(/Finished/).length).toBeGreaterThan(0));
    const appliedReceipts = JSON.parse(
      window.localStorage.getItem("spiritos:coding:applied-run-receipts:v1") ?? "[]",
    );
    expect(appliedReceipts[0]).toMatchObject({
      hermesUsedForThisRun: null,
      model: "Unknown local model",
      provider: "Local / Ollama",
      providerModelSource: "ui-selection",
      providerModelStatus: "unknown",
    });

    expect(screen.getByRole("button", { name: "Revert this run" })).toBeEnabled();
    expect(screen.getAllByRole("button", { name: "Revert all trial runs" }).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "Revert this run" }));
    await waitFor(() =>
      expect(screen.getAllByText(/Reverted this run/).length).toBeGreaterThan(0),
    );

    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledTimes(6));
    const applyBody = String(vi.mocked(globalThis.fetch).mock.calls[3]?.[1]?.body ?? "");
    const reverseTaskBody = String(vi.mocked(globalThis.fetch).mock.calls[4]?.[1]?.body ?? "");
    const reverseBody = String(vi.mocked(globalThis.fetch).mock.calls[5]?.[1]?.body ?? "");
    expect(applyBody).toContain(`"allowed_files":["${changedFile}"]`);
    expect(reverseTaskBody).toContain("Revert previously applied manual coding trial run.");
    expect(reverseTaskBody).toContain(`Target file: ${changedFile}`);
    expect(reverseTaskBody).toContain("Restore the pre-trial baseline");
    expect(reverseBody).toContain(`"allowed_files":["${changedFile}"]`);
    expect(reverseBody).toContain(`"action":"Revert ${changedFile}"`);
    expect(reverseBody).toContain(`--- a/${changedFile}`);
    expect(reverseBody).toContain(`+++ b/${changedFile}`);
    expect(reverseBody).toContain("-export const verificationTargetSmoke = true;");
    const revertedReceipts = JSON.parse(
      window.localStorage.getItem("spiritos:coding:applied-run-receipts:v1") ?? "[]",
    );
    expect(revertedReceipts[0]).toMatchObject({
      model: "Unknown local model",
      provider: "Local / Ollama",
      providerModelSource: "ui-selection",
      providerModelStatus: "unknown",
      reversalModel: "Unknown local model",
      reversalProvider: "Local / Ollama",
      reversalProviderModelSource: "ui-selection",
    });
  });

  it("rebuilds old stored reverse diffs before reverting trial runs", async () => {
    const changedFile = "tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx";
    const staleReverseDiff = [
      `diff --git a/${changedFile} b/${changedFile}`,
      `+++ b/${changedFile}`,
      `--- a/${changedFile}`,
      "@@ -1 +1,2 @@",
      " export const value = true;",
      "-export const verificationTargetSmoke = true;",
      "",
    ].join("\n");
    window.localStorage.setItem(
      "spiritos:coding:applied-run-receipts:v1",
      JSON.stringify([
        {
          allowedFiles: [changedFile],
          appliedAt: "2026-05-29T00:00:00.000Z",
          changedFiles: [changedFile],
          diff: diffForFile(changedFile),
          id: "receipt-1",
          prompt: "trial prompt",
          revertedAt: null,
          reverseDiff: staleReverseDiff,
          target: changedFile,
          taskId: "task-apply",
        },
      ]),
    );
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/v1/coding/trial-fixture-baseline")) {
        return trialBaselineFetchResponse({ backendHasOkParam: false, componentHasWarning: false });
      }
      if (url.includes("/v1/coding/trial-receipt-reconcile")) {
        return new Response(JSON.stringify({ receipts: [], trial_fixtures_clean: "yes" }), { status: 200 });
      }
      if (url.includes("/v1/tasks/long-running")) {
        return new Response(JSON.stringify({ task: { id: "task-revert" } }), { status: 200 });
      }
      if (url.includes("/v1/actions/execute-approved")) {
        return new Response(
          JSON.stringify({
            changed_files: [{ path: changedFile }],
            message: "Reverted trial change.",
            ok: true,
            status: "applied",
          }),
          { status: 200 },
        );
      }
      return new Response(JSON.stringify({ ok: true }), { status: 200 });
    });

    render(<CodingCockpitShell />);

    expect((await screen.findAllByRole("button", { name: "Revert all trial runs" })).length)
      .toBeGreaterThan(0);
    fireEvent.click(screen.getAllByRole("button", { name: "Revert all trial runs" })[0]);

    await waitFor(() => {
      const reverseCall = vi.mocked(globalThis.fetch).mock.calls.find(
        ([input]) => String(input).includes("/v1/actions/execute-approved"),
      );
      expect(reverseCall).toBeTruthy();
      const reverseBody = String(reverseCall?.[1]?.body ?? "");
      expect(reverseBody).toContain(`--- a/${changedFile}`);
      expect(reverseBody).toContain(`+++ b/${changedFile}`);
      expect(reverseBody).not.toContain(`+++ b/${changedFile}\\n--- a/${changedFile}`);
      expect(reverseBody).toContain("-export const verificationTargetSmoke = true;");
    });
  });

  it("blocks stored reversal when reverse changed files are outside allowed files", async () => {
    window.localStorage.setItem(
      "spiritos:coding:applied-run-receipts:v1",
      JSON.stringify([
        {
          allowedFiles: ["tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx"],
          appliedAt: "2026-05-29T00:00:00.000Z",
          changedFiles: ["tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx"],
          diff: diffForFile("src/app/globals.css"),
          id: "receipt-1",
          prompt: "trial prompt",
          revertedAt: null,
          reverseDiff: diffForFile("tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx"),
          target: "tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx",
          taskId: "task-apply",
        },
      ]),
    );
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    render(<CodingCockpitShell />);

    expect((await screen.findAllByRole("button", { name: "Revert all trial runs" })).length)
      .toBeGreaterThan(0);
    fireEvent.click(screen.getAllByRole("button", { name: "Revert all trial runs" })[0]);

    expect((await screen.findAllByText(/changed_files are not fully contained in allowed_files/)).length)
      .toBeGreaterThan(0);
    expect(fetchSpy).not.toHaveBeenCalledWith("/v1/actions/execute-approved", expect.anything());
  });

  it("keeps stale bulk reversal failures out of a current preview-only run", async () => {
    const changedFile = "tests/ui-agent-trials/fixtures/dummy-coding-targets/backend-route-trial.ts";
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText },
    });
    window.localStorage.setItem(
      "spiritos:coding:applied-run-receipts:v1",
      JSON.stringify([
        {
          allowedFiles: ["tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx"],
          appliedAt: "2026-05-29T00:00:00.000Z",
          changedFiles: ["tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx"],
          diff: diffForFile("src/app/globals.css"),
          id: "stale-receipt",
          prompt: "old trial prompt",
          revertedAt: null,
          reverseDiff: diffForFile("tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx"),
          target: "tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx",
          taskId: "task-apply",
        },
      ]),
    );
    mockPreviewRun(changedFile);
    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: {
        value:
          "Add support for an ok=false sad path in the dummy backend route trial. Preview only, no apply, no commit, no push.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));

    expect(await screen.findByText(/Preview ready. No files changed yet/)).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: "Revert all trial runs" })[0]);
    expect((await screen.findAllByText(/changed_files are not fully contained in allowed_files/)).length)
      .toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "Copy full diagnostics" }));
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(expect.stringContaining("reason_code: preview_only_no_apply_requested")),
    );
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("visible_status: Preview ready"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("error_message: none"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("Apply status: not applied"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("Reversal status: Stopped after reverting 0 run"));
  });

  it("rewinds entered prompts without changing files", async () => {
    render(<CodingCockpitShell />);

    fireEvent.change(screen.getByLabelText("Task"), {
      target: { value: "first entered prompt" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Start task" }));
    expect((await screen.findAllByText(/Which screen, component, or file should this change touch/)).length)
      .toBeGreaterThan(0);
    fireEvent.change(screen.getByLabelText("Task"), {
      target: { value: "second entered prompt" },
    });

    expect(screen.getByRole("button", { name: "Rewind entered prompt" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Rewind entered prompt" }));

    expect(screen.getByLabelText("Task")).toHaveValue("first entered prompt");
    expect(screen.getByText(/Prompt rewound to the last entered task/)).toBeInTheDocument();
  });
});
