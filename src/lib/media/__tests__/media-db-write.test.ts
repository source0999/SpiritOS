import { describe, expect, it } from "vitest";

import { MEDIA_DB_SEED_ORDER } from "@/lib/media/media-db-seed";
import {
  writeMediaDbSeedRecords,
  type MediaDbWritableTables,
} from "@/lib/media/media-db-write";
import { durableDemoMediaRecords } from "@/lib/media/media-durable-demo-records";
import type { DurableMediaLibraryRecords } from "@/lib/media/media-durable-types";

function createWritableTableDoubles() {
  const writes: Array<{
    tableName: keyof DurableMediaLibraryRecords;
    recordCount: number;
  }> = [];
  const tables = Object.fromEntries(
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
  ) as MediaDbWritableTables;

  return { tables, writes };
}

describe("writeMediaDbSeedRecords", () => {
  it("writes durable demo records in dependency-safe seed order", async () => {
    const { tables, writes } = createWritableTableDoubles();

    await writeMediaDbSeedRecords(tables, durableDemoMediaRecords);

    expect(writes.map((write) => write.tableName)).toEqual(MEDIA_DB_SEED_ORDER);
  });

  it("returns a write summary with record counts for every table", async () => {
    const { tables } = createWritableTableDoubles();

    await expect(
      writeMediaDbSeedRecords(tables, durableDemoMediaRecords),
    ).resolves.toEqual({
      source: "durable-demo-media-records",
      entries: MEDIA_DB_SEED_ORDER.map((tableName) => ({
        tableName,
        recordCount: durableDemoMediaRecords[tableName].length,
      })),
    });
  });

  it("does not open IndexedDB directly", async () => {
    const { tables } = createWritableTableDoubles();

    await writeMediaDbSeedRecords(tables);

    expect(typeof globalThis.indexedDB).toBe("undefined");
  });
});
