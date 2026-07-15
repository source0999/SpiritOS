export async function POST() {
  return Response.json({
    accepted_packet_may_draft_coding_task: true,
    advisory_only: true,
    apply_authority: false,
    approval_authority: false,
    bounded_coding_task_draft: {
      allowed_files: ["src/components/coding/CodingCockpitShell.tsx"],
      blocked_until_human_accepts_design_packet: true,
      target_files: ["src/components/coding/CodingCockpitShell.tsx"],
      task: "Convert an accepted design packet into an exact bounded coding task draft.",
    },
    commit_authority: false,
    design_packet: {
      packet_id: "design-vault-preview-local",
      schema_version: "design_packet_preview_v1",
      source: "design_agent_or_vault_manual_packet",
      status: "preview_ready",
    },
    design_packet_state: {
      accept_available: true,
      accepted: false,
      reject_available: true,
      rejected: false,
    },
    drift_map: {
      component_drift: "review_required",
      css_mutation_authority: false,
      token_drift: "review_required",
    },
    hidden_execution_started: false,
    provider_call_made: false,
    push_authority: false,
    quality_bar: {
      criteria: [
        "exact route/component/CSS mapping",
        "clear visual intent",
        "no fake A-grade claim",
        "manual browser proof required before polish",
      ],
      standard: "AAA/Codex-like application standard",
      status: "ready_for_review",
    },
    route_component_css_map: [
      {
        component: "src/components/coding/CodingCockpitShell.tsx",
        css: "src/styles/dashboard-demo-v4.css",
        css_mutation_authority: false,
        route: "/coding",
      },
    ],
  });
}
