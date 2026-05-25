import { describe, expect, it } from "vitest";

import { durableDemoMediaRecords } from "@/lib/media/media-durable-demo-records";
import {
  createStaticMediaReadRepository,
  staticMediaReadRepository,
} from "@/lib/media/media-read-repository";

describe("media-read-repository", () => {
  it("returns the configured durable media records without writing", () => {
    const repository = createStaticMediaReadRepository(durableDemoMediaRecords);

    expect(repository.getRecords()).toBe(durableDemoMediaRecords);
  });

  it("adapts static records through the existing durable media adapter", () => {
    const repository = createStaticMediaReadRepository(durableDemoMediaRecords);
    const adapterResult = repository.getAdapterResult();

    expect(adapterResult.mediaProfiles.map((profile) => profile.id)).toEqual([
      "britton",
      "friend",
      "guest",
    ]);
    expect(adapterResult.flattenedCatalogItems.map((item) => item.id)).toEqual([
      "movie-local-lights",
      "movie-workbench-weekend",
      "episode-signal-house-s1e1",
      "episode-signal-house-s1e2",
    ]);
  });

  it("exports a default static read repository for the current local proof", () => {
    expect(staticMediaReadRepository.getRecords()).toBe(durableDemoMediaRecords);
  });
});
