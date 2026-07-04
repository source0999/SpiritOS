import { beforeEach, describe, expect, it, vi } from "vitest";
import { failSpiritFlixJob, getSpiritFlixJobHistory, requeueSpiritFlixJob } from "@/lib/spiritflix/admin/jobs";
import { GET, POST } from "../jobs/[jobId]/route";

vi.mock("@/lib/spiritflix/admin/jobs", () => ({
  failSpiritFlixJob: vi.fn(),
  getSpiritFlixJobHistory: vi.fn(),
  requeueSpiritFlixJob: vi.fn(),
}));

const job = {
  schema: "spiritflix-admin-job/v1" as const,
  jobId: "sf-job-abc",
  videoId: "video:abc",
  videoPath: "/mnt/spirit-8tb/media/yes/clip.mp4",
  fileName: "clip.mp4",
  fileSizeBytes: 10,
  mtimeMs: 100,
  state: "queued" as const,
  attempt: 1,
  createdAt: "2026-07-04T00:00:00.000Z",
  updatedAt: "2026-07-04T00:00:00.000Z",
  eventCount: 1,
  lastEventId: "sf-job-event-1",
};

function context(jobId = "sf-job-abc") {
  return { params: Promise.resolve({ jobId }) } as never;
}

function postBody(body: Record<string, unknown>) {
  return new Request("http://localhost/api/spiritflix/admin/jobs/sf-job-abc", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }) as never;
}

describe("SpiritFlix admin job detail API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns read-only job event history", async () => {
    vi.mocked(getSpiritFlixJobHistory).mockResolvedValue({
      schema: "spiritflix-admin-job-history/v1",
      generatedAt: "2026-07-04T00:00:00.000Z",
      jobId: "sf-job-abc",
      job,
      events: [{ ...job, eventId: "sf-job-event-1" }],
      totalEventCount: 1,
    });

    const response = await GET(new Request("http://localhost/api/spiritflix/admin/jobs/sf-job-abc") as never, context());
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(body.events).toHaveLength(1);
    expect(getSpiritFlixJobHistory).toHaveBeenCalledWith("sf-job-abc");
  });

  it("returns 404 when a job has no history", async () => {
    vi.mocked(getSpiritFlixJobHistory).mockResolvedValue({
      schema: "spiritflix-admin-job-history/v1",
      generatedAt: "2026-07-04T00:00:00.000Z",
      jobId: "missing",
      job: null,
      events: [],
      totalEventCount: 0,
    });

    const response = await GET(new Request("http://localhost/api/spiritflix/admin/jobs/missing") as never, context("missing"));
    expect(response.status).toBe(404);
  });

  it("appends a failed event through control-plane only", async () => {
    vi.mocked(failSpiritFlixJob).mockResolvedValue({
      schema: "spiritflix-admin-job-control/v1",
      action: "fail",
      job: { ...job, state: "failed", errorReasonCode: "operator_hold", errorReason: "manual hold" },
      event: { ...job, eventId: "sf-job-event-2", state: "failed", errorReasonCode: "operator_hold", errorReason: "manual hold" },
    });

    const response = await POST(postBody({ action: "fail", reasonCode: "operator_hold", reason: "manual hold" }), context());
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.action).toBe("fail");
    expect(failSpiritFlixJob).toHaveBeenCalledWith({ jobId: "sf-job-abc", reasonCode: "operator_hold", reason: "manual hold" });
  });

  it("appends a requeue event through control-plane only", async () => {
    vi.mocked(requeueSpiritFlixJob).mockResolvedValue({
      schema: "spiritflix-admin-job-control/v1",
      action: "requeue",
      job,
      event: { ...job, eventId: "sf-job-event-3", previousState: "failed" },
    });

    const response = await POST(postBody({ action: "requeue" }), context());
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.action).toBe("requeue");
    expect(requeueSpiritFlixJob).toHaveBeenCalledWith({ jobId: "sf-job-abc" });
  });

  it("rejects invalid control actions", async () => {
    const response = await POST(postBody({ action: "scan-now" }), context());
    expect(response.status).toBe(400);
    expect(failSpiritFlixJob).not.toHaveBeenCalled();
    expect(requeueSpiritFlixJob).not.toHaveBeenCalled();
  });
});
