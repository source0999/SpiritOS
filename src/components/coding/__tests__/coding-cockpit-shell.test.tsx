import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import CodingCockpitShell from "@/components/coding/CodingCockpitShell";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("CodingCockpitShell", () => {
  it("renders a clean cockpit shell without diagnostic console clutter", () => {
    render(<CodingCockpitShell />);

    expect(screen.getByRole("heading", { level: 1, name: "Coding" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Spirit workspace navigation" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Source" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Dashboard" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: /advanced diagnostics/i })).toHaveAttribute(
      "href",
      "/proxy-backend",
    );
    expect(screen.getByText("Task Composer")).toBeInTheDocument();
    expect(screen.getByText("Advanced options")).toBeInTheDocument();
    expect(screen.getByText(/Preview does not write files/)).toBeInTheDocument();
    expect(screen.getByText("Preview safely")).toBeDisabled();
    expect(screen.getByTestId("mobile-action-bar")).toHaveTextContent("No files changed");
    expect(screen.getByRole("button", { name: "Preview" })).toBeDisabled();
    expect(screen.getByLabelText("Coding status")).toHaveTextContent("Draft");
    expect(screen.getByLabelText("Coding status")).toHaveTextContent("Apply");
    expect(screen.getByLabelText("Coding status")).toHaveTextContent("Verify");
    expect(screen.getByRole("heading", { name: "Task Timeline" })).toBeInTheDocument();
    expect(screen.getByText("Architect")).toBeInTheDocument();
    expect(screen.getByText("Coder")).toBeInTheDocument();
    expect(screen.getByText("Reviewer")).toBeInTheDocument();
    expect(screen.getByText("Verifier")).toBeInTheDocument();
    expect(screen.getByText("Approval Gate")).toBeInTheDocument();
    expect(screen.getByText("Apply Result")).toBeInTheDocument();
    expect(screen.getByText("Terminal/Test Evidence")).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "Task actions" })).toHaveTextContent(
      "Current Task",
    );
    expect(screen.getByRole("complementary", { name: "Task actions" })).toHaveTextContent(
      "No active task",
    );
    expect(screen.getByRole("complementary", { name: "Task actions" })).toHaveTextContent(
      "Next Safe Action",
    );

    expect(screen.queryByText(/raw debug json/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/replayable logs/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/proxy safety smoke proposals/i)).not.toBeInTheDocument();
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

    expect(screen.getByRole("button", { name: "Preview safely" })).toBeDisabled();
    expect(screen.getByText(/Task required/)).toBeInTheDocument();
    expect(screen.getByText(/Target required/)).toBeInTheDocument();
    expect(screen.getByText(/Allowed files required/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Task"), {
      target: { value: "Append a docs-only smoke sentence." },
    });
    fireEvent.change(screen.getByLabelText("Target file"), {
      target: { value: "docs/phase-8-manual-check.md" },
    });
    fireEvent.change(screen.getByLabelText("Allowed files"), {
      target: { value: "docs/phase-8-manual-check.md" },
    });

    expect(screen.getByText(/No files will be changed during preview/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Preview safely" }));
    expect(await screen.findByText(/Preview ready. No files changed yet/)).toBeInTheDocument();
    expect(screen.getAllByText("Needs approval").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Evidence available").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Approval is required before apply/).length).toBeGreaterThan(0);
    expect(screen.getByText("approval available")).toBeInTheDocument();
    expect(screen.getByText(/Approval is separate from apply/)).toBeInTheDocument();
    expect(screen.getAllByText(/Commit and push are not available here/).length).toBeGreaterThan(0);
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
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("separates approval from apply and executes approved diff through Source Proxy route", async () => {
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
    fireEvent.click(screen.getByRole("button", { name: "Preview safely" }));

    expect(await screen.findByText(/Preview ready. No files changed yet/)).toBeInTheDocument();
    expect(screen.getByText(/approval available/)).toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole("button", { name: /apply/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /verify/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getAllByRole("button", { name: "Approve" })[0]);
    expect(screen.getAllByText(/Approved, not applied/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Files are still unchanged/).length).toBeGreaterThan(0);
    expect(globalThis.fetch).toHaveBeenCalledTimes(2);

    fireEvent.click(screen.getByRole("button", { name: "Apply approved diff" }));
    await waitFor(() =>
      expect(screen.getAllByText(/Applied, verification required/).length).toBeGreaterThan(0),
    );
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
    expect(screen.getAllByText(/Commit and push are not available here/).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: /verify/i })).not.toBeInTheDocument();
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

    expect(screen.getByText(/Protected target blocked in UI/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Preview safely" })).toBeDisabled();
  });

  it("shows a backend blocker when proposal preview returns no diff", async () => {
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
    fireEvent.click(screen.getByRole("button", { name: "Preview safely" }));

    expect(await screen.findByText(/Preview blocked. No files changed/)).toBeInTheDocument();
    expect(screen.getAllByText(/Codex route is config blocked/).length).toBeGreaterThan(0);
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("blocks unverified already-satisfied responses without approval or apply controls", async () => {
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
    fireEvent.click(screen.getByRole("button", { name: "Preview safely" }));

    expect(await screen.findByText(/Preview blocked. No files changed/)).toBeInTheDocument();
    expect(screen.getAllByText(/cannot verify the target content without a diff/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/coder_no_changes_needed_unverified/).length).toBeGreaterThan(0);
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
  });
});
