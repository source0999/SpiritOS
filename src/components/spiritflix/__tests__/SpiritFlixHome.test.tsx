import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getBoundedHomeFaceMetadataItems, SpiritFlixHome } from "../SpiritFlixHome";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem, SpiritFlixGalleryResponse, SpiritFlixHomeData } from "@/lib/spiritflix-types";

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

const historyItem: JellyfinItem = {
  Id: "history-1",
  Name: "Watched On Fold",
  Type: "Video",
  MediaType: "Video",
  RunTimeTicks: 6000000000,
  UserData: {
    PlaybackPositionTicks: 1800000000,
    Played: false,
    PlayedPercentage: 30,
    PlayCount: 1,
    LastPlayedDate: "2026-06-06T12:30:00.000Z",
  },
};

const modelItem: JellyfinItem = {
  Id: "model-1",
  Name: "Scene One",
  Type: "Video",
  MediaType: "Video",
  SeriesName: "Sava Schultz",
  MediaStreams: [{ Type: "Video", Width: 1080, Height: 1920 }],
};

const landscapeItem: JellyfinItem = {
  Id: "landscape-1",
  Name: "Wide Scene",
  Type: "Video",
  MediaType: "Video",
  SeriesName: "Sava Schultz",
  MediaStreams: [{ Type: "Video", Width: 1920, Height: 1080 }],
};

const twitterItem: JellyfinItem = {
  Id: "twitter-1",
  Name: "Twitter Clip",
  Type: "Video",
  MediaType: "Video",
  SeriesName: "Sava Schultz",
  Path: "/mnt/spirit-8tb/media/yes/twitter/Sava Schultz/Twitter Clip.mp4",
  MediaSources: [{ Path: "/mnt/spirit-8tb/media/yes/twitter/Sava Schultz/Twitter Clip.mp4" }],
  MediaStreams: [{ Type: "Video", Width: 1080, Height: 1920 }],
};

const twitterFolderItem: JellyfinItem = {
  Id: "twitter-folder-1",
  Name: "Luna Clip",
  Type: "Video",
  MediaType: "Video",
  SeriesName: "Videos From X",
  Path: "/mnt/spirit-8tb/media/yes/videos from x/luna clip.mp4",
  MediaSources: [{ Path: "/mnt/spirit-8tb/media/yes/videos from x/luna clip.mp4" }],
  MediaStreams: [{ Type: "Video", Width: 1080, Height: 1920 }],
};

const manualModelItem: JellyfinItem = {
  Id: "manual-model-1",
  Name: "Manual Model Scene",
  Type: "Video",
  MediaType: "Video",
  SeriesName: "Videos From X",
  ManualModelName: "Luna x pearl",
  MediaStreams: [{ Type: "Video", Width: 1080, Height: 1920 }],
};

const emptyGallery: SpiritFlixGalleryResponse = {
  schema: "spiritflix-model-gallery/v1",
  generatedAt: "2026-06-06T12:31:00.000Z",
  items: [],
  groups: [],
  summary: {
    galleryItems: 0,
    modelsWithGallery: 0,
  },
};

function createClient(
  gallery: SpiritFlixGalleryResponse = emptyGallery,
  overrides: Partial<JellyfinClient> = {},
): JellyfinClient {
  return {
    getFaceOrganizerMetadata: vi.fn().mockResolvedValue({
      knownPerformers: [],
      videos: {},
      scannedCount: 0,
      generatedAt: "2026-06-06T12:31:00.000Z",
    }),
    getGallery: vi.fn().mockResolvedValue(gallery),
    getImageProxyUrl: vi.fn(() => "/api/spiritflix/jellyfin-image?test=1"),
    getImageObjectUrl: vi.fn().mockRejectedValue(new Error("No image in test")),
    getAllLibraryItems: vi.fn().mockResolvedValue([]),
    getLibraryItemsPage: vi.fn().mockResolvedValue({
      items: [],
      totalRecordCount: 0,
      startIndex: 0,
      limit: 50,
      hasMore: false,
    }),
    ...overrides,
  } as unknown as JellyfinClient;
}

function createData(overrides: Partial<SpiritFlixHomeData> = {}): SpiritFlixHomeData {
  return {
    libraries: [{ Id: "library-1", Name: "Library" }],
    playlists: [],
    selectedLibraryId: "library-1",
    featuredItems: [],
    libraryItems: [historyItem],
    continueWatching: [historyItem],
    watchHistory: [historyItem],
    latestAdded: [],
    favorites: [],
    ...overrides,
  };
}

describe("SpiritFlixHome watch history", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
    window.matchMedia = vi.fn().mockReturnValue({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/spiritflix/model-index")) {
          return Promise.resolve(Response.json({
            schema: "spiritflix-manual-model-index/v1",
            updatedAt: "2026-06-20T00:00:00.000Z",
            models: [],
            items: [],
          }));
        }
        return Promise.resolve(Response.json({
          schema: "spiritflix-manual-tag-index/v1",
          updatedAt: "2026-06-20T00:00:00.000Z",
          tags: [],
          items: [],
        }));
      }),
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("caps cold Home face metadata requests to a deterministic page-load batch", () => {
    const playableItems = Array.from({ length: 300 }, (_, index) => ({
      ...modelItem,
      Id: `face-meta-${index}`,
      Name: `Face Metadata ${index}`,
    }));

    const bounded = getBoundedHomeFaceMetadataItems(playableItems);

    expect(bounded).toHaveLength(20);
    expect(bounded[0]).toEqual(expect.objectContaining({ Id: "face-meta-0" }));
    expect(bounded.at(-1)).toEqual(expect.objectContaining({ Id: "face-meta-19" }));
  });

  it("keeps the load overlay visible until visible face metadata is ready", async () => {
    const onVisibleMetadataReady = vi.fn();
    const faceItems = Array.from({ length: 25 }, (_, index) => ({
      ...modelItem,
      Id: `visible-face-${index}`,
      Name: `Visible Face ${index}`,
    }));
    const client = createClient();

    render(
      <SpiritFlixHome
        client={client}
        data={createData({
          libraryItems: faceItems,
          continueWatching: [],
          watchHistory: [],
        })}
        loading={true}
        loadProgress={{ percent: 76, label: "Loading shelves" }}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
        onVisibleMetadataReady={onVisibleMetadataReady}
      />,
    );

    expect(screen.getByRole("progressbar", { name: /loading shelves/i })).toHaveAttribute("aria-valuenow", "76");
    await waitFor(() => expect(client.getFaceOrganizerMetadata).toHaveBeenCalled());
    const metadataItems = vi.mocked(client.getFaceOrganizerMetadata).mock.calls[0]?.[0] ?? [];
    expect(metadataItems).toHaveLength(20);
    await waitFor(() => expect(onVisibleMetadataReady).toHaveBeenCalled());
  });

  it("shows private watch history in the library and plays from the synced resume point", async () => {
    const onPlay = vi.fn();

    const { container } = render(
      <SpiritFlixHome
        client={createClient()}
        data={createData()}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={onPlay}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /history/i }));

    await screen.findByText("Jun 6, 8:30 AM");
    const historyButton = container.querySelector(".spiritflix-library-row--history");
    expect(historyButton).toBeInTheDocument();
    expect(screen.getByText(/3:00 \/ 10:00 \/ 7m left/i)).toBeInTheDocument();

    fireEvent.click(historyButton as HTMLElement);

    await waitFor(() => {
      expect(onPlay).toHaveBeenCalledWith(
        expect.objectContaining({ Id: "history-1" }),
        expect.arrayContaining([expect.objectContaining({ Id: "history-1" })]),
        "Watch History",
        1800000000,
      );
    });
    expect(onPlay.mock.calls[0]?.[1]?.[0]).toEqual(expect.objectContaining({ Id: "history-1" }));
  });

  it("does not show favorited library videos on the Home page", () => {
    const favoriteOnlyItem: JellyfinItem = {
      ...historyItem,
      Id: "favorite-home-hidden",
      Name: "Favorite Only Library Clip",
    };

    render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          selectedLibraryId: null,
          continueWatching: [],
          latestAdded: [],
          favorites: [favoriteOnlyItem],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    expect(screen.queryByRole("heading", { name: "Favorites" })).not.toBeInTheDocument();
    expect(screen.queryByText("Favorite Only Library Clip")).not.toBeInTheDocument();
  });

  it("shows actual library favorites even when the favorites page misses a row", () => {
    const actualFavorite: JellyfinItem = {
      ...modelItem,
      Id: "actual-favorite",
      Name: "Actual Favorite",
      UserData: { IsFavorite: true },
    };
    const favoritePageItemWithoutUserData: JellyfinItem = {
      ...landscapeItem,
      Id: "favorite-page-item",
      Name: "Server Favorite",
      UserData: undefined,
    };

    render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraryItems: [actualFavorite],
          continueWatching: [],
          watchHistory: [],
          favorites: [favoritePageItemWithoutUserData],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    expect(screen.getByRole("heading", { name: "Favorites" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Favorites" }).closest("section")).toHaveTextContent("2 videos");
    expect(screen.getAllByText("Actual Favorite").length).toBeGreaterThan(0);
    expect(screen.getByText("Server Favorite")).toBeInTheDocument();
  });

  it("opens the Favorites section heading into a full favorites video grid", async () => {
    const favoriteGridItem: JellyfinItem = {
      ...modelItem,
      Id: "favorite-grid",
      Name: "Favorite Grid Clip",
      UserData: undefined,
    };

    render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraryItems: [modelItem],
          continueWatching: [],
          watchHistory: [],
          favorites: [favoriteGridItem],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /open favorites videos/i }));

    await waitFor(() => {
      expect(screen.queryByRole("button", { name: /open favorites videos/i })).not.toBeInTheDocument();
    });
    expect(screen.getByText("1 video")).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Favorite Grid Clip" })).toBeInTheDocument();
  });

  it("shows a live loading state instead of stale empty library copy while library rows refresh", () => {
    render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraries: [{ Id: "library-1", Name: "Library" }],
          selectedLibraryId: "library-1",
          libraryItems: [],
          continueWatching: [],
          watchHistory: [],
          latestAdded: [],
          favorites: [],
        })}
        loading={true}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    expect(screen.getByRole("progressbar", { name: /loading library/i })).toHaveAttribute("aria-valuenow", "0");
    expect(screen.queryByText(/Library has no indexed videos yet/i)).not.toBeInTheDocument();
  });

  it("renders Anime as seasons and episodes without library dashboard controls", async () => {
    const onPlay = vi.fn();
    const animeEpisode: JellyfinItem = {
      Id: "kenshin-1",
      Name: "The Handsome Swordsman of Legend",
      Type: "Video",
      MediaType: "Video",
      SeriesName: "Rurouni Kenshin (1996)",
      Path: "/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 01/Rurouni Kenshin (1996) - S01E01.mp4",
      ParentIndexNumber: 1,
      IndexNumber: 1,
      RunTimeTicks: 15000000000,
      MediaStreams: [{ Type: "Video", Width: 720, Height: 540 }],
    };

    const { container } = render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraries: [{ Id: "anime-library", Name: "Anime" }],
          selectedLibraryId: "anime-library",
          libraryItems: [animeEpisode],
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={onPlay}
      />,
    );

    expect(screen.getByText("Jellyfin / Anime")).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { name: "Rurouni Kenshin (1996)" })).toHaveLength(2);
    expect(screen.getByRole("heading", { name: "Season 1" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Episode 1 The Handsome Swordsman of Legend/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /History/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Gallery/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Models/i })).not.toBeInTheDocument();
    expect(screen.queryByText("All Models")).not.toBeInTheDocument();
    expect(screen.queryByText("Manual tags")).not.toBeInTheDocument();
    expect(screen.queryByText("Shuffle Gooner Mix")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Episode 1 The Handsome Swordsman of Legend/i }));

    expect(onPlay).toHaveBeenCalledWith(
      animeEpisode,
      [animeEpisode],
      "Rurouni Kenshin (1996) / Season 1",
      undefined,
    );
  });

  it("groups Anime episodes by folder path when Jellyfin series metadata is stale", async () => {
    const onPlay = vi.fn();
    const kenshinEpisode: JellyfinItem = {
      Id: "kenshin-1",
      Name: "The Handsome Swordsman of Legend",
      Type: "Video",
      MediaType: "Video",
      SeriesName: "Rurouni Kenshin (1996)",
      Path: "/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 01/Rurouni Kenshin (1996) - S01E01.mp4",
      ParentIndexNumber: 1,
      IndexNumber: 1,
      RunTimeTicks: 15000000000,
      MediaStreams: [{ Type: "Video", Width: 720, Height: 540 }],
    };
    const gurrenEpisodeWithWrongSeries: JellyfinItem = {
      Id: "gurren-1",
      Name: "Bust Through the Heavens with Your Drill!",
      Type: "Video",
      MediaType: "Video",
      SeriesName: "Rurouni Kenshin (1996)",
      Path: "/mnt/spirit-8tb/media/anime/Gurren Lagann (2007)/Season 01/Gurren Lagann (2007) - S01E01.mp4",
      ParentIndexNumber: 1,
      IndexNumber: 1,
      RunTimeTicks: 15000000000,
      MediaStreams: [{ Type: "Video", Width: 1280, Height: 720 }],
    };

    const { container } = render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraries: [{ Id: "anime-library", Name: "Anime" }],
          selectedLibraryId: "anime-library",
          libraryItems: [kenshinEpisode, gurrenEpisodeWithWrongSeries],
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={onPlay}
      />,
    );

    expect(screen.getAllByRole("heading", { name: "Gurren Lagann (2007)" })).toHaveLength(2);
    expect(screen.getByRole("button", { name: /Rurouni Kenshin \(1996\)/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Episode 1 Bust Through the Heavens/i }));

    expect(onPlay).toHaveBeenCalledWith(
      gurrenEpisodeWithWrongSeries,
      [gurrenEpisodeWithWrongSeries],
      "Gurren Lagann (2007) / Season 1",
      undefined,
    );
  });

  it("shows resumable watch history in Continue Watching when Jellyfin misses the resume lane", async () => {
    const onPlay = vi.fn();

    render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraryItems: [],
          continueWatching: [],
          watchHistory: [historyItem],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={onPlay}
      />,
    );

    const resumeButton = await screen.findByRole("button", { name: /resume watched on fold at 3:00 \/ 10:00/i });
    expect(resumeButton).toBeInTheDocument();

    fireEvent.click(resumeButton);

    expect(onPlay).toHaveBeenCalledWith(
      expect.objectContaining({ Id: "history-1" }),
      [expect.objectContaining({ Id: "history-1" })],
      "Continue Watching",
      1800000000,
    );
  });

  it("shows uploaded gallery pictures and opens the fullscreen gallery viewer", async () => {
    const gallery: SpiritFlixGalleryResponse = {
      schema: "spiritflix-model-gallery/v1",
      generatedAt: "2026-06-06T12:31:00.000Z",
      items: [
        {
          id: "sava-schultz/pic.jpg",
          modelName: "Sava Schultz",
          modelKey: "savaschultz",
          modelSlug: "sava-schultz",
          fileName: "pic.jpg",
          src: "/api/spiritflix/gallery/image?model=sava-schultz&file=pic.jpg",
          thumbnailSrc: "/api/spiritflix/gallery/image?model=sava-schultz&file=pic.jpg",
          collection: "Launch Set",
          uploadedAt: "2026-06-06T12:31:00.000Z",
        },
      ],
      groups: [
        {
          name: "Sava Schultz",
          modelKey: "savaschultz",
          modelSlug: "sava-schultz",
          itemCount: 1,
        },
      ],
      summary: {
        galleryItems: 1,
        modelsWithGallery: 1,
      },
    };

    render(
      <SpiritFlixHome
        client={createClient(gallery)}
        data={createData()}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /gallery/i }));

    expect(await screen.findByText("Sava Schultz")).toBeInTheDocument();
    expect(screen.getByText("Launch Set")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /sava schultz gallery/i }));

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByLabelText("Gallery seconds per picture")).toHaveValue(5);
  });

  it("restores the selected model view from the route state", async () => {
    render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraryItems: [manualModelItem, historyItem],
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        initialModelName="Luna x pearl"
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    expect(await screen.findByRole("heading", { name: "Luna x pearl" })).toBeInTheDocument();
    expect(screen.queryByText("Watched On Fold")).not.toBeInTheDocument();
  });

  it("filters the library by a manual tag from the URL-backed chip row", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve(Response.json({
          schema: "spiritflix-manual-tag-index/v1",
          updatedAt: "2026-06-20T00:00:00.000Z",
          tags: [
            { tag: "busty", label: "busty", count: 1 },
            { tag: "solo", label: "solo", count: 0 },
          ],
          items: [
            {
              schema: "spiritflix-manual-tags/v1",
              itemId: "model-1",
              manualTags: ["busty"],
              updatedAt: "2026-06-20T00:00:00.000Z",
              source: "manual",
            },
          ],
        })),
      ),
    );

    const { container } = render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraryItems: [modelItem, historyItem],
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /list/i }));
    const bustyFilter = await screen.findByRole("button", { name: /^busty\s+1$/i }, { timeout: 5000 });
    fireEvent.click(bustyFilter);

    await waitFor(() => {
      const list = container.querySelector(".spiritflix-library-list");
      expect(list).toHaveTextContent("Scene One");
      expect(list).not.toHaveTextContent("Watched On Fold");
    });
    expect(window.location.search).toContain("tag=busty");
  });

  it("filters visible library videos and shuffle queues by portrait or landscape", async () => {
    const onPlay = vi.fn();
    const getAllLibraryItems = vi.fn().mockResolvedValue([modelItem, landscapeItem]);
    const { container } = render(
      <SpiritFlixHome
        client={createClient(emptyGallery, { getAllLibraryItems } as Partial<JellyfinClient>)}
        data={createData({
          libraryItems: [modelItem, landscapeItem],
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={onPlay}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /all videos \/ model/i }));
    fireEvent.click(await screen.findByRole("button", { name: /^portrait\s+1$/i }));
    fireEvent.click(screen.getByRole("button", { name: /list/i }));

    await waitFor(() => {
      const list = container.querySelector(".spiritflix-library-list");
      expect(list).toHaveTextContent("Scene One");
      expect(list).not.toHaveTextContent("Wide Scene");
    });

    fireEvent.click(screen.getByRole("button", { name: /shuffle library portrait videos/i }));

    await waitFor(() => {
      expect(onPlay).toHaveBeenCalledWith(
        expect.objectContaining({ Id: "model-1" }),
        [expect.objectContaining({ Id: "model-1" })],
        "Library / Portrait Shuffle",
      );
    });
  });

  it("excludes Twitter videos from visible library results and shuffle queues", async () => {
    const onPlay = vi.fn();
    const getAllLibraryItems = vi.fn().mockResolvedValue([modelItem, twitterItem, twitterFolderItem]);
    const { container } = render(
      <SpiritFlixHome
        client={createClient(emptyGallery, { getAllLibraryItems } as Partial<JellyfinClient>)}
        data={createData({
          libraryItems: [modelItem, twitterItem, twitterFolderItem],
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={onPlay}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /all videos \/ model/i }));
    fireEvent.click(await screen.findByRole("button", { name: /hide twitter \/ x\s+2/i }));
    fireEvent.click(screen.getByRole("button", { name: /list/i }));

    await waitFor(() => {
      const list = container.querySelector(".spiritflix-library-list");
      expect(list).toHaveTextContent("Scene One");
      expect(list).not.toHaveTextContent("Twitter Clip");
      expect(list).not.toHaveTextContent("Luna Clip");
    });

    fireEvent.click(screen.getByRole("button", { name: /shuffle library all videos/i }));

    await waitFor(() => {
      expect(onPlay).toHaveBeenCalledWith(
        expect.objectContaining({ Id: "model-1" }),
        [expect.objectContaining({ Id: "model-1" })],
        "Library Shuffle",
      );
    });
  });

  it("loads the full library before starting the library shuffle queue even when the visible page says complete", async () => {
    const onPlay = vi.fn();
    const fullLibraryItem = {
      ...modelItem,
      Id: "full-library-2",
      Name: "Full Library Two",
    };
    const getAllLibraryItems = vi.fn().mockResolvedValue([modelItem, fullLibraryItem]);

    render(
      <SpiritFlixHome
        client={createClient(emptyGallery, { getAllLibraryItems } as Partial<JellyfinClient>)}
        data={createData({
          libraryItems: [modelItem],
          libraryPaging: {
            loaded: 1,
            total: 1,
            pageSize: 1,
            hasMore: false,
          },
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={onPlay}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /shuffle library all videos/i }));

    await waitFor(() => expect(getAllLibraryItems).toHaveBeenCalledWith("library-1", { searchTerm: "", fields: "card" }));
    await waitFor(() => expect(onPlay).toHaveBeenCalled());

    const queueItems = onPlay.mock.calls[0]?.[1] as JellyfinItem[];
    expect(queueItems.map((item) => item.Id).sort()).toEqual(["full-library-2", "model-1"]);
  });

  it("builds an unexplored shuffle from fresh full-library watch state", async () => {
    const onPlay = vi.fn();
    const exploredItem = { ...historyItem, Id: "already-started", Name: "Already Started" };
    const unexploredItem = { ...modelItem, Id: "never-started", Name: "Never Started" };
    const getAllLibraryItems = vi.fn().mockResolvedValue([exploredItem, unexploredItem]);

    render(
      <SpiritFlixHome
        client={createClient(emptyGallery, { getAllLibraryItems } as Partial<JellyfinClient>)}
        data={createData({ libraryItems: [exploredItem, unexploredItem], continueWatching: [], watchHistory: [] })}
        loading={false}
        error=""
        session={{ serverUrl: "https://jellyfin.local", accessToken: "token", userId: "user-1", username: "private-user" }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={onPlay}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /all videos \/ model/i }));
    fireEvent.click(await screen.findByRole("button", { name: "Unexplored" }));
    fireEvent.click(screen.getByRole("button", { name: /shuffle unexplored library all videos/i }));

    await waitFor(() => {
      expect(onPlay).toHaveBeenCalledWith(
        expect.objectContaining({ Id: "never-started" }),
        [expect.objectContaining({ Id: "never-started" })],
        "Library Unexplored Shuffle",
      );
    });
    expect(getAllLibraryItems).toHaveBeenCalledWith("library-1", { searchTerm: "", fields: "card" });
  });

  it("adds the videos-from-x folder as a Twitter source category in the model pane", async () => {
    const { container } = render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraryItems: [modelItem, twitterItem, twitterFolderItem, landscapeItem],
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    const twitterCategory = await screen.findByRole("button", { name: /twitter\s+2 videos/i });
    expect(screen.queryByRole("button", { name: /videos from x\s+1 videos/i })).not.toBeInTheDocument();
    fireEvent.click(twitterCategory);
    fireEvent.click(screen.getByRole("button", { name: /list/i }));

    await waitFor(() => {
      const list = container.querySelector(".spiritflix-library-list");
      expect(list).toHaveTextContent("Twitter Clip");
      expect(list).toHaveTextContent("Luna Clip");
      expect(list).not.toHaveTextContent("Scene One");
      expect(list).not.toHaveTextContent("Wide Scene");
    });
    expect(screen.getByRole("heading", { name: "Twitter" })).toBeInTheDocument();
  });

  it("shows manual model assignments in the Models page", async () => {
    render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraryItems: [modelItem, manualModelItem],
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /^models$/i }));

    expect(await screen.findByRole("heading", { name: "Models" })).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: /luna x pearl\s+1 video/i })).toBeInTheDocument();
  });

  it("keeps the Models view reachable from the mobile modebar", async () => {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query.includes("pointer: coarse"),
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }));
    const client = createClient(emptyGallery, {
      getAllLibraryItems: vi.fn().mockResolvedValue([modelItem, manualModelItem]),
    } as Partial<JellyfinClient>);

    render(
      <SpiritFlixHome
        client={client}
        data={createData({
          libraryItems: [modelItem, manualModelItem],
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Open Models" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "All Models" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Open Models" }));

    expect(await screen.findByRole("heading", { name: "Models" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open Models" })).toHaveAttribute("aria-pressed", "true");
  });

  it("does not render catalog-only models without loaded videos", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/spiritflix/model-index")) {
          return Promise.resolve(Response.json({
            schema: "spiritflix-manual-model-index/v1",
            updatedAt: "2026-06-28T00:00:00.000Z",
            models: [{ modelName: "Alexa Pearl", count: 7, catalogCount: 7, assignedCount: 0, catalogStatus: "profile-url", source: "registry" }],
            items: [],
          }));
        }
        return Promise.resolve(Response.json({
          schema: "spiritflix-manual-tag-index/v1",
          updatedAt: "2026-06-28T00:00:00.000Z",
          tags: [],
          items: [],
        }));
      }),
    );

    render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraryItems: [modelItem],
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /^models$/i }));

    expect(await screen.findByRole("button", { name: /unknown\s+1 video/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /alexa pearl/i })).not.toBeInTheDocument();
  });

  it("collapses untrusted videos while keeping trusted face matches and Twitter", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/spiritflix/model-index")) {
          return Promise.resolve(Response.json({
            schema: "spiritflix-manual-model-index/v1",
            updatedAt: "2026-06-28T00:00:00.000Z",
            models: [
              { modelName: "Lexi Marvel", count: 5, catalogCount: 5, assignedCount: 0, catalogStatus: "needs-review", source: "registry" },
              { modelName: "Nly", count: 1, catalogCount: 1, assignedCount: 0, catalogStatus: "local-auto", source: "registry" },
            ],
            items: [],
          }));
        }
        return Promise.resolve(Response.json({
          schema: "spiritflix-manual-tag-index/v1",
          updatedAt: "2026-06-28T00:00:00.000Z",
          tags: [],
          items: [],
        }));
      }),
    );
    const trustedFaceItem: JellyfinItem = {
      ...modelItem,
      Id: "trusted-face-1",
      Name: "Trusted Face Scene",
      SeriesName: "Unsorted",
    };
    const garbageFaceItem: JellyfinItem = {
      ...modelItem,
      Id: "garbage-face-1",
      Name: "Garbage Face Scene",
      SeriesName: "Unsorted",
    };
    const unknownItem: JellyfinItem = {
      ...modelItem,
      Id: "unknown-1",
      Name: "Unknown Scene",
      SeriesName: "Unsorted",
    };
    const client = createClient();
    vi.mocked(client.getFaceOrganizerMetadata).mockResolvedValue({
      knownPerformers: [],
      videos: {
        "trusted-face-1": {
          itemId: "trusted-face-1",
          primaryPerformer: { name: "Lexi Marvel", confidence: 0.86 },
          performers: [{ name: "Lexi Marvel", confidence: 0.86 }],
          status: "needs_review",
          label: "Needs review: Lexi Marvel",
          confidence: 0.86,
          verificationNeeded: true,
        },
        "garbage-face-1": {
          itemId: "garbage-face-1",
          primaryPerformer: { name: "Nly", confidence: 0.94 },
          performers: [{ name: "Nly", confidence: 0.94 }],
          status: "needs_review",
          label: "Needs review: Nly",
          confidence: 0.94,
          verificationNeeded: true,
        },
      },
      scannedCount: 2,
      generatedAt: "2026-06-21T04:08:00.000Z",
    });

    render(
      <SpiritFlixHome
        client={client}
        data={createData({
          libraryItems: [trustedFaceItem, garbageFaceItem, unknownItem, twitterFolderItem],
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /^models$/i }));

    expect(await screen.findByRole("button", { name: /lexi marvel\s+1 video/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /twitter\s+1 video/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /unknown\s+2 videos/i })).toBeInTheDocument();
    expect(screen.queryByText("Nly")).not.toBeInTheDocument();
  });

  it("uses trusted catalog aliases from filenames and paths for model groups", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/spiritflix/model-index")) {
          return Promise.resolve(Response.json({
            schema: "spiritflix-manual-model-index/v1",
            updatedAt: "2026-07-06T00:00:00.000Z",
            models: [
              {
                modelName: "Vibe With Mommy",
                count: 0,
                catalogCount: 22,
                assignedCount: 0,
                aliases: ["vibe-with-mommy"],
                catalogStatus: "profile-url",
                source: "registry",
              },
            ],
            items: [],
          }));
        }
        return Promise.resolve(Response.json({
          schema: "spiritflix-manual-tag-index/v1",
          updatedAt: "2026-07-06T00:00:00.000Z",
          tags: [],
          items: [],
        }));
      }),
    );

    const filenameItems: JellyfinItem[] = [
      {
        ...modelItem,
        Id: "vibe-name-1",
        Name: "vibewithmommy new clip",
        SeriesName: "Unsorted",
        Path: "/mnt/spirit-8tb/media/yes/other/vibewithmommy new clip.mp4",
        MediaSources: [{ Path: "/mnt/spirit-8tb/media/yes/other/vibewithmommy new clip.mp4" }],
      },
      {
        ...modelItem,
        Id: "vibe-ocr-1",
        Name: "random upload",
        SeriesName: "Unsorted",
        Path: "/mnt/spirit-8tb/media/yes/other/vibewithmorim_scene.mp4",
        MediaSources: [{ Path: "/mnt/spirit-8tb/media/yes/other/vibewithmorim_scene.mp4" }],
      },
      {
        ...modelItem,
        Id: "unknown-name-1",
        Name: "Nly random one off",
        SeriesName: "Unsorted",
        Path: "/mnt/spirit-8tb/media/yes/other/nly-random.mp4",
        MediaSources: [{ Path: "/mnt/spirit-8tb/media/yes/other/nly-random.mp4" }],
      },
    ];

    render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraryItems: filenameItems,
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /^models$/i }));

    expect(await screen.findByRole("button", { name: /vibe with mommy\s+2 videos/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /unknown\s+1 video/i })).toBeInTheDocument();
    expect(screen.queryByText("Nly")).not.toBeInTheDocument();
  });

  it("enriches full-library model groups with face metadata beyond the first loaded page", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/spiritflix/model-index")) {
          return Promise.resolve(Response.json({
            schema: "spiritflix-manual-model-index/v1",
            updatedAt: "2026-06-28T00:00:00.000Z",
            models: [{ modelName: "Lexi Marvel", count: 25, catalogCount: 25, assignedCount: 0, catalogStatus: "needs-review", source: "registry" }],
            items: [],
          }));
        }
        return Promise.resolve(Response.json({
          schema: "spiritflix-manual-tag-index/v1",
          updatedAt: "2026-06-28T00:00:00.000Z",
          tags: [],
          items: [],
        }));
      }),
    );
    const fullLibraryItems = Array.from({ length: 25 }, (_, index) => ({
      ...modelItem,
      Id: `lexi-full-${index + 1}`,
      Name: `Lexi Full Library ${index + 1}`,
      SeriesName: "Unsorted",
    }));
    const getLibraryItemsPage = vi.fn().mockResolvedValue({
      items: fullLibraryItems,
      totalRecordCount: 25,
      startIndex: 0,
      limit: 50,
      hasMore: false,
    });
    const getFaceOrganizerMetadata = vi.fn().mockImplementation((items: JellyfinItem[]) =>
      Promise.resolve({
        knownPerformers: [],
        enrolledSources: {
          leximarvel: { name: "Lexi Marvel", candidateVideos: 25, source: "model_index" },
        },
        videos: Object.fromEntries(
          items.map((item) => [
            item.Id,
            {
              itemId: item.Id,
              primaryPerformer: { name: "Lexi Marvel", confidence: 0.91 },
              performers: [{ name: "Lexi Marvel", confidence: 0.91 }],
              status: "needs_review",
              label: "Needs review: Lexi Marvel",
              confidence: 0.91,
              verificationNeeded: true,
            },
          ]),
        ),
        scannedCount: items.length,
        generatedAt: "2026-06-21T04:08:00.000Z",
      }),
    );
    const client = createClient(emptyGallery, { getLibraryItemsPage, getFaceOrganizerMetadata } as Partial<JellyfinClient>);

    render(
      <SpiritFlixHome
        client={client}
        data={createData({
          libraryItems: fullLibraryItems.slice(0, 20),
          continueWatching: [],
          watchHistory: [],
          libraryPaging: {
            loaded: 20,
            total: 25,
            pageSize: 20,
            hasMore: true,
          },
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    await waitFor(
      () => expect(getLibraryItemsPage).toHaveBeenCalledWith("library-1", expect.objectContaining({ fields: "card", limit: 50, startIndex: 0 })),
      { timeout: 3000 },
    );
    await waitFor(() => {
      expect(getFaceOrganizerMetadata.mock.calls.some(([items]) => items.length === 25)).toBe(true);
    });

    fireEvent.click(screen.getByRole("button", { name: /^models$/i }));

    expect(await screen.findByRole("button", { name: /lexi marvel\s+25 videos/i })).toBeInTheDocument();
  });

  it("hydrates model groups from the full library instead of only the first loaded page", async () => {
    const client = createClient(emptyGallery, {
      getLibraryItemsPage: vi.fn().mockResolvedValue({
        items: [modelItem, manualModelItem],
        totalRecordCount: 2,
        startIndex: 0,
        limit: 50,
        hasMore: false,
      }),
    } as Partial<JellyfinClient>);

    const { container } = render(
      <SpiritFlixHome
        client={client}
        data={createData({
          libraryItems: [modelItem],
          continueWatching: [],
          watchHistory: [],
          libraryPaging: {
            loaded: 1,
            total: 2,
            pageSize: 1,
            hasMore: true,
          },
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    await waitFor(
      () => expect(client.getLibraryItemsPage).toHaveBeenCalledWith("library-1", expect.objectContaining({ fields: "card", limit: 50, startIndex: 0 })),
      { timeout: 3000 },
    );

    fireEvent.click(screen.getByRole("button", { name: /^models$/i }));
    const lunaButtons = await screen.findAllByRole("button", { name: /luna x pearl\s+1 video/i });
    fireEvent.click(lunaButtons[0]);
    fireEvent.click(screen.getByRole("button", { name: /grid/i }));

    await waitFor(() => {
      const grid = container.querySelector(".spiritflix-library-grid");
      expect(grid?.querySelector("[aria-label='Manual Model Scene']")).toBeInTheDocument();
    });
    expect(screen.queryByText(/Library has no indexed videos yet/i)).not.toBeInTheDocument();
  });

  it("does not render the Latest Added rail on the library dashboard", async () => {
    render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraryItems: [modelItem],
          latestAdded: [historyItem],
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    expect(screen.queryByRole("heading", { name: "Latest Added" })).not.toBeInTheDocument();
  });

  it("uses the Latest Added feed for the Library Last added sort without adding a rail", async () => {
    window.localStorage.setItem(
      "spiritflix_library_ui_state",
      JSON.stringify({
        selectedLibraryId: "library-1",
        selectedModel: null,
        selectedManualTag: null,
        excludedCategories: [],
        viewMode: "grid",
        sortMode: "dateAdded",
        sortDirection: "desc",
        orientationFilter: "all",
        filtersOpen: false,
        pageIndex: 0,
      }),
    );
    const alphabeticalLibraryItem = {
      ...modelItem,
      Id: "alpha-library",
      Name: "Alphabetical Library Page Item",
      DateCreated: "2026-01-01T00:00:00.000Z",
    };
    const realLatestItem = {
      ...landscapeItem,
      Id: "real-latest",
      Name: "Actual Latest Added Item",
      DateCreated: "2026-07-01T00:00:00.000Z",
    };

    render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraryItems: [alphabeticalLibraryItem],
          latestAdded: [realLatestItem],
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    // The Library Last-added sort surfaces the real Latest Added feed item.
    expect(await screen.findByLabelText("Actual Latest Added Item")).toBeInTheDocument();
    // And the Library dashboard must NOT render a standalone "Latest Added" rail
    // (that section belongs to Home only).
    expect(screen.queryByRole("heading", { name: "Latest Added" })).not.toBeInTheDocument();
  });

  it("does not restart the full-library scan when toggling Models and Grid", async () => {
    const getLibraryItemsPage = vi.fn().mockResolvedValue({
      items: [modelItem, manualModelItem],
      totalRecordCount: 2,
      startIndex: 0,
      limit: 50,
      hasMore: false,
    });
    const client = createClient(emptyGallery, { getLibraryItemsPage } as Partial<JellyfinClient>);

    render(
      <SpiritFlixHome
        client={client}
        data={createData({
          libraryItems: [modelItem],
          continueWatching: [],
          watchHistory: [],
          libraryPaging: {
            loaded: 1,
            total: 2,
            pageSize: 1,
            hasMore: true,
          },
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    await waitFor(() => expect(getLibraryItemsPage).toHaveBeenCalledTimes(1), { timeout: 3000 });
    fireEvent.click(screen.getByRole("button", { name: /^models$/i }));
    await screen.findByRole("heading", { name: "Models" });
    fireEvent.click(screen.getByRole("button", { name: /^grid$/i }));
    fireEvent.click(screen.getByRole("button", { name: /^models$/i }));

    expect(getLibraryItemsPage).toHaveBeenCalledTimes(1);
  });

  it("keeps model groups ordered by video count even when face status changes", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/spiritflix/model-index")) {
          return Promise.resolve(Response.json({
            schema: "spiritflix-manual-model-index/v1",
            updatedAt: "2026-06-28T00:00:00.000Z",
            models: [{ modelName: "Zoey Uso", count: 2, catalogCount: 2, assignedCount: 0, catalogStatus: "profile-url", source: "registry" }],
            items: [],
          }));
        }
        return Promise.resolve(Response.json({
          schema: "spiritflix-manual-tag-index/v1",
          updatedAt: "2026-06-28T00:00:00.000Z",
          tags: [],
          items: [],
        }));
      }),
    );
    const oneVideoConfirmedModel: JellyfinItem = {
      ...modelItem,
      Id: "zoey-1",
      Name: "Zoey Solo",
      SeriesName: "Zoey Uso",
    };
    const manyVideoFolderItems: JellyfinItem[] = Array.from({ length: 4 }, (_, index) => ({
      ...modelItem,
      Id: `videos-from-x-${index + 1}`,
      Name: `Videos From X ${index + 1}`,
      SeriesName: "videos from x",
      Path: `/mnt/spirit-8tb/media/yes/videos from x/clip-${index + 1}.mp4`,
      MediaSources: [{ Path: `/mnt/spirit-8tb/media/yes/videos from x/clip-${index + 1}.mp4` }],
    }));
    const client = createClient();
    vi.mocked(client.getFaceOrganizerMetadata).mockResolvedValue({
      knownPerformers: [],
      videos: {
        "zoey-1": {
          itemId: "zoey-1",
          primaryPerformer: { name: "Zoey Uso", confidence: 0.99 },
          performers: [{ name: "Zoey Uso", confidence: 0.99 }],
          status: "confirmed",
          label: "Confirmed: Zoey Uso",
          confidence: 0.99,
          verificationNeeded: false,
        },
      },
      scannedCount: 1,
      generatedAt: "2026-06-21T04:08:00.000Z",
    });

    const { container } = render(
      <SpiritFlixHome
        client={client}
        data={createData({
          libraryItems: [oneVideoConfirmedModel, ...manyVideoFolderItems],
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /^models$/i }));
    expect(await screen.findByRole("heading", { name: "Models" })).toBeInTheDocument();

    await waitFor(() => {
      const labels = Array.from(container.querySelectorAll(".spiritflix-model-directory .spiritflix-model-card strong"))
        .map((node) => node.textContent);
      expect(labels).toEqual(["All Models", "Twitter", "Zoey Uso"]);
    });
  });

  it("renders library videos as 20-item pages with arrow navigation", async () => {
    const libraryItems = Array.from({ length: 45 }, (_, index) => ({
      ...modelItem,
      Id: `model-${String(index + 1).padStart(2, "0")}`,
      Name: `Scene ${String(index + 1).padStart(2, "0")}`,
    }));

    const { container } = render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraryItems,
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    await waitFor(() => {
      expect(container.querySelectorAll(".spiritflix-library-grid .spiritflix-feed-card")).toHaveLength(20);
    });
    expect(screen.getByText(/Page 1 of 3 \/ 1-20 of 45/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous video page" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Next video page" }));

    await waitFor(() => {
      expect(screen.getByText(/Page 2 of 3 \/ 21-40 of 45/i)).toBeInTheDocument();
    });
    expect(container.querySelectorAll(".spiritflix-library-grid .spiritflix-feed-card")).toHaveLength(20);

    fireEvent.click(screen.getByRole("button", { name: "Next video page" }));

    await waitFor(() => {
      expect(screen.getByText(/Page 3 of 3 \/ 41-45 of 45/i)).toBeInTheDocument();
    });
    expect(container.querySelectorAll(".spiritflix-library-grid .spiritflix-feed-card")).toHaveLength(5);
    expect(screen.getByRole("button", { name: "Next video page" })).toBeDisabled();
  });

  it("shows server-side library paging and asks for more videos without pretending all items are loaded", async () => {
    const libraryItems = Array.from({ length: 24 }, (_, index) => ({
      ...modelItem,
      Id: `paged-model-${String(index + 1).padStart(2, "0")}`,
      Name: `Paged Scene ${String(index + 1).padStart(2, "0")}`,
    }));
    const onLoadMoreLibrary = vi.fn();

    render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraryItems,
          continueWatching: [],
          watchHistory: [],
          libraryPaging: {
            loaded: 24,
            total: 90,
            pageSize: 24,
            hasMore: true,
          },
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
        onLoadMoreLibrary={onLoadMoreLibrary}
      />,
    );

    expect(await screen.findByText(/Page 1 of 2 \/ 1-20 of 24 loaded of 90/i)).toBeInTheDocument();
    const videoStat = Array.from(document.querySelectorAll(".spiritflix-library-stat"))
      .find((node) => node.textContent?.includes("Videos"));
    expect(videoStat).toHaveTextContent("90");
    expect(videoStat).toHaveTextContent("24 loaded");

    fireEvent.click(screen.getByRole("button", { name: "Next video page" }));
    await waitFor(() => expect(screen.getByText(/Page 2 of 2 \/ 21-24 of 24 loaded of 90/i)).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Next video page" }));

    expect(onLoadMoreLibrary).toHaveBeenCalledTimes(1);
  });

  it("restores the saved library page after a refresh", async () => {
    const libraryItems = Array.from({ length: 45 }, (_, index) => ({
      ...modelItem,
      Id: `model-${String(index + 1).padStart(2, "0")}`,
      Name: `Scene ${String(index + 1).padStart(2, "0")}`,
    }));
    window.localStorage.setItem(
      "spiritflix_library_ui_state",
      JSON.stringify({
        selectedLibraryId: "library-1",
        selectedModel: null,
        selectedManualTag: null,
        viewMode: "grid",
        sortMode: "title",
        sortDirection: "asc",
        orientationFilter: "all",
        filtersOpen: true,
        pageIndex: 1,
      }),
    );

    const { container } = render(
      <SpiritFlixHome
        client={createClient()}
        data={createData({
          libraryItems,
          continueWatching: [],
          watchHistory: [],
        })}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    expect(await screen.findByText(/Page 2 of 3 \/ 21-40 of 45/i)).toBeInTheDocument();
    expect(container.querySelector(".spiritflix-filter-trigger")).toHaveAttribute("aria-expanded", "true");
  });

  it("restores the saved history category after a refresh", async () => {
    window.localStorage.setItem(
      "spiritflix_library_ui_state",
      JSON.stringify({
        selectedLibraryId: "library-1",
        selectedModel: null,
        selectedManualTag: null,
        viewMode: "history",
        sortMode: "model",
        sortDirection: "desc",
        orientationFilter: "all",
        filtersOpen: false,
        pageIndex: 0,
      }),
    );

    const { container } = render(
      <SpiritFlixHome
        client={createClient()}
        data={createData()}
        loading={false}
        error=""
        session={{
          serverUrl: "https://jellyfin.local",
          accessToken: "token",
          userId: "user-1",
          username: "private-user",
        }}
        searchTerm=""
        serverInfo={{ ServerName: "Jellyfin" }}
        onLogout={vi.fn()}
        onRefresh={vi.fn()}
        onSearch={vi.fn()}
        onSelectHome={vi.fn()}
        onSelectLibrary={vi.fn()}
        onSelectModel={vi.fn()}
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    const historyButton = await screen.findByRole("button", { name: /history/i });
    expect(historyButton).toHaveAttribute("aria-pressed", "true");
    await waitFor(() => {
      expect(container.querySelector(".spiritflix-library-list--history")).toHaveTextContent("Watched On Fold");
    });
    expect(screen.queryByText(/Page 1 of/i)).not.toBeInTheDocument();
  });
});
