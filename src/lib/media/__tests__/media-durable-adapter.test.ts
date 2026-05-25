import { describe, expect, it } from "vitest";

import { mediaProfiles as localMediaProfiles } from "@/lib/media/demo-catalog";
import { adaptDurableMediaLibrary, DurableMediaAdapterError } from "@/lib/media/media-durable-adapter";
import { durableDemoMediaRecords } from "@/lib/media/media-durable-demo-records";
import type { DurableMediaLibraryRecords } from "@/lib/media/media-durable-types";

function cloneRecords(): DurableMediaLibraryRecords {
  return JSON.parse(JSON.stringify(durableDemoMediaRecords)) as DurableMediaLibraryRecords;
}

describe("adaptDurableMediaLibrary", () => {
  it("maps durable profile records into current media profile shape", () => {
    const adapter = adaptDurableMediaLibrary(cloneRecords());

    expect(adapter.mediaProfiles).toEqual(localMediaProfiles);
  });

  it("maps durable movie records into current movie item shape", () => {
    const adapter = adaptDurableMediaLibrary(cloneRecords());
    const localLights = adapter.getCatalogItemById("movie-local-lights");

    expect(localLights).toMatchObject({
      id: "movie-local-lights",
      type: "movie",
      title: "Local Lights",
      mediaSource: "/media/sample-movie.mp4",
      sourceKind: "authorized-local-sample",
      sourceLabel: "Authorized local MP4 sample",
      metadata: {
        releaseYear: 2026,
        genres: ["Drama", "Local Demo"],
        rating: "PG",
        libraryStatus: "ready-for-owned-file",
        localFileStrategy: "manual-public-media-match",
        curation: {
          expectedFileName: "sample-movie.mp4",
        },
      },
    });
  });

  it("maps durable show, season, and episode records into current show shape", () => {
    const adapter = adaptDurableMediaLibrary(cloneRecords());

    expect(adapter.demoCatalog.shows).toHaveLength(1);
    expect(adapter.demoCatalog.shows[0]).toMatchObject({
      id: "show-signal-house",
      type: "show",
      title: "Signal House",
      seasons: [
        {
          id: "signal-house-season-1",
          seasonNumber: 1,
          title: "Season 1",
        },
      ],
    });
    expect(adapter.demoCatalog.shows[0].seasons[0].episodes.map((episode) => episode.id)).toEqual([
      "episode-signal-house-s1e1",
      "episode-signal-house-s1e2",
    ]);
    expect(adapter.demoCatalog.shows[0].seasons[0].episodes[0]).toMatchObject({
      type: "episode",
      showId: "show-signal-house",
      seasonId: "signal-house-season-1",
      episodeNumber: 1,
      mediaSource: "/media/sample-episode-1.mp4",
    });
  });

  it("assembles flattened catalog items deterministically", () => {
    const adapter = adaptDurableMediaLibrary(cloneRecords());

    expect(adapter.flattenedCatalogItems.map((item) => item.id)).toEqual([
      "movie-local-lights",
      "movie-workbench-weekend",
      "episode-signal-house-s1e1",
      "episode-signal-house-s1e2",
    ]);
  });

  it("maps durable profile state records into current MediaProfileState shape", () => {
    const adapter = adaptDurableMediaLibrary(cloneRecords());
    const brittonState = adapter.loadProfileState("britton");
    const friendState = adapter.loadProfileState("friend");

    expect(brittonState.watchlistIds).toEqual(["movie-local-lights"]);
    expect(brittonState.progress["movie-local-lights"]).toMatchObject({
      itemId: "movie-local-lights",
      seconds: 65,
    });
    expect(brittonState.curationChecks["movie-local-lights"]).toMatchObject({
      authorizedFileConfirmed: true,
    });
    expect(brittonState.playbackAcceptance["movie-local-lights"]).toMatchObject({
      sourceReadyConfirmed: true,
      refreshProgressConfirmed: true,
      profileIsolationConfirmed: true,
    });
    expect(friendState).toEqual({
      profileId: "friend",
      watchlistIds: [],
      progress: {},
      curationChecks: {},
      playbackAcceptance: {},
    });
  });

  it("reports catalog items that reference missing media sources", () => {
    const records = cloneRecords();
    records.catalogItems[0].mediaSourceId = "missing-source";

    expect(() => adaptDurableMediaLibrary(records)).toThrow(DurableMediaAdapterError);
    expect(() => adaptDurableMediaLibrary(records)).toThrow(
      "Missing media source: missing-source",
    );
  });

  it("reports orphan episode placement records", () => {
    const records = cloneRecords();
    records.episodePlacements[0].seasonId = "missing-season";

    expect(() => adaptDurableMediaLibrary(records)).toThrow(DurableMediaAdapterError);
    expect(() => adaptDurableMediaLibrary(records)).toThrow(
      "Missing season: missing-season",
    );
  });
});
