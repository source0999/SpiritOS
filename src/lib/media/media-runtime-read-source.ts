import type { SpiritMediaDB } from "@/lib/media/media-db";
import { readMediaDbWhenAvailable } from "@/lib/media/media-db-browser-read";
import type { DurableMediaAdapterResult } from "@/lib/media/media-durable-types";
import { mediaCatalogSource } from "@/lib/media/media-catalog-source";

export type MediaRuntimeReadSource =
  | {
      status: "dexie";
      adapterResult: DurableMediaAdapterResult;
    }
  | {
      status: "local-fallback";
      reason: "indexeddb-unavailable";
      adapterResult: DurableMediaAdapterResult;
    };

export type MediaRuntimeReadSourceOptions = {
  db?: SpiritMediaDB | null;
};

export async function resolveMediaRuntimeReadSource(
  options: MediaRuntimeReadSourceOptions = {},
): Promise<MediaRuntimeReadSource> {
  const db = "db" in options ? options.db : undefined;
  const dbReadResult = await readMediaDbWhenAvailable(db);

  if (dbReadResult.status === "ready") {
    return {
      status: "dexie",
      adapterResult: dbReadResult.adapterResult,
    };
  }

  return {
    status: "local-fallback",
    reason: dbReadResult.reason,
    adapterResult: mediaCatalogSource,
  };
}
