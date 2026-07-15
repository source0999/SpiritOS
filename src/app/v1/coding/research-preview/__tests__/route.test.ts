/// <reference types="vitest/globals" />

import { POST } from "../route";

function jsonRequest(body: unknown): Request {
  return new Request("http://localhost/v1/coding/research-preview", {
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" },
    method: "POST",
  });
}

describe("coding research preview route", () => {
  it("normalizes an advisory research packet without granting authority", async () => {
    const response = await POST(
      jsonRequest({
        allowed_files: ["labs/coding/CodingCommandCenterShell.tsx"],
        prompt: "Attach Scout context to the coding cockpit.",
        research_sources: [
          {
            kind: "web",
            snippet: "Search result summary with source URL.",
            title: "SearXNG result",
            url: "https://example.test/result",
          },
        ],
        target_files: ["labs/coding/CodingCommandCenterShell.tsx"],
        task_id: "PLAN-4",
      }),
    );

    await expect(response.json()).resolves.toMatchObject({
      accepted_research_to_coding_handoff: true,
      advisory_only: true,
      allowed_files: ["labs/coding/CodingCommandCenterShell.tsx"],
      apply_authority: false,
      commit_authority: false,
      hidden_execution_started: false,
      human_review_required: true,
      mac_node: {
        health: "unverified",
        status: "blocked",
      },
      preview_only: true,
      plan4_route_status: "dormant",
      provider_call_made: false,
      push_authority: false,
      queue_worker_started: false,
      research_lane_status: "ready",
      research_packet_id: "research-PLAN-4",
      research_sources: [
        {
          kind: "web",
          title: "SearXNG result",
          url: "https://example.test/result",
        },
      ],
      scout_bridge: {
        import_mode: "manual_preview_only",
        packet_status: "preview_only",
      },
      search: {
        capability: "blocked_until_manual_json_health_check",
        status: "blocked",
      },
      shell_command_started: false,
      target_files: ["labs/coding/CodingCommandCenterShell.tsx"],
    });
    expect(response.status).toBe(200);
    expect(response.headers.get("x-spiritos-plan4-route-status")).toBe("dormant");
  });

  it("blocks incomplete packets instead of inventing search evidence", async () => {
    const response = await POST(jsonRequest({ prompt: "Research this task." }));

    await expect(response.json()).resolves.toMatchObject({
      accepted_research_to_coding_handoff: false,
      advisory_only: true,
      apply_authority: false,
      blocked_reasons: ["missing_target_files", "missing_allowed_files"],
      preview_only: true,
      provider_call_made: false,
      plan4_route_status: "dormant",
      research_lane_status: "blocked",
      research_sources: [
        {
          kind: "repo",
          title: "Source Proxy preflight roadmap",
          url: "docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md",
        },
      ],
    });
    expect(response.status).toBe(200);
    expect(response.headers.get("x-spiritos-plan4-route-status")).toBe("dormant");
  });

  it("keeps Mac, Scout, apply, commit, push, queue, and shell actions blocked", async () => {
    const response = await POST(
      jsonRequest({
        allowed_files: ["docs/source-proxy.md"],
        prompt: "Use the Scout packet as context only.",
        target_files: ["docs/source-proxy.md"],
      }),
    );
    const payload = await response.json();

    expect(payload.blocked_actions).toEqual(
      expect.arrayContaining([
        "autonomous_scout_discovery",
        "hidden_scheduled_search",
        "provider_model_call",
        "mac_service_control",
        "repo_write_from_mac",
        "cart_mutation",
        "approval",
        "apply",
        "commit",
        "push",
        "auto",
      ]),
    );
    expect(payload.apply_authority).toBe(false);
    expect(payload.commit_authority).toBe(false);
    expect(payload.push_authority).toBe(false);
    expect(payload.queue_worker_started).toBe(false);
    expect(payload.shell_command_started).toBe(false);
  });
});
