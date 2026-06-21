import { describe, expect, it } from "vitest";
import {
  confidenceBand,
  findSmartTagDefinition,
  getSmartTagVocabulary,
  isKnownSmartTagId,
  normalizeSmartTagId,
  tagDefinitionRequiresReviewByPolicy,
} from "../vocabulary";
import type { SpiritFlixSmartTagGroup } from "../types";

const VALID_GROUPS = new Set<SpiritFlixSmartTagGroup>([
  "format",
  "source",
  "performer",
  "scene",
  "activity",
  "position",
  "style",
  "quality",
  "watermark",
  "safety",
  "unknown",
]);

describe("SpiritFlix smart tag vocabulary", () => {
  it("keeps all ids unique and kebab-case", () => {
    const vocabulary = getSmartTagVocabulary();
    const ids = vocabulary.map((entry) => entry.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const id of ids) {
      expect(id).toMatch(/^[a-z0-9]+(?:-[a-z0-9]+)*$/);
    }
  });

  it("uses only valid groups", () => {
    for (const entry of getSmartTagVocabulary()) {
      expect(VALID_GROUPS.has(entry.group)).toBe(true);
    }
  });

  it("marks explicit, performer, position, and safety tags as review-required by policy", () => {
    const reviewIds = [
      "known-performer",
      "toy",
      "oral",
      "missionary",
      "needs-review",
      "needs-title-cleanup",
      "unclear",
      "site-token",
      "source-unknown",
      "converted",
      "uhd",
    ];
    for (const id of reviewIds) {
      const definition = findSmartTagDefinition(id);
      expect(definition).toBeDefined();
      expect(tagDefinitionRequiresReviewByPolicy(definition!)).toBe(true);
      expect(definition!.reviewRequired).toBe(true);
    }
  });

  it("keeps broad scene/source tags review-optional in vocabulary", () => {
    const broadIds = ["solo", "indoor", "amateur", "compilation", "unknown-performer"];
    for (const id of broadIds) {
      const definition = findSmartTagDefinition(id);
      expect(definition?.reviewRequired).toBe(false);
    }
  });

  it("resolves ids and labels through normalizeSmartTagId", () => {
    expect(isKnownSmartTagId("pov")).toBe(true);
    expect(normalizeSmartTagId("POV")).toBe("pov");
    expect(normalizeSmartTagId("unknown performer")).toBe("unknown-performer");
    expect(normalizeSmartTagId("not-a-real-tag")).toBeNull();
  });

  it("maps confidence bands", () => {
    expect(confidenceBand(0.95)).toBe("high");
    expect(confidenceBand(0.9)).toBe("high");
    expect(confidenceBand(0.75)).toBe("medium");
    expect(confidenceBand(0.5)).toBe("weak");
    expect(confidenceBand(0.2)).toBe("ignore");
  });
});
