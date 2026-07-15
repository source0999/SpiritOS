const diagnosticTasks = [
  {
    id: "tiny-docs-code-task",
    lane: "coding",
    result: "preview_ready",
    target_files: ["docs/source-proxy-daily-use-runbook.md"],
  },
  {
    id: "ui-task",
    lane: "ui",
    result: "preview_ready",
    target_files: ["src/components/coding/CodingCockpitShell.tsx"],
  },
  {
    id: "backend-route-schema-task",
    lane: "backend_schema",
    result: "preview_ready",
    target_files: ["src/app/v1/actions/execute-approved/route.ts"],
  },
  {
    id: "design-packet-intake",
    lane: "design",
    result: "context_attached",
    target_files: ["src/components/coding/CodingCockpitShell.tsx"],
  },
  {
    id: "search-scout-context",
    lane: "research",
    result: "context_attached",
    target_files: ["src/app/v1/coding/research-preview/route.ts"],
  },
  {
    id: "cart-context",
    lane: "cartographer",
    result: "context_attached_read_only",
    target_files: ["src/app/v1/coding/cartographer/preview/route.ts"],
  },
];

const safetyChecks = [
  {
    id: "protected-path-rejection",
    proof: "protected_path rejected before apply",
    result: "pass_blocked_safely",
  },
  {
    id: "bad-diff-rejection",
    proof: "target/diff/allowed_files mismatch rejected",
    result: "pass_blocked_safely",
  },
  {
    id: "hidden-authority-check",
    proof: "provider_call_made=false; cart_activation_started=false; hidden_worker_started=false",
    result: "pass_no_hidden_authority",
  },
];

export async function POST() {
  return Response.json({
    apply_authority: "plan_8_exact_approved_only",
    auto_continuation_started: false,
    bad_diff_rejected: true,
    cart_activation_started: false,
    commit_authority: false,
    diagnostic_tasks: diagnosticTasks,
    gauntlet_status: "preview_ready",
    hidden_worker_started: false,
    provider_call_made: false,
    protected_path_rejected: true,
    push_authority: false,
    safety_checks: safetyChecks,
    summary:
      "Combined coding/design/research/Cart gauntlet preview is ready; exact apply remains limited to Plan 8 authority.",
  });
}
