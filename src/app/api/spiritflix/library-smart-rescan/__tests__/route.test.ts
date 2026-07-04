import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { listSpiritFlixJobs } from "@/lib/spiritflix/admin/jobs";
import { POST } from "../route";

describe("SpiritFlix library smart-rescan enqueue API", () => {
  let mediaRoot = "";
  let yesRoot = "";
  let videoPath = "";
  let previousAllowedRoots: string | undefined;
  let previousSmartRescanSource: string | undefined;

  beforeEach(async () => {
    previousAllowedRoots = process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
    previousSmartRescanSource = process.env.SPIRITFLIX_SMART_RESCAN_SOURCE;
    mediaRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-smart-rescan-"));
    yesRoot = path.join(mediaRoot, "yes");
    await fs.mkdir(yesRoot, { recursive: true });
    videoPath = path.join(yesRoot, "clip.mp4");
    await fs.writeFile(videoPath, "fake-video");
    process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS = mediaRoot;
    process.env.SPIRITFLIX_SMART_RESCAN_SOURCE = yesRoot;
  });

  afterEach(async () => {
    if (previousAllowedRoots === undefined) delete process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
    else process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS = previousAllowedRoots;
    if (previousSmartRescanSource === undefined) delete process.env.SPIRITFLIX_SMART_RESCAN_SOURCE;
    else process.env.SPIRITFLIX_SMART_RESCAN_SOURCE = previousSmartRescanSource;
    await fs.rm(mediaRoot, { recursive: true, force: true });
  });

  function post(body: Record<string, unknown>) {
    return POST(
      new Request("http://localhost/api/spiritflix/library-smart-rescan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }) as never,
    );
  }

  it("returns 202 and creates a queued durable job for a video target", async () => {
    const response = await post({ path: videoPath });
    const body = await response.json();

    expect(response.status).toBe(202);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(body).toEqual(
      expect.objectContaining({
        schema: "spiritflix-library-smart-rescan-enqueue/v1",
        state: "queued",
        generatedAt: expect.stringMatching(/^\d{4}-\d{2}-\d{2}T/),
        accepted: 1,
        duplicateExisting: 0,
        skipped: 0,
        jobId: expect.stringMatching(/^sf-job-/),
      }),
    );
    expect(body.jobs[0]).toEqual(
      expect.objectContaining({
        videoPath,
        fileName: "clip.mp4",
        state: "queued",
        worker: "library-smart-rescan",
        eventCount: 1,
        lastEventId: expect.stringMatching(/^sf-job-event-/),
        details: expect.objectContaining({
          autoMove: false,
          autoDbEnrollment: false,
          enqueueOnly: true,
          workerConsumed: false,
          reasonCode: "enqueue_requested",
          targetHash: expect.stringMatching(/^[a-f0-9]{24}$/),
        }),
      }),
    );

    const durable = await listSpiritFlixJobs({ mediaRoot, activeOnly: true });
    expect(durable.jobs).toHaveLength(1);
    expect(durable.jobs[0]).toEqual(expect.objectContaining({ jobId: body.jobId, state: "queued" }));
  });

  it("returns the existing active job for duplicate enqueue requests", async () => {
    const first = await post({ path: videoPath });
    const firstBody = await first.json();
    const second = await post({ path: videoPath });
    const secondBody = await second.json();

    expect(second.status).toBe(202);
    expect(secondBody.accepted).toBe(0);
    expect(secondBody.duplicateExisting).toBe(1);
    expect(secondBody.duplicates[0]).toEqual(
      expect.objectContaining({
        reasonCode: "active_job_exists",
        referencedJobId: firstBody.jobId,
        referencedEventCount: 1,
        job: expect.objectContaining({ jobId: firstBody.jobId, state: "queued" }),
      }),
    );

    const durable = await listSpiritFlixJobs({ mediaRoot });
    expect(durable.jobs).toHaveLength(1);
  });

  it("returns a safe 400 for invalid targets without creating jobs", async () => {
    const response = await post({ path: path.join(os.tmpdir(), "outside-spiritflix.mp4") });
    const body = await response.json();

    expect(response.status).toBe(400);
    expect(body).toEqual(
      expect.objectContaining({
        accepted: 0,
        duplicateExisting: 0,
        skipped: 1,
      }),
    );
    expect(body.skippedItems[0]).toEqual(expect.objectContaining({
      reasonCode: "invalid_target",
      source: "library-smart-rescan",
      targetHash: expect.stringMatching(/^[a-f0-9]{24}$/),
    }));

    const durable = await listSpiritFlixJobs({ mediaRoot });
    expect(durable.jobs).toHaveLength(0);
  });
});
