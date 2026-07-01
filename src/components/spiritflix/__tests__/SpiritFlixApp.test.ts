import { describe, expect, it } from "vitest";
import {
  applyManualModelNameToHomeData,
  applyManualModelNameToQueue,
  buildLiveLibraryLoadingHomeData,
  buildSpiritFlixBrowsePath,
  inferPlaybackQueueForItem,
  removeDeletedItemFromHomeData,
  removeDeletedItemFromQueue,
  reorderQueueItems,
} from "../SpiritFlixApp";
import { filterItemsByVideoOrientation, getVideoOrientation } from "@/lib/spiritflix-orientation";
import type { JellyfinItem, SpiritFlixHomeData } from "@/lib/spiritflix-types";

function video(id: string, name: string): JellyfinItem {
  return {
    Id: id,
    Name: name,
    Type: "Video",
    MediaType: "Video",
  };
}

function trashedVideo(id: string, name: string): JellyfinItem {
  return {
    ...video(id, name),
    Path: `/mnt/spirit-8tb/media/.trash/20260621/yes/${name}.mp4`,
    MediaSources: [{ Path: `/mnt/spirit-8tb/media/.trash/20260621/yes/${name}.mp4` }],
  };
}

function homeData(overrides: Partial<SpiritFlixHomeData> = {}): SpiritFlixHomeData {
  return {
    libraries: [],
    playlists: [],
    selectedLibraryId: null,
    featuredItems: [],
    libraryItems: [],
    continueWatching: [],
    watchHistory: [],
    latestAdded: [],
    favorites: [],
    ...overrides,
  };
}

describe("inferPlaybackQueueForItem", () => {
  it("uses Latest Added as the details modal playback queue when the selected item came from that rail", () => {
    const first = video("latest-1", "Latest One");
    const second = video("latest-2", "Latest Two");

    const queue = inferPlaybackQueueForItem(
      first,
      homeData({
        latestAdded: [first, second],
        libraryItems: [first],
      }),
    );

    expect(queue?.sourceTitle).toBe("Latest Added");
    expect(queue?.items).toEqual([first, second]);
  });
});

describe("buildSpiritFlixBrowsePath", () => {
  it("uses the base SpiritFlix route for home browsing", () => {
    expect(buildSpiritFlixBrowsePath({ libraryId: null, modelName: null })).toBe("/spiritflix");
  });

  it("keeps library and model browsing state in the URL without a playback route", () => {
    expect(buildSpiritFlixBrowsePath({ libraryId: "library-1", modelName: "Sava Schultz" })).toBe(
      "/spiritflix?library=library-1&model=Sava+Schultz",
    );
  });
});

describe("buildLiveLibraryLoadingHomeData", () => {
  it("preserves library navigation but removes stale media rows during a live library load", () => {
    const stale = video("stale", "Stale Cached Clip");
    const next = buildLiveLibraryLoadingHomeData(
      homeData({
        libraries: [{ Id: "library-1", Name: "Library" }],
        selectedLibraryId: "library-1",
        libraryItems: [stale],
        continueWatching: [stale],
        watchHistory: [stale],
        latestAdded: [stale],
        favorites: [stale],
      }),
      "library-1",
    );

    expect(next.libraries).toEqual([{ Id: "library-1", Name: "Library" }]);
    expect(next.selectedLibraryId).toBe("library-1");
    expect(next.libraryItems).toEqual([]);
    expect(next.continueWatching).toEqual([]);
    expect(next.watchHistory).toEqual([]);
    expect(next.latestAdded).toEqual([]);
    expect(next.favorites).toEqual([]);
  });
});

describe("reorderQueueItems", () => {
  it("moves a dragged queue item before the item it is dropped over", () => {
    const first = video("first", "First");
    const second = video("second", "Second");
    const third = video("third", "Third");

    expect(reorderQueueItems([first, second, third], "third", "first")).toEqual([
      third,
      first,
      second,
    ]);
  });
});

describe("SpiritFlix delete cleanup helpers", () => {
  it("removes a deleted item from every home list", () => {
    const deleted = video("deleted", "Deleted");
    const kept = video("kept", "Kept");
    const next = removeDeletedItemFromHomeData(
      homeData({
        featuredItems: [deleted, kept],
        libraryItems: [deleted, kept],
        continueWatching: [deleted, kept],
        watchHistory: [deleted, kept],
        latestAdded: [deleted, kept],
        favorites: [deleted, kept],
      }),
      deleted.Id,
    );

    expect(next.featuredItems).toEqual([kept]);
    expect(next.libraryItems).toEqual([kept]);
    expect(next.continueWatching).toEqual([kept]);
    expect(next.watchHistory).toEqual([kept]);
    expect(next.latestAdded).toEqual([kept]);
    expect(next.favorites).toEqual([kept]);
  });

  it("removes trash-folder items from every home list", () => {
    const trashed = trashedVideo("trashed", "Trashed");
    const kept = video("kept", "Kept");
    const next = removeDeletedItemFromHomeData(
      homeData({
        featuredItems: [trashed, kept],
        libraryItems: [trashed, kept],
        continueWatching: [trashed, kept],
        watchHistory: [trashed, kept],
        latestAdded: [trashed, kept],
        favorites: [trashed, kept],
      }),
      "not-the-trash-id",
    );

    expect(next.featuredItems).toEqual([kept]);
    expect(next.libraryItems).toEqual([kept]);
    expect(next.continueWatching).toEqual([kept]);
    expect(next.watchHistory).toEqual([kept]);
    expect(next.latestAdded).toEqual([kept]);
    expect(next.favorites).toEqual([kept]);
  });

  it("removes the deleted queue item and advances to the requested next item", () => {
    const first = video("first", "First");
    const deleted = video("deleted", "Deleted");
    const third = video("third", "Third");

    const result = removeDeletedItemFromQueue(
      {
        items: [first, deleted, third],
        originalItems: [first, deleted, third],
        currentIndex: 1,
        sourceTitle: "Library Shuffle",
      },
      deleted.Id,
      third,
    );

    expect(result.nextItem).toBe(third);
    expect(result.queue?.items).toEqual([first, third]);
    expect(result.queue?.originalItems).toEqual([first, third]);
    expect(result.queue?.currentIndex).toBe(1);
  });

  it("removes trash-folder items from playback queues", () => {
    const first = video("first", "First");
    const trashed = trashedVideo("trashed", "Trashed");
    const third = video("third", "Third");

    const result = removeDeletedItemFromQueue(
      {
        items: [first, trashed, third],
        originalItems: [first, trashed, third],
        currentIndex: 0,
        sourceTitle: "Library Shuffle",
      },
      "not-the-trash-id",
      null,
    );

    expect(result.queue?.items).toEqual([first, third]);
    expect(result.queue?.originalItems).toEqual([first, third]);
  });
});

describe("SpiritFlix manual model optimistic updates", () => {
  it("updates all visible home copies and playback queue copies for a saved model", () => {
    const saved = video("saved", "Saved");
    const other = video("other", "Other");
    const nextHome = applyManualModelNameToHomeData(
      homeData({
        featuredItems: [saved],
        libraryItems: [saved, other],
        continueWatching: [saved],
        watchHistory: [saved],
        latestAdded: [saved],
        favorites: [saved],
      }),
      "saved",
      "Luna x pearl",
    );
    const nextQueue = applyManualModelNameToQueue(
      {
        items: [saved, other],
        originalItems: [saved, other],
        currentIndex: 0,
        sourceTitle: "Portrait Shuffle",
      },
      "saved",
      "Luna x pearl",
    );

    expect(nextHome.libraryItems[0].ManualModelName).toBe("Luna x pearl");
    expect(nextHome.featuredItems[0].ManualModelName).toBe("Luna x pearl");
    expect(nextHome.continueWatching[0].ManualModelName).toBe("Luna x pearl");
    expect(nextHome.watchHistory[0].ManualModelName).toBe("Luna x pearl");
    expect(nextHome.latestAdded[0].ManualModelName).toBe("Luna x pearl");
    expect(nextHome.favorites[0].ManualModelName).toBe("Luna x pearl");
    expect(nextHome.libraryItems[1].ManualModelName).toBeUndefined();
    expect(nextQueue?.items[0].ManualModelName).toBe("Luna x pearl");
    expect(nextQueue?.originalItems?.[0].ManualModelName).toBe("Luna x pearl");
    expect(nextQueue?.items[1].ManualModelName).toBeUndefined();
  });
});

describe("SpiritFlix video orientation filters", () => {
  it("classifies portrait and landscape videos from Jellyfin video stream dimensions", () => {
    const portrait = {
      ...video("portrait", "Portrait"),
      MediaStreams: [{ Type: "Video", Width: 1080, Height: 1920 }],
    };
    const landscape = {
      ...video("landscape", "Landscape"),
      MediaStreams: [{ Type: "Video", Width: 1920, Height: 1080 }],
    };
    const unknown = video("unknown", "Unknown");

    expect(getVideoOrientation(portrait)).toBe("portrait");
    expect(getVideoOrientation(landscape)).toBe("landscape");
    expect(getVideoOrientation(unknown)).toBeNull();
    expect(filterItemsByVideoOrientation([portrait, landscape, unknown], "portrait")).toEqual([portrait]);
  });
});
