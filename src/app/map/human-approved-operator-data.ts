export const humanApprovedOperatorStatusChips = [
  "Plan 2 display-only",
  "Human approval required",
  "No token runtime",
] as const;

export const humanApprovalRequiredFields = [
  {
    label: "Operator id",
    fallback: "missing-operator-id",
    blockedReason: "The requesting operator identity is not present.",
  },
  {
    label: "Approver id",
    fallback: "missing-approver-id",
    blockedReason: "The approving human identity is not present.",
  },
  {
    label: "Approval packet id",
    fallback: "missing-approval-packet-id",
    blockedReason: "No reviewed approval packet id is available.",
  },
  {
    label: "Run id",
    fallback: "missing-run-id",
    blockedReason: "No exact reviewed run id is available.",
  },
  {
    label: "Action type",
    fallback: "missing-action-type",
    blockedReason: "No exact display-only action type is available.",
  },
  {
    label: "Exact allowed files",
    fallback: "missing-allowed-files",
    blockedReason: "No exact allowed file list is available.",
  },
  {
    label: "Exact forbidden files",
    fallback: "missing-forbidden-files",
    blockedReason: "No exact forbidden file list is available.",
  },
  {
    label: "Approval expiry",
    fallback: "missing-expiry",
    blockedReason: "No bounded approval expiry is available.",
  },
  {
    label: "Rollback instructions",
    fallback: "missing-rollback",
    blockedReason: "No exact rollback instructions are available.",
  },
  {
    label: "Verification instructions",
    fallback: "missing-verification",
    blockedReason: "No exact verification instructions are available.",
  },
  {
    label: "Current HEAD",
    fallback: "missing-current-head",
    blockedReason: "No reviewed current HEAD is available.",
  },
  {
    label: "Expected dirty tree state",
    fallback: "missing-dirty-tree-state",
    blockedReason: "No expected dirty tree state is available.",
  },
  {
    label: "Kill switch state",
    fallback: "missing-kill-switch-state",
    blockedReason: "No reviewed kill switch state is available.",
  },
  {
    label: "Trust tier",
    fallback: "missing-trust-tier",
    blockedReason: "No reviewed trust tier is available.",
  },
  {
    label: "Human approval timestamp",
    fallback: "missing-human-approval-timestamp",
    blockedReason: "No human approval timestamp is available.",
  },
] as const;

export const humanApprovalBlockedStates = [
  {
    label: "Missing human approval",
    detail: "Plan 2 cannot proceed without explicit human approval for exact scope.",
  },
  {
    label: "Self-approval",
    detail: "Cartographer cannot approve its own action or token.",
  },
  {
    label: "Stale HEAD",
    detail: "Approval is blocked when current HEAD does not match the reviewed HEAD.",
  },
  {
    label: "Dirty-tree mismatch",
    detail: "Approval is blocked when dirty-tree state differs from the reviewed expectation.",
  },
  {
    label: "Expired approval",
    detail: "Approval is blocked when the approval expiry has passed.",
  },
  {
    label: "Kill switch blocked",
    detail: "Approval is blocked when the kill switch state is active or unknown.",
  },
  {
    label: "Missing rollback",
    detail: "Approval is blocked without concrete rollback instructions.",
  },
  {
    label: "Missing verification",
    detail: "Approval is blocked without concrete verification instructions.",
  },
] as const;

export const humanApprovedOperatorForbiddenActions = [
  "Approval-token runtime creation",
  "Approval-token storage",
  "Approval recording",
  "Self-approval",
  "Backend mutation endpoint calls",
  "Durable queue storage",
  "Durable event storage",
  "Queue execution",
  "Command execution through Cartographer",
  "Evidence writes",
  "Receipt writes",
  "Branch or worktree creation",
  "Commit, push, merge, stash, checkout, clean, or delete",
  "Runtime, test, dashboard, /coding, package, config, env, generated, Scout, API, or Source Proxy mutation",
  "Limited unattended operation",
  "Full auto",
] as const;

export const humanApprovedOperatorRecommendationPacket = {
  packet_id: "plan-2-human-approved-operator-display-only",
  status_date: "2026-05-22",
  packet_kind: "display-only-human-approved-operator",
  approval_state: "blocked-until-explicit-human-approval",
  fallback_reason: "No exact human-approved runtime packet exists in this display-only lane.",
  recommendation_summary:
    "Show approval requirements and blocked states only. Do not create tokens, approve actions, execute queues, run commands, write evidence, or promote authority.",
  manual_next_step:
    "Human operator must review the Plan 2 display-only implementation and explicitly approve any later authority expansion.",
  authority_denials: [
    "approval-token runtime is not approved",
    "durable queue storage is not approved",
    "durable event storage is not approved",
    "command execution is not granted",
    "queue execution is not granted",
    "limited unattended operation is not granted",
    "full auto is not granted",
  ],
} as const;

export const humanApprovalPacketShape = {
  packet_kind: "display-only-human-approved-operator",
  allowed_approval_states: [
    "blocked-until-explicit-human-approval",
    "missing-required-field",
    "fallback-display-only",
    "not-approved",
  ],
  required_top_level_fields: [
    "packet_id",
    "status_date",
    "packet_kind",
    "approval_state",
    "fallback_reason",
    "required_fields",
    "blocked_states",
    "forbidden_actions",
    "recommendation_summary",
    "manual_next_step",
    "authority_denials",
  ],
  forbidden_top_level_fields: [
    "approval_token",
    "approval_secret",
    "bearer_token",
    "queue_execution_state",
    "command",
    "shell",
    "apply_instruction",
    "write_instruction",
    "commit_instruction",
    "push_instruction",
  ],
} as const;

export const humanApprovalFallbackProof = [
  "Missing or incomplete approval packet data renders as blocked display state.",
  "Required fields include explicit fallback labels and blocked reasons.",
  "Packet shape lists allowed approval states and forbidden executable fields.",
  "Authority denials remain visible when approval data is unavailable.",
  "No approval token, queue execution, command execution, write instruction, or self-approval field is present.",
] as const;
