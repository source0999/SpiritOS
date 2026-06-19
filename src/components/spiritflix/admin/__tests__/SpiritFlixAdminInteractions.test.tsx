import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SPIRITFLIX_MEDIA_ROOT } from "@/lib/spiritflix/admin/constants";
import { SpiritFlixAdminApp } from "../SpiritFlixAdminApp";

function yesFolderPayload() {
  return {
    schema: "spiritflix-admin-fs/v1",
    generatedAt: "2026-06-16T12:00:00.000Z",
    root: `${SPIRITFLIX_MEDIA_ROOT}/yes`,
    currentPath: `${SPIRITFLIX_MEDIA_ROOT}/yes`,
    breadcrumbs: [{ name: "yes", path: `${SPIRITFLIX_MEDIA_ROOT}/yes` }],
    totalRecordCount: 2,
    items: [
      {
        id: "file:/mnt/spirit-8tb/media/yes/Beta Clip.mp4",
        name: "Beta Clip.mp4",
        type: "file",
        path: "/mnt/spirit-8tb/media/yes/Beta Clip.mp4",
        parentPath: "/mnt/spirit-8tb/media/yes",
        extension: ".mp4",
        sizeBytes: 2048,
        dateModified: "2026-06-16T12:00:00.000Z",
        playable: true,
      },
      {
        id: "file:/mnt/spirit-8tb/media/yes/Alpha Clip.mkv",
        name: "Alpha Clip.mkv",
        type: "file",
        path: "/mnt/spirit-8tb/media/yes/Alpha Clip.mkv",
        parentPath: "/mnt/spirit-8tb/media/yes",
        extension: ".mkv",
        sizeBytes: 1024,
        dateModified: "2026-06-14T12:00:00.000Z",
        playable: true,
      },
    ],
  };
}

function mockAdminFetch() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.startsWith("/api/spiritflix/admin/jellyfin-index")) {
        return Response.json({ items: [], source: "unconfigured" });
      }
      if (url.startsWith("/api/spiritflix/admin/thumbnail")) {
        return new Response(new Blob([new Uint8Array([0xff, 0xd8, 0xff, 0xd9])]), { status: 200, headers: { "Content-Type": "image/jpeg" } });
      }
      if (url.startsWith("/api/spiritflix/admin/fs")) {
        return Response.json(yesFolderPayload());
      }
      if (url.startsWith("/api/spiritflix/admin/smart/analysis")) {
        return Response.json({ analysis: null, sidecarPath: null });
      }
      if (url.startsWith("/api/spiritflix/admin/smart/batch")) {
        const body = init?.body ? JSON.parse(String(init.body)) as { action?: string } : {};
        if (body.action === "renamePlan") {
          return Response.json({
            schema: "spiritflix-smart-rename-plan/v1",
            generatedAt: "2026-06-18T12:00:00.000Z",
            rootPath: `${SPIRITFLIX_MEDIA_ROOT}/yes`,
            recursive: false,
            maxItems: 50,
            applyEnabled: false,
            applyGate: "Preview/export only. Real rename or move must use a future explicit Level 2 apply task.",
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
          });
        }
        return Response.json({
          schema: "spiritflix-smart-batch/v1",
          generatedAt: "2026-06-18T12:00:00.000Z",
          mode: "preview",
          rootPath: `${SPIRITFLIX_MEDIA_ROOT}/yes`,
          recursive: false,
          maxItems: 12,
          counts: {
            candidates: 2,
            analyzed: 0,
            skipped: 0,
            already_current: 0,
            failed: 0,
            needs_review: 0,
            rename_preview_available: 0,
          },
          items: [
            {
              path: "/mnt/spirit-8tb/media/yes/Beta Clip.mp4",
              name: "Beta Clip.mp4",
              parentPath: "/mnt/spirit-8tb/media/yes",
              extension: ".mp4",
              status: "candidate",
              sidecarCurrent: false,
              needsReview: false,
              suggestedTagCount: 0,
              renamePreviewAvailable: false,
              reviewStatus: "unreviewed",
            },
          ],
        });
      }
      return Response.json({ items: [] });
    }),
  );
}

describe("SpiritFlix admin Level 2R interactions", () => {
  beforeEach(() => {
    window.localStorage.clear();
    Object.defineProperty(URL, "createObjectURL", { configurable: true, value: vi.fn(() => "blob:thumb") });
    Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: vi.fn() });
    mockAdminFetch();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  async function openYesFolder() {
    render(<SpiritFlixAdminApp />);
    fireEvent.click(screen.getByRole("button", { name: "yes" }));
    await screen.findAllByTestId("admin-item-card");
  }

  it("renders a 3-dot menu button on video cards", async () => {
    await openYesFolder();
    expect(screen.getByRole("button", { name: "Actions for Beta Clip.mp4" })).toBeInTheDocument();
  });

  it("selects a card on single click without opening details", async () => {
    await openYesFolder();
    const card = screen.getAllByTestId("admin-item-card").find((entry) => entry.textContent?.includes("Alpha Clip.mkv"));
    expect(card).toBeTruthy();
    fireEvent.click(card as HTMLElement);
    expect(card).toHaveClass("is-selected");
    expect(screen.queryByLabelText("Admin details")).not.toBeInTheDocument();
    expect(screen.getAllByTestId("admin-item-card").length).toBeGreaterThan(0);
  });

  it("opens the 3-dot menu with CRUD actions for a video", async () => {
    await openYesFolder();
    fireEvent.click(screen.getByRole("button", { name: "Actions for Beta Clip.mp4" }));
    expect(screen.getByRole("menu", { name: "File actions" })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "Rename" })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "Move" })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "Soft delete" })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "Edit metadata" })).toBeInTheDocument();
    expect(screen.queryByRole("menuitem", { name: /hard delete/i })).not.toBeInTheDocument();
  });

  it("opens context menu on right-click and prevents default", async () => {
    await openYesFolder();
    const card = screen.getAllByTestId("admin-item-card").find((entry) => entry.textContent?.includes("Beta Clip.mp4"));
    const prevented = vi.fn();
    fireEvent.contextMenu(card as HTMLElement, { preventDefault: prevented });
    expect(screen.getByRole("menu", { name: "File actions" })).toBeInTheDocument();
  });

  it("opens details only from Info menu action", async () => {
    await openYesFolder();
    fireEvent.click(screen.getByRole("button", { name: "Actions for Alpha Clip.mkv" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Info" }));
    expect(screen.getByLabelText("Admin details")).toHaveTextContent("Alpha Clip.mkv");
    expect(screen.getAllByTestId("admin-item-card").length).toBe(2);
  });

  it("opens rename action dialog from card menu", async () => {
    await openYesFolder();
    fireEvent.click(screen.getByRole("button", { name: "Actions for Beta Clip.mp4" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Rename" }));
    expect(screen.getByRole("dialog", { name: "SpiritFlix admin actions" })).toHaveTextContent(/Rename/i);
    expect(screen.getByRole("button", { name: "Preview rename" })).toBeInTheDocument();
  });

  it("opens soft delete action dialog from card menu with auto-preview", async () => {
    await openYesFolder();

    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.startsWith("/api/spiritflix/admin/actions")) {
        return Response.json({
          schema: "spiritflix-admin-action/v1",
          action: "softDelete",
          phase: "preview",
          previewId: "preview-soft",
          allowed: true,
          message: "Move item to soft trash",
          preview: { affectedPaths: ["/mnt/spirit-8tb/media/yes/Beta Clip.mp4"], warnings: ["Soft delete moves to SpiritFlix trash, not permanent delete."] },
        });
      }
      if (url.startsWith("/api/spiritflix/admin/fs")) {
        return Response.json(yesFolderPayload());
      }
      if (url.startsWith("/api/spiritflix/admin/jellyfin-index")) {
        return Response.json({ items: [], source: "unconfigured" });
      }
      if (url.startsWith("/api/spiritflix/admin/thumbnail")) {
        return new Response(new Blob([new Uint8Array([0xff, 0xd8, 0xff, 0xd9])]), { status: 200, headers: { "Content-Type": "image/jpeg" } });
      }
      return Response.json({ items: [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    fireEvent.click(screen.getByRole("button", { name: "Actions for Beta Clip.mp4" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Soft delete" }));
    expect(screen.getByRole("dialog", { name: "SpiritFlix admin actions" })).toHaveTextContent(/Soft delete/i);
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith("/api/spiritflix/admin/actions", expect.anything());
      expect(screen.getByRole("button", { name: "Confirm — move to trash" })).toBeEnabled();
      expect(screen.getByText("Affected paths:")).toBeInTheDocument();
      expect(screen.getAllByText("/mnt/spirit-8tb/media/yes/Beta Clip.mp4").length).toBeGreaterThan(0);
    });
  });

  it("preserves scroll position after selecting an item", async () => {
    await openYesFolder();
    const explorer = document.querySelector(".spiritflix-admin-explorer") as HTMLElement;
    Object.defineProperty(explorer, "scrollTop", { configurable: true, value: 240, writable: true });
    explorer.scrollTop = 240;

    const card = screen.getAllByTestId("admin-item-card")[0];
    fireEvent.click(card);
    await waitFor(() => {
      expect(explorer.scrollTop).toBe(240);
    });
  });

  it("keeps optional global Manage fallback working", async () => {
    await openYesFolder();
    fireEvent.click(screen.getByRole("button", { name: "Manage" }));
    expect(screen.getByRole("dialog", { name: "SpiritFlix admin actions" })).toBeInTheDocument();
  });

  it("shows Smart tags in the video 3-dot menu and right-click menu", async () => {
    await openYesFolder();
    fireEvent.click(screen.getByRole("button", { name: "Actions for Beta Clip.mp4" }));
    expect(screen.getByRole("menuitem", { name: "Smart tags" })).toBeInTheDocument();

    const card = screen.getAllByTestId("admin-item-card").find((entry) => entry.textContent?.includes("Beta Clip.mp4"));
    fireEvent.contextMenu(card as HTMLElement);
    expect(screen.getByRole("menuitem", { name: "Smart tags" })).toBeInTheDocument();
  });

  it("opens smart review panel without removing the grid", async () => {
    await openYesFolder();
    fireEvent.click(screen.getByRole("button", { name: "Actions for Beta Clip.mp4" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Smart tags" }));
    expect(screen.getByRole("dialog", { name: "Smart tag review" })).toBeInTheDocument();
    expect(screen.getAllByTestId("admin-item-card").length).toBe(2);
    expect(screen.queryByRole("button", { name: /apply rename/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply move/i })).not.toBeInTheDocument();
  });

  it("does not auto-analyze when opening smart review", async () => {
    await openYesFolder();
    const fetchMock = vi.mocked(fetch);
    const callsBefore = fetchMock.mock.calls.length;
    fireEvent.click(screen.getByRole("button", { name: "Actions for Alpha Clip.mkv" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Smart tags" }));
    await screen.findByRole("dialog", { name: "Smart tag review" });
    const smartCalls = fetchMock.mock.calls.slice(callsBefore).filter(([input]) => String(input).includes("/smart/analysis"));
    expect(smartCalls.some(([, init]) => init?.method === "POST")).toBe(false);
    expect(smartCalls.some(([input]) => String(input).includes("path="))).toBe(true);
  });

  it("opens batch smart analysis panel and previews the current folder", async () => {
    await openYesFolder();
    fireEvent.click(screen.getByRole("button", { name: "Batch smart analyze" }));
    expect(screen.getByRole("dialog", { name: "Smart batch analysis" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Preview folder" }));
    await waitFor(() => {
      expect(screen.getAllByText("Beta Clip.mp4").length).toBeGreaterThan(1);
      expect(screen.getByText("Candidates")).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: /apply rename/i })).not.toBeInTheDocument();
  });

  it("shows a preview-only rename plan from the batch panel", async () => {
    await openYesFolder();
    fireEvent.click(screen.getByRole("button", { name: "Batch smart analyze" }));
    fireEvent.click(screen.getByRole("button", { name: "Rename plan" }));
    await waitFor(() => {
      expect(screen.getByText("Preview/export only. Real rename or move must use a future explicit Level 2 apply task.")).toBeInTheDocument();
      expect(screen.getByText("Beta Clip HD.mp4 - reviewed - ready")).toBeInTheDocument();
    });
    expect(screen.getByText("Apply enabled")).toBeInTheDocument();
    expect(screen.getByText("No")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply rename/i })).not.toBeInTheDocument();
  });
});
