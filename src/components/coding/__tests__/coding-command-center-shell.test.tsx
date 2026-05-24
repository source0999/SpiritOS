import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import CodingCommandCenterShell from "@/components/coding/CodingCommandCenterShell";

const navMock = vi.hoisted(() => ({ path: "/coding" }));

vi.mock("next/navigation", () => ({
  usePathname: () => navMock.path,
}));

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
  window.localStorage.removeItem("spiritos:coding-command-center:task-story");
});

function taskCreateResponse(taskId = "task-123") {
  return new Response(JSON.stringify({ task: { id: taskId } }), { status: 200 });
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
    expect(screen.queryByRole("navigation", { name: "Dashboard mobile navigation" }))
      .not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start new chat" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Selected workspace: SpiritOS" })).toHaveTextContent(
      "/home/source/SpiritOS",
    );
    expect(screen.getByRole("button", { name: "Selected workspace: SpiritOS" })).toHaveTextContent(
      "Selected workspace; no commit, push, branch, or worktree action is available here",
    );
    const futureWorkspaceButton = screen.getByRole("button", {
      name: /Future workspace option: .*Projects/,
    });
    expect(futureWorkspaceButton).toBeDisabled();
    expect(futureWorkspaceButton).toHaveAttribute("aria-disabled", "true");
    expect(futureWorkspaceButton).toHaveTextContent(
      "Bridge-gated future project source; read-only/proposal-only until explicitly approved",
    );
    expect(futureWorkspaceButton).toHaveTextContent(
      "Unavailable from this selector; external workspace actions stay proposal-only",
    );
    expect(screen.getByRole("button", { name: "Start new project placeholder" }))
      .toHaveAttribute("aria-disabled", "true");
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
    expect(screen.getAllByText("SpiritOS").length).toBeGreaterThan(0);
    expect(screen.getByText("Local LLM default")).toBeInTheDocument();
    expect(screen.getByText("GPT/cloud unavailable")).toBeInTheDocument();
    expect(screen.getByText("Default route where local coding support is available."))
      .toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Codex worker: proposal-only" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Future providers: future" })).toBeInTheDocument();
    expect(screen.getByText("Intent: local LLM route. No provider call has run yet."))
      .toBeInTheDocument();
    expect(screen.getByText("Active task area")).toBeInTheDocument();
    expect(screen.getByText("SpiritOS is selected by default")).toBeInTheDocument();
    expect(
      screen.getByText(
        "C:\\Projects is read-only/proposal-only; no external workspace action is available from this selector.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Coding command composer")).toHaveAttribute(
      "placeholder",
      "Ask for a plan, start a coding task, or gather repo context.",
    );
    expect(screen.getByRole("button", { name: "Desktop submit task" })).toBeDisabled();
    expect(screen.getAllByText("Trial prompt and steps")).toHaveLength(2);
    expect(
      screen.getAllByText("Current step: paste the copy-paste task, click Coding mode, then Submit task."),
    ).toHaveLength(2);
    expect(screen.getAllByText("Copy-paste task")).toHaveLength(2);
    expect(screen.getAllByRole("button", { name: "Use task" })).toHaveLength(2);
    expect(screen.getByRole("button", { name: "Mobile use task" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Copy task" })).toHaveLength(2);
    expect(screen.getByRole("button", { name: "Mobile copy task" })).toBeInTheDocument();
    expect(screen.getAllByText("3. Click Submit task. Enter only adds a new line."))
      .toHaveLength(2);
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

    expect(screen.getByRole("heading", { level: 2, name: "No active run" })).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();
    expect(screen.getByText("Preview")).toBeInTheDocument();
    expect(screen.getByText("Approval")).toBeInTheDocument();
    expect(screen.getByText("Apply")).toBeInTheDocument();
    expect(screen.getByText("Verify")).toBeInTheDocument();
    expect(screen.getByText(/Preview requires bounded task data/))
      .toBeInTheDocument();

    expect(screen.queryByRole("button", { name: /apply approved diff/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /commit|push/i })).not.toBeInTheDocument();
  });

  it("keeps workspace, provider, and safety status visible without implying execution", () => {
    render(<CodingCommandCenterShell />);

    expect(screen.getByRole("button", { name: "Selected workspace: SpiritOS" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Future workspace option: .*Projects/ }))
      .toBeDisabled();
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

  it("creates a visible local task packet from bounded composer input", () => {
    render(<CodingCommandCenterShell />);

    fireEvent.change(screen.getByLabelText("Coding command composer"), {
      target: {
        value:
          "Create a docs-only patch task. Target file: docs/proxy-test-runner-plan.md. Allowed files: docs/proxy-test-runner-plan.md. Add one short sentence.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));

    expect(screen.getByText("Patch docs/proxy-test-runner-plan.md")).toBeInTheDocument();
    expect(screen.getByText("Task submitted locally. Preview is ready to request; no files changed."))
      .toBeInTheDocument();
    expect(screen.getAllByText(/Target file:/)[0]).toHaveTextContent(
      "Target file: docs/proxy-test-runner-plan.md",
    );
    expect(screen.getAllByText(/Allowed files:/)[0]).toHaveTextContent(
      "Allowed files: docs/proxy-test-runner-plan.md",
    );
    const scopeReview = screen.getByRole("region", { name: "Inferred scope review" });
    expect(within(scopeReview).getByText("Scope review")).toBeInTheDocument();
    expect(within(scopeReview).getByText("Status: ready")).toBeInTheDocument();
    expect(within(scopeReview).getByText("Task type: docs")).toBeInTheDocument();
    expect(within(scopeReview).getByText("Expected checks: git diff --check")).toBeInTheDocument();
    expect(within(scopeReview).getByText("Safe next action: review_scope")).toBeInTheDocument();
    expect(screen.getByText(/Bounded task data present/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Desktop preview safely" })).toBeEnabled();
  });

  it("accepts plain-English browser intake and shows scope review before preview", () => {
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
    expect(screen.getByRole("button", { name: "Desktop preview safely" })).toBeEnabled();
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
    expect(screen.getByRole("button", { name: "Approve preview" })).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "Current step: review the diff, then click Approve preview if it only touches the allowed docs file.",
      ),
    ).toHaveLength(1);
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

    expect(screen.getByRole("button", { name: "Desktop preview safely" })).toBeEnabled();
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
      await vi.advanceTimersByTimeAsync(30_000);
    });

    const timeoutMessage = "Creating preview task timed out after 30 seconds. No files changed.";
    expect(screen.getByText(timeoutMessage)).toBeInTheDocument();
    expect(screen.getByText(`Preview: ${timeoutMessage}`)).toBeInTheDocument();
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

    fireEvent.click(screen.getAllByRole("button", { name: "Copy task" })[0]);

    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Create a docs-only patch task."),
    );
    expect(await screen.findAllByText("Trial task inserted, submitted, and copied. Tap Preview safely."))
      .toHaveLength(2);
    expect(screen.getByLabelText("Coding command composer")).toHaveValue(
      "Create a docs-only patch task. Target file: docs/proxy-test-runner-plan.md. Allowed files: docs/proxy-test-runner-plan.md. Add one short sentence explaining that verification receipts should include changed files, commands run, and pass/fail results.",
    );
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

    fireEvent.touchEnd(screen.getByRole("button", { name: "Mobile copy task" }));

    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Create a docs-only patch task."),
    );
    expect(await screen.findAllByText("Trial task inserted, submitted, and copied. Tap Preview safely."))
      .toHaveLength(2);
    expect(screen.getByLabelText("Mobile coding command composer")).toHaveValue(
      "Create a docs-only patch task. Target file: docs/proxy-test-runner-plan.md. Allowed files: docs/proxy-test-runner-plan.md. Add one short sentence explaining that verification receipts should include changed files, commands run, and pass/fail results.",
    );
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

    await act(async () => {
      fireEvent.click(screen.getAllByRole("button", { name: "Copy task" })[0]);
    });

    expect(await screen.findAllByText("Copy unavailable on this device, so the task was inserted and submitted. Tap Preview safely."))
      .toHaveLength(2);
    expect(screen.getByLabelText("Coding command composer")).toHaveValue(
      "Create a docs-only patch task. Target file: docs/proxy-test-runner-plan.md. Allowed files: docs/proxy-test-runner-plan.md. Add one short sentence explaining that verification receipts should include changed files, commands run, and pass/fail results.",
    );
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

    await act(async () => {
      fireEvent.click(screen.getAllByRole("button", { name: "Copy task" })[0]);
    });

    expect(await screen.findAllByText("Trial task inserted, submitted, and copied. Tap Preview safely."))
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

    await act(async () => {
      fireEvent.click(screen.getAllByRole("button", { name: "Copy task" })[0]);
    });

    expect(execCommand).toHaveBeenCalledWith("copy");
    expect(writeText).not.toHaveBeenCalled();
    expect(await screen.findAllByText("Trial task inserted, submitted, and copied. Tap Preview safely."))
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

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Copy receipt" }));
    });

    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("Verification receipt"),
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
    expect(screen.queryByText(/verification passed/i)).not.toBeInTheDocument();
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
        new Response(JSON.stringify({ message: "protected path blocked", status: "blocked" }), {
          status: 200,
        }),
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

    expect(await screen.findByText("protected path blocked")).toBeInTheDocument();
    expect(screen.getByText("Approval gate display: locked because preview is blocked."))
      .toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /approve/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply/i })).not.toBeInTheDocument();
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
        value:
          "Create a docs-only patch task. Target file: docs/proxy-test-runner-plan.md. Allowed files: docs/proxy-test-runner-plan.md. Add one short sentence explaining that verification receipts should include changed files, commands run, and pass/fail results.",
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
      screen.getAllByText(
        "Trial complete: no-op evidence is ready. Copy the receipt or start a different bounded task.",
      ),
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
        value:
          "Create a docs-only patch task. Target file: docs/proxy-test-runner-plan.md. Allowed files: docs/proxy-test-runner-plan.md. Add one short sentence.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));
    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));

    const blockedMessage =
      "Preview blocked: Source Proxy needs more codebase context before it can produce a safe diff. No files changed.";
    expect(await screen.findByText(blockedMessage)).toBeInTheDocument();
    expect(screen.getByText(`Preview: ${blockedMessage}`)).toBeInTheDocument();
    expect(screen.getByText(`Safe next action: ${blockedMessage}`)).toBeInTheDocument();
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
        value:
          "Create a docs-only patch task. Target file: docs/proxy-test-runner-plan.md. Allowed files: docs/proxy-test-runner-plan.md. Add one short sentence explaining that verification receipts should include changed files, commands run, and pass/fail results.",
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Desktop submit task" }));
    fireEvent.click(screen.getByRole("button", { name: "Desktop preview safely" }));

    expect((await screen.findAllByText("Preview evidence")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Changed files: docs/proxy-test-runner-plan.md").length).toBeGreaterThan(0);
    expect(
      screen.getByText(
        "Approval gate display: clean preview evidence available; approval requires human click before apply.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Approval: Clean preview evidence exists; explicit human approval is available."))
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
        "Apply scope: locked until approval; preview scope is docs/proxy-test-runner-plan.md.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Review-only preview/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Write actions/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Approve preview" }));
    expect(screen.getByText("Preview approved locally. No files changed yet."))
      .toBeInTheDocument();
    expect(
      screen.getByText(
        "Approval gate display: human approval recorded; apply requires the approved route.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Approval: Approved locally.")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Apply scope: approved route may write only docs/proxy-test-runner-plan.md.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Source Proxy task id/)).not.toBeInTheDocument();
    expect(screen.queryByText(/fallback diff/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Apply approved diff" })).toBeEnabled();
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
    expect(screen.getByText(/Preview requires bounded task data/))
      .toBeInTheDocument();
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
    expect(screen.queryByRole("button", { name: /apply approved diff/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /commit|push/i })).not.toBeInTheDocument();
  });

  it("starts a local new chat and makes it active", () => {
    render(<CodingCommandCenterShell />);

    fireEvent.click(screen.getByRole("button", { name: "Start new chat" }));

    expect(screen.getByRole("heading", { level: 2, name: "New chat 1" })).toBeInTheDocument();
    expect(screen.getByText("Empty chat 1, ready for a prompt")).toBeInTheDocument();

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
