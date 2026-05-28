export async function POST() {
  return Response.json({
    activation_started: false,
    advisory_only: true,
    apply_authority: false,
    approval_token_consumed: false,
    cart_lane_status: "control_preview_only",
    commit_authority: false,
    evidence_browser: {
      mode: "read_only_index",
      receipt_writes_enabled: false,
      sources: [
        "docs/cartographer-live-evidence/",
        "docs/cartographer-live-receipts/",
        "data/cartographer-v1-freeze/freeze-marker.json",
      ],
    },
    live_map_mutation_started: false,
    preflight_readiness: {
      blockers: [
        "cart_activation_blocked",
        "queue_workflow_token_actions_preview_only",
        "approval_token_consumption_blocked",
      ],
      status: "blocked_until_explicit_plan_authority",
    },
    push_authority: false,
    queue_worker_started: false,
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
    shell_command_started: false,
    token_action_plans: [
      {
        action: "queue_workflow_token_preview",
        rejection_proof: "approval_token_consumed=false; queue_worker_started=false",
        status: "rejected_preview_only",
      },
      {
        action: "cart_live_map_activation",
        rejection_proof: "activation_started=false; live_map_mutation_started=false",
        status: "rejected_preview_only",
      },
    ],
  });
}
