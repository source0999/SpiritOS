import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SpiritFlixApp } from "../SpiritFlixApp";
import type { JellyfinClient, JellyfinItemPage } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem, SpiritFlixSession } from "@/lib/spiritflix-types";

type Deferred<T> = {
  promise: Promise<T>;
  resolve: (value: T) => void;
  reject: (error: unknown) => void;
};

const mocks = vi.hoisted(() => ({
  client: null as unknown as JellyfinClient,
  session: {
    serverUrl: "https://jellyfin.local",
    accessToken: "token",
    userId: "user-1",
    username: "private-user",
  } as SpiritFlixSession,
}));

vi.mock("@/lib/spiritflix-jellyfin-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/spiritflix-jellyfin-client")>();
  return {
    ...actual,
    getStoredSession: vi.fn(() => mocks.session),
    JellyfinClient: vi.fn(function JellyfinClient() { return mocks.client; }),
  };
});

function deferred<T>(): Deferred<T> {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((nextResolve, nextReject) => {
    resolve = nextResolve;
    reject = nextReject;
  });
  return { promise, resolve, reject };
}

function page(items: JellyfinItem[], limit = 48): JellyfinItemPage {
  return {
    items,
    totalRecordCount: items.length,
    startIndex: 0,
    limit,
    hasMore: false,
  };
}

const libraryItem: JellyfinItem = {
  Id: "scene-1",
  Name: "Scene One",
  Type: "Video",
  MediaType: "Video",
  SeriesName: "Sava Schultz",
  MediaStreams: [{ Type: "Video", Width: 1080, Height: 1920 }],
};

function createClient(overrides: Record<string, unknown> = {}): JellyfinClient {
  return {
    checkPublicInfo: vi.fn().mockResolvedValue({ ServerName: "Jellyfin" }),
    getLibraries: vi.fn().mockResolvedValue([{ Id: "library-1", Name: "Library", CollectionType: "movies" }]),
    getLibraryItemsPage: vi.fn().mockResolvedValue(page([libraryItem])),
    getLibraryFeaturedItemsPage: vi.fn().mockResolvedValue(page([])),
    getContinueWatchingPage: vi.fn().mockResolvedValue(page([])),
    getLibraryResumeItemsPage: vi.fn().mockResolvedValue(page([])),
    getWatchHistoryPage: vi.fn().mockResolvedValue(page([])),
    getLatestAddedPage: vi.fn().mockResolvedValue(page([])),
    getFavoritesPage: vi.fn().mockResolvedValue(page([])),
    getLibraryLatestAddedPage: vi.fn().mockResolvedValue(page([])),
    getLibraryFavoriteItemsPage: vi.fn().mockResolvedValue(page([])),
    getFaceOrganizerMetadata: vi.fn().mockResolvedValue({ knownPerformers: [], videos: {}, scannedCount: 0 }),
    getGallery: vi.fn().mockResolvedValue({
      schema: "spiritflix-model-gallery/v1",
      generatedAt: "2026-07-04T00:00:00.000Z",
      items: [],
      groups: [],
      summary: { galleryItems: 0, modelsWithGallery: 0 },
    }),
    getImageProxyUrl: vi.fn(() => "/api/spiritflix/jellyfin-image?test=1"),
    getImageObjectUrl: vi.fn().mockRejectedValue(new Error("No image in test")),
    getAllLibraryItems: vi.fn().mockResolvedValue([]),
    ...overrides,
  } as unknown as JellyfinClient;
}

describe("SpiritFlixApp live library loading", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
    window.history.replaceState(window.history.state, "", "/spiritflix?library=library-1");
    window.matchMedia = vi.fn().mockReturnValue({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(Response.json({
        schema: "spiritflix-manual-model-index/v1",
        updatedAt: "2026-07-04T00:00:00.000Z",
        models: [],
        items: [],
      })),
    );
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("does not show a blocking loader splash while shelves stream in", async () => {
    const slowShelves = deferred<JellyfinItemPage>();
    mocks.client = createClient({
      getLibraryFeaturedItemsPage: vi.fn(() => slowShelves.promise),
      getLibraryResumeItemsPage: vi.fn(() => slowShelves.promise),
      getWatchHistoryPage: vi.fn(() => slowShelves.promise),
      getLibraryLatestAddedPage: vi.fn(() => slowShelves.promise),
      getLibraryFavoriteItemsPage: vi.fn(() => slowShelves.promise),
    });

    render(<SpiritFlixApp />);

    await waitFor(() => expect(mocks.client.getLibraryItemsPage).toHaveBeenCalled());
    // The blocking splash was removed entirely — content streams in without a
    // fake progress gate. No progressbar should ever appear for library loads.
    await waitFor(() => expect(screen.queryByRole("progressbar")).not.toBeInTheDocument());
  });

  it("does not flash the restore-session splash at 0 percent", async () => {
    mocks.client = createClient();

    render(<SpiritFlixApp />);

    expect(screen.queryByRole("progressbar", { name: /connecting to jellyfin/i })).not.toBeInTheDocument();
    await waitFor(() => expect(mocks.client.getLibraryItemsPage).toHaveBeenCalled());
  });

  it("does not block or time out when the first Jellyfin library request never settles", async () => {
    vi.useFakeTimers();
    mocks.client = createClient({
      getLibraries: vi.fn(() => new Promise(() => {})),
    });

    render(<SpiritFlixApp />);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    // No blocking loader, no fake timeout error UI — the app simply waits for
    // the request and renders whatever is available.
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    expect(screen.queryByText("Jellyfin request timed out while loading library data.")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
  });

  it("uses the route library for silent focus refreshes on mobile navigation races", async () => {
    const libraries = [
      { Id: "library-1", Name: "Library", CollectionType: "movies" },
      { Id: "library-2", Name: "Other", CollectionType: "movies" },
    ];
    const getLibraryItemsPage = vi.fn((libraryId: string) =>
      Promise.resolve(
        page([
          {
            ...libraryItem,
            Id: `${libraryId}-scene`,
            Name: `${libraryId} Scene`,
          },
        ]),
      ),
    );
    mocks.client = createClient({
      getLibraries: vi.fn().mockResolvedValue(libraries),
      getLibraryItemsPage,
    });

    render(<SpiritFlixApp />);

    await waitFor(() => expect(getLibraryItemsPage).toHaveBeenCalledWith("library-1", expect.objectContaining({ fields: "card" })));
    await waitFor(() => expect(screen.queryByRole("progressbar")).not.toBeInTheDocument());

    getLibraryItemsPage.mockClear();
    window.history.pushState(window.history.state, "", "/spiritflix?library=library-2");

    await act(async () => {
      window.dispatchEvent(new Event("focus"));
    });

    await waitFor(() => expect(getLibraryItemsPage).toHaveBeenCalledWith("library-2", expect.objectContaining({ fields: "card" })));
    expect(getLibraryItemsPage).not.toHaveBeenCalledWith("library-1", expect.anything());
  });

  it("does not show the blocking loader when switching libraries over visible content", async () => {
    const libraries = [
      { Id: "library-1", Name: "Library", CollectionType: "movies" },
      { Id: "library-2", Name: "Other", CollectionType: "movies" },
    ];
    const slowOtherLibrary = deferred<JellyfinItemPage>();
    const getLibraryItemsPage = vi.fn((libraryId: string) =>
      libraryId === "library-2"
        ? slowOtherLibrary.promise
        : Promise.resolve(page([{ ...libraryItem, Id: "library-1-scene", Name: "Library One Scene" }])),
    );
    mocks.client = createClient({
      getLibraries: vi.fn().mockResolvedValue(libraries),
      getLibraryItemsPage,
    });

    render(<SpiritFlixApp />);

    expect(await screen.findAllByText("Library One Scene")).not.toHaveLength(0);
    await waitFor(() => expect(screen.queryByRole("progressbar")).not.toBeInTheDocument());

    await act(async () => {
      screen.getByRole("button", { name: "Other" }).click();
    });

    await waitFor(() => expect(getLibraryItemsPage).toHaveBeenCalledWith("library-2", expect.objectContaining({ fields: "card" })));
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();

    slowOtherLibrary.resolve(page([{ ...libraryItem, Id: "library-2-scene", Name: "Other Scene" }]));
    expect(await screen.findAllByText("Other Scene")).not.toHaveLength(0);
  });

  it("honors the Library navbar shell route instead of forcing it to yes", async () => {
    const libraries = [
      {
        Id: "home-videos-shell",
        Name: "Home Videos and Photos",
        Type: "MediaBrowser.Controller.Entities.CollectionFolder",
        CollectionType: "homevideos",
        Path: "/config/root/default/Home Videos and Photos",
      },
      {
        Id: "yes-folder",
        Name: "yes",
        Type: "Folder",
        Path: "/media/yes",
      },
    ];
    const getLibraryItemsPage = vi.fn((libraryId: string) =>
      Promise.resolve(
        page([
          {
            ...libraryItem,
            Id: `${libraryId}-scene`,
            Name: `${libraryId} Scene`,
          },
        ]),
      ),
    );
    mocks.client = createClient({
      getLibraries: vi.fn().mockResolvedValue(libraries),
      getLibraryItemsPage,
    });
    window.history.replaceState(window.history.state, "", "/spiritflix?library=home-videos-shell");

    render(<SpiritFlixApp />);

    await waitFor(() => expect(getLibraryItemsPage).toHaveBeenCalledWith("home-videos-shell", expect.objectContaining({ fields: "card" })));
    expect(getLibraryItemsPage).not.toHaveBeenCalledWith("yes-folder", expect.anything());
    expect(window.location.search).toBe("?library=home-videos-shell");
  });

  it("refreshes latest added immediately when a mobile tab comes back into focus", async () => {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query.includes("pointer: coarse"),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }));
    const staleUpload = { ...libraryItem, Id: "old-upload", Name: "Old Upload" };
    const freshUpload = { ...libraryItem, Id: "fresh-upload", Name: "Fresh Phone Upload" };
    window.history.replaceState(window.history.state, "", "/spiritflix");
    const getLatestAddedPage = vi
      .fn()
      .mockResolvedValueOnce(page([staleUpload], 12))
      .mockResolvedValue(page([freshUpload], 12));
    mocks.client = createClient({ getLatestAddedPage });

    render(<SpiritFlixApp />);

    expect(await screen.findAllByText("Old Upload")).not.toHaveLength(0);
    await waitFor(() => expect(getLatestAddedPage).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.queryByRole("progressbar")).not.toBeInTheDocument());

    await act(async () => {
      window.dispatchEvent(new Event("focus"));
    });

    await waitFor(() => expect(getLatestAddedPage).toHaveBeenCalledTimes(2));
    expect(await screen.findAllByText("Fresh Phone Upload")).not.toHaveLength(0);
  });

  it("loads the same latest added count on mobile as desktop", async () => {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query.includes("pointer: coarse"),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }));
    const getLatestAddedPage = vi.fn().mockResolvedValue(page([], 18));
    mocks.client = createClient({ getLatestAddedPage });
    window.history.replaceState(window.history.state, "", "/spiritflix");

    render(<SpiritFlixApp />);

    await waitFor(() => expect(getLatestAddedPage).toHaveBeenCalledWith(expect.objectContaining({ limit: 18, fields: "card" })));
  });
});
