import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SpiritFlixHome } from "../SpiritFlixHome";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem, SpiritFlixGalleryResponse, SpiritFlixHomeData } from "@/lib/spiritflix-types";

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

function createClient(gallery: SpiritFlixGalleryResponse = emptyGallery): JellyfinClient {
  return {
    getFaceOrganizerMetadata: vi.fn().mockResolvedValue({
      knownPerformers: [],
      videos: {},
      scannedCount: 0,
      generatedAt: "2026-06-06T12:31:00.000Z",
    }),
    getGallery: vi.fn().mockResolvedValue(gallery),
    getImageObjectUrl: vi.fn().mockRejectedValue(new Error("No image in test")),
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
    window.matchMedia = vi.fn().mockReturnValue({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });
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
  });

  it("shows resumable watch history in Continue Watching when Jellyfin misses the resume lane", async () => {
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
        onOpenDetails={vi.fn()}
        onPlay={vi.fn()}
      />,
    );

    expect(
      await screen.findByRole("button", { name: /resume watched on fold at 3:00 \/ 10:00/i }),
    ).toBeInTheDocument();
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
});
