import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { createSmartAnalysisPathKey } from "../analysis-paths";
import { writeSmartAnalysis } from "../analysis-store";
import { buildSpiritFlixSmartRenamePlan } from "../rename-plan";
import { validateSpiritFlixSmartAnalysis, type SpiritFlixSmartAnalysis } from "../types";

let tempRoot = "";
let originalRoots: string | undefined;

async function writeVideo(relativePath: string, content = "fake-video") {
  const videoPath = path.join(tempRoot, relativePath);
  await fs.mkdir(path.dirname(videoPath), { recursive: true });
  await fs.writeFile(videoPath, content);
  return videoPath;
}

async function writeAnalysis(videoPath: string, overrides: Partial<SpiritFlixSmartAnalysis> = {}) {
  const stat = await fs.stat(videoPath);
  const analysis = validateSpiritFlixSmartAnalysis({
    version: 1,
    videoPath,
    pathKey: createSmartAnalysisPathKey({ videoPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs }),
    fileName: path.basename(videoPath),
    fileSizeBytes: stat.size,
    mtimeMs: stat.mtimeMs,
    analyzedAt: "2026-06-19T00:00:00.000Z",
    analyzerVersion: "spiritflix-smart/s8",
    status: "approved",
    safety: { safeToSuggest: false, reasons: ["test"], requiresHumanReview: true },
    media: {},
    samples: [],
    suggestedTags: [
      { id: "hd", label: "HD", group: "quality", confidence: 0.9, evidenceTimestamps: [], reviewRequired: false },
      { id: "watermark", label: "Watermark", group: "watermark", confidence: 0.7, evidenceTimestamps: [], reviewRequired: true },
    ],
    suggestedDisplayTitle: "Clean Clip",
    suggestedFilename: "suggested-from-scanner.mp4",
    confidence: 0.8,
    reviewedMetadata: {
      reviewedAt: "2026-06-19T00:00:00.000Z",
      reviewedBy: "spiritflix-admin",
      reviewStatus: "reviewed",
      approvedTagIds: ["hd"],
      rejectedTagIds: ["watermark"],
    },
    ...overrides,
  });
  await writeSmartAnalysis(analysis, { mediaRoot: tempRoot });
  return analysis;
}

describe("SpiritFlix smart rename plan", () => {
  beforeEach(async () => {
    originalRoots = process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
    tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-rename-plan-"));
    process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS = tempRoot;
  });

  afterEach(async () => {
    if (originalRoots === undefined) delete process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
    else process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS = originalRoots;
    await fs.rm(tempRoot, { force: true, recursive: true });
  });

  it("builds a preview-only plan from reviewed approved metadata", async () => {
    const videoPath = await writeVideo("yes/old.mp4");
    await writeAnalysis(videoPath, {
      reviewedMetadata: {
        reviewedAt: "2026-06-19T00:00:00.000Z",
        reviewedBy: "spiritflix-admin",
        reviewStatus: "reviewed",
        approvedTagIds: ["hd"],
        rejectedTagIds: ["watermark"],
        editedFilenameSuggestion: "Better Name.mp4",
      },
    });

    const plan = await buildSpiritFlixSmartRenamePlan({ path: path.join(tempRoot, "yes") });

    expect(plan.schema).toBe("spiritflix-smart-rename-plan/v1");
    expect(plan.applyEnabled).toBe(false);
    expect(plan.counts.ready).toBe(1);
    expect(plan.items[0]).toMatchObject({
      currentName: "old.mp4",
      suggestedName: "Better Name.mp4",
      readyForLevel2Preview: true,
      approvedTags: ["HD"],
      rejectedTagIds: ["watermark"],
    });
  });

  it("excludes rejected tags from generated filename suggestions", async () => {
    const videoPath = await writeVideo("yes/rejected-tag.mp4");
    await writeAnalysis(videoPath);

    const plan = await buildSpiritFlixSmartRenamePlan({ path: path.join(tempRoot, "yes") });

    expect(plan.items[0].suggestedName).toBe("Clean Clip HD.mp4");
    expect(plan.items[0].suggestedName).not.toMatch(/Watermark/i);
  });

  it("blocks unsafe sanitized filename suggestions", async () => {
    const videoPath = await writeVideo("yes/unsafe.mp4");
    await writeAnalysis(videoPath, {
      reviewedMetadata: {
        reviewedAt: "2026-06-19T00:00:00.000Z",
        reviewedBy: "spiritflix-admin",
        reviewStatus: "reviewed",
        approvedTagIds: ["hd"],
        rejectedTagIds: [],
        editedFilenameSuggestion: "../bad/name.mp4",
      },
    });

    const plan = await buildSpiritFlixSmartRenamePlan({ path: path.join(tempRoot, "yes") });

    expect(plan.items[0].status).toBe("blocked");
    expect(plan.items[0].warnings.join(" ")).toMatch(/slashes|traversal/i);
  });

  it("detects duplicate target names in the same plan", async () => {
    const first = await writeVideo("yes/a.mp4");
    const second = await writeVideo("yes/b.mp4");
    await writeAnalysis(first, {
      reviewedMetadata: {
        reviewedAt: "2026-06-19T00:00:00.000Z",
        reviewedBy: "spiritflix-admin",
        reviewStatus: "reviewed",
        approvedTagIds: ["hd"],
        rejectedTagIds: [],
        editedFilenameSuggestion: "Same Name.mp4",
      },
    });
    await writeAnalysis(second, {
      reviewedMetadata: {
        reviewedAt: "2026-06-19T00:00:00.000Z",
        reviewedBy: "spiritflix-admin",
        reviewStatus: "reviewed",
        approvedTagIds: ["hd"],
        rejectedTagIds: [],
        editedFilenameSuggestion: "Same Name.mp4",
      },
    });

    const plan = await buildSpiritFlixSmartRenamePlan({ path: path.join(tempRoot, "yes") });

    expect(plan.counts.collisions).toBe(2);
    expect(plan.items.every((item) => item.readyForLevel2Preview === false)).toBe(true);
  });

  it("detects existing target path conflicts", async () => {
    const videoPath = await writeVideo("yes/source.mp4");
    await writeVideo("yes/Existing.mp4");
    await writeAnalysis(videoPath, {
      reviewedMetadata: {
        reviewedAt: "2026-06-19T00:00:00.000Z",
        reviewedBy: "spiritflix-admin",
        reviewStatus: "reviewed",
        approvedTagIds: ["hd"],
        rejectedTagIds: [],
        editedFilenameSuggestion: "Existing.mp4",
      },
    });

    const plan = await buildSpiritFlixSmartRenamePlan({ path: path.join(tempRoot, "yes") });

    expect(plan.counts.target_conflicts).toBe(1);
    expect(plan.items.find((item) => item.currentName === "source.mp4")?.warnings).toContain("Target path already exists.");
  });

  it("skips unsupported or missing-analysis media instead of mutating files", async () => {
    await writeVideo("yes/no-analysis.mp4");
    await fs.writeFile(path.join(tempRoot, "yes/note.txt"), "not-video");

    const plan = await buildSpiritFlixSmartRenamePlan({ path: path.join(tempRoot, "yes") });

    expect(plan.counts.skipped).toBe(1);
    expect(plan.items[0].warnings).toContain("No smart analysis sidecar exists for this video.");
    expect(plan.applyEnabled).toBe(false);
  });
});
