import { beforeEach, describe, expect, it, vi } from "vitest";
import { runSpiritFlixJobWorkerOnce } from "@/lib/spiritflix/admin/jobs";
import { POST } from "../jobs/worker/route";

vi.mock("@/lib/spiritflix/admin/jobs", () => ({
  runSpiritFlixJobWorkerOnce: vi.fn(),
}));

describe("SpiritFlix admin job worker API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("runs one no-media-mutation worker tick", async () => {
    vi.mocked(runSpiritFlixJobWorkerOnce).mockResolvedValue({
      schema: "spiritflix-admin-job-worker-run/v1",
      mode: "no_media_mutation",
      workerId: "admin-worker-api",
      claimed: true,
      completed: true,
      finalState: "needs_review",
      events: [],
    });

    const response = await POST(new Request("http://localhost/api/spiritflix/admin/jobs/worker", { method: "POST", body: "{}" }) as never);
    const body = await response.json();

    expect(response.status).toBe(202);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(body).toEqual(expect.objectContaining({ mode: "no_media_mutation", claimed: true }));
    expect(runSpiritFlixJobWorkerOnce).toHaveBeenCalledWith({ jobId: undefined, finalState: undefined, placeholderState: undefined, mode: "no_media_mutation", workerId: "admin-worker-api" });
  });

  it("returns 200 when no queued job is claimed", async () => {
    vi.mocked(runSpiritFlixJobWorkerOnce).mockResolvedValue({
      schema: "spiritflix-admin-job-worker-run/v1",
      mode: "no_media_mutation",
      workerId: "admin-worker-api",
      claimed: false,
      completed: false,
      reasonCode: "no_queued_jobs",
      events: [],
    });

    const response = await POST(new Request("http://localhost/api/spiritflix/admin/jobs/worker", { method: "POST", body: "{}" }) as never);
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.reasonCode).toBe("no_queued_jobs");
  });

  it("rejects invalid JSON without running the worker", async () => {
    const response = await POST(new Request("http://localhost/api/spiritflix/admin/jobs/worker", { method: "POST", body: "not-json" }) as never);
    expect(response.status).toBe(400);
    expect(runSpiritFlixJobWorkerOnce).not.toHaveBeenCalled();
  });
});
