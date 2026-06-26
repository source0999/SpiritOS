/// <reference types="vitest/globals" />

import { POST } from "../route";

describe("coding helper agents preview route", () => {
  it("returns advisory helper roles with task and result packets", async () => {
    const response = await POST();

    await expect(response.json()).resolves.toMatchObject({
      advisory_only: true,
      apply_authority: false,
      commit_authority: false,
      dispatch_started: false,
      hidden_worker_started: false,
      helper_roles: [
        {
          authority_level: "advisory_read_only",
          id: "component-mapper",
          name: "Component Mapper",
        },
        {
          authority_level: "advisory_read_only",
          id: "safety-reviewer",
          name: "Safety Reviewer",
        },
        {
          authority_level: "advisory_read_only",
          id: "test-scribe",
          name: "Test Scribe",
        },
      ],
      lease_created: false,
      lock_created: false,
      plan4_route_status: "dormant",
      provider_call_made: false,
      push_authority: false,
      result_packets: [
        {
          helper_id: "component-mapper",
        },
        {
          helper_id: "safety-reviewer",
        },
        {
          helper_id: "test-scribe",
        },
      ],
      task_packets: [
        {
          helper_id: "component-mapper",
          mode: "read_only_context",
        },
        {
          helper_id: "safety-reviewer",
          mode: "read_only_safety",
        },
        {
          helper_id: "test-scribe",
          mode: "read_only_verification",
        },
      ],
      write_authority: false,
    });
    expect(response.status).toBe(200);
    expect(response.headers.get("x-spiritos-plan4-route-status")).toBe("dormant");
  });

  it("keeps conflicts visible instead of resolving them with hidden authority", async () => {
    const response = await POST();
    const payload = await response.json();

    expect(payload.conflicts).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          status: "visible_disagreement",
          title: "Scope suggestion vs safety boundary",
        }),
        expect.objectContaining({
          status: "authority_blocked",
          title: "Verification suggestion vs execution",
        }),
      ]),
    );
    expect(payload.timeline_events).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          helper_id: "component-mapper",
          source: "preview_route",
          status: "advisory_ready",
        }),
      ]),
    );
  });
});
