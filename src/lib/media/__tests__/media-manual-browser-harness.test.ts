import { describe, expect, it } from "vitest";

import { MEDIA_DB_SEED_ORDER } from "@/lib/media/media-db-seed";
import type { DurableMediaLibraryRecords } from "@/lib/media/media-durable-types";
import type { MediaLocalStorageMigratedRecords } from "@/lib/media/media-local-storage-migration";
import {
  installMediaManualBrowserHarness,
  MEDIA_MANUAL_BROWSER_HARNESS_GLOBAL,
  type MediaManualBrowserHarness,
} from "@/lib/media/media-manual-browser-harness";
import {
  createMediaProfileStorageKey,
  MEDIA_SELECTED_PROFILE_STORAGE_KEY,
} from "@/lib/media/media-local-storage-snapshot";

const checkedAt = "2026-05-23T20:35:00.000Z";
const migrationWriteOrder: Array<keyof MediaLocalStorageMigratedRecords> = [
  "watchlistEntries",
  "playbackProgress",
  "curationChecks",
  "playbackAcceptance",
];

type HarnessWindowDouble = {
  localStorage?: Storage;
  [MEDIA_MANUAL_BROWSER_HARNESS_GLOBAL]?: MediaManualBrowserHarness;
};

function createStorage(items: Record<string, string>) {
  return {
    getItem: (key: string) => items[key] ?? null,
    setItem: () => undefined,
    removeItem: () => undefined,
    clear: () => undefined,
    key: () => null,
    length: Object.keys(items).length,
  } as Storage;
}

function createFakeDb() {
  const writes: Array<{
    tableName: keyof DurableMediaLibraryRecords | keyof MediaLocalStorageMigratedRecords;
    recordCount: number;
  }> = [];
  const tableNames = Array.from(
    new Set([...MEDIA_DB_SEED_ORDER, ...migrationWriteOrder]),
  );
  const db = Object.fromEntries(
    tableNames.map((tableName) => [
      tableName,
      {
        bulkPut: async (records: unknown[]) => {
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

describe("installMediaManualBrowserHarness", () => {
  it("returns null outside a browser window boundary", () => {
    expect(
      installMediaManualBrowserHarness({
        targetWindow: null,
      }),
    ).toBeNull();
  });

  it("installs and uninstalls the manual harness on an explicit window", () => {
    const targetWindow: HarnessWindowDouble = {};

    const harness = installMediaManualBrowserHarness({ targetWindow });

    expect(harness).not.toBeNull();
    expect(targetWindow[MEDIA_MANUAL_BROWSER_HARNESS_GLOBAL]).toBe(harness);
    harness?.uninstall();
    expect(targetWindow[MEDIA_MANUAL_BROWSER_HARNESS_GLOBAL]).toBeUndefined();
  });

  it("runs manual IndexedDB acceptance through the installed harness", async () => {
    const targetWindow: HarnessWindowDouble = {
      localStorage: createStorage({
        [MEDIA_SELECTED_PROFILE_STORAGE_KEY]: JSON.stringify("britton"),
        [createMediaProfileStorageKey("britton")]: JSON.stringify({
          watchlistIds: ["movie-local-lights"],
        }),
      }),
    };
    const { db, writes } = createFakeDb();
    const harness = installMediaManualBrowserHarness({ targetWindow });

    await expect(
      harness?.runIndexedDbAcceptance({
        db: db as never,
        checkedAt,
      }),
    ).resolves.toMatchObject({
      source: "media-indexeddb-manual-acceptance",
      checkedAt,
      status: "passed",
    });
    expect(writes.map((write) => write.tableName)).toEqual([
      ...MEDIA_DB_SEED_ORDER,
      ...migrationWriteOrder,
    ]);
  });
});
