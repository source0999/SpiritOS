import { describe, expect, it } from "vitest";

import { readMediaDbWhenAvailable } from "@/lib/media/media-db-browser-read";
import { durableDemoMediaRecords } from "@/lib/media/media-durable-demo-records";
import type { DurableMediaLibraryRecords } from "@/lib/media/media-durable-types";

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

describe("readMediaDbWhenAvailable", () => {
  it("returns unavailable when IndexedDB/Dexie is not available", async () => {
    await expect(readMediaDbWhenAvailable(null)).resolves.toEqual({
      status: "unavailable",
      reason: "indexeddb-unavailable",
    });
  });

  it("returns an adapted media library when a DB boundary is available", async () => {
    const { db, reads } = createFakeDb();

    await expect(readMediaDbWhenAvailable(db as never)).resolves.toMatchObject({
      status: "ready",
      adapterResult: {
        mediaProfiles: expect.arrayContaining([
          {
            id: "britton",
            name: "Britton",
          },
        ]),
        demoCatalog: {
          movies: expect.arrayContaining([
            expect.objectContaining({
              id: "movie-local-lights",
              title: "Local Lights",
            }),
          ]),
        },
      },
    });
    expect(reads).toEqual(Object.keys(durableDemoMediaRecords));
  });
});
