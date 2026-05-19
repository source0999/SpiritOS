/// <reference types="vitest" />

import { render, screen, waitFor, within } from "@testing-library/react";

import { HomelabCartographerWidget } from "../HomelabCartographerWidget";

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
});

describe("HomelabCartographerWidget", () => {
  it("shows a loading state before Cartographer responds", () => {
    globalThis.fetch = vi.fn(() => new Promise<Response>(() => {})) as typeof fetch;

    render(<HomelabCartographerWidget />);

    expect(screen.getByText("Spirit Cartographer")).toBeInTheDocument();
    expect(screen.getByText("Loading")).toBeInTheDocument();
    expect(screen.getByText("Loading Cartographer state.")).toBeInTheDocument();
  });

  it("renders read-only v1 closeout dashboard cards", async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: "observing",
            write_actions_enabled: false,
            authority_granted: false,
            actions_taken: false,
            dashboard_mode: "read_only_v1_closeout_surface",
            docs_path: "docs/cartographer-v1-evidence-artifacts.md",
            docs_label: "Cartographer v1 evidence artifact contract",
            primary_status: "blocked_missing_evidence",
            primary_label: "Blocked by missing evidence",
            v1_ready: false,
            readiness: "not_ready",
            blocker_count: 8,
            freeze_marker_status: "missing",
            next_action: "Record three clean diagnostic or closeout proof artifacts with passing results.",
            dashboard_cards: [
              {
                card_id: "v1-readiness",
                label: "V1 readiness",
                status: "not_ready",
                value: "blocked",
                detail: "8 blockers",
                endpoint: "/v1/cartographer/v1-readiness",
              },
              {
                card_id: "v1-evidence",
                label: "Evidence",
                status: "blocked",
                value: 8,
                detail: "missing real proof artifacts",
                endpoint: "/v1/cartographer/v1-evidence",
              },
              {
                card_id: "v1-freeze-marker",
                label: "Freeze marker",
                status: "missing",
                value: "data/cartographer-v1-freeze/freeze-marker.json",
                detail: "external marker validation",
                endpoint: "/v1/cartographer/v1-freeze-marker-validation",
              },
              {
                card_id: "v1-authority",
                label: "Authority",
                status: "locked",
                value: "locked",
                detail: "passing checks do not grant authority",
                endpoint: "/v1/cartographer/v1-closeout-status",
              },
              {
                card_id: "v1-docs",
                label: "Evidence contract",
                status: "read_only",
                value: "docs/cartographer-v1-evidence-artifacts.md",
                detail: "human-recorded artifact shapes",
                endpoint: "/v1/cartographer/v1-closeout-dashboard",
              },
            ],
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            level: 1,
            mode: "dry_run",
            authority_granted: false,
            write_actions_enabled: false,
            apply_enabled: false,
            commit_enabled: false,
            push_enabled: false,
            docs_autopilot_daily_cap: 0,
            autopilot_kill_switch: true,
            candidate_count: 2,
            blockers: [],
            rollback_hints: ["No rollback needed for dry-run evidence; no files were written."],
            operator_review_required: true,
            recommended_next_action: "operator_review_required",
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            level: 2,
            mode: "api_contract_review_packet",
            contract_version: "cartographer.level_2.api_contract.v1",
            current_readiness: {
              label: "blocked",
              docs_apply_enabled: false,
              blocker_count: 2,
              blockers: ["level_1_review_gate", "dirty_tree_classified"],
            },
            dirty_tree_summary: {
              dirty_tree_block: true,
              unclassified_blocker_count: 42,
              blocking_policy: "any file outside explicit Level 2 docs/evidence classifications blocks apply",
            },
            required_apply_request_fields: ["proposal_id", "approval_id", "approval_actor"],
            required_receipt_fields: [
              "schema_version",
              "level",
              "proposal_id",
              "approval_id",
              "commit_created",
              "push_created",
              "branch_created",
              "rollback_command",
            ],
            forbidden_actions: [
              "apply without human approval",
              "source code edits",
              "commit creation",
              "push queue creation",
            ],
            manual_checks: [
              'PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_2 or apply"',
            ],
            expected_output: ["Level 2 readiness remains blocked."],
            next_increment: "Level 2 UI Review Card Read-Only Projection",
          }),
          { status: 200 },
        ),
      ) as typeof fetch;

    render(<HomelabCartographerWidget />);

    await waitFor(() => {
      expect(screen.getByText("Blocked by missing evidence")).toBeInTheDocument();
    });

    expect(globalThis.fetch).toHaveBeenCalledWith("/v1/cartographer/v1-closeout-dashboard", {
      cache: "no-store",
    });
    expect(globalThis.fetch).toHaveBeenCalledWith("/v1/cartographer/docs-autopilot/dry-run", {
      cache: "no-store",
    });
    expect(globalThis.fetch).toHaveBeenCalledWith("/v1/cartographer/level-2-api-contract", {
      cache: "no-store",
    });
    expect(screen.getByText("Autonomy level")).toBeInTheDocument();
    expect(screen.getAllByText("Level 1 candidate")).toHaveLength(2);
    expect(screen.getByText("Dry-run only")).toBeInTheDocument();
    expect(screen.getByText("Kill switch")).toBeInTheDocument();
    expect(screen.getByText("Daily cap 0")).toBeInTheDocument();
    expect(screen.getByText("Review")).toBeInTheDocument();
    expect(screen.getByText("2 proposals")).toBeInTheDocument();
    expect(screen.getByText("Apply / commit / push")).toBeInTheDocument();
    expect(screen.getByText("Disabled / Disabled / Disabled")).toBeInTheDocument();
    const mobileReview = within(screen.getByLabelText("Level 1 mobile review"));
    expect(mobileReview.getByText("Status")).toBeInTheDocument();
    expect(mobileReview.getByText("Blocker")).toBeInTheDocument();
    expect(mobileReview.getByText("Next")).toBeInTheDocument();
    expect(mobileReview.getByText("Evidence")).toBeInTheDocument();
    expect(mobileReview.getByText("None")).toBeInTheDocument();
    expect(screen.getByText("V1 readiness")).toBeInTheDocument();
    expect(screen.getAllByText("Evidence")).toHaveLength(2);
    expect(screen.getByText("Freeze marker")).toBeInTheDocument();
    expect(screen.getByText("Authority")).toBeInTheDocument();
    expect(screen.getByText("Evidence contract")).toBeInTheDocument();
    expect(screen.getByText("locked")).toBeInTheDocument();
    expect(screen.getByText("docs/cartographer-v1-evidence-artifacts.md")).toHaveAttribute(
      "title",
      "docs/cartographer-v1-evidence-artifacts.md",
    );
    expect(screen.getByText("data/cartographer-v1-freeze/freeze-marker.json")).toHaveAttribute(
      "title",
      "data/cartographer-v1-freeze/freeze-marker.json",
    );
    expect(screen.getAllByText("operator_review_required")).toHaveLength(2);
    expect(
      screen.getByText(
        "No rollback needed for dry-run evidence; no files were written. Approve, apply, commit, and push controls stay hidden.",
      ),
    ).toBeInTheDocument();
    const levelTwoReview = within(screen.getByLabelText("Level 2 human-approved docs apply"));
    expect(levelTwoReview.getByText("Human-approved docs apply")).toBeInTheDocument();
    expect(levelTwoReview.getByText("Blocked")).toBeInTheDocument();
    expect(levelTwoReview.getByText("blocked")).toBeInTheDocument();
    expect(levelTwoReview.getByText("Dirty blockers")).toBeInTheDocument();
    expect(levelTwoReview.getByText("42")).toBeInTheDocument();
    expect(levelTwoReview.getByText("Receipt fields")).toBeInTheDocument();
    expect(levelTwoReview.getByText("8")).toBeInTheDocument();
    expect(levelTwoReview.getByText("Commit disabled. Push disabled. Source edits disabled.")).toBeInTheDocument();
    expect(
      levelTwoReview.getByText("Rollback instructions are required in every approved proposal."),
    ).toBeInTheDocument();
    expect(
      levelTwoReview.getByText(
        'Manual check: PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_2 or apply"',
      ),
    ).toBeInTheDocument();
    expect(
      levelTwoReview.getByText("Blocker: level_1_review_gate. No Level 2 execution control is exposed here."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /approve|apply|push|commit/i })).toBeNull();
  });

  it("shows unavailable without exposing write controls when the bridge fails", async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            status: "unavailable",
            write_actions_enabled: false,
            error: "The dashboard could not reach the Source Proxy Cartographer endpoint.",
            dashboard_cards: [],
          }),
          { status: 200 },
        ),
      ),
    ) as typeof fetch;

    render(<HomelabCartographerWidget />);

    await waitFor(() => {
      expect(screen.getByText("Unavailable")).toBeInTheDocument();
    });

    expect(
      screen.getByText("The dashboard could not reach the Source Proxy Cartographer endpoint."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /approve|apply|push|commit/i })).toBeNull();
  });
});
