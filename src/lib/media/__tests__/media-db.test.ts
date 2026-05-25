import { describe, expect, it } from "vitest";

import {
  isBrowserMediaDbAvailable,
  MEDIA_DB_NAME,
  MEDIA_DB_STORES,
  MEDIA_DB_VERSION,
  mediaDb,
  SpiritMediaDB,
} from "@/lib/media/media-db";

describe("media-db", () => {
  it("defines the dedicated media Dexie database name and version", () => {
    expect(MEDIA_DB_NAME).toBe("SpiritMediaDB");
    expect(MEDIA_DB_VERSION).toBe(1);
  });

  it("defines the expected media metadata stores and indexes", () => {
    expect(MEDIA_DB_STORES).toEqual({
      accounts: "id, updatedAt",
      profiles: "id, accountId, sortOrder, updatedAt",
      sources: "id, accountId, sourceKind, updatedAt",
      catalogItems: "id, accountId, mediaSourceId, type, updatedAt",
      genres: "id, accountId, name, updatedAt",
      catalogItemGenres:
        "[catalogItemId+genreId], catalogItemId, genreId, sortOrder",
      shows: "id, accountId, updatedAt",
      seasons: "id, showId, seasonNumber, updatedAt",
      episodePlacements: "catalogItemId, showId, seasonId, episodeNumber",
      watchlistEntries:
        "[profileId+catalogItemId], profileId, catalogItemId, createdAt",
      playbackProgress:
        "[profileId+catalogItemId], profileId, catalogItemId, updatedAt",
      curationChecks:
        "[profileId+catalogItemId], profileId, catalogItemId, updatedAt",
      playbackAcceptance:
        "[profileId+catalogItemId], profileId, catalogItemId, updatedAt",
    });
  });

  it("keeps the module-level database closed outside browser IndexedDB", () => {
    expect(isBrowserMediaDbAvailable()).toBe(false);
    expect(mediaDb).toBeNull();
  });

  it("can construct the schema without opening IndexedDB", () => {
    const db = new SpiritMediaDB();

    expect(db.name).toBe(MEDIA_DB_NAME);
    expect(db.tables.map((table) => table.name).sort()).toEqual(
      Object.keys(MEDIA_DB_STORES).sort(),
    );

    db.close();
  });
});
