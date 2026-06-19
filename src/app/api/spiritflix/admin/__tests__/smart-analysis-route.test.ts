import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { writeSmartAnalysis } from "@/lib/spiritflix/admin/smart";
import { createSmartAnalysisPathKey } from "@/lib/spiritflix/admin/smart/analysis-paths";
import { validateSpiritFlixSmartAnalysis } from "@/lib/spiritflix/admin/smart/types";
import { GET, POST } from "../smart/analysis/route";

vi.mock("@/lib/spiritflix/admin/smart/review", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/spiritflix/admin/smart/review")>();
  return {
    ...actual,
    runSpiritFlixSmartReviewPipeline: vi.fn(),
    markSpiritFlixSmartAnalysisReviewed: vi.fn(),
  };
});

import { markSpiritFlixSmartAnalysisReviewed, runSpiritFlixSmartReviewPipeline } from "@/lib/spiritflix/admin/smart/review";

let tempRoot = "";
let originalRoots: string | undefined;
let videoPath = "";

function getRequest(targetPath: string) {
  return new Request(`http://localhost/api/spiritflix/admin/smart/analysis?path=${encodeURIComponent(targetPath)}`) as never;
}

function postRequest(body: Record<string, unknown>) {
  return new Request("http://localhost/api/spiritflix/admin/smart/analysis", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }) as never;
}

const sampleAnalysis = {
  version: 1 as const,
  videoPath: "",
  pathKey: "abc123",
  fileName: "clip.mp4",
  fileSizeBytes: 12,
  mtimeMs: 1,
  analyzedAt: "2026-06-16T00:00:00.000Z",
  analyzerVersion: "spiritflix-smart/s4",
  status: "needs_review" as const,
  safety: { safeToSuggest: false, reasons: [], requiresHumanReview: true },
  media: { durationSeconds: 90, width: 1280, height: 720 },
  samples: [{ timestampSeconds: 5, timestampLabel: "5s", observations: ["sampled frame"], tags: [], confidence: 0 }],
  suggestedTags: [{ id: "hd", label: "HD", group: "quality" as const, confidence: 0.8, evidenceTimestamps: [], reviewRequired: false }],
  suggestedDisplayTitle: "Clip",
  suggestedFilename: "Clip.mp4",
  confidence: 0.8,
  notes: "test",
};

async function seedAnalysis(mediaRoot: string) {
  const stat = await fs.stat(videoPath);
  const pathKey = createSmartAnalysisPathKey({ videoPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs });
  const analysis = validateSpiritFlixSmartAnalysis({
    ...sampleAnalysis,
    videoPath,
    fileSizeBytes: stat.size,
    mtimeMs: stat.mtimeMs,
    pathKey,
  });
  await writeSmartAnalysis(analysis, { mediaRoot });
  return analysis;
}

describe("SpiritFlix smart analysis API", () => {
  beforeEach(async () => {
    originalRoots = process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
    tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-smart-api-"));
    process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS = tempRoot;
    const videoDir = path.join(tempRoot, "yes");
    await fs.mkdir(videoDir, { recursive: true });
    videoPath = path.join(videoDir, "clip.mp4");
    await fs.writeFile(videoPath, "fake-video");
    vi.mocked(runSpiritFlixSmartReviewPipeline).mockReset();
    vi.mocked(markSpiritFlixSmartAnalysisReviewed).mockReset();
  });

  afterEach(async () => {
    if (originalRoots === undefined) delete process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
    else process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS = originalRoots;
    await fs.rm(tempRoot, { force: true, recursive: true });
  });

  it("GET returns null for missing sidecar", async () => {
    const response = await GET(getRequest(videoPath));
    const body = await response.json();
    expect(response.status).toBe(200);
    expect(body.analysis).toBeNull();
    expect(body.sidecarPath).toContain(".spiritflix-admin/analysis");
  });

  it("GET rejects traversal/outside root", async () => {
    const outside = await GET(getRequest("/etc/passwd"));
    expect(outside.status).toBe(400);
    const traversal = await GET(getRequest(`${tempRoot}${path.sep}..${path.sep}outside/clip.mp4`));
    expect(traversal.status).toBe(400);
  });

  it("POST analyze runs one-video pipeline and returns analysis", async () => {
    vi.mocked(runSpiritFlixSmartReviewPipeline).mockResolvedValue({ ...sampleAnalysis, videoPath });
    const response = await POST(postRequest({ path: videoPath, action: "analyze" }));
    const body = await response.json();
    expect(response.status).toBe(200);
    expect(body.analysis.suggestedDisplayTitle).toBe("Clip");
    expect(runSpiritFlixSmartReviewPipeline).toHaveBeenCalledWith(videoPath, expect.objectContaining({ mediaRoot: tempRoot }));
    expect(body.sidecarPath).toContain(".spiritflix-admin/analysis");
  });

  it("POST rejects folder path", async () => {
    const folderPath = path.join(tempRoot, "yes");
    const response = await POST(postRequest({ path: folderPath, action: "analyze" }));
    const body = await response.json();
    expect(response.status).toBe(400);
    expect(body.error).toMatch(/video file/i);
    expect(runSpiritFlixSmartReviewPipeline).not.toHaveBeenCalled();
  });

  it("POST is one-video only and does not call Level 2", async () => {
    const source = await fs.readFile(path.join(process.cwd(), "src/app/api/spiritflix/admin/smart/analysis/route.ts"), "utf8");
    expect(source).not.toMatch(/actions\/route|executeSpiritFlix|previewAction/i);
    vi.mocked(runSpiritFlixSmartReviewPipeline).mockResolvedValue({ ...sampleAnalysis, videoPath });
    await POST(postRequest({ path: videoPath }));
    expect(runSpiritFlixSmartReviewPipeline).toHaveBeenCalledTimes(1);
  });

  it("saveReview rejects unknown fields", async () => {
    await seedAnalysis(tempRoot);
    const response = await POST(
      postRequest({
        path: videoPath,
        action: "saveReview",
        review: { approvedTagIds: ["hd"], rejectedTagIds: [], evilField: true },
      }),
    );
    const body = await response.json();
    expect(response.status).toBe(400);
    expect(body.error).toMatch(/unknown field/i);
  });

  it("saveReview rejects unknown tag ids", async () => {
    await seedAnalysis(tempRoot);
    const response = await POST(
      postRequest({
        path: videoPath,
        action: "saveReview",
        review: { approvedTagIds: ["not-real"], rejectedTagIds: [] },
      }),
    );
    const body = await response.json();
    expect(response.status).toBe(400);
    expect(body.error).toMatch(/known tag id/i);
  });

  it("saveReview writes only analysis sidecar and preserves samples", async () => {
    await seedAnalysis(tempRoot);
    const response = await POST(
      postRequest({
        path: videoPath,
        action: "saveReview",
        review: {
          approvedTagIds: ["hd"],
          rejectedTagIds: [],
          editedDisplayTitle: "Reviewed Clip",
          editedFilenameSuggestion: "Reviewed Clip.mp4",
        },
      }),
    );
    const body = await response.json();
    expect(response.status).toBe(200);
    expect(body.analysis.reviewedMetadata.approvedTagIds).toEqual(["hd"]);
    expect(body.analysis.samples).toHaveLength(1);
    expect(body.analysis.suggestedDisplayTitle).toBe("Clip");
    expect(body.sidecarPath).toContain(".spiritflix-admin/analysis");
    expect(body.sidecarPath).not.toContain(path.dirname(videoPath));
    await expect(fs.stat(body.sidecarPath)).resolves.toBeDefined();
  });

  it("rejects applyRename and applyMove actions", async () => {
    const rename = await POST(postRequest({ path: videoPath, action: "applyRename" }));
    expect(rename.status).toBe(400);
    const move = await POST(postRequest({ path: videoPath, action: "applyMove" }));
    expect(move.status).toBe(400);
  });
});
