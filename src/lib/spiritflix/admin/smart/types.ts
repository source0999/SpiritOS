// ── SpiritFlix Smart Analysis types (S1) ─────────────────────────────
// Schema + validators only. Scanner lane writes these; never mutates media.

export type SpiritFlixSmartStatus =
  | "not_analyzed"
  | "analyzing"
  | "needs_review"
  | "suggested"
  | "approved"
  | "rejected"
  | "blocked";

export type SpiritFlixSmartTagGroup =
  | "format"
  | "source"
  | "performer"
  | "scene"
  | "activity"
  | "position"
  | "style"
  | "quality"
  | "watermark"
  | "safety"
  | "unknown";

export type SpiritFlixSmartConfidenceBand = "high" | "medium" | "weak" | "ignore";

export interface SpiritFlixSmartTag {
  id: string;
  label: string;
  group: SpiritFlixSmartTagGroup;
  confidence: number;
  evidenceTimestamps: number[];
  reviewRequired: boolean;
}

export interface SpiritFlixSmartSample {
  timestampSeconds: number;
  timestampLabel: string;
  cacheKey?: string;
  observations: string[];
  tags: SpiritFlixSmartTag[];
  confidence: number;
}

export interface SpiritFlixSmartAnalysis {
  version: 1;
  videoPath: string;
  pathKey: string;
  fileName: string;
  fileSizeBytes: number;
  mtimeMs: number;
  analyzedAt: string;
  analyzerVersion: string;
  status: SpiritFlixSmartStatus;
  safety: {
    safeToSuggest: boolean;
    reasons: string[];
    requiresHumanReview: boolean;
  };
  media: {
    durationSeconds?: number;
    width?: number;
    height?: number;
    codec?: string;
    container?: string;
  };
  samples: SpiritFlixSmartSample[];
  suggestedTags: SpiritFlixSmartTag[];
  suggestedCategory?: string;
  suggestedCollections?: string[];
  suggestedDisplayTitle?: string;
  suggestedFilename?: string;
  suggestedTargetFolder?: string;
  confidence: number;
  notes?: string;
}

const SMART_STATUSES = new Set<SpiritFlixSmartStatus>([
  "not_analyzed",
  "analyzing",
  "needs_review",
  "suggested",
  "approved",
  "rejected",
  "blocked",
]);

const SMART_TAG_GROUPS = new Set<SpiritFlixSmartTagGroup>([
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

const POLLUTION_KEYS = new Set(["__proto__", "constructor", "prototype"]);

export const SMART_ANALYSIS_LIMITS = {
  maxSamples: 100,
  maxTagsPerList: 200,
  maxObservationsPerSample: 50,
  maxEvidenceTimestamps: 50,
  maxSafetyReasons: 20,
  maxCollections: 50,
  maxNotesLength: 8_192,
  maxPathLength: 4_096,
  maxLabelLength: 256,
  maxIdLength: 128,
  maxPayloadBytes: 512_000,
} as const;

function assertNoPollutionKeys(record: Record<string, unknown>, context: string): void {
  for (const key of Object.keys(record)) {
    if (POLLUTION_KEYS.has(key)) {
      throw new Error(`Unsafe key "${key}" in ${context}.`);
    }
  }
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function assertConfidence(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 1) {
    throw new Error(`${field} must be a number between 0 and 1.`);
  }
  return value;
}

function assertNonEmptyString(value: unknown, field: string, maxLength: number = SMART_ANALYSIS_LIMITS.maxPathLength): string {
  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`${field} must be a non-empty string.`);
  }
  if (value.length > maxLength) {
    throw new Error(`${field} is too long.`);
  }
  if (value.includes("\0")) {
    throw new Error(`${field} contains invalid characters.`);
  }
  return value;
}

function assertOptionalString(value: unknown, field: string, maxLength: number = SMART_ANALYSIS_LIMITS.maxLabelLength): string | undefined {
  if (value === undefined) return undefined;
  return assertNonEmptyString(value, field, maxLength);
}

function assertSafePathString(value: unknown, field: string): string {
  const pathValue = assertNonEmptyString(value, field);
  if (pathValue.split(/[\\/]+/).some((segment) => segment === "..")) {
    throw new Error(`${field} must not contain traversal segments.`);
  }
  return pathValue;
}

export function validateSpiritFlixSmartTag(value: unknown): SpiritFlixSmartTag {
  if (!isPlainObject(value)) throw new Error("Tag must be an object.");
  assertNoPollutionKeys(value, "tag");

  const id = assertNonEmptyString(value.id, "tag.id", SMART_ANALYSIS_LIMITS.maxIdLength);
  const label = assertNonEmptyString(value.label, "tag.label", SMART_ANALYSIS_LIMITS.maxLabelLength);
  const group = value.group;
  if (typeof group !== "string" || !SMART_TAG_GROUPS.has(group as SpiritFlixSmartTagGroup)) {
    throw new Error("tag.group is invalid.");
  }
  const confidence = assertConfidence(value.confidence, "tag.confidence");
  if (!Array.isArray(value.evidenceTimestamps)) {
    throw new Error("tag.evidenceTimestamps must be an array.");
  }
  if (value.evidenceTimestamps.length > SMART_ANALYSIS_LIMITS.maxEvidenceTimestamps) {
    throw new Error("tag.evidenceTimestamps is too large.");
  }
  const evidenceTimestamps = value.evidenceTimestamps.map((entry, index) => {
    if (typeof entry !== "number" || !Number.isFinite(entry) || entry < 0) {
      throw new Error(`tag.evidenceTimestamps[${index}] must be a non-negative number.`);
    }
    return entry;
  });
  if (typeof value.reviewRequired !== "boolean") {
    throw new Error("tag.reviewRequired must be a boolean.");
  }

  return { id, label, group: group as SpiritFlixSmartTagGroup, confidence, evidenceTimestamps, reviewRequired: value.reviewRequired };
}

export function validateSpiritFlixSmartSample(value: unknown): SpiritFlixSmartSample {
  if (!isPlainObject(value)) throw new Error("Sample must be an object.");
  assertNoPollutionKeys(value, "sample");

  const timestampSeconds =
    typeof value.timestampSeconds === "number" && Number.isFinite(value.timestampSeconds) && value.timestampSeconds >= 0
      ? value.timestampSeconds
      : (() => {
          throw new Error("sample.timestampSeconds must be a non-negative number.");
        })();
  const timestampLabel = assertNonEmptyString(value.timestampLabel, "sample.timestampLabel", 64);
  const cacheKey = value.cacheKey === undefined ? undefined : assertNonEmptyString(value.cacheKey, "sample.cacheKey", 128);
  if (!Array.isArray(value.observations)) throw new Error("sample.observations must be an array.");
  if (value.observations.length > SMART_ANALYSIS_LIMITS.maxObservationsPerSample) {
    throw new Error("sample.observations is too large.");
  }
  const observations = value.observations.map((entry, index) =>
    assertNonEmptyString(entry, `sample.observations[${index}]`, SMART_ANALYSIS_LIMITS.maxLabelLength),
  );
  if (!Array.isArray(value.tags)) throw new Error("sample.tags must be an array.");
  if (value.tags.length > SMART_ANALYSIS_LIMITS.maxTagsPerList) {
    throw new Error("sample.tags is too large.");
  }
  const tags = value.tags.map((entry) => validateSpiritFlixSmartTag(entry));
  const confidence = assertConfidence(value.confidence, "sample.confidence");

  return { timestampSeconds, timestampLabel, cacheKey, observations, tags, confidence };
}

export function validateSpiritFlixSmartAnalysis(value: unknown): SpiritFlixSmartAnalysis {
  if (!isPlainObject(value)) throw new Error("Analysis must be an object.");
  assertNoPollutionKeys(value, "analysis");

  if (value.version !== 1) throw new Error("analysis.version must be 1.");

  const videoPath = assertSafePathString(value.videoPath, "videoPath");
  const pathKey = assertNonEmptyString(value.pathKey, "pathKey", 128);
  const fileName = assertNonEmptyString(value.fileName, "fileName", 512);
  const fileSizeBytes =
    typeof value.fileSizeBytes === "number" && Number.isFinite(value.fileSizeBytes) && value.fileSizeBytes >= 0
      ? value.fileSizeBytes
      : (() => {
          throw new Error("fileSizeBytes must be a non-negative number.");
        })();
  const mtimeMs =
    typeof value.mtimeMs === "number" && Number.isFinite(value.mtimeMs) && value.mtimeMs >= 0
      ? value.mtimeMs
      : (() => {
          throw new Error("mtimeMs must be a non-negative number.");
        })();
  const analyzedAt = assertNonEmptyString(value.analyzedAt, "analyzedAt", 64);
  const analyzerVersion = assertNonEmptyString(value.analyzerVersion, "analyzerVersion", 128);

  const status = value.status;
  if (typeof status !== "string" || !SMART_STATUSES.has(status as SpiritFlixSmartStatus)) {
    throw new Error("status is invalid.");
  }

  if (!isPlainObject(value.safety)) throw new Error("safety must be an object.");
  assertNoPollutionKeys(value.safety, "safety");
  if (typeof value.safety.safeToSuggest !== "boolean") throw new Error("safety.safeToSuggest must be a boolean.");
  if (!Array.isArray(value.safety.reasons)) throw new Error("safety.reasons must be an array.");
  if (value.safety.reasons.length > SMART_ANALYSIS_LIMITS.maxSafetyReasons) {
    throw new Error("safety.reasons is too large.");
  }
  const reasons = value.safety.reasons.map((entry, index) =>
    assertNonEmptyString(entry, `safety.reasons[${index}]`, SMART_ANALYSIS_LIMITS.maxLabelLength),
  );
  if (typeof value.safety.requiresHumanReview !== "boolean") {
    throw new Error("safety.requiresHumanReview must be a boolean.");
  }

  if (!isPlainObject(value.media)) throw new Error("media must be an object.");
  assertNoPollutionKeys(value.media, "media");
  const media: SpiritFlixSmartAnalysis["media"] = {};
  if (value.media.durationSeconds !== undefined) {
    if (typeof value.media.durationSeconds !== "number" || !Number.isFinite(value.media.durationSeconds) || value.media.durationSeconds < 0) {
      throw new Error("media.durationSeconds must be a non-negative number.");
    }
    media.durationSeconds = value.media.durationSeconds;
  }
  if (value.media.width !== undefined) {
    if (typeof value.media.width !== "number" || !Number.isFinite(value.media.width) || value.media.width <= 0) {
      throw new Error("media.width must be a positive number.");
    }
    media.width = value.media.width;
  }
  if (value.media.height !== undefined) {
    if (typeof value.media.height !== "number" || !Number.isFinite(value.media.height) || value.media.height <= 0) {
      throw new Error("media.height must be a positive number.");
    }
    media.height = value.media.height;
  }
  if (value.media.codec !== undefined) media.codec = assertNonEmptyString(value.media.codec, "media.codec", 64);
  if (value.media.container !== undefined) media.container = assertNonEmptyString(value.media.container, "media.container", 64);

  if (!Array.isArray(value.samples)) throw new Error("samples must be an array.");
  if (value.samples.length > SMART_ANALYSIS_LIMITS.maxSamples) throw new Error("samples is too large.");
  const samples = value.samples.map((entry) => validateSpiritFlixSmartSample(entry));

  if (!Array.isArray(value.suggestedTags)) throw new Error("suggestedTags must be an array.");
  if (value.suggestedTags.length > SMART_ANALYSIS_LIMITS.maxTagsPerList) throw new Error("suggestedTags is too large.");
  const suggestedTags = value.suggestedTags.map((entry) => validateSpiritFlixSmartTag(entry));

  const suggestedCategory = assertOptionalString(value.suggestedCategory, "suggestedCategory");
  let suggestedCollections: string[] | undefined;
  if (value.suggestedCollections !== undefined) {
    if (!Array.isArray(value.suggestedCollections)) throw new Error("suggestedCollections must be an array.");
    if (value.suggestedCollections.length > SMART_ANALYSIS_LIMITS.maxCollections) {
      throw new Error("suggestedCollections is too large.");
    }
    suggestedCollections = value.suggestedCollections.map((entry, index) =>
      assertNonEmptyString(entry, `suggestedCollections[${index}]`, SMART_ANALYSIS_LIMITS.maxLabelLength),
    );
  }

  const suggestedDisplayTitle = assertOptionalString(value.suggestedDisplayTitle, "suggestedDisplayTitle", 512);
  const suggestedFilename = assertOptionalString(value.suggestedFilename, "suggestedFilename", 512);
  const suggestedTargetFolder =
    value.suggestedTargetFolder === undefined ? undefined : assertSafePathString(value.suggestedTargetFolder, "suggestedTargetFolder");

  const confidence = assertConfidence(value.confidence, "confidence");

  let notes: string | undefined;
  if (value.notes !== undefined) {
    notes = assertNonEmptyString(value.notes, "notes", SMART_ANALYSIS_LIMITS.maxNotesLength);
  }

  const serialized = JSON.stringify({
    version: 1,
    videoPath,
    pathKey,
    fileName,
    samples,
    suggestedTags,
    notes,
  });
  if (serialized.length > SMART_ANALYSIS_LIMITS.maxPayloadBytes) {
    throw new Error("Analysis payload is too large.");
  }

  return {
    version: 1,
    videoPath,
    pathKey,
    fileName,
    fileSizeBytes,
    mtimeMs,
    analyzedAt,
    analyzerVersion,
    status: status as SpiritFlixSmartStatus,
    safety: {
      safeToSuggest: value.safety.safeToSuggest,
      reasons,
      requiresHumanReview: value.safety.requiresHumanReview,
    },
    media,
    samples,
    suggestedTags,
    suggestedCategory,
    suggestedCollections,
    suggestedDisplayTitle,
    suggestedFilename,
    suggestedTargetFolder,
    confidence,
    notes,
  };
}

export function parseSpiritFlixSmartAnalysisJson(raw: string): SpiritFlixSmartAnalysis {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new Error("Analysis sidecar is not valid JSON.");
  }
  return validateSpiritFlixSmartAnalysis(parsed);
}
