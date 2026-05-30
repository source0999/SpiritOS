/// <reference types="vitest/globals" />

import { POST } from "../route";

function jsonRequest(body: unknown): Request {
  return new Request("http://localhost/v1/coding/mac-advisory", {
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" },
    method: "POST",
  });
}

describe("coding Mac advisory route", () => {
  it("keeps route responses advisory-only without Source Proxy authority drift", async () => {
    const response = await POST(
      jsonRequest({
        input_summary: "Summarize a bounded docs packet.",
        job_id: "route-mac-docs",
        job_type: "docs_summary_packet",
      }),
    );
    const payload = await response.json();

    expect(response.status).toBe(200);
    expect(payload).toMatchObject({
      advisory_only: true,
      apply_authority: false,
      commit_authority: false,
      hidden_worker_started: false,
      mac_repo_write_authority: false,
      persistent_daemon_started: false,
      preview_only: true,
      provider_call_made: false,
      push_authority: false,
      source_proxy_authority_gate: true,
    });
    expect(payload.packet.repo_write_authority).toBe(false);
    expect(["completed", "blocked"]).toContain(payload.packet.status);
  });

  it("blocks unsupported job types through the packet contract", async () => {
    const response = await POST(
      jsonRequest({
        input_summary: "Please apply this from the Mac.",
        job_id: "route-mac-block",
        job_type: "apply_packet",
      }),
    );
    const payload = await response.json();

    expect(payload.packet.status).toBe("blocked");
    expect(payload.packet.repo_write_authority).toBe(false);
    expect(payload.hidden_worker_started).toBe(false);
    expect(payload.persistent_daemon_started).toBe(false);
  });
});
