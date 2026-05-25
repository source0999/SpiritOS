import { MEDIA_DB_SEED_ORDER } from "@/lib/media/media-db-seed";
import { durableDemoMediaRecords } from "@/lib/media/media-durable-demo-records";
import type { DurableMediaLibraryRecords } from "@/lib/media/media-durable-types";

type BulkWritableTable<TRecord> = {
  bulkPut: (records: TRecord[]) => Promise<unknown>;
};

export type MediaDbWritableTables = {
  [TableName in keyof DurableMediaLibraryRecords]: BulkWritableTable<
    DurableMediaLibraryRecords[TableName][number]
  >;
};

export type MediaDbWriteSummaryEntry = {
  tableName: keyof DurableMediaLibraryRecords;
  recordCount: number;
};

export type MediaDbWriteSummary = {
  source: "durable-demo-media-records";
  entries: MediaDbWriteSummaryEntry[];
};

async function writeMediaDbSeedTable<TableName extends keyof DurableMediaLibraryRecords>(
  tables: MediaDbWritableTables,
  records: DurableMediaLibraryRecords,
  tableName: TableName,
): Promise<MediaDbWriteSummaryEntry> {
  const tableRecords = records[tableName];
  const table = tables[tableName] as BulkWritableTable<
    DurableMediaLibraryRecords[TableName][number]
  >;

  await table.bulkPut(
    tableRecords as DurableMediaLibraryRecords[TableName][number][],
  );

  return {
    tableName,
    recordCount: tableRecords.length,
  };
}

export async function writeMediaDbSeedRecords(
  tables: MediaDbWritableTables,
  records: DurableMediaLibraryRecords = durableDemoMediaRecords,
): Promise<MediaDbWriteSummary> {
  const entries: MediaDbWriteSummaryEntry[] = [];

  for (const tableName of MEDIA_DB_SEED_ORDER) {
    entries.push(await writeMediaDbSeedTable(tables, records, tableName));
  }

  return {
    source: "durable-demo-media-records",
    entries,
  };
}
