import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { getSpiritFlixJobHistory, listSpiritFlixJobs, runSpiritFlixJobWorkerOnce } from "@/lib/spiritflix/admin/jobs";
import type { SpiritFlixFaceOrganizerDryRunResult } from "@/lib/spiritflix/admin/jobs";
import type { SpiritFlixSmartAnalysis } from "@/lib/spiritflix/admin/smart/types";
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

  function fakeAnalysis(): SpiritFlixSmartAnalysis {
    return {
      version: 1,
      videoPath,
      pathKey: "smart-rescan-analysis-key",
      fileName: "clip.mp4",
      fileSizeBytes: 10,
      mtimeMs: 123,
      analyzedAt: "2026-07-04T12:00:00.000Z",
      analyzerVersion: "spiritflix-smart/s2",
      status: "needs_review",
      safety: { safeToSuggest: false, reasons: ["test review"], requiresHumanReview: true },
      media: { codec: "h264", container: "mp4", durationSeconds: 90, width: 1280, height: 720 },
      samples: [{ timestampSeconds: 5, timestampLabel: "5s", cacheKey: "frame-a", observations: ["sampled frame"], tags: [], confidence: 0 }],
      suggestedTags: [],
      confidence: 0,
      notes: "technical metadata collected",
    };
  }

  function fakeFaceResult(): SpiritFlixFaceOrganizerDryRunResult {
    return {
      schema: "spiritflix-face-organizer-dry-run/v1",
      ok: true,
      command: "python3",
      args: ["scripts/media/face_organizer.py", "--scan-video", videoPath, "--dry-run"],
      code: 0,
      timedOut: false,
      stdout: JSON.stringify({ matchedModel: "Sava Schultz", confidence: 0.91, faceCount: 1 }),
      stderr: "",
      safety: { dryRun: true, apply: false, mediaMutation: false },
      match: {
        status: "high_confidence_match",
        matchedModel: "Sava Schultz",
        confidence: 0.91,
        faceCount: 1,
        parsed: true,
        reasonCode: "high_confidence_known_match",
      },
    };
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

  it("enqueues work that the safe worker can claim and process", async () => {
    const response = await post({ path: videoPath });
    const body = await response.json();

    const result = await runSpiritFlixJobWorkerOnce({ mediaRoot, jobId: body.jobId, scanVideo: async () => fakeAnalysis(), faceOrganizer: async () => fakeFaceResult() });

    expect(result).toEqual(expect.objectContaining({ claimed: true, completed: true, finalState: "ready" }));
    const history = await getSpiritFlixJobHistory(body.jobId, { mediaRoot });
    expect(history.events.map((event) => event.state)).toEqual(["queued", "scanning", "matching", "ready"]);
    expect(history.job?.details).toEqual(expect.objectContaining({ matchStatus: "high_confidence_match", matchedModel: "Sava Schultz" }));
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
