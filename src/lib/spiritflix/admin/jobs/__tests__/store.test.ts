import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  appendSpiritFlixJobState,
  createSpiritFlixJobVideoId,
  getSpiritFlixJobEventsPath,
  listSpiritFlixJobs,
} from "../store";

describe("SpiritFlix admin job store", () => {
  let mediaRoot = "";
  let videoPath = "";
  let mtimeMs = 0;
  let fileSizeBytes = 0;

  beforeEach(async () => {
    mediaRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-jobs-"));
    const videoDir = path.join(mediaRoot, "yes");
    await fs.mkdir(videoDir, { recursive: true });
    videoPath = path.join(videoDir, "clip.mp4");
    await fs.writeFile(videoPath, "fake-video");
    const stat = await fs.stat(videoPath);
    mtimeMs = stat.mtimeMs;
    fileSizeBytes = stat.size;
  });

  afterEach(async () => {
    await fs.rm(mediaRoot, { force: true, recursive: true });
  });

  function jobInput() {
    return { videoPath, fileSizeBytes, mtimeMs };
  }

  it("appends and reads durable JSONL job state", async () => {
    await appendSpiritFlixJobState({ ...jobInput(), state: "discovered" }, { mediaRoot });
    await appendSpiritFlixJobState({ ...jobInput(), state: "queued" }, { mediaRoot });

    const raw = await fs.readFile(getSpiritFlixJobEventsPath({ mediaRoot }), "utf8");
    expect(raw.trim().split("\n")).toHaveLength(2);

    const response = await listSpiritFlixJobs({ mediaRoot });
    expect(response.schema).toBe("spiritflix-admin-jobs/v1");
    expect(response.jobs).toHaveLength(1);
    expect(response.totalEventCount).toBe(2);
    expect(response.jobs[0]).toEqual(expect.objectContaining({
      state: "queued",
      attempt: 1,
      eventCount: 2,
      lastEventId: expect.stringMatching(/^sf-job-event-/),
    }));
  });

  it("validates job transitions", async () => {
    await appendSpiritFlixJobState({ ...jobInput(), state: "discovered" }, { mediaRoot });
    await expect(appendSpiritFlixJobState({ ...jobInput(), state: "moving" }, { mediaRoot })).rejects.toThrow(/transition/i);
  });

  it("prevents conflicting active jobs for the same video identity", async () => {
    await appendSpiritFlixJobState({ ...jobInput(), state: "queued", jobId: "sf-job-a" }, { mediaRoot });

    await expect(
      appendSpiritFlixJobState({ ...jobInput(), state: "queued", jobId: "sf-job-b" }, { mediaRoot }),
    ).rejects.toThrow(/active SpiritFlix job/i);
  });

  it("stores failed reasons and filters active jobs", async () => {
    await appendSpiritFlixJobState({ ...jobInput(), state: "queued" }, { mediaRoot });
    await appendSpiritFlixJobState({ ...jobInput(), state: "scanning" }, { mediaRoot });
    await appendSpiritFlixJobState({ ...jobInput(), state: "failed", errorReasonCode: "face_detector_exit", errorReason: "face detector exited 2" }, { mediaRoot });

    const allJobs = await listSpiritFlixJobs({ mediaRoot });
    expect(allJobs.jobs[0]).toEqual(expect.objectContaining({
      state: "failed",
      errorReasonCode: "face_detector_exit",
      errorReason: "face detector exited 2",
      eventCount: 3,
    }));

    const activeJobs = await listSpiritFlixJobs({ mediaRoot, activeOnly: true });
    expect(activeJobs.jobs).toHaveLength(0);
  });

  it("filters by video id", async () => {
    const videoId = createSpiritFlixJobVideoId(jobInput());
    await appendSpiritFlixJobState({ ...jobInput(), state: "queued" }, { mediaRoot });

    const response = await listSpiritFlixJobs({ mediaRoot, videoId });
    expect(response.jobs).toHaveLength(1);
    expect(response.jobs[0]?.videoId).toBe(videoId);
  });

  it("keeps append-only event counts readable across reloads and retries failed jobs", async () => {
    await appendSpiritFlixJobState({ ...jobInput(), state: "queued" }, { mediaRoot });
    await appendSpiritFlixJobState({ ...jobInput(), state: "scanning" }, { mediaRoot });
    await appendSpiritFlixJobState({ ...jobInput(), state: "failed", errorReasonCode: "scan_failed", errorReason: "scanner timed out" }, { mediaRoot });
    await appendSpiritFlixJobState({ ...jobInput(), state: "queued", worker: "operator-retry" }, { mediaRoot });

    const raw = await fs.readFile(getSpiritFlixJobEventsPath({ mediaRoot }), "utf8");
    expect(raw.trim().split("\n")).toHaveLength(4);
    const response = await listSpiritFlixJobs({ mediaRoot });
    expect(response.totalEventCount).toBe(4);
    expect(response.jobs[0]).toEqual(expect.objectContaining({ state: "queued", attempt: 2, eventCount: 4, worker: "operator-retry" }));
  });
});
