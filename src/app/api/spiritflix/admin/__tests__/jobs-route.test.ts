import { afterEach, describe, expect, it, vi } from "vitest";
import { listSpiritFlixJobs } from "@/lib/spiritflix/admin/jobs";
import { GET } from "../jobs/route";

vi.mock("@/lib/spiritflix/admin/jobs", () => ({
  listSpiritFlixJobs: vi.fn(),
}));

describe("SpiritFlix admin jobs API", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns durable job state with no-store caching", async () => {
    vi.mocked(listSpiritFlixJobs).mockResolvedValue({
      schema: "spiritflix-admin-jobs/v1",
      generatedAt: "2026-07-04T00:00:00.000Z",
      totalRecordCount: 1,
      totalEventCount: 2,
      query: { activeOnly: true, videoId: "video:abc" },
      jobs: [
        {
          schema: "spiritflix-admin-job/v1",
          jobId: "sf-job-abc",
          videoId: "video:abc",
          videoPath: "/mnt/spirit-8tb/media/yes/clip.mp4",
          fileName: "clip.mp4",
          fileSizeBytes: 10,
          mtimeMs: 100,
          state: "queued",
          attempt: 1,
          createdAt: "2026-07-04T00:00:00.000Z",
          updatedAt: "2026-07-04T00:00:00.000Z",
          eventCount: 2,
          lastEventId: "sf-job-event-2026-07-04T00:00:00.000Z-abcd1234",
        },
      ],
    });

    const response = await GET(new Request("http://localhost/api/spiritflix/admin/jobs?activeOnly=1&videoId=video%3Aabc") as never);
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(body.jobs[0]).toEqual(expect.objectContaining({ state: "queued", videoId: "video:abc" }));
    expect(body.jobs[0]).toEqual(expect.objectContaining({ eventCount: 2, lastEventId: expect.stringMatching(/^sf-job-event-/) }));
    expect(listSpiritFlixJobs).toHaveBeenCalledWith({ activeOnly: true, videoId: "video:abc" });
  });
});
