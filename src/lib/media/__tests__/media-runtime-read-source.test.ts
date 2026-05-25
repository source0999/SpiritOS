import { describe, expect, it } from "vitest";

import { durableDemoMediaRecords } from "@/lib/media/media-durable-demo-records";
import type { DurableMediaLibraryRecords } from "@/lib/media/media-durable-types";
import { mediaCatalogSource } from "@/lib/media/media-catalog-source";
import { resolveMediaRuntimeReadSource } from "@/lib/media/media-runtime-read-source";

function createFakeDb(records: DurableMediaLibraryRecords = durableDemoMediaRecords) {
  const reads: Array<keyof DurableMediaLibraryRecords> = [];
  const db = Object.fromEntries(
    Object.keys(records).map((tableName) => [
      tableName,
      {
        toArray: async () => {
          reads.push(tableName as keyof DurableMediaLibraryRecords);
          return records[tableName as keyof DurableMediaLibraryRecords];
        },
      },
    ]),
  );

  return { db, reads };
}

describe("resolveMediaRuntimeReadSource", () => {
  it("falls back to the local proof catalog when IndexedDB is unavailable", async () => {
    await expect(resolveMediaRuntimeReadSource({ db: null })).resolves.toEqual({
      status: "local-fallback",
      reason: "indexeddb-unavailable",
      adapterResult: mediaCatalogSource,
    });
  });

  it("returns Dexie adapter results when a DB read boundary is available", async () => {
    const { db, reads } = createFakeDb();

    await expect(resolveMediaRuntimeReadSource({ db: db as never })).resolves.toMatchObject({
      status: "dexie",
      adapterResult: {
        mediaProfiles: expect.arrayContaining([
          {
            id: "britton",
            name: "Britton",
          },
        ]),
        flattenedCatalogItems: expect.arrayContaining([
          expect.objectContaining({
            id: "movie-local-lights",
            title: "Local Lights",
          }),
        ]),
      },
    });
    expect(reads).toEqual(Object.keys(durableDemoMediaRecords));
  });
});
