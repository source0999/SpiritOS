import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import SpiritFlixAdminPage from "@/app/spiritflix/admin/page";
import { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix-types";
import { SPIRITFLIX_MEDIA_ROOT } from "@/lib/spiritflix/admin/constants";
import { SpiritFlixAdminApp } from "../SpiritFlixAdminApp";
import { buildAdminBreadcrumbSegments } from "../SpiritFlixAdminBreadcrumbs";
import { SpiritFlixAdminThumbnail } from "../SpiritFlixAdminThumbnail";

function mediaRootPayload() {
  return {
    schema: "spiritflix-admin-fs/v1",
    generatedAt: "2026-06-16T12:00:00.000Z",
    root: SPIRITFLIX_MEDIA_ROOT,
    currentPath: SPIRITFLIX_MEDIA_ROOT,
    breadcrumbs: [{ name: "media", path: SPIRITFLIX_MEDIA_ROOT }],
    totalRecordCount: 6,
    items: [
      { id: "folder:yes", name: "yes", type: "folder", path: `${SPIRITFLIX_MEDIA_ROOT}/yes`, parentPath: SPIRITFLIX_MEDIA_ROOT, dateModified: "2026-06-15T12:00:00.000Z" },
      { id: "folder:anime", name: "anime", type: "folder", path: `${SPIRITFLIX_MEDIA_ROOT}/anime`, parentPath: SPIRITFLIX_MEDIA_ROOT, dateModified: "2026-06-15T12:00:00.000Z" },
      { id: "folder:movies", name: "movies", type: "folder", path: `${SPIRITFLIX_MEDIA_ROOT}/movies`, parentPath: SPIRITFLIX_MEDIA_ROOT, dateModified: "2026-06-15T12:00:00.000Z" },
      { id: "folder:tv", name: "tv", type: "folder", path: `${SPIRITFLIX_MEDIA_ROOT}/tv`, parentPath: SPIRITFLIX_MEDIA_ROOT, dateModified: "2026-06-15T12:00:00.000Z" },
      { id: "folder:music", name: "music", type: "folder", path: `${SPIRITFLIX_MEDIA_ROOT}/music`, parentPath: SPIRITFLIX_MEDIA_ROOT, dateModified: "2026-06-15T12:00:00.000Z" },
      { id: "folder:other", name: "other", type: "folder", path: `${SPIRITFLIX_MEDIA_ROOT}/other`, parentPath: SPIRITFLIX_MEDIA_ROOT, dateModified: "2026-06-15T12:00:00.000Z" },
    ],
  };
}

function yesFolderPayload(path = `${SPIRITFLIX_MEDIA_ROOT}/yes`) {
  return {
    schema: "spiritflix-admin-fs/v1",
    generatedAt: "2026-06-16T12:00:00.000Z",
    root: `${SPIRITFLIX_MEDIA_ROOT}/yes`,
    currentPath: path,
    breadcrumbs: [{ name: "yes", path }],
    totalRecordCount: 4,
    items: [
      {
        id: "folder:/mnt/spirit-8tb/media/yes/Series",
        name: "Series",
        type: "folder",
        path: "/mnt/spirit-8tb/media/yes/Series",
        parentPath: "/mnt/spirit-8tb/media/yes",
        dateModified: "2026-06-15T12:00:00.000Z",
      },
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
      {
        id: "file:/mnt/spirit-8tb/media/yes/Alpha Clip.media-ingest.json",
        name: "Alpha Clip.media-ingest.json",
        type: "file",
        path: "/mnt/spirit-8tb/media/yes/Alpha Clip.media-ingest.json",
        parentPath: "/mnt/spirit-8tb/media/yes",
        extension: ".json",
        sizeBytes: 128,
        dateModified: "2026-06-14T12:00:00.000Z",
        playable: false,
      },
    ],
  };
}

function mockAdminFetch(mode: "media" | "yes" = "media") {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.startsWith("/api/spiritflix/admin/jellyfin-index")) {
      return Response.json({ items: [], source: "unconfigured" });
    }
    if (url.startsWith("/api/spiritflix/admin/thumbnail")) {
      return new Response(new Blob([new Uint8Array([0xff, 0xd8, 0xff, 0xd9])]), { status: 200, headers: { "Content-Type": "image/jpeg" } });
    }
    if (url.startsWith("/api/spiritflix/admin/fs")) {
      if (url.includes(encodeURIComponent(`${SPIRITFLIX_MEDIA_ROOT}/yes`))) {
        return Response.json(yesFolderPayload());
      }
      return Response.json(mode === "yes" ? yesFolderPayload() : mediaRootPayload());
    }
    if (url.startsWith("/api/spiritflix/jellyfin-image")) return new Response(new Blob(["image"], { type: "image/jpeg" }), { status: 200 });
    return Response.json({
      schema: "spiritflix-admin-library/v1",
      generatedAt: "2026-06-16T12:00:00.000Z",
      libraries: [{ Id: "library-1", Name: "Movies" }],
      totalRecordCount: 1,
      query: {},
      items: [
        {
          id: "jellyfin:item-beta",
          name: "Beta Clip",
          type: "jellyfin-item",
          jellyfinId: "item-beta",
          jellyfinItemId: "item-beta",
          path: "/mnt/spirit-8tb/media/yes/Beta Clip.mp4",
          jellyfinPath: "/media/yes/Beta Clip.mp4",
          extension: ".mp4",
          playable: true,
          hasImage: true,
          imageType: "Primary",
          imageStatus: "available",
          jellyfinItem: {
            Id: "item-beta",
            Name: "Beta Clip",
            Type: "Video",
            MediaType: "Video",
            Path: "/media/yes/Beta Clip.mp4",
            ImageTags: { Primary: "poster" },
            MediaSources: [{ Path: "/media/yes/Beta Clip.mp4" }],
          },
        },
      ],
    });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("SpiritFlixAdminApp", () => {
  beforeEach(() => {
    window.localStorage.clear();
    Object.defineProperty(URL, "createObjectURL", { configurable: true, value: vi.fn(() => "blob:spiritflix-admin-thumb") });
    Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: vi.fn() });
    window.localStorage.setItem(
      "spiritflix_private_gooner_session",
      JSON.stringify({
        serverUrl: "http://127.0.0.1:8096",
        accessToken: "token",
        userId: "user-1",
        username: "admin",
      }),
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("opens unified file-manager mode at the media root by default", async () => {
    const fetchMock = mockAdminFetch();
    render(<SpiritFlixAdminPage />);

    expect(screen.getByText("SpiritFlix Files")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Jellyfin" })).not.toBeInTheDocument();
    const folderCards = await screen.findAllByTestId("admin-item-card");
    expect(folderCards.map((card) => card.textContent)).toEqual(expect.arrayContaining([expect.stringContaining("yes"), expect.stringContaining("anime"), expect.stringContaining("movies")]));
    expect(screen.getByLabelText("Media folders")).toHaveTextContent("media-inbox");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(`/api/spiritflix/admin/fs?path=${encodeURIComponent(SPIRITFLIX_MEDIA_ROOT)}`),
      expect.objectContaining({ method: "GET" }),
    );
    expect(screen.queryByLabelText("Admin details")).not.toBeInTheDocument();
  });

  it("enables Level 2 manage actions after activation", async () => {
    mockAdminFetch();
    render(<SpiritFlixAdminApp />);
    await screen.findAllByTestId("admin-item-card");
    const manage = screen.getByRole("button", { name: "Manage" });
    expect(manage).toBeEnabled();
    fireEvent.click(manage);
    expect(screen.getByRole("dialog", { name: "SpiritFlix admin actions" })).toBeInTheDocument();
  });

  it("shows clean basenames and dates on cards without full paths", async () => {
    mockAdminFetch("yes");
    render(<SpiritFlixAdminApp />);

    fireEvent.click(screen.getByRole("button", { name: "yes" }));
    expect((await screen.findAllByText("Alpha Clip.mkv"))[0]).toBeInTheDocument();
    const card = screen.getAllByTestId("admin-item-card").find((entry) => entry.textContent?.includes("Alpha Clip.mkv"));
    expect(card?.textContent).not.toContain("/mnt/spirit-8tb/media/yes/Alpha Clip.mkv");
    expect(card?.textContent).toMatch(/Modified/);
  });

  it("filters metadata, updates controls, and opens details from Info action", async () => {
    const fetchMock = mockAdminFetch("yes");
    render(<SpiritFlixAdminApp />);

    fireEvent.click(screen.getByRole("button", { name: "yes" }));
    expect((await screen.findAllByText("Alpha Clip.mkv"))[0]).toBeInTheDocument();
    expect(screen.queryByText("Alpha Clip.media-ingest.json")).not.toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("List view"));
    fireEvent.change(screen.getByLabelText("Search admin media"), { target: { value: "clip" } });
    fireEvent.change(screen.getByLabelText("Sort admin media"), { target: { value: "title" } });

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("sortBy=title"), expect.objectContaining({ method: "GET" }));
    });

    const card = screen.getAllByTestId("admin-item-card").find((entry) => entry.textContent?.includes("Alpha Clip.mkv"));
    fireEvent.click(card as HTMLElement);
    expect(screen.queryByLabelText("Admin details")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Actions for Alpha Clip.mkv" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Info" }));
    expect(screen.getByLabelText("Admin details")).toHaveTextContent("/mnt/spirit-8tb/media/yes/Alpha Clip.mkv");

    fireEvent.click(screen.getByLabelText("Grid view"));
    fireEvent.click(screen.getByLabelText("Show metadata"));
    expect((await screen.findAllByText("Alpha Clip.media-ingest.json"))[0]).toBeInTheDocument();
  });

  it("matches Jellyfin posters via path aliases and uses local thumbnails as fallback", async () => {
    mockAdminFetch("yes");
    render(<SpiritFlixAdminApp />);

    fireEvent.click(screen.getByRole("button", { name: "yes" }));

    await waitFor(() => {
      const betaCard = screen.getAllByTestId("admin-item-card").find((card) => card.textContent?.includes("Beta Clip.mp4"));
      expect(betaCard).toHaveAttribute("data-image-status", "available");
      expect(betaCard).toHaveAttribute("data-jellyfin-match", "exact-path");
    });

    const alphaCard = screen.getAllByTestId("admin-item-card").find((card) => card.textContent?.includes("Alpha Clip.mkv"));
    expect(alphaCard).toHaveAttribute("data-image-status", "missing");
    await waitFor(() => {
      const thumbs = screen.getAllByAltText("Alpha Clip.mkv");
      expect(thumbs[0]).toHaveAttribute("src", expect.stringContaining("/api/spiritflix/admin/thumbnail?"));
    });
  });

  it("builds Root > DATA > media breadcrumbs that stay inside the media root", () => {
    const crumbs = buildAdminBreadcrumbSegments(SPIRITFLIX_MEDIA_ROOT);
    expect(crumbs.map((crumb) => crumb.name).join(" > ")).toBe("Root > DATA > media");
    expect(crumbs[0]?.path).toBe(SPIRITFLIX_MEDIA_ROOT);
    expect(buildAdminBreadcrumbSegments(`${SPIRITFLIX_MEDIA_ROOT}/yes`).map((crumb) => crumb.name).join(" > ")).toBe("Root > DATA > media > yes");
  });

  it("falls back gracefully when a matched Jellyfin image fails to load", async () => {
    const client = new JellyfinClient("http://127.0.0.1:8096", "token", "user-1");
    vi.spyOn(client, "getImageObjectUrl").mockRejectedValue(new Error("missing image"));
    const jellyfinItem: JellyfinItem = {
      Id: "item-1",
      Name: "Image Fail",
      Type: "Video",
      MediaType: "Video",
      ImageTags: { Primary: "poster" },
    };

    render(
      <SpiritFlixAdminThumbnail
        client={client}
        item={{
          id: "file:/mnt/spirit-8tb/media/yes/Image Fail.mp4",
          name: "Image Fail.mp4",
          type: "file",
          path: "/mnt/spirit-8tb/media/yes/Image Fail.mp4",
          playable: true,
          imageType: "Primary",
          imageStatus: "available",
          jellyfinItem,
        }}
      />,
    );

    await waitFor(() => {
      expect(document.querySelector('[data-thumbnail-source="local"], .spiritflix-admin-thumbnail__fallback')).toBeTruthy();
    });
  });
});
