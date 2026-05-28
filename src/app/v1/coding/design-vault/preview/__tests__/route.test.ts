/// <reference types="vitest/globals" />

import { POST } from "../route";

describe("coding design vault preview route", () => {
  it("returns a preview-only design packet with accept/reject state", async () => {
    const response = await POST();

    await expect(response.json()).resolves.toMatchObject({
      advisory_only: true,
      apply_authority: false,
      approval_authority: false,
      design_packet: {
        schema_version: "design_packet_preview_v1",
        status: "preview_ready",
      },
      design_packet_state: {
        accept_available: true,
        accepted: false,
        reject_available: true,
        rejected: false,
      },
      hidden_execution_started: false,
      provider_call_made: false,
    });
    expect(response.status).toBe(200);
  });

  it("maps accepted design context to exact files without CSS mutation authority", async () => {
    const response = await POST();
    const payload = await response.json();

    expect(payload.route_component_css_map).toEqual([
      {
        component: "src/components/coding/CodingCommandCenterShell.tsx",
        css: "src/styles/dashboard-demo-v4.css",
        css_mutation_authority: false,
        route: "/coding",
      },
    ]);
    expect(payload.bounded_coding_task_draft).toMatchObject({
      allowed_files: ["src/components/coding/CodingCommandCenterShell.tsx"],
      blocked_until_human_accepts_design_packet: true,
      target_files: ["src/components/coding/CodingCommandCenterShell.tsx"],
    });
    expect(payload.drift_map).toMatchObject({
      component_drift: "review_required",
      css_mutation_authority: false,
      token_drift: "review_required",
    });
    expect(payload.quality_bar).toMatchObject({
      standard: "AAA/Codex-like application standard",
      status: "ready_for_review",
    });
  });
});
