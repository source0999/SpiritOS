import type {
  MediaLocalStorageMigratedRecords,
  MediaLocalStorageMigrationPlan,
} from "@/lib/media/media-local-storage-migration";

type BulkWritableTable<TRecord> = {
  bulkPut: (records: TRecord[]) => Promise<unknown>;
};

export type MediaLocalStorageMigrationWritableTables = {
  [TableName in keyof MediaLocalStorageMigratedRecords]: BulkWritableTable<
    MediaLocalStorageMigratedRecords[TableName][number]
  >;
};

export type MediaLocalStorageMigrationWriteSummaryEntry = {
  tableName: keyof MediaLocalStorageMigratedRecords;
  recordCount: number;
};

export type MediaLocalStorageMigrationWriteSummary = {
  source: "media-local-storage";
  selectedProfileId: MediaLocalStorageMigrationPlan["selectedProfileId"];
  migratedAt: string;
  skippedEntryCount: number;
  entries: MediaLocalStorageMigrationWriteSummaryEntry[];
};

const migrationWriteOrder = [
  "watchlistEntries",
  "playbackProgress",
  "curationChecks",
  "playbackAcceptance",
] as const satisfies ReadonlyArray<keyof MediaLocalStorageMigratedRecords>;

async function writeMigrationTable<
  TableName extends keyof MediaLocalStorageMigratedRecords,
>(
  tables: MediaLocalStorageMigrationWritableTables,
  records: MediaLocalStorageMigratedRecords,
  tableName: TableName,
): Promise<MediaLocalStorageMigrationWriteSummaryEntry> {
  const tableRecords = records[tableName];
  const table = tables[tableName] as BulkWritableTable<
    MediaLocalStorageMigratedRecords[TableName][number]
  >;

  await table.bulkPut(
    tableRecords as MediaLocalStorageMigratedRecords[TableName][number][],
  );

  return {
    tableName,
    recordCount: tableRecords.length,
  };
}

export async function writeMediaLocalStorageMigrationPlan(
  tables: MediaLocalStorageMigrationWritableTables,
  plan: MediaLocalStorageMigrationPlan,
): Promise<MediaLocalStorageMigrationWriteSummary> {
  const entries: MediaLocalStorageMigrationWriteSummaryEntry[] = [];

  for (const tableName of migrationWriteOrder) {
    entries.push(await writeMigrationTable(tables, plan.records, tableName));
  }

  return {
    source: plan.source,
    selectedProfileId: plan.selectedProfileId,
    migratedAt: plan.migratedAt,
    skippedEntryCount: plan.skippedEntries.length,
    entries,
  };
}
