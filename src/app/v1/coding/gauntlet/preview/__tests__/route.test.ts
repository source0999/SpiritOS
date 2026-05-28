/// <reference types="vitest/globals" />

import { POST } from "../route";

describe("coding gauntlet preview route", () => {
  it("returns combined coding, UI, backend, design, research, and Cart diagnostics", async () => {
    const response = await POST();

    await expect(response.json()).resolves.toMatchObject({
      apply_authority: "plan_8_exact_approved_only",
      auto_continuation_started: false,
      cart_activation_started: false,
      commit_authority: false,
      gauntlet_status: "preview_ready",
      hidden_worker_started: false,
      provider_call_made: false,
      push_authority: false,
      diagnostic_tasks: [
        { id: "tiny-docs-code-task", lane: "coding", result: "preview_ready" },
        { id: "ui-task", lane: "ui", result: "preview_ready" },
        { id: "backend-route-schema-task", lane: "backend_schema", result: "preview_ready" },
        { id: "design-packet-intake", lane: "design", result: "context_attached" },
        { id: "search-scout-context", lane: "research", result: "context_attached" },
        { id: "cart-context", lane: "cartographer", result: "context_attached_read_only" },
      ],
    });
    expect(response.status).toBe(200);
  });

  it("proves protected paths, bad diffs, and hidden authority are blocked", async () => {
    const response = await POST();
    const payload = await response.json();

    expect(payload.protected_path_rejected).toBe(true);
    expect(payload.bad_diff_rejected).toBe(true);
    expect(payload.safety_checks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "protected-path-rejection",
          result: "pass_blocked_safely",
        }),
        expect.objectContaining({
          id: "bad-diff-rejection",
          result: "pass_blocked_safely",
        }),
        expect.objectContaining({
          id: "hidden-authority-check",
          proof: "provider_call_made=false; cart_activation_started=false; hidden_worker_started=false",
          result: "pass_no_hidden_authority",
        }),
      ]),
    );
  });
});
