import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SpiritFlixSmartBatchPanel } from "../SpiritFlixSmartBatchPanel";
import type { SpiritFlixSmartBatchItem, SpiritFlixSmartBatchPreview, SpiritFlixSmartRenamePlan } from "@/lib/spiritflix/admin/smart";

const longName = "A Very Long Clip Name With Many Words That Should Stay Readable Instead Of Collapsing Into One Letter Columns 2026 Final Cut.mp4";

function item(overrides: Partial<SpiritFlixSmartBatchItem>): SpiritFlixSmartBatchItem {
  return {
    path: "/mnt/spirit-8tb/media/yes/Beta Clip.mp4",
    name: "Beta Clip.mp4",
    parentPath: "/mnt/spirit-8tb/media/yes",
    extension: ".mp4",
    status: "candidate",
    sidecarCurrent: false,
    needsReview: false,
    suggestedTagCount: 0,
    tags: [],
    qualityBadges: [],
    modelName: "Unknown Model",
    modelSource: "unknown",
    visualTaggingAvailable: false,
    approvedTagCount: 0,
    rejectedTagCount: 0,
    pendingTagCount: 0,
    renamePreviewAvailable: false,
    reviewStatus: "unreviewed",
    renamePreviewStatus: "unavailable",
    renameWarnings: [],
    ...overrides,
  };
}

function batch(overrides: Partial<SpiritFlixSmartBatchPreview>): SpiritFlixSmartBatchPreview {
  const items = overrides.items ?? [];
  return {
    schema: "spiritflix-smart-batch/v1",
    generatedAt: "2026-06-19T12:00:00.000Z",
    mode: "preview",
    rootPath: "/mnt/spirit-8tb/media/yes",
    recursive: false,
    maxItems: 12,
    counts: {
      candidates: items.filter((entry) => entry.status === "candidate").length,
      analyzed: items.filter((entry) => entry.status === "analyzed").length,
      skipped: 0,
      already_current: items.filter((entry) => entry.status === "already_current").length,
      failed: items.filter((entry) => entry.status === "failed").length,
      needs_review: items.filter((entry) => entry.needsReview).length,
      rename_preview_available: items.filter((entry) => entry.renamePreviewAvailable).length,
    },
    visualContentTaggingEnabled: false,
    visualContentTaggingMessage: "Analyze folder samples frames and asks the local visual model for review-required content tags. No tags or names are applied until confirm.",
    items,
    ...overrides,
  };
}

const previewBatch = batch({
  mode: "preview",
  items: [item({ name: longName, path: `/mnt/spirit-8tb/media/yes/${longName}` })],
});

const analyzedBatch = batch({
  mode: "run",
  items: [
    item({
      status: "analyzed",
      sidecarCurrent: true,
      needsReview: true,
      analysisStatus: "needs_review",
      suggestedTagCount: 2,
      tags: [
        { id: "watermark", label: "Watermark", group: "watermark", confidence: 0.68, reviewRequired: true, reviewState: "pending" },
      ],
      qualityBadges: [{ id: "hd", label: "HD", group: "quality", confidence: 0.92, reviewRequired: false, reviewState: "pending" }],
      modelName: "Aaliyah Yasan",
      modelSource: "path",
      nameReason: "Aaliyah Yasan fallback uses model identity with Untitled 01 because the filename is random or ambiguous.",
      pendingTagCount: 1,
      renamePreviewStatus: "provisional",
      proposedFilename: "Aaliyah Yasan - Untitled 01",
      proposedTargetPath: "/mnt/spirit-8tb/media/yes/Beta Clip HD.mp4",
      renameBlocker: "Review or approve tags/metadata to unlock rename preview.",
      renameWarnings: ["Provisional preview, not eligible for apply until reviewed."],
      sidecarRef: "analysis/abc123def456.json",
    }),
  ],
});

const reviewedBatch = batch({
  mode: "run",
  items: [
    item({
      status: "analyzed",
      sidecarCurrent: true,
      needsReview: false,
      reviewStatus: "reviewed",
      analysisStatus: "approved",
      tags: [],
      qualityBadges: [{ id: "hd", label: "HD", group: "quality", confidence: 0.92, reviewRequired: false, reviewState: "approved" }],
      modelName: "Aaliyah Yasan",
      modelSource: "path",
      nameReason: "Readable title preserved; extension is kept only for target-path preview.",
      approvedTagCount: 0,
      renamePreviewAvailable: true,
      renamePreviewStatus: "ready",
      proposedFilename: "Beta Clip HD",
      proposedTargetPath: "/mnt/spirit-8tb/media/yes/Beta Clip HD.mp4",
    }),
  ],
});

const renamePlan: SpiritFlixSmartRenamePlan = {
  schema: "spiritflix-smart-rename-plan/v1",
  generatedAt: "2026-06-19T12:00:00.000Z",
  rootPath: "/mnt/spirit-8tb/media/yes",
  recursive: false,
  maxItems: 50,
  applyEnabled: false,
  applyGate: "Real rename/move apply is disabled until Britton explicitly approves a future apply task.",
  counts: {
    candidates: 1,
    ready: 1,
    blocked: 0,
    needs_review: 0,
    skipped: 0,
    collisions: 0,
    target_conflicts: 0,
  },
  items: [
    {
      sourcePath: "/mnt/spirit-8tb/media/yes/Beta Clip.mp4",
      currentName: "Beta Clip.mp4",
      suggestedName: "Beta Clip HD.mp4",
      targetPath: "/mnt/spirit-8tb/media/yes/Beta Clip HD.mp4",
      status: "ready",
      reviewStatus: "reviewed",
      approvedTags: ["HD"],
      rejectedTagIds: [],
      warnings: [],
      readyForLevel2Preview: true,
    },
  ],
};

describe("SpiritFlixSmartBatchPanel", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("renders preview candidates cleanly and tells the operator to analyze first", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(previewBatch));
    render(<SpiritFlixSmartBatchPanel currentPath="/mnt/spirit-8tb/media/yes" open onClose={() => undefined} />);

    fireEvent.click(screen.getByRole("button", { name: "Preview folder" }));

    expect(await screen.findByText(longName)).toBeInTheDocument();
    expect(screen.getAllByText("candidate").length).toBeGreaterThan(0);
    expect(screen.getByText("No tags yet - run Analyze folder")).toBeInTheDocument();
    expect(screen.getByText("Run Analyze folder first")).toBeInTheDocument();
    expect(screen.getByText(/local visual model/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Analyze folder first" })).toBeInTheDocument();
  });

  it("shows analyzed content tags, technical badges, and provisional recommended name messaging", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(analyzedBatch));
    render(<SpiritFlixSmartBatchPanel currentPath="/mnt/spirit-8tb/media/yes" open onClose={() => undefined} />);

    fireEvent.click(screen.getByRole("button", { name: "Analyze folder" }));

    expect(await screen.findByText("Watermark")).toBeInTheDocument();
    expect(screen.getAllByText("HD").length).toBeGreaterThan(0);
    expect(screen.getByText("Quality/technical")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Aaliyah Yasan - Untitled 01")).toBeInTheDocument();
    expect(screen.getByText("Aaliyah Yasan")).toBeInTheDocument();
    expect(screen.getByText("Provisional recommended name, not apply-ready")).toBeInTheDocument();
    expect(screen.getByText(/Why this name:/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Review/approve items to create final rename plan" })).toBeInTheDocument();
  });

  it("shows reviewed rows with ready recommended names", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(reviewedBatch));
    render(<SpiritFlixSmartBatchPanel currentPath="/mnt/spirit-8tb/media/yes" open onClose={() => undefined} />);

    fireEvent.click(screen.getByRole("button", { name: "Analyze folder" }));

    await waitFor(() => expect(screen.getAllByText("reviewed").length).toBeGreaterThan(0));
    expect(screen.getByDisplayValue("Beta Clip HD")).toBeInTheDocument();
    expect(screen.getByText("Ready recommended name")).toBeInTheDocument();
    expect(screen.getByText("Ready names")).toBeInTheDocument();
  });

  it("lets the operator edit and approve only the recommended name", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(analyzedBatch)).mockResolvedValueOnce(Response.json(reviewedBatch));
    render(<SpiritFlixSmartBatchPanel currentPath="/mnt/spirit-8tb/media/yes" open onClose={() => undefined} />);

    fireEvent.click(screen.getByRole("button", { name: "Analyze folder" }));

    const input = await screen.findByLabelText("Recommended name for Beta Clip.mp4");
    fireEvent.change(input, { target: { value: "Aaliyah Yasan - solo indoor 1" } });
    fireEvent.click(screen.getByRole("button", { name: "Approve name" }));

    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    expect(JSON.parse(String(vi.mocked(fetch).mock.calls[1][1]?.body))).toMatchObject({
      action: "review",
      reviewMode: "approve_name",
      editedFilenameSuggestion: "Aaliyah Yasan - solo indoor 1",
      paths: ["/mnt/spirit-8tb/media/yes/Beta Clip.mp4"],
    });
  });

  it("does not show technical metadata as primary Smart Tags", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(reviewedBatch));
    render(<SpiritFlixSmartBatchPanel currentPath="/mnt/spirit-8tb/media/yes" open onClose={() => undefined} />);

    fireEvent.click(screen.getByRole("button", { name: "Analyze folder" }));

    const smartTagHeading = await screen.findByText("Smart tags");
    const smartTagSection = smartTagHeading.closest("section") as HTMLElement;
    expect(within(smartTagSection).queryByText("HD")).not.toBeInTheDocument();
    expect(screen.getByText("Quality/technical")).toBeInTheDocument();
  });

  it("keeps diagnostics hidden by default and expands Advanced details on demand", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(analyzedBatch));
    render(<SpiritFlixSmartBatchPanel currentPath="/mnt/spirit-8tb/media/yes" open onClose={() => undefined} />);

    fireEvent.click(screen.getByRole("button", { name: "Analyze folder" }));

    await screen.findByText("Advanced details");
    const details = document.querySelector(".spiritflix-smart-batch__advanced") as HTMLDetailsElement;
    expect(details).not.toHaveAttribute("open");

    fireEvent.click(screen.getByText("Advanced details"));
    expect(details).toHaveAttribute("open");
    expect(screen.getByText("analysis/abc123def456.json")).toBeInTheDocument();
    expect(screen.getByText("Target path")).toBeInTheDocument();
  });

  it("uses CSS that prevents one-character filename columns", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(previewBatch));
    render(<SpiritFlixSmartBatchPanel currentPath="/mnt/spirit-8tb/media/yes" open onClose={() => undefined} />);

    fireEvent.click(screen.getByRole("button", { name: "Preview folder" }));

    const name = await screen.findByText(longName);
    expect(name).toHaveClass("spiritflix-smart-batch__name");
    expect(document.querySelector(".spiritflix-smart-batch__item-header")).toBeInTheDocument();
    expect(document.querySelector(".spiritflix-smart-batch__actions")).toBeInTheDocument();
  });

  it("shows preview-only rename plans without exposing real apply", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(Response.json(reviewedBatch)).mockResolvedValueOnce(Response.json(renamePlan));
    render(<SpiritFlixSmartBatchPanel currentPath="/mnt/spirit-8tb/media/yes" open onClose={() => undefined} />);

    fireEvent.click(screen.getByRole("button", { name: "Analyze folder" }));
    await screen.findByText("Ready recommended name");
    fireEvent.click(screen.getByRole("button", { name: "View rename plan" }));

    await waitFor(() => expect(screen.getByText("Real rename/move apply is disabled until Britton explicitly approves a future apply task.")).toBeInTheDocument());
    const renamePlanSection = screen.getByRole("heading", { name: "Rename plan" }).closest("section") as HTMLElement;
    expect(within(renamePlanSection).getByText("Beta Clip HD.mp4 - ready recommended name")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply rename/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply move/i })).not.toBeInTheDocument();
  });
});
