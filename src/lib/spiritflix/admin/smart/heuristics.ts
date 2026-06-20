// ── SpiritFlix S3 filename/path/metadata heuristics ────────────────
// Text-only lane. Never reads or classifies frame images.

import path from "node:path";
import { findSmartTagDefinition } from "./vocabulary";
import type { SpiritFlixSmartPerformerIdentity, SpiritFlixSmartTag } from "./types";

export interface SpiritFlixSmartHeuristicInput {
  videoPath: string;
  fileName: string;
  parentPath?: string;
  modelSequenceNumber?: number;
  fileSizeBytes?: number;
  mtimeMs?: number;
  media?: {
    durationSeconds?: number;
    width?: number;
    height?: number;
    codec?: string;
    container?: string;
    bitRate?: number;
    frameRate?: number;
  };
}

const NOISE_TOKENS = new Set([
  "1080p",
  "1080",
  "720p",
  "720",
  "480p",
  "480",
  "2160p",
  "4k",
  "uhd",
  "x264",
  "x265",
  "h264",
  "h265",
  "hevc",
  "avc",
  "webrip",
  "web-dl",
  "webdl",
  "web",
  "dl",
  "bluray",
  "blu-ray",
  "bdrip",
  "camrip",
  "mp4",
  "mkv",
  "mov",
  "m4v",
  "webm",
  "avi",
  "www",
  "com",
  "net",
  "org",
  "download",
  "copy",
  "final",
  "fixed",
  "converted",
  "repack",
  "rip",
]);

const KNOWN_SITE_TOKENS = new Set([
  "onlyfans",
  "pornhub",
  "xvideos",
  "xhamster",
  "redtube",
  "spankbang",
  "eporner",
  "youporn",
  "xnxx",
  "fansly",
  "manyvids",
  "chaturbate",
  "clips4sale",
  "brazzers",
  "realitykings",
  "naughtyamerica",
  "bangbros",
]);

const SHORT_DURATION_SECONDS = 300;
const LONG_DURATION_SECONDS = 1_800;
const COMPILATION_DURATION_SECONDS = 3_600;

const COMPILATION_TOKENS = new Set(["compilation", "comp", "pmv", "mix", "montage", "best-of", "bestof"]);
const PRIMARY_CONTENT_GROUPS = new Set(["scene", "body", "appearance", "apparel", "activity", "position", "style", "watermark"]);
const TECHNICAL_OR_STATUS_TAG_IDS = new Set([
  "solo",
  "duo",
  "indoor",
  "outdoor",
  "mp4-container",
  "mkv-container",
  "webm-container",
  "short",
  "long",
  "converted",
  "hd",
  "full-hd",
  "uhd",
  "unknown-performer",
  "known-performer",
  "needs-title-cleanup",
  "needs-review",
  "source-unknown",
  "site-token",
]);
const MODEL_FOLDER_MARKERS = new Set(["model", "models", "performer", "performers"]);
const GENERIC_FOLDER_NAMES = new Set(["yes", "media", "data", "movies", "movie", "tv", "anime", "music", "other", "unknown"]);

function normalizeToken(value: string): string {
  return value.trim().toLowerCase();
}

function splitNameSegments(value: string): string[] {
  return value
    .replace(/\.[a-z0-9]{2,4}$/i, "")
    .split(/[._\-\s]+/)
    .map((segment) => segment.trim())
    .filter(Boolean);
}

export function tokenizeSpiritFlixName(value: string): string[] {
  const segments = splitNameSegments(path.basename(value));
  const pathSegments = value
    .replace(/\\/g, "/")
    .split("/")
    .flatMap((segment) => splitNameSegments(segment));
  const combined = [...segments, ...pathSegments];
  const seen = new Set<string>();
  const tokens: string[] = [];
  for (const segment of combined) {
    const token = normalizeToken(segment);
    if (!token || seen.has(token)) continue;
    seen.add(token);
    tokens.push(token);
  }
  return tokens;
}

export function stripKnownNoiseTokens(value: string): string {
  const kept = tokenizeSpiritFlixName(value).filter((token) => !NOISE_TOKENS.has(token));
  return kept.join(" ");
}

export function normalizeSpiritFlixTitle(value: string): string {
  const stem = path.basename(value, path.extname(value));
  const tokens = splitNameSegments(stem)
    .map((segment) => segment.trim())
    .filter((segment) => segment && !NOISE_TOKENS.has(normalizeToken(segment)));

  if (tokens.length === 0) {
    return stem.replace(/[._]+/g, " ").trim() || stem;
  }

  return tokens
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
}

export function stripVideoExtension(value: string): string {
  return path.basename(value, path.extname(value)).trim();
}

export function titleCaseSlug(value: string): string {
  return value
    .replace(/[_+]+/g, "-")
    .split(/[-\s]+/)
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

export function modelIdentityFromPath(input: SpiritFlixSmartHeuristicInput): SpiritFlixSmartPerformerIdentity | undefined {
  const normalized = (input.parentPath ?? path.dirname(input.videoPath)).replace(/\\/g, "/");
  const segments = normalized.split("/").filter(Boolean);
  for (let index = segments.length - 1; index >= 0; index -= 1) {
    const segment = segments[index]?.toLowerCase();
    if (!segment || !MODEL_FOLDER_MARKERS.has(segment)) continue;
    const candidate = segments[index + 1];
    if (!candidate) continue;
    const name = titleCaseSlug(candidate);
    if (!name || GENERIC_FOLDER_NAMES.has(name.toLowerCase())) continue;
    return {
      name,
      source: "path",
      confidence: 0.72,
      evidenceRef: normalized,
      requiresReview: true,
    };
  }
  return undefined;
}

export function unknownModelIdentity(): SpiritFlixSmartPerformerIdentity {
  return {
    name: "Unknown Model",
    source: "unknown",
    confidence: 0.2,
    requiresReview: true,
  };
}

export function isPrimarySmartContentTag(tag: Pick<SpiritFlixSmartTag, "id" | "group">): boolean {
  return PRIMARY_CONTENT_GROUPS.has(tag.group) && !TECHNICAL_OR_STATUS_TAG_IDS.has(tag.id);
}

export function isTechnicalOrStatusTag(tag: Pick<SpiritFlixSmartTag, "id" | "group">): boolean {
  return TECHNICAL_OR_STATUS_TAG_IDS.has(tag.id) || tag.group === "quality" || tag.group === "format" || tag.group === "safety" || tag.group === "performer";
}

export function isRandomOrHashSpiritFlixFilename(input: SpiritFlixSmartHeuristicInput): boolean {
  const stem = stripVideoExtension(input.fileName).trim();
  const normalizedStem = stem.replace(/\s+/g, " ");
  const compact = normalizedStem.replace(/[^a-z0-9]/gi, "");
  if (!compact) return true;
  if (/^\d+$/.test(compact) && compact.length >= 4) return true;
  if (/^[a-f0-9]{12,}$/i.test(compact)) return true;
  if (/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(normalizedStem)) return true;
  if (/^[a-z0-9]{16,}$/i.test(compact) && !/[\s._@-]/.test(normalizedStem)) {
    const vowels = compact.match(/[aeiou]/gi)?.length ?? 0;
    const digitCount = compact.match(/\d/g)?.length ?? 0;
    const hasMixedCase = /[a-z]/.test(stem) && /[A-Z]/.test(stem);
    const vowelRatio = vowels / compact.length;
    if (hasMixedCase || digitCount >= 4 || vowelRatio < 0.28 || vowelRatio > 0.62) return true;
  }
  return false;
}

function makeTag(id: string, confidence: number, reviewOverride?: boolean): SpiritFlixSmartTag | null {
  const definition = findSmartTagDefinition(id);
  if (!definition) return null;
  return {
    id: definition.id,
    label: definition.label,
    group: definition.group,
    confidence,
    evidenceTimestamps: [],
    reviewRequired: reviewOverride ?? definition.reviewRequired,
  };
}

function dedupeTags(tags: SpiritFlixSmartTag[]): SpiritFlixSmartTag[] {
  const byId = new Map<string, SpiritFlixSmartTag>();
  for (const tag of tags) {
    const existing = byId.get(tag.id);
    if (!existing || tag.confidence > existing.confidence) {
      byId.set(tag.id, tag);
    }
  }
  return [...byId.values()].sort((left, right) => left.id.localeCompare(right.id));
}

export function inferSourceTokens(input: SpiritFlixSmartHeuristicInput): string[] {
  const haystack = tokenizeSpiritFlixName(`${input.parentPath ?? ""} ${input.fileName}`);
  return haystack.filter((token) => KNOWN_SITE_TOKENS.has(token));
}

export function inferQualityTags(input: SpiritFlixSmartHeuristicInput): SpiritFlixSmartTag[] {
  const tags: SpiritFlixSmartTag[] = [];
  const tokens = tokenizeSpiritFlixName(input.fileName);
  const width = input.media?.width;
  const height = input.media?.height;

  if (width && height && height > width) {
    tags.push(makeTag("vertical", 0.85, false)!);
  }

  if (tokens.includes("low-light") || tokens.includes("lowlight")) {
    tags.push(makeTag("low-light", 0.7, true)!);
  }

  const heightTag = resolveResolutionTag(height, tokens);
  if (heightTag) tags.push(heightTag);

  return dedupeTags(tags.filter(Boolean) as SpiritFlixSmartTag[]);
}

function resolveResolutionTag(height: number | undefined, tokens: string[]): SpiritFlixSmartTag | null {
  if (tokens.includes("2160p") || tokens.includes("4k") || (height && height >= 2160)) {
    return makeTag("uhd", height && height >= 2160 ? 0.9 : 0.65, true);
  }
  if (tokens.includes("1080p") || tokens.includes("1080") || (height && height >= 1080)) {
    return makeTag("full-hd", height && height >= 1080 ? 0.9 : 0.65, false);
  }
  if (tokens.includes("720p") || tokens.includes("720") || (height && height >= 720)) {
    return makeTag("hd", height && height >= 720 ? 0.85 : 0.6, false);
  }
  if (tokens.includes("480p") || tokens.includes("480") || (height && height > 0 && height < 720)) {
    return makeTag("hd", 0.55, true);
  }
  return null;
}

export function inferFormatTags(input: SpiritFlixSmartHeuristicInput): SpiritFlixSmartTag[] {
  const tags: SpiritFlixSmartTag[] = [];
  const tokens = tokenizeSpiritFlixName(`${input.parentPath ?? ""} ${input.fileName}`);
  const duration = input.media?.durationSeconds;
  const extension = path.extname(input.fileName).toLowerCase().replace(/^\./, "");

  if (extension) {
    const containerTag = extensionToTag(extension, input.media?.container);
    if (containerTag) tags.push(containerTag);
  }

  if (tokens.includes("converted") || tokens.includes("repack")) {
    tags.push(makeTag("converted", 0.75, true)!);
  }

  if (duration !== undefined) {
    if (duration <= SHORT_DURATION_SECONDS) {
      tags.push(makeTag("short", 0.8, false)!);
    } else if (duration >= LONG_DURATION_SECONDS) {
      tags.push(makeTag("long", 0.8, false)!);
    }
  }

  const hasCompilationToken = tokens.some((token) => COMPILATION_TOKENS.has(token));
  if (hasCompilationToken) {
    tags.push(makeTag("compilation", 0.7, true)!);
  } else if (duration !== undefined && duration >= COMPILATION_DURATION_SECONDS) {
    tags.push(makeTag("compilation", 0.45, true)!);
  }

  return dedupeTags(tags.filter(Boolean) as SpiritFlixSmartTag[]);
}

function extensionToTag(extension: string, container?: string): SpiritFlixSmartTag | null {
  const normalizedContainer = container?.toLowerCase() ?? "";
  if (["mp4", "m4v", "mov"].includes(extension) || normalizedContainer.includes("mp4")) {
    return makeTag("mp4-container", 0.7, false);
  }
  if (extension === "mkv" || normalizedContainer.includes("matroska")) {
    return makeTag("mkv-container", 0.7, false);
  }
  if (extension === "webm" || normalizedContainer.includes("webm")) {
    return makeTag("webm-container", 0.7, false);
  }
  return null;
}

export function inferSourceTags(input: SpiritFlixSmartHeuristicInput): SpiritFlixSmartTag[] {
  const sourceTokens = inferSourceTokens(input);
  const tags: SpiritFlixSmartTag[] = [];

  for (const token of sourceTokens) {
    tags.push({
      id: "site-token",
      label: "site token",
      group: "source",
      confidence: 0.75,
      evidenceTimestamps: [],
      reviewRequired: true,
    });
    void token;
  }

  if (sourceTokens.length === 0) {
    const maybeSource = tokenizeSpiritFlixName(input.fileName).some((token) => token.includes("rip") || token.includes("cam"));
    if (maybeSource) {
      tags.push(makeTag("source-unknown", 0.5, true)!);
    }
  }

  return dedupeTags(tags.filter(Boolean) as SpiritFlixSmartTag[]);
}

export function inferPerformerTags(_input: SpiritFlixSmartHeuristicInput): SpiritFlixSmartTag[] {
  return [makeTag("unknown-performer", 0.6, false)!];
}

export function inferCategoryHint(input: SpiritFlixSmartHeuristicInput): string | undefined {
  const normalized = (input.parentPath ?? input.videoPath).replace(/\\/g, "/").toLowerCase();
  const categories = ["yes", "anime", "movies", "tv", "music", "other"] as const;
  for (const category of categories) {
    if (normalized.includes(`/${category}/`) || normalized.endsWith(`/${category}`)) {
      return category;
    }
  }
  return undefined;
}

export function isAmbiguousSpiritFlixFilename(input: SpiritFlixSmartHeuristicInput): boolean {
  const title = normalizeSpiritFlixTitle(input.fileName);
  const tokens = stripKnownNoiseTokens(input.fileName).split(/\s+/).filter(Boolean);
  if (title.length < 3 || tokens.length <= 1) return true;
  const meaningful = tokens.filter((token) => !/^\d+$/.test(token));
  if (meaningful.length === 0) return true;
  if (tokens.length <= 2 && tokens.every((token) => token.length <= 3 || /^\d+$/.test(token))) return true;
  return false;
}

export function buildHeuristicNotes(input: SpiritFlixSmartHeuristicInput): string[] {
  const notes: string[] = ["S3 heuristics used filename, path, and technical metadata only."];
  const sourceTokens = inferSourceTokens(input);
  if (sourceTokens.length > 0) {
    notes.push(`literal source/site tokens: ${sourceTokens.join(", ")}`);
  } else {
    notes.push("no literal source/site tokens detected");
  }
  if (isAmbiguousSpiritFlixFilename(input)) {
    notes.push("insufficient filename context, needs review");
  }
  return notes;
}
