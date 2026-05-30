import { afterEach, describe, expect, it, vi } from "vitest";
import { GET, POST } from "../route";

vi.mock("@/lib/mac-worker/client", () => ({
  runMacWorkerJob: vi.fn().mockResolvedValue({
    job_id: "job-1",
    job_type: "trial_context_assist",
    node_id: "spirit-mac-mini",
    started_at: "2026-05-28T00:00:00.000Z",
    completed_at: "2026-05-28T00:00:01.000Z",
    success: true,
    result: { summary: "Mac searched repo context" },
    stdout: "",
    stderr: "",
    error: null,
    duration_ms: 1000,
    artifacts: [],
    candidate_files: ["src/lib/coding/agent-trials-ui.ts"],
    recommended_checks: ["git diff --check"],
  }),
}));

vi.mock("@/lib/mac-worker/registry", () => ({
  getMacWorkerStatus: vi.fn(() => ({
    node_id: "spirit-mac-mini",
    label: "Mac Mini",
    hostname: "spirit-mac-mini.local",
    ssh_alias: "spirit-mac-mini",
    role: "macos-worker",
    online: true,
    worker_available: true,
    repo_present: true,
    supported_job_types: ["trial_context_assist", "run_safe_check", "system_status"],
    last_job_type: "system_status",
    last_used_at: "2026-05-28T00:00:01.000Z",
    last_success: true,
    result_summary: "Mac worker status returned",
    error: null,
    last_reason_code: null,
    blocked_command: null,
    safe_checks_blocked: false,
  })),
}));

afterEach(() => {
  vi.restoreAllMocks();
});

describe("/api/coding/mac-worker", () => {
  it("returns registry status", async () => {
    const response = await GET();
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.status.node_id).toBe("spirit-mac-mini");
    expect(json.status.supported_job_types).toContain("trial_context_assist");
    expect(json.status).toMatchObject({
      online: true,
      worker_available: true,
      repo_present: true,
      last_success: true,
      safe_checks_blocked: false,
    });
  });

  it("runs a Mac job and returns recorded candidate files", async () => {
    const response = await POST(
      new Request("http://localhost/api/coding/mac-worker", {
        method: "POST",
        body: JSON.stringify({
          job_type: "trial_context_assist",
          input: { prompt: "fix the trial target discovery" },
        }),
      }),
    );
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.ok).toBe(true);
    expect(json.result.candidate_files).toEqual(["src/lib/coding/agent-trials-ui.ts"]);
  });

  it("rejects unsupported jobs instead of faking success", async () => {
    const response = await POST(
      new Request("http://localhost/api/coding/mac-worker", {
        method: "POST",
        body: JSON.stringify({ job_type: "dangerous_shell", input: {} }),
      }),
    );
    const json = await response.json();

    expect(response.status).toBe(400);
    expect(json.ok).toBe(false);
    expect(json.error).toContain("Unsupported");
  });
});
