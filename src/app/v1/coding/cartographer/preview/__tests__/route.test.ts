/// <reference types="vitest/globals" />

import { POST } from "../route";

describe("coding Cartographer preview route", () => {
  it("returns read-only Cart status, evidence, and route protection", async () => {
    const response = await POST();

    await expect(response.json()).resolves.toMatchObject({
      activation_started: false,
      advisory_only: true,
      apply_authority: false,
      cart_lane_status: "control_preview_only",
      evidence_browser: {
        mode: "read_only_index",
        receipt_writes_enabled: false,
      },
      live_map_mutation_started: false,
      route_protection: [
        {
          authority: "read_only",
          method: "GET",
          route: "/v1/cartographer/live-state",
        },
        {
          authority: "blocked_preview_only",
          method: "POST",
          route: "/v1/cartographer/docs-autopilot/apply",
        },
        {
          authority: "blocked_preview_only",
          method: "POST",
          route: "/v1/cartographer/push-queue/{push_id}/approve",
        },
      ],
    });
    expect(response.status).toBe(200);
  });

  it("rejects queue, workflow, token, and live-map actions as preview only", async () => {
    const response = await POST();
    const payload = await response.json();

    expect(payload.approval_token_consumed).toBe(false);
    expect(payload.queue_worker_started).toBe(false);
    expect(payload.shell_command_started).toBe(false);
    expect(payload.token_action_plans).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          action: "queue_workflow_token_preview",
          rejection_proof: "approval_token_consumed=false; queue_worker_started=false",
          status: "rejected_preview_only",
        }),
        expect.objectContaining({
          action: "cart_live_map_activation",
          rejection_proof: "activation_started=false; live_map_mutation_started=false",
          status: "rejected_preview_only",
        }),
      ]),
    );
    expect(payload.preflight_readiness).toMatchObject({
      blockers: [
        "cart_activation_blocked",
        "queue_workflow_token_actions_preview_only",
        "approval_token_consumption_blocked",
      ],
      status: "blocked_until_explicit_plan_authority",
    });
  });
});
