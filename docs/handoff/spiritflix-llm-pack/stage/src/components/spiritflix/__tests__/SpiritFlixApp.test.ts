import { describe, expect, it } from "vitest";
import { buildSpiritFlixBrowsePath, inferPlaybackQueueForItem } from "../SpiritFlixApp";
import type { JellyfinItem, SpiritFlixHomeData } from "@/lib/spiritflix-types";

function video(id: string, name: string): JellyfinItem {
  return {
    Id: id,
    Name: name,
    Type: "Video",
    MediaType: "Video",
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
