import { describe, expect, it } from "vitest";

import { MEDIA_DB_SEED_ORDER } from "@/lib/media/media-db-seed";
import { seedMediaDbWhenAvailable } from "@/lib/media/media-db-browser-write";
import { durableDemoMediaRecords } from "@/lib/media/media-durable-demo-records";
import type { DurableMediaLibraryRecords } from "@/lib/media/media-durable-types";

function createFakeDb() {
  const writes: Array<{
    tableName: keyof DurableMediaLibraryRecords;
    recordCount: number;
  }> = [];
  const db = Object.fromEntries(
    MEDIA_DB_SEED_ORDER.map((tableName) => [
      tableName,
      {
        bulkPut: async (
          records: DurableMediaLibraryRecords[typeof tableName],
        ) => {
          writes.push({
            tableName,
            recordCount: records.length,
          });
        },
      },
    ]),
  );

  return { db, writes };
}

describe("seedMediaDbWhenAvailable", () => {
  it("returns unavailable when IndexedDB/Dexie is not available", async () => {
    await expect(seedMediaDbWhenAvailable(null)).resolves.toEqual({
      status: "unavailable",
      reason: "indexeddb-unavailable",
    });
  });

  it("writes seed records when a database-like table boundary is provided", async () => {
    const { db, writes } = createFakeDb();

    await expect(seedMediaDbWhenAvailable(db as never)).resolves.toMatchObject({
      status: "seeded",
      summary: {
        source: "durable-demo-media-records",
      },
    });
    expect(writes.map((write) => write.tableName)).toEqual(MEDIA_DB_SEED_ORDER);
    expect(writes.map((write) => write.recordCount)).toEqual(
      MEDIA_DB_SEED_ORDER.map(
        (tableName) => durableDemoMediaRecords[tableName].length,
      ),
    );
  });
});
