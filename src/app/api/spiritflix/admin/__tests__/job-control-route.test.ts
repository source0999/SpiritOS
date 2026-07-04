import { afterEach, describe, expect, it, vi } from "vitest";
import { appendSpiritFlixJobState, getSpiritFlixJobHistory, reverseSpiritFlixOrganizeReceipt } from "@/lib/spiritflix/admin/jobs";
import { POST } from "../jobs/[jobId]/route";

vi.mock("@/lib/spiritflix/admin/jobs", () => ({
  appendSpiritFlixJobState: vi.fn(),
  failSpiritFlixJob: vi.fn(),
  getSpiritFlixJobHistory: vi.fn(),
  requeueSpiritFlixJob: vi.fn(),
  reverseSpiritFlixOrganizeReceipt: vi.fn(),
}));

describe("SpiritFlix admin job control API", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("reverses the latest worker move receipt and records a review state", async () => {
    vi.mocked(getSpiritFlixJobHistory).mockResolvedValue({
      schema: "spiritflix-admin-job-history/v1",
      generatedAt: "2026-07-04T00:00:00.000Z",
      jobId: "sf-job-abc",
      totalEventCount: 4,
      job: {
        schema: "spiritflix-admin-job/v1",
        jobId: "sf-job-abc",
        videoId: "video:abc",
        videoPath: "/media/yes/clip.mp4",
        fileName: "clip.mp4",
        fileSizeBytes: 10,
        mtimeMs: 100,
        state: "ready",
        attempt: 1,
        createdAt: "2026-07-04T00:00:00.000Z",
        updatedAt: "2026-07-04T00:00:00.000Z",
        eventCount: 4,
        lastEventId: "sf-job-event-abc",
        details: {
          organizeReceipt: {
            schema: "spiritflix-organize-receipt/v1",
            mode: "execute",
            allowed: true,
            sourcePath: "/media/yes/clip.mp4",
            targetPath: "/media/yes/Sava Schultz/clip.mp4",
            duplicateTarget: false,
            sourceBefore: { fileSizeBytes: 10, mtimeMs: 100 },
            rollback: { moveBackTo: "/media/yes/clip.mp4", removeCreatedTarget: "/media/yes/Sava Schultz/clip.mp4" },
            reasonCode: "high_confidence_preview_ready",
          },
        },
      },
      events: [],
    });
    vi.mocked(reverseSpiritFlixOrganizeReceipt).mockResolvedValue({
      schema: "spiritflix-organize-reverse-receipt/v1",
      sourcePath: "/media/yes/Sava Schultz/clip.mp4",
      restoredPath: "/media/yes/clip.mp4",
      sourceExistsBefore: true,
      restoredExistsAfter: true,
      receiptId: "sf-admin-receipt-reverse",
      reasonCode: "reversed",
    });
    vi.mocked(appendSpiritFlixJobState).mockResolvedValue({
      schema: "spiritflix-admin-job/v1",
      eventId: "sf-job-event-reverse",
      jobId: "sf-job-abc",
      videoId: "video:abc",
      videoPath: "/media/yes/clip.mp4",
      fileName: "clip.mp4",
      fileSizeBytes: 10,
      mtimeMs: 100,
      state: "needs_review",
      attempt: 1,
      createdAt: "2026-07-04T00:00:00.000Z",
      updatedAt: "2026-07-04T00:00:01.000Z",
      eventCount: 5,
      lastEventId: "sf-job-event-reverse",
    });

    const response = await POST(
      new Request("http://localhost/api/spiritflix/admin/jobs/sf-job-abc", {
        method: "POST",
        body: JSON.stringify({ action: "reverse_move" }),
      }) as never,
      { params: Promise.resolve({ jobId: "sf-job-abc" }) },
    );
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.action).toBe("reverse_move");
    expect(reverseSpiritFlixOrganizeReceipt).toHaveBeenCalledWith(expect.objectContaining({ targetPath: "/media/yes/Sava Schultz/clip.mp4" }));
    expect(appendSpiritFlixJobState).toHaveBeenCalledWith(expect.objectContaining({
      jobId: "sf-job-abc",
      state: "needs_review",
      details: expect.objectContaining({ action: "reverse_move", mediaMutation: true }),
    }));
  });
});
