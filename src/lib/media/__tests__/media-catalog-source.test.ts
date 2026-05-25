import { describe, expect, it } from "vitest";

import {
  demoCatalog as originalDemoCatalog,
  flattenedCatalogItems as originalFlattenedCatalogItems,
  getCatalogItemById as getOriginalCatalogItemById,
  mediaProfiles as originalMediaProfiles,
} from "@/lib/media/demo-catalog";
import {
  demoCatalog as catalogSourceDemoCatalog,
  flattenedCatalogItems as catalogSourceFlattenedCatalogItems,
  getCatalogItemById as getCatalogSourceItemById,
  mediaProfiles as catalogSourceMediaProfiles,
} from "@/lib/media/media-catalog-source";

describe("media-catalog-source", () => {
  it("keeps adapter-backed profiles in parity with the original typed catalog", () => {
    expect(catalogSourceMediaProfiles).toEqual(originalMediaProfiles);
  });

  it("keeps adapter-backed catalog groups in parity with the original typed catalog", () => {
    expect(catalogSourceDemoCatalog).toEqual(originalDemoCatalog);
  });

  it("keeps adapter-backed flattened item order in parity with the original typed catalog", () => {
    expect(catalogSourceFlattenedCatalogItems.map((item) => item.id)).toEqual(
      originalFlattenedCatalogItems.map((item) => item.id),
    );
    expect(catalogSourceFlattenedCatalogItems).toEqual(
      originalFlattenedCatalogItems,
    );
  });

  it("keeps adapter-backed item lookup in parity with the original typed catalog", () => {
    for (const item of originalFlattenedCatalogItems) {
      expect(getCatalogSourceItemById(item.id)).toEqual(
        getOriginalCatalogItemById(item.id),
      );
    }

    expect(getCatalogSourceItemById("missing-item")).toBeUndefined();
  });

  it("keeps local source and curation metadata in parity", () => {
    for (const item of catalogSourceFlattenedCatalogItems) {
      const originalItem = getOriginalCatalogItemById(item.id);

      expect(originalItem).toBeDefined();
      expect(item.mediaSource).toBe(originalItem?.mediaSource);
      expect(item.sourceKind).toBe(originalItem?.sourceKind);
      expect(item.sourceLabel).toBe(originalItem?.sourceLabel);
      expect(item.metadata.localFileStrategy).toBe(
        originalItem?.metadata.localFileStrategy,
      );
      expect(item.metadata.curation).toEqual(originalItem?.metadata.curation);
      expect(item.metadata.genres).toEqual(originalItem?.metadata.genres);
    }
  });
});
