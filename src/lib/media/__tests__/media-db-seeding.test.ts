import { describe, expect, it } from "vitest";

import {
  createMediaDbSeedPlan,
  getMediaDbSeedRecords,
  MEDIA_DB_SEED_ORDER,
} from "@/lib/media/media-db-seed";
import { durableDemoMediaRecords } from "@/lib/media/media-durable-demo-records";

describe("media-db-seeding", () => {
  it("keeps seed order aligned with dependency-safe media tables", () => {
    expect(MEDIA_DB_SEED_ORDER).toEqual([
      "accounts",
      "profiles",
      "sources",
      "catalogItems",
      "genres",
      "catalogItemGenres",
      "shows",
      "seasons",
      "episodePlacements",
      "watchlistEntries",
      "playbackProgress",
      "curationChecks",
      "playbackAcceptance",
    ]);
  });

  it("creates a seed plan with counts for every durable record group", () => {
    expect(createMediaDbSeedPlan()).toEqual({
      source: "durable-demo-media-records",
      entries: MEDIA_DB_SEED_ORDER.map((tableName) => ({
        tableName,
        recordCount: durableDemoMediaRecords[tableName].length,
      })),
    });
  });

  it("returns the static durable demo records without cloning or writing", () => {
    expect(getMediaDbSeedRecords()).toBe(durableDemoMediaRecords);
  });
});
