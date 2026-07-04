import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { buildSpiritFlixFaceOrganizerDryRunArgs, parseSpiritFlixFaceOrganizerMatch, runSpiritFlixFaceOrganizerDryRun } from "../face-organizer-bridge";

describe("SpiritFlix face organizer dry-run bridge", () => {
  let tempRoot = "";
  let scriptPath = "";

  beforeEach(async () => {
    tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-face-bridge-"));
    scriptPath = path.join(tempRoot, "fake-face-organizer.js");
    await fs.writeFile(
      scriptPath,
      "process.stdout.write(JSON.stringify({ args: process.argv.slice(2) }));",
    );
  });

  afterEach(async () => {
    await fs.rm(tempRoot, { recursive: true, force: true });
  });

  it("builds a scan-video dry-run command without apply", () => {
    const args = buildSpiritFlixFaceOrganizerDryRunArgs("/media/clip.mp4", {
      scriptPath: "scripts/media/face_organizer.py",
      sourceDir: "/media",
      dbDir: "/db",
      frameCount: 2,
    });

    expect(args).toEqual([
      "scripts/media/face_organizer.py",
      "--scan-video",
      "/media/clip.mp4",
      "--dry-run",
      "--source",
      "/media",
      "--db",
      "/db",
      "--frame-count",
      "2",
    ]);
    expect(args).not.toContain("--apply");
  });

  it("runs through an injectable command and reports safety flags", async () => {
    const result = await runSpiritFlixFaceOrganizerDryRun("/media/clip.mp4", {
      command: process.execPath,
      scriptPath,
      sourceDir: "/media",
      timeoutMs: 5_000,
    });

    expect(result.ok).toBe(true);
    expect(result.safety).toEqual({ dryRun: true, apply: false, mediaMutation: false });
    expect(result.args).toContain("--dry-run");
    expect(result.args).not.toContain("--apply");
    expect(JSON.parse(result.stdout)).toEqual(expect.objectContaining({
      args: expect.arrayContaining(["--scan-video", "/media/clip.mp4", "--dry-run"]),
    }));
    expect(result.match.status).toBe("unknown");
  });

  it("parses high-confidence, low-confidence, and no-face structured dry-run output", () => {
    expect(parseSpiritFlixFaceOrganizerMatch({
      ok: true,
      stdout: JSON.stringify({ matchedModel: "Sava Schultz", confidence: 0.94, faceCount: 1 }),
      stderr: "",
      code: 0,
      timedOut: false,
    })).toEqual(expect.objectContaining({
      status: "high_confidence_match",
      matchedModel: "Sava Schultz",
      confidence: 0.94,
      reasonCode: "high_confidence_known_match",
    }));

    expect(parseSpiritFlixFaceOrganizerMatch({
      ok: true,
      stdout: JSON.stringify({ matchedModel: "Sava Schultz", confidence: 0.42, faceCount: 1 }),
      stderr: "",
      code: 0,
      timedOut: false,
    })).toEqual(expect.objectContaining({
      status: "low_confidence_match",
      matchedModel: "Sava Schultz",
      confidence: 0.42,
      reasonCode: "low_confidence_match",
    }));

    expect(parseSpiritFlixFaceOrganizerMatch({
      ok: true,
      stdout: JSON.stringify({ status: "no_faces", faceCount: 0 }),
      stderr: "",
      code: 0,
      timedOut: false,
    })).toEqual(expect.objectContaining({
      status: "no_faces",
      faceCount: 0,
      reasonCode: "no_faces_found",
    }));
  });

  it("parses the real dry-run JSON payload after InsightFace provider logs", () => {
    const stdout = `Applied providers: ['CPUExecutionProvider'], with options: {'CPUExecutionProvider': {}}\nset det-size: (640, 640)\n{\n  "video_path": "/tmp/live-face-proof.mp4",\n  "performers": [\n    {\n      "name": "unknown performer",\n      "confidence": 0.0,\n      "similarity": 0.0,\n      "status": "unknown",\n      "verification_needed": true\n    }\n  ]\n}`;

    expect(parseSpiritFlixFaceOrganizerMatch({
      ok: true,
      stdout,
      stderr: "dry-run: would write sidecar",
      code: 0,
      timedOut: false,
    })).toEqual(expect.objectContaining({
      status: "unknown",
      parsed: true,
      reasonCode: "face_organizer_unknown_performer",
    }));
  });
});
