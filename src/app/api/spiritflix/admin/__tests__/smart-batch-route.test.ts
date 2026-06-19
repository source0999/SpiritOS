import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { createSmartAnalysisPathKey, writeSmartAnalysis } from "@/lib/spiritflix/admin/smart";
import { validateSpiritFlixSmartAnalysis } from "@/lib/spiritflix/admin/smart/types";
import { GET, POST } from "../smart/batch/route";

let tempRoot = "";
let originalRoots: string | undefined;

function getRequest(targetPath: string) {
  return new Request(`http://localhost/api/spiritflix/admin/smart/batch?path=${encodeURIComponent(targetPath)}&maxItems=10`) as never;
}

function postRequest(body: Record<string, unknown>) {
  return new Request("http://localhost/api/spiritflix/admin/smart/batch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }) as never;
}

async function seedCurrent(videoPath: string) {
  const stat = await fs.stat(videoPath);
  await writeSmartAnalysis(validateSpiritFlixSmartAnalysis({
    version: 1,
    videoPath,
    pathKey: createSmartAnalysisPathKey({ videoPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs }),
    fileName: path.basename(videoPath),
    fileSizeBytes: stat.size,
    mtimeMs: stat.mtimeMs,
    analyzedAt: "2026-06-18T00:00:00.000Z",
    analyzerVersion: "spiritflix-smart/s5",
    status: "suggested",
    safety: { safeToSuggest: false, reasons: ["test"], requiresHumanReview: true },
    media: {},
    samples: [],
    suggestedTags: [{ id: "hd", label: "HD", group: "quality", confidence: 0.8, evidenceTimestamps: [], reviewRequired: false }],
    suggestedDisplayTitle: "Clip",
    suggestedFilename: "Clip Better.mp4",
    confidence: 0.4,
  }), { mediaRoot: tempRoot });
}

describe("SpiritFlix smart batch API", () => {
  beforeEach(async () => {
    originalRoots = process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
    tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-smart-batch-api-"));
    process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS = tempRoot;
    await fs.mkdir(path.join(tempRoot, "yes"), { recursive: true });
    await fs.writeFile(path.join(tempRoot, "yes/clip.mp4"), "fake-video");
    await fs.writeFile(path.join(tempRoot, "yes/note.txt"), "not-video");
  });

  afterEach(async () => {
    if (originalRoots === undefined) delete process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
    else process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS = originalRoots;
    await fs.rm(tempRoot, { force: true, recursive: true });
  });

  it("GET previews batch candidates for a folder", async () => {
    const response = await GET(getRequest(path.join(tempRoot, "yes")));
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.schema).toBe("spiritflix-smart-batch/v1");
    expect(body.mode).toBe("preview");
    expect(body.counts.candidates).toBe(1);
    expect(body.items[0].name).toBe("clip.mp4");
  });

  it("POST preview returns already_current for unchanged sidecars", async () => {
    const videoPath = path.join(tempRoot, "yes/clip.mp4");
    await seedCurrent(videoPath);

    const response = await POST(postRequest({ path: path.join(tempRoot, "yes"), action: "preview", maxItems: 10 }));
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.counts.already_current).toBe(1);
    expect(body.items[0].status).toBe("already_current");
  });

  it("rejects unsupported batch actions", async () => {
    const response = await POST(postRequest({ path: path.join(tempRoot, "yes"), action: "executeRename" }));
    const body = await response.json();

    expect(response.status).toBe(400);
    expect(body.error).toMatch(/unsupported/i);
  });

  it("batch approves tags through the review action", async () => {
    const videoPath = path.join(tempRoot, "yes/clip.mp4");
    await seedCurrent(videoPath);

    const response = await POST(postRequest({
      path: path.join(tempRoot, "yes"),
      action: "review",
      reviewMode: "approve_all_tags",
      maxItems: 10,
    }));
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.items[0].reviewStatus).toBe("reviewed");
    expect(body.counts.rename_preview_available).toBe(1);
  });

  it("exports a preview-only rename plan through the batch route", async () => {
    const videoPath = path.join(tempRoot, "yes/clip.mp4");
    await seedCurrent(videoPath);
    await POST(postRequest({
      path: path.join(tempRoot, "yes"),
      action: "review",
      reviewMode: "approve_all_tags",
      maxItems: 10,
    }));

    const response = await POST(postRequest({
      path: path.join(tempRoot, "yes"),
      action: "renamePlan",
      maxItems: 10,
    }));
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.schema).toBe("spiritflix-smart-rename-plan/v1");
    expect(body.applyEnabled).toBe(false);
    expect(body.items[0].suggestedName).toMatch(/HD\.mp4$/);
  });

  it("rejects unsupported review modes without stack traces", async () => {
    const response = await POST(postRequest({
      path: path.join(tempRoot, "yes"),
      action: "review",
      reviewMode: "rename_now",
    }));
    const body = await response.json();

    expect(response.status).toBe(400);
    expect(body.error).toMatch(/unsupported/i);
    expect(body.error).not.toMatch(/\n\s+at\s+/);
  });
});
