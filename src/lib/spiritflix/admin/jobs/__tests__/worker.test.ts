import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { SpiritFlixFaceOrganizerDryRunResult } from "../face-organizer-bridge";
import type { SpiritFlixConversionReceipt } from "../conversion-bridge";
import type { SpiritFlixSmartAnalysis } from "../../smart/types";
import { appendSpiritFlixJobState, getSpiritFlixJobHistory, requeueSpiritFlixJob } from "../store";
import type { SpiritFlixJobWorkerConversionBridge, SpiritFlixJobWorkerFaceOrganizer, SpiritFlixJobWorkerScanVideo } from "../types";
import { claimNextSpiritFlixQueuedJob, runSpiritFlixJobWorkerOnce } from "../worker";

describe("SpiritFlix admin job worker", () => {
  let mediaRoot = "";
  let videoPath = "";
  let mtimeMs = 0;
  let fileSizeBytes = 0;

  beforeEach(async () => {
    mediaRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-worker-"));
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

  function fakeAnalysis(media: SpiritFlixSmartAnalysis["media"] = { codec: "h264", container: "mov,mp4,m4a,3gp,3g2,mj2", durationSeconds: 91, width: 1920, height: 1080 }): SpiritFlixSmartAnalysis {
    return {
      version: 1,
      videoPath,
      pathKey: "analysis-key",
      fileName: "clip.mp4",
      fileSizeBytes,
      mtimeMs,
      analyzedAt: new Date("2026-07-04T12:00:00.000Z").toISOString(),
      analyzerVersion: "spiritflix-smart/s2",
      status: "needs_review",
      safety: {
        safeToSuggest: false,
        reasons: ["test review"],
        requiresHumanReview: true,
      },
      media,
      samples: [
        { timestampSeconds: 5, timestampLabel: "5s", cacheKey: "frame-a", observations: ["sampled frame"], tags: [], confidence: 0 },
        { timestampSeconds: 45, timestampLabel: "45s", observations: ["sampled frame"], tags: [], confidence: 0 },
      ],
      suggestedTags: [],
      confidence: 0,
      notes: "technical metadata collected",
    };
  }

  function scannerReturning(analysis = fakeAnalysis()): SpiritFlixJobWorkerScanVideo {
    return vi.fn(async () => analysis);
  }

  function faceResult(overrides: Partial<SpiritFlixFaceOrganizerDryRunResult> = {}): SpiritFlixFaceOrganizerDryRunResult {
    return {
      schema: "spiritflix-face-organizer-dry-run/v1",
      ok: true,
      command: "python3",
      args: ["scripts/media/face_organizer.py", "--scan-video", videoPath, "--dry-run"],
      code: 0,
      timedOut: false,
      stdout: JSON.stringify({ matchedModel: "Sava Schultz", confidence: 0.93, faceCount: 1 }),
      stderr: "face stderr",
      safety: { dryRun: true, apply: false, mediaMutation: false },
      match: {
        status: "high_confidence_match",
        matchedModel: "Sava Schultz",
        confidence: 0.93,
        faceCount: 1,
        parsed: true,
        reasonCode: "high_confidence_known_match",
      },
      ...overrides,
    };
  }

  function faceOrganizerReturning(result = faceResult()): SpiritFlixJobWorkerFaceOrganizer {
    return vi.fn(async () => result);
  }

  function conversionReceipt(overrides: Partial<SpiritFlixConversionReceipt> = {}): SpiritFlixConversionReceipt {
    const outputPath = path.join(mediaRoot, ".spiritflix-admin", "conversions", "clip-mobile.mp4");
    return {
      schema: "spiritflix-conversion-receipt/v1",
      receiptId: "sf-conversion-test",
      jobId: "sf-job-test",
      status: "queued",
      mode: "enqueue",
      sourcePath: videoPath,
      outputPath,
      originalPreserved: true,
      sourceBefore: { fileSizeBytes, mtimeMs },
      command: "ffmpeg",
      args: ["-i", videoPath, outputPath],
      code: null,
      timedOut: false,
      stdout: "",
      stderr: "",
      rollback: { deleteOutputPath: outputPath, sourceUntouched: true },
      ...overrides,
    };
  }

  function conversionBridgeReturning(receipt = conversionReceipt()): SpiritFlixJobWorkerConversionBridge {
    return vi.fn(async () => receipt);
  }

  it("claims queued jobs and locks them from a second claim", async () => {
    const queued = await appendSpiritFlixJobState({ ...jobInput(), state: "queued" }, { mediaRoot });

    const first = await claimNextSpiritFlixQueuedJob({ mediaRoot, workerId: "worker-a" });
    const second = await claimNextSpiritFlixQueuedJob({ mediaRoot, workerId: "worker-b" });

    expect(first.claimed).toBe(true);
    expect(first.event).toEqual(expect.objectContaining({ state: "scanning", worker: "worker-a" }));
    expect(first.event?.details).toEqual(expect.objectContaining({ locked: true, mediaMutation: false, scanStarted: true, scanCompleted: false }));
    expect(second).toEqual(expect.objectContaining({ claimed: false, reasonCode: "no_queued_jobs" }));

    const history = await getSpiritFlixJobHistory(queued.jobId, { mediaRoot });
    expect(history.events.map((event) => event.state)).toEqual(["queued", "scanning"]);
  });

  it("runs scan and high-confidence face matching to ready when conversion is skipped", async () => {
    const scanVideo = scannerReturning();
    const faceOrganizer = faceOrganizerReturning();
    const queued = await appendSpiritFlixJobState({ ...jobInput(), state: "queued" }, { mediaRoot });

    const result = await runSpiritFlixJobWorkerOnce({ mediaRoot, workerId: "worker-a", scanVideo, faceOrganizer });

    expect(scanVideo).toHaveBeenCalledWith(videoPath, expect.objectContaining({ mediaRoot }));
    expect(faceOrganizer).toHaveBeenCalledWith(videoPath, expect.objectContaining({ sourceDir: mediaRoot }));
    expect(result).toEqual(expect.objectContaining({ claimed: true, completed: true, finalState: "ready" }));
    expect(result.events.map((event) => event.state)).toEqual(["scanning", "matching", "ready"]);
    expect(await fs.readFile(videoPath, "utf8")).toBe("fake-video");

    const history = await getSpiritFlixJobHistory(queued.jobId, { mediaRoot });
    expect(history.events.map((event) => event.state)).toEqual(["queued", "scanning", "matching", "ready"]);
    expect(history.events[2]?.details).toEqual(expect.objectContaining({
      analyzerVersion: "spiritflix-smart/s2",
      conversionDecision: "skip",
      conversionStarted: false,
      faceOrganizerDryRun: true,
      frameSampleCount: 1,
      matchConfidence: 0.93,
      matchedModel: "Sava Schultz",
      matchStatus: "high_confidence_match",
      mediaMutation: false,
      sampleCount: 2,
      scanCompleted: true,
    }));
    expect(history.job?.details).toHaveProperty("organizeReceipt.targetPath", path.join(mediaRoot, "yes", "Sava Schultz", "clip.mp4"));
    expect(history.job?.details).toHaveProperty("organizeReceipt.rollback.moveBackTo", videoPath);
    expect(history.job?.details).toHaveProperty("pendingEnrollment.sourceVideo", videoPath);
    expect(history.job?.details).toHaveProperty("pendingEnrollment.enabled", false);
    expect(history.job?.details).toEqual(expect.objectContaining({ autoMove: false, autoDbEnrollment: false, conversionStarted: false, mediaMutation: false }));
    const sidecar = JSON.parse(await fs.readFile(`${videoPath}.face-meta.json`, "utf8"));
    expect(sidecar).toEqual(expect.objectContaining({
      schema: "spiritflix-face-match-sidecar/v1",
      jobId: queued.jobId,
      matchStatus: "high_confidence_match",
      matchedModel: "Sava Schultz",
      confidence: 0.93,
    }));
  });

  it("auto-moves and auto-enrolls high-confidence matches only when env gates are enabled", async () => {
    const enrollmentBridge = vi.fn(async () => ({
      schema: "spiritflix-enrollment-receipt/v1" as const,
      status: "completed" as const,
      matchedModel: "Sava Schultz",
      confidence: 0.93,
      sourceVideo: path.join(mediaRoot, "yes", "Sava Schultz", "clip.mp4"),
      sidecarPath: `${videoPath}.face-meta.json`,
      minFaceScore: 0.86,
      command: "python3",
      args: [],
      code: 0,
      stdout: "enrolled",
      stderr: "",
      reasonCode: "enrolled",
    }));
    const queued = await appendSpiritFlixJobState({ ...jobInput(), state: "queued" }, { mediaRoot });

    const result = await runSpiritFlixJobWorkerOnce({
      mediaRoot,
      scanVideo: scannerReturning(),
      faceOrganizer: faceOrganizerReturning(),
      autoMove: true,
      autoEnroll: true,
      enrollmentBridge,
    });

    expect(result.finalState).toBe("ready");
    const history = await getSpiritFlixJobHistory(queued.jobId, { mediaRoot });
    const targetPath = path.join(mediaRoot, "yes", "Sava Schultz", "clip.mp4");
    expect(await fs.readFile(targetPath, "utf8")).toBe("fake-video");
    await expect(fs.stat(videoPath)).rejects.toThrow();
    expect(enrollmentBridge).toHaveBeenCalledWith(expect.objectContaining({
      matchedModel: "Sava Schultz",
      sourceVideo: targetPath,
      sidecarPath: `${videoPath}.face-meta.json`,
      minFaceScore: 0.86,
    }));
    expect(history.job?.details).toEqual(expect.objectContaining({ autoMove: true, autoDbEnrollment: true }));
    expect(history.job?.details).toHaveProperty("moveReceiptIds.before");
    expect(history.job?.details).toHaveProperty("moveReceiptIds.after");
    expect(history.job?.details).toHaveProperty("enrollmentReceipt.status", "completed");
  });

  it("keeps low-confidence face matches in needs_review", async () => {
    const faceOrganizer = faceOrganizerReturning(faceResult({
      stdout: JSON.stringify({ matchedModel: "Sava Schultz", confidence: 0.52, faceCount: 1 }),
      match: {
        status: "low_confidence_match",
        matchedModel: "Sava Schultz",
        confidence: 0.52,
        faceCount: 1,
        parsed: true,
        reasonCode: "low_confidence_match",
      },
    }));
    const queued = await appendSpiritFlixJobState({ ...jobInput(), state: "queued" }, { mediaRoot });

    const result = await runSpiritFlixJobWorkerOnce({ mediaRoot, scanVideo: scannerReturning(), faceOrganizer });

    expect(result.finalState).toBe("needs_review");
    const history = await getSpiritFlixJobHistory(queued.jobId, { mediaRoot });
    expect(history.events.map((event) => event.state)).toEqual(["queued", "scanning", "matching", "needs_review"]);
    expect(history.job?.details).toEqual(expect.objectContaining({ matchStatus: "low_confidence_match", matchConfidence: 0.52 }));
  });

  it("keeps no-face dry-run output in needs_review", async () => {
    const faceOrganizer = faceOrganizerReturning(faceResult({
      stdout: JSON.stringify({ status: "no_faces", faceCount: 0 }),
      match: {
        status: "no_faces",
        faceCount: 0,
        parsed: true,
        reasonCode: "no_faces_found",
      },
    }));
    const queued = await appendSpiritFlixJobState({ ...jobInput(), state: "queued" }, { mediaRoot });

    const result = await runSpiritFlixJobWorkerOnce({ mediaRoot, scanVideo: scannerReturning(), faceOrganizer });

    expect(result.finalState).toBe("needs_review");
    const history = await getSpiritFlixJobHistory(queued.jobId, { mediaRoot });
    expect(history.events.map((event) => event.state)).toEqual(["queued", "scanning", "matching", "needs_review"]);
    expect(history.job?.details).toEqual(expect.objectContaining({ matchStatus: "no_faces" }));
  });

  it("records conversion-needed state without starting conversion for non-mobile probe output", async () => {
    const scanVideo = scannerReturning(fakeAnalysis({ codec: "hevc", container: "matroska,webm", durationSeconds: 120 }));
    const queued = await appendSpiritFlixJobState({ ...jobInput(), state: "queued" }, { mediaRoot });

    const conversionBridge = conversionBridgeReturning();
    const result = await runSpiritFlixJobWorkerOnce({ mediaRoot, scanVideo, faceOrganizer: faceOrganizerReturning(), conversionBridge });

    expect(result.events.map((event) => event.state)).toEqual(["scanning", "converting", "needs_review"]);
    expect(conversionBridge).toHaveBeenCalledWith(expect.objectContaining({
      mediaRoot,
      jobId: queued.jobId,
      videoPath,
      mode: "enqueue",
    }));
    const history = await getSpiritFlixJobHistory(queued.jobId, { mediaRoot });
    expect(history.events.map((event) => event.state)).toEqual(["queued", "scanning", "converting", "needs_review"]);
    expect(history.events[2]?.details).toEqual(expect.objectContaining({
      conversionBridge: "worker_owned_conversion_bridge",
      conversionDecision: "queue_later",
      conversionReasonCode: "worker_conversion_required",
      conversionStatus: "queued",
      matchStatus: "high_confidence_match",
      mediaMutation: false,
      scanCompleted: true,
    }));
    expect(history.events[2]?.details).toHaveProperty("conversionReceipt.rollback.sourceUntouched", true);
  });

  it("marks conversion failure as failed with the receipt error", async () => {
    const scanVideo = scannerReturning(fakeAnalysis({ codec: "hevc", container: "matroska,webm", durationSeconds: 120 }));
    const failedConversion = conversionBridgeReturning(conversionReceipt({
      status: "failed",
      mode: "execute",
      code: 1,
      stderr: "ffmpeg exploded",
      errorReason: "ffmpeg exited with an error",
    }));
    const queued = await appendSpiritFlixJobState({ ...jobInput(), state: "queued" }, { mediaRoot });

    const result = await runSpiritFlixJobWorkerOnce({ mediaRoot, scanVideo, faceOrganizer: faceOrganizerReturning(), conversionBridge: failedConversion, conversionMode: "execute" });

    expect(result).toEqual(expect.objectContaining({ finalState: "failed", reasonCode: "conversion_failed" }));
    const history = await getSpiritFlixJobHistory(queued.jobId, { mediaRoot });
    expect(history.events.map((event) => event.state)).toEqual(["queued", "scanning", "failed"]);
    expect(history.job?.details).toHaveProperty("conversionReceipt.stderr", "ffmpeg exploded");
  });

  it("fails claimed jobs when the source disappears", async () => {
    const queued = await appendSpiritFlixJobState({ ...jobInput(), state: "queued" }, { mediaRoot });
    await fs.rm(videoPath);

    const result = await runSpiritFlixJobWorkerOnce({ mediaRoot, scanVideo: scannerReturning(), faceOrganizer: faceOrganizerReturning() });

    expect(result).toEqual(expect.objectContaining({ claimed: true, completed: true, finalState: "failed", reasonCode: "source_missing" }));
    const history = await getSpiritFlixJobHistory(queued.jobId, { mediaRoot });
    expect(history.events.map((event) => event.state)).toEqual(["queued", "scanning", "failed"]);
    expect(history.job).toEqual(expect.objectContaining({ errorReasonCode: "source_missing" }));
  });

  it("fails claimed jobs when the scanner fails", async () => {
    const scanVideo = vi.fn(async () => {
      throw new Error("ffprobe exited with an error.");
    });
    const queued = await appendSpiritFlixJobState({ ...jobInput(), state: "queued" }, { mediaRoot });

    const result = await runSpiritFlixJobWorkerOnce({ mediaRoot, scanVideo, faceOrganizer: faceOrganizerReturning() });

    expect(result).toEqual(expect.objectContaining({ finalState: "failed", reasonCode: "scan_failed" }));
    const history = await getSpiritFlixJobHistory(queued.jobId, { mediaRoot });
    expect(history.events.map((event) => event.state)).toEqual(["queued", "scanning", "failed"]);
    expect(history.job?.details).toEqual(expect.objectContaining({
      mediaMutation: false,
      scanCompleted: false,
      scannerError: "ffprobe exited with an error.",
    }));
  });

  it("fails claimed jobs when face organizer dry-run fails", async () => {
    const failedFaceOrganizer = faceOrganizerReturning(faceResult({
      ok: false,
      code: 2,
      stdout: "",
      stderr: "python traceback",
      match: {
        status: "command_failed",
        parsed: false,
        reasonCode: "face_organizer_failed",
      },
    }));
    const queued = await appendSpiritFlixJobState({ ...jobInput(), state: "queued" }, { mediaRoot });

    const result = await runSpiritFlixJobWorkerOnce({ mediaRoot, scanVideo: scannerReturning(), faceOrganizer: failedFaceOrganizer });

    expect(result).toEqual(expect.objectContaining({ finalState: "failed", reasonCode: "face_organizer_failed" }));
    const history = await getSpiritFlixJobHistory(queued.jobId, { mediaRoot });
    expect(history.events.map((event) => event.state)).toEqual(["queued", "scanning", "failed"]);
    expect(history.job?.details).toEqual(expect.objectContaining({
      matchStatus: "command_failed",
      mediaMutation: false,
      scanCompleted: true,
    }));
    expect(history.job?.details).toHaveProperty("faceOrganizer.stderr", "python traceback");
    expect(history.job?.details).toHaveProperty("faceOrganizer.code", 2);
  });

  it("retries failed jobs and lets the worker process the requeued attempt", async () => {
    const scanVideo = scannerReturning();
    const faceOrganizer = faceOrganizerReturning();
    const queued = await appendSpiritFlixJobState({ ...jobInput(), state: "queued" }, { mediaRoot });
    await runSpiritFlixJobWorkerOnce({ mediaRoot, finalState: "failed", failReasonCode: "scan_review_error", failReason: "test failure", scanVideo, faceOrganizer });
    await requeueSpiritFlixJob({ jobId: queued.jobId }, { mediaRoot });

    const result = await runSpiritFlixJobWorkerOnce({ mediaRoot, finalState: "ready", scanVideo, faceOrganizer });

    expect(result.finalState).toBe("ready");
    const history = await getSpiritFlixJobHistory(queued.jobId, { mediaRoot });
    expect(history.events.map((event) => event.state)).toEqual(["queued", "scanning", "matching", "failed", "queued", "scanning", "matching", "ready"]);
    expect(history.job).toEqual(expect.objectContaining({ state: "ready", attempt: 2 }));
  });
});
