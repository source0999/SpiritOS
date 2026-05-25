import { adaptDurableMediaLibrary } from "@/lib/media/media-durable-adapter";
import { durableDemoMediaRecords } from "@/lib/media/media-durable-demo-records";

export const mediaCatalogSource = adaptDurableMediaLibrary(
  durableDemoMediaRecords,
);

export const mediaProfiles = mediaCatalogSource.mediaProfiles;
export const demoCatalog = mediaCatalogSource.demoCatalog;
export const flattenedCatalogItems = mediaCatalogSource.flattenedCatalogItems;
export const getCatalogItemById = mediaCatalogSource.getCatalogItemById;
