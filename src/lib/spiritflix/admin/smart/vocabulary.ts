// ── SpiritFlix controlled tag vocabulary (S1) ────────────────────────
// Broad private tags only. Nothing auto-applies in S1.

import type { SpiritFlixSmartConfidenceBand, SpiritFlixSmartTagGroup } from "./types";

export interface SpiritFlixSmartTagDefinition {
  id: string;
  label: string;
  group: SpiritFlixSmartTagGroup;
  /** Vocabulary default — suggested tags still carry their own flag at runtime. */
  reviewRequired: boolean;
}

const EXPLICIT_ACTIVITY_IDS = new Set([
  "toy",
  "oral",
  "manual",
  "intercourse",
  "anal",
  "lesbian",
  "massage",
  "riding",
  "missionary",
  "doggy",
  "standing",
  "seated",
  "climax",
  "multiple-climax",
]);

const SEED_VOCABULARY: SpiritFlixSmartTagDefinition[] = [
  { id: "solo", label: "solo", group: "scene", reviewRequired: false },
  { id: "duo", label: "duo", group: "scene", reviewRequired: false },
  { id: "group", label: "group", group: "scene", reviewRequired: false },
  { id: "pov", label: "POV", group: "style", reviewRequired: false },
  { id: "indoor", label: "indoor", group: "scene", reviewRequired: false },
  { id: "outdoor", label: "outdoor", group: "scene", reviewRequired: false },
  { id: "curvy", label: "curvy", group: "body", reviewRequired: true },
  { id: "busty", label: "busty", group: "body", reviewRequired: true },
  { id: "bbw", label: "BBW", group: "body", reviewRequired: true },
  { id: "petite", label: "petite", group: "body", reviewRequired: true },
  { id: "slim", label: "slim", group: "body", reviewRequired: true },
  { id: "tattoos", label: "tattoos", group: "appearance", reviewRequired: true },
  { id: "glasses", label: "glasses", group: "appearance", reviewRequired: true },
  { id: "brunette", label: "brunette", group: "appearance", reviewRequired: true },
  { id: "black-hair", label: "black hair", group: "appearance", reviewRequired: true },
  { id: "blonde", label: "blonde", group: "appearance", reviewRequired: true },
  { id: "redhead", label: "redhead", group: "appearance", reviewRequired: true },
  { id: "hijab", label: "hijab", group: "apparel", reviewRequired: true },
  { id: "lingerie", label: "lingerie", group: "apparel", reviewRequired: true },
  { id: "stockings", label: "stockings", group: "apparel", reviewRequired: true },
  { id: "amateur", label: "amateur", group: "source", reviewRequired: false },
  { id: "professional", label: "professional", group: "source", reviewRequired: false },
  { id: "compilation", label: "compilation", group: "format", reviewRequired: false },
  { id: "short", label: "short", group: "format", reviewRequired: false },
  { id: "long", label: "long", group: "format", reviewRequired: false },
  { id: "converted", label: "converted", group: "format", reviewRequired: true },
  { id: "vertical", label: "vertical", group: "format", reviewRequired: false },
  { id: "mp4-container", label: "mp4", group: "format", reviewRequired: false },
  { id: "mkv-container", label: "mkv", group: "format", reviewRequired: false },
  { id: "webm-container", label: "webm", group: "format", reviewRequired: false },
  { id: "hd", label: "HD", group: "quality", reviewRequired: false },
  { id: "full-hd", label: "full HD", group: "quality", reviewRequired: false },
  { id: "uhd", label: "UHD", group: "quality", reviewRequired: true },
  { id: "source-unknown", label: "source unknown", group: "source", reviewRequired: true },
  { id: "site-token", label: "site token", group: "source", reviewRequired: true },
  { id: "low-light", label: "low-light", group: "scene", reviewRequired: false },
  { id: "watermark", label: "watermark", group: "watermark", reviewRequired: false },
  { id: "unknown-performer", label: "unknown performer", group: "performer", reviewRequired: false },
  { id: "known-performer", label: "known performer", group: "performer", reviewRequired: true },
  { id: "toy", label: "toy", group: "activity", reviewRequired: true },
  { id: "oral", label: "oral", group: "activity", reviewRequired: true },
  { id: "manual", label: "manual", group: "activity", reviewRequired: true },
  { id: "intercourse", label: "intercourse", group: "activity", reviewRequired: true },
  { id: "anal", label: "anal", group: "activity", reviewRequired: true },
  { id: "lesbian", label: "lesbian", group: "activity", reviewRequired: true },
  { id: "cosplay", label: "cosplay", group: "style", reviewRequired: true },
  { id: "massage", label: "massage", group: "activity", reviewRequired: true },
  { id: "riding", label: "riding", group: "position", reviewRequired: true },
  { id: "missionary", label: "missionary", group: "position", reviewRequired: true },
  { id: "doggy", label: "doggy", group: "position", reviewRequired: true },
  { id: "standing", label: "standing", group: "position", reviewRequired: true },
  { id: "seated", label: "seated", group: "position", reviewRequired: true },
  { id: "climax", label: "climax", group: "activity", reviewRequired: true },
  { id: "multiple-climax", label: "multiple climax", group: "activity", reviewRequired: true },
  { id: "unclear", label: "unclear", group: "unknown", reviewRequired: true },
  { id: "needs-review", label: "needs review", group: "safety", reviewRequired: true },
  { id: "needs-title-cleanup", label: "needs title cleanup", group: "safety", reviewRequired: true },
];

const vocabularyById = new Map(SEED_VOCABULARY.map((entry) => [entry.id, entry]));

export function getSmartTagVocabulary(): readonly SpiritFlixSmartTagDefinition[] {
  return SEED_VOCABULARY;
}

export function findSmartTagDefinition(id: string): SpiritFlixSmartTagDefinition | undefined {
  return vocabularyById.get(id);
}

export function isKnownSmartTagId(id: string): boolean {
  return vocabularyById.has(id);
}

export function normalizeSmartTagId(labelOrId: string): string | null {
  const trimmed = labelOrId.trim().toLowerCase();
  if (!trimmed) return null;
  if (vocabularyById.has(trimmed)) return trimmed;

  const kebab = trimmed
    .replace(/[_\s]+/g, "-")
    .replace(/[^a-z0-9-]/g, "")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
  if (kebab && vocabularyById.has(kebab)) return kebab;

  const byLabel = SEED_VOCABULARY.find((entry) => entry.label.toLowerCase() === trimmed);
  return byLabel?.id ?? null;
}

export function confidenceBand(confidence: number): SpiritFlixSmartConfidenceBand {
  if (!Number.isFinite(confidence) || confidence < 0.4) return "ignore";
  if (confidence >= 0.9) return "high";
  if (confidence >= 0.7) return "medium";
  return "weak";
}

/** Test helper — explicit/position/performer/safety tags must require review in vocabulary. */
export function tagDefinitionRequiresReviewByPolicy(definition: SpiritFlixSmartTagDefinition): boolean {
  if (definition.group === "safety") return true;
  if (definition.group === "performer" && definition.id === "known-performer") return true;
  if (definition.group === "position") return true;
  if (EXPLICIT_ACTIVITY_IDS.has(definition.id)) return true;
  if (definition.id === "unclear" || definition.id === "needs-review") return true;
  return definition.reviewRequired;
}
