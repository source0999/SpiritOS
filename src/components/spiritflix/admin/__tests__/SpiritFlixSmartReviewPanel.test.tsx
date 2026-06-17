import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { SpiritFlixAdminItem } from "@/lib/spiritflix/admin/types";
import { SpiritFlixSmartReviewPanel } from "../SpiritFlixSmartReviewPanel";

const video: SpiritFlixAdminItem = {
  id: "file:clip",
  name: "Beta Clip.mp4",
  type: "file",
  path: "/mnt/spirit-8tb/media/yes/Beta Clip.mp4",
  parentPath: "/mnt/spirit-8tb/media/yes",
  playable: true,
  extension: ".mp4",
};

const analysisPayload = {
  analysis: {
    version: 1,
    videoPath: video.path,
    pathKey: "abc",
    fileName: "Beta Clip.mp4",
    fileSizeBytes: 100,
    mtimeMs: 1,
    analyzedAt: "2026-06-16T00:00:00.000Z",
    analyzerVersion: "spiritflix-smart/s3",
    status: "needs_review",
    safety: { safeToSuggest: false, reasons: ["review"], requiresHumanReview: true },
    media: { durationSeconds: 120, width: 1920, height: 1080 },
    samples: [{ timestampSeconds: 10, timestampLabel: "10s", observations: ["sampled frame"], tags: [], confidence: 0 }],
    suggestedTags: [{ id: "full-hd", label: "full HD", group: "quality", confidence: 0.8, evidenceTimestamps: [], reviewRequired: false }],
    suggestedDisplayTitle: "Beta Clip",
    suggestedFilename: "Beta Clip - full HD.mp4",
    suggestedCategory: "yes",
    confidence: 0.8,
    notes: "heuristics only",
  },
  sidecarPath: "/mnt/spirit-8tb/media/.spiritflix-admin/analysis/abc.json",
};

describe("SpiritFlixSmartReviewPanel", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("/api/spiritflix/admin/smart/analysis") && (!init || init.method === "GET")) {
          return Response.json({ analysis: null, sidecarPath: null });
        }
        if (url.includes("/api/spiritflix/admin/smart/analysis") && init?.method === "POST") {
          return Response.json(analysisPayload);
        }
        return Response.json({});
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("shows Analyze button when no analysis exists and does not auto-analyze on open", async () => {
    render(<SpiritFlixSmartReviewPanel item={video} open onClose={() => undefined} />);
    await screen.findByRole("dialog", { name: "Smart tag review" });
    expect(screen.getByRole("button", { name: "Analyze this video" })).toBeInTheDocument();
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(1);
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(expect.stringContaining("path="), expect.objectContaining({ method: "GET" }));
  });

  it("displays existing analysis suggestions", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(analysisPayload));
    render(<SpiritFlixSmartReviewPanel item={video} open onClose={() => undefined} />);
    await screen.findByText("Beta Clip");
    expect(screen.getByText("Beta Clip - full HD.mp4")).toBeInTheDocument();
    expect(screen.getByText("full HD")).toBeInTheDocument();
    expect(screen.getAllByText("80%")).toHaveLength(2);
  });

  it("calls smart analysis API only when Analyze is clicked", async () => {
    render(<SpiritFlixSmartReviewPanel item={video} open onClose={() => undefined} />);
    await screen.findByRole("button", { name: "Analyze this video" });
    fireEvent.click(screen.getByRole("button", { name: "Analyze this video" }));
    await waitFor(() => expect(vi.mocked(fetch)).toHaveBeenCalledTimes(2));
    expect(vi.mocked(fetch)).toHaveBeenLastCalledWith(
      "/api/spiritflix/admin/smart/analysis",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("does not expose apply rename/move actions", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(analysisPayload));
    render(<SpiritFlixSmartReviewPanel item={video} open onClose={() => undefined} />);
    await screen.findByText("Beta Clip");
    expect(screen.queryByRole("button", { name: /apply rename/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply move/i })).not.toBeInTheDocument();
  });
});
