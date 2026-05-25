import { adaptDurableMediaLibrary } from "@/lib/media/media-durable-adapter";
import { durableDemoMediaRecords } from "@/lib/media/media-durable-demo-records";
import type {
  DurableMediaAdapterResult,
  DurableMediaLibraryRecords,
} from "@/lib/media/media-durable-types";

export type MediaReadRepository = {
  getRecords: () => DurableMediaLibraryRecords;
  getAdapterResult: () => DurableMediaAdapterResult;
};

export function createStaticMediaReadRepository(
  records: DurableMediaLibraryRecords = durableDemoMediaRecords,
): MediaReadRepository {
  return {
    getRecords: () => records,
    getAdapterResult: () => adaptDurableMediaLibrary(records),
  };
}

export const staticMediaReadRepository = createStaticMediaReadRepository();
