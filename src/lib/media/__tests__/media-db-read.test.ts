import { describe, expect, it } from "vitest";

import {
  createMediaDbReadRepository,
  readMediaDbRecords,
  type MediaDbReadableTables,
} from "@/lib/media/media-db-read";
import { durableDemoMediaRecords } from "@/lib/media/media-durable-demo-records";
import type { DurableMediaLibraryRecords } from "@/lib/media/media-durable-types";

function createReadableTableDoubles(
  records: DurableMediaLibraryRecords = durableDemoMediaRecords,
) {
  const reads: Array<keyof DurableMediaLibraryRecords> = [];
  const tables = Object.fromEntries(
    Object.keys(records).map((tableName) => [
      tableName,
      {
        toArray: async () => {
          reads.push(tableName as keyof DurableMediaLibraryRecords);
          return records[tableName as keyof DurableMediaLibraryRecords];
        },
      },
    ]),
  ) as MediaDbReadableTables;

  return { tables, reads };
}

describe("media-db-read", () => {
  it("reads durable media records from every DB table", async () => {
    const { tables, reads } = createReadableTableDoubles();

    await expect(readMediaDbRecords(tables)).resolves.toEqual(
      durableDemoMediaRecords,
    );
    expect(reads).toEqual(Object.keys(durableDemoMediaRecords));
  });

  it("adapts DB records through the durable media adapter", async () => {
    const { tables } = createReadableTableDoubles();
    const repository = createMediaDbReadRepository(tables);

    const adapterResult = await repository.getAdapterResult();

    expect(adapterResult.mediaProfiles).toContainEqual({
      id: "britton",
      name: "Britton",
    });
    expect(adapterResult.demoCatalog.movies).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "movie-local-lights",
          title: "Local Lights",
        }),
      ]),
    );
  });

  it("does not open IndexedDB directly", async () => {
    const { tables } = createReadableTableDoubles();

    await readMediaDbRecords(tables);

    expect(typeof globalThis.indexedDB).toBe("undefined");
  });
});
