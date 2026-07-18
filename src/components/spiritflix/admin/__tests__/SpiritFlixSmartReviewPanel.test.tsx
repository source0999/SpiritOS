import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { SpiritFlixAdminItem } from "@/lib/spiritflix/admin/types";
import { SpiritFlixSmartReviewPanel } from "../SpiritFlixSmartReviewPanel";

vi.mock("@/lib/spiritflix/admin/approved-mutation-client", () => ({
  fetchApprovedSpiritFlixAdminMutation: async (
    _writer: string,
    url: string,
    mutation: Record<string, unknown>,
    init: RequestInit = {},
  ) => fetch(url, {
    ...init,
    body: JSON.stringify({ ...mutation, approval_id: "approval-component-test" }),
    headers: { "Content-Type": "application/json", ...init.headers },
    method: init.method ?? "POST",
  }),
}));

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
    status: "suggested",
    safety: { safeToSuggest: false, reasons: ["review"], requiresHumanReview: true },
    media: { durationSeconds: 120, width: 1920, height: 1080 },
    samples: [{ timestampSeconds: 10, timestampLabel: "10s", observations: ["sampled frame"], tags: [], confidence: 0 }],
    suggestedTags: [{ id: "full-hd", label: "full HD", group: "quality", confidence: 0.8, evidenceTimestamps: [], reviewRequired: false }],
    suggestedDisplayTitle: "Beta Clip",
    suggestedFilename: "Beta Clip - full HD.mp4",
    suggestedCategory: "yes",
    confidence: 0.8,
    notes: "heuristics only",
    reviewedMetadata: {
      reviewedAt: "2026-06-16T01:00:00.000Z",
      reviewedBy: "spiritflix-admin" as const,
      reviewStatus: "reviewed" as const,
      approvedTagIds: ["full-hd"],
      rejectedTagIds: [],
      editedDisplayTitle: "Beta Clip",
    },
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
          const body = JSON.parse(String(init.body));
          if (body.action === "saveReview") {
            return Response.json(analysisPayload);
          }
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

  it("renders approve/reject controls and metadata-only warning", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(analysisPayload));
    render(<SpiritFlixSmartReviewPanel item={video} open onClose={() => undefined} />);
    await screen.findByText(/confirms only metadata sidecars/i);
    expect(await screen.findByRole("button", { name: /Approve full HD/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Reject full HD/i })).toBeInTheDocument();
    expect(screen.getByText(/does not rename the file yet/i)).toBeInTheDocument();
  });

  it("approve tag updates local state", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(analysisPayload));
    render(<SpiritFlixSmartReviewPanel item={video} open onClose={() => undefined} />);
    await screen.findByRole("button", { name: /Reset full HD/i });
    fireEvent.click(screen.getByRole("button", { name: /Approve full HD/i }));
    expect(screen.getByText(/1 approved · 0 rejected · 0 pending/)).toBeInTheDocument();
  });

  it("reject tag updates local state", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      Response.json({
        ...analysisPayload,
        analysis: {
          ...analysisPayload.analysis,
          reviewedMetadata: undefined,
          suggestedTags: [
            { id: "hd", label: "HD", group: "quality", confidence: 0.7, evidenceTimestamps: [], reviewRequired: false },
          ],
        },
      }),
    );
    render(<SpiritFlixSmartReviewPanel item={video} open onClose={() => undefined} />);
    await screen.findByRole("button", { name: /Reject HD/i });
    fireEvent.click(screen.getByRole("button", { name: /Reject HD/i }));
    expect(screen.getByText(/0 approved · 1 rejected · 0 pending/)).toBeInTheDocument();
  });

  it("edited title input works", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(analysisPayload));
    render(<SpiritFlixSmartReviewPanel item={video} open onClose={() => undefined} />);
    const input = await screen.findByDisplayValue("Beta Clip");
    fireEvent.change(input, { target: { value: "Edited Beta" } });
    expect(screen.getByDisplayValue("Edited Beta")).toBeInTheDocument();
  });

  it("Save review calls saveReview API", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(analysisPayload));
    render(<SpiritFlixSmartReviewPanel item={video} open onClose={() => undefined} />);
    await screen.findByRole("button", { name: "Save review" });
    fireEvent.click(screen.getByRole("button", { name: "Save review" }));
    await waitFor(() => expect(vi.mocked(fetch)).toHaveBeenCalledTimes(2));
    expect(vi.mocked(fetch)).toHaveBeenLastCalledWith(
      "/api/spiritflix/admin/smart/analysis",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining('"action":"saveReview"'),
      }),
    );
  });

  it("confirm approved metadata calls confirmMetadata API", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(analysisPayload));
    render(<SpiritFlixSmartReviewPanel item={video} open onClose={() => undefined} />);
    await screen.findByRole("button", { name: "Confirm approved tags and name" });
    fireEvent.click(screen.getByRole("button", { name: "Confirm approved tags and name" }));
    await waitFor(() => expect(vi.mocked(fetch)).toHaveBeenCalledTimes(2));
    expect(vi.mocked(fetch)).toHaveBeenLastCalledWith(
      "/api/spiritflix/admin/smart/analysis",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining('"action":"confirmMetadata"'),
      }),
    );
  });

  it("reviewed status displays after save response", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(analysisPayload));
    render(<SpiritFlixSmartReviewPanel item={video} open onClose={() => undefined} />);
    await screen.findByText("Reviewed");
  });

  it("does not expose apply rename/move actions", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(analysisPayload));
    render(<SpiritFlixSmartReviewPanel item={video} open onClose={() => undefined} />);
    await screen.findByRole("button", { name: /Prepare rename preview/i });
    expect(screen.queryByRole("button", { name: /apply rename/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply move/i })).not.toBeInTheDocument();
  });
});
