const helperRoles = [
  {
    authority_level: "advisory_read_only",
    blocked_actions: ["write", "dispatch", "lease", "lock", "branch", "worktree", "provider_call"],
    id: "component-mapper",
    name: "Component Mapper",
    result_packet: {
      confidence: "medium",
      summary: "Maps the task to likely component, docs, and test zones for human review.",
    },
    task_packet: {
      mode: "read_only_context",
      purpose: "Suggest likely implementation areas without changing files.",
    },
  },
  {
    authority_level: "advisory_read_only",
    blocked_actions: ["approval", "apply", "commit", "push", "protected_path_relaxation"],
    id: "safety-reviewer",
    name: "Safety Reviewer",
    result_packet: {
      confidence: "high",
      summary: "Keeps allowed files, protected paths, and no-authority flags visible.",
    },
    task_packet: {
      mode: "read_only_safety",
      purpose: "Review scope and authority boundaries before preview.",
    },
  },
  {
    authority_level: "advisory_read_only",
    blocked_actions: ["test_execution", "package_install", "shell_expansion", "worker_start"],
    id: "test-scribe",
    name: "Test Scribe",
    result_packet: {
      confidence: "medium",
      summary: "Suggests focused checks after the exact files are known.",
    },
    task_packet: {
      mode: "read_only_verification",
      purpose: "Draft verification suggestions without running commands.",
    },
  },
];

const dormantRouteHeaders = {
  "x-spiritos-plan4-route-status": "dormant",
  "x-spiritos-plan4-canonical-replacement": "/v1/decisions/prompt-packet",
};

export async function POST() {
  return Response.json({
    advisory_only: true,
    apply_authority: false,
    commit_authority: false,
    conflicts: [
      {
        detail:
          "Component Mapper may suggest implementation zones; Safety Reviewer keeps protected paths blocked.",
        status: "visible_disagreement",
        title: "Scope suggestion vs safety boundary",
      },
      {
        detail:
          "Test Scribe can recommend checks, but shell execution remains a human-controlled chat action.",
        status: "authority_blocked",
        title: "Verification suggestion vs execution",
      },
    ],
    dispatch_started: false,
    helper_roles: helperRoles,
    hidden_worker_started: false,
    lease_created: false,
    lock_created: false,
    plan4_canonical_replacement: "/v1/decisions/prompt-packet",
    plan4_route_status: "dormant",
    provider_call_made: false,
    push_authority: false,
    result_packets: helperRoles.map((role) => ({
      helper_id: role.id,
      ...role.result_packet,
    })),
    task_packets: helperRoles.map((role) => ({
      helper_id: role.id,
      ...role.task_packet,
    })),
    timeline_events: helperRoles.map((role, index) => ({
      helper_id: role.id,
      index: index + 1,
      source: "preview_route",
      status: "advisory_ready",
      title: `${role.name} advisory packet ready`,
    })),
    write_authority: false,
  }, { headers: dormantRouteHeaders });
}
