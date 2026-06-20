import fs from "node:fs/promises";
import path from "node:path";
import { findSmartTagDefinition, getSmartTagVocabulary, normalizeSmartTagId } from "./vocabulary";
import type { SpiritFlixSmartAnalysis, SpiritFlixSmartSample, SpiritFlixSmartTag, SpiritFlixSmartVisualAnalysisFrame } from "./types";

export const SPIRITFLIX_SMART_ANALYZER_VERSION_S9 = "spiritflix-smart/s9";

const DEFAULT_OLLAMA_MODEL = "gemma3n:e4b";
const DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434/api/generate";
const DEFAULT_TIMEOUT_MS = 90_000;
const MAX_VISUAL_SAMPLES = 8;
const MIN_TAG_CONFIDENCE = 0.45;

const VISUAL_TAG_IDS = getSmartTagVocabulary()
  .filter((entry) => ["scene", "body", "appearance", "apparel", "activity", "position", "style", "watermark"].includes(entry.group))
  .filter((entry) => !["solo", "duo", "group", "indoor", "outdoor", "low-light", "brunette", "black-hair", "blonde", "redhead"].includes(entry.id))
  .map((entry) => entry.id);

export interface SpiritFlixVisualAnalysisOptions {
  enabled?: boolean;
  mediaRoot?: string;
  ollamaModel?: string;
  ollamaUrl?: string;
  timeoutMs?: number;
  maxSamples?: number;
}

interface VisualModelTag {
  id?: unknown;
  label?: unknown;
  confidence?: unknown;
  evidence?: unknown;
}

interface VisualModelResponse {
  tags?: unknown;
  observations?: unknown;
  confidence?: unknown;
}

function clampConfidence(value: unknown, fallback = 0.55): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return Math.max(0, Math.min(1, value));
}

function extractJsonObject(value: string): VisualModelResponse | null {
  const fenced = value.match(/```(?:json)?\s*([\s\S]*?)```/i)?.[1];
  const raw = (fenced ?? value).trim();
  const start = raw.indexOf("{");
  const end = raw.lastIndexOf("}");
  if (start < 0 || end <= start) return null;
  try {
    return JSON.parse(raw.slice(start, end + 1)) as VisualModelResponse;
  } catch {
    return null;
  }
}

function makeVisualTag(entry: VisualModelTag, timestampSeconds: number): SpiritFlixSmartTag | null {
  const id = typeof entry.id === "string"
    ? normalizeSmartTagId(entry.id)
    : typeof entry.label === "string"
      ? normalizeSmartTagId(entry.label)
      : null;
  if (!id || !VISUAL_TAG_IDS.includes(id)) return null;
  const definition = findSmartTagDefinition(id);
  if (!definition) return null;
  const confidence = clampConfidence(entry.confidence);
  if (confidence < MIN_TAG_CONFIDENCE) return null;
  return {
    id: definition.id,
    label: definition.label,
    group: definition.group,
    confidence,
    evidenceTimestamps: [timestampSeconds],
    reviewRequired: true,
  };
}

function normalizeVisualTags(tags: SpiritFlixSmartTag[]): SpiritFlixSmartTag[] {
  const byId = new Map(tags.map((tag) => [tag.id, tag]));
  byId.delete("indoor");
  byId.delete("low-light");
  byId.delete("solo");
  byId.delete("duo");
  byId.delete("group");
  byId.delete("outdoor");
  byId.delete("brunette");
  byId.delete("black-hair");
  byId.delete("blonde");
  byId.delete("redhead");
  return [...byId.values()].sort((left, right) => right.confidence - left.confidence);
}

function promptForFrame(sample: SpiritFlixSmartSample): string {
  return [
    "You are tagging one sampled video frame for a private local media library.",
    "Return JSON only. Do not include markdown.",
    `Frame timestamp: ${sample.timestampLabel}.`,
    `Allowed tag ids: ${VISUAL_TAG_IDS.join(", ")}.`,
    "Do not tag people counts or generic scene counts: never return solo, duo, or group.",
    "Do not return location-only tags such as indoor or outdoor.",
    "Return only relevant descriptive tags about visible body type, clothing, styling, activity, pose, setting, or watermark.",
    "Do not tag hair color. Do not use generic filler tags.",
    "Actively check for visible supported body/apparel tags such as curvy, busty, BBW, petite, slim, hijab, lingerie, stockings, tattoos, and glasses when the frame clearly supports them.",
    "Do not infer race, ethnicity, nationality, religion, or identity from appearance. Only tag visible clothing items such as hijab when clearly visible.",
    "Use only visible evidence. If unsure, return unclear with low confidence.",
    "Schema: {\"tags\":[{\"id\":\"tag-id\",\"confidence\":0.0,\"evidence\":\"short visible cue\"}],\"observations\":[\"short cue\"],\"confidence\":0.0}",
  ].join("\n");
}

async function postOllamaImage(
  framePath: string,
  prompt: string,
  options: Required<Pick<SpiritFlixVisualAnalysisOptions, "ollamaModel" | "ollamaUrl" | "timeoutMs">>,
): Promise<VisualModelResponse> {
  const image = await fs.readFile(framePath, "base64");
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), options.timeoutMs);
  try {
    const response = await fetch(options.ollamaUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: options.ollamaModel,
        prompt,
        images: [image],
        stream: false,
        options: { temperature: 0 },
      }),
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error(`local visual model returned HTTP ${response.status}`);
    }
    const payload = await response.json() as { response?: unknown };
    const parsed = typeof payload.response === "string" ? extractJsonObject(payload.response) : null;
    if (!parsed) throw new Error("local visual model did not return parseable JSON");
    return parsed;
  } finally {
    clearTimeout(timeout);
  }
}

function mergeSampleTags(sample: SpiritFlixSmartSample, tags: SpiritFlixSmartTag[]): SpiritFlixSmartSample {
  const byId = new Map<string, SpiritFlixSmartTag>();
  for (const tag of [...sample.tags, ...tags]) {
    const existing = byId.get(tag.id);
    if (!existing || tag.confidence > existing.confidence) byId.set(tag.id, tag);
  }
  const mergedTags = [...byId.values()].sort((left, right) => right.confidence - left.confidence);
  return {
    ...sample,
    tags: mergedTags,
    confidence: mergedTags.length ? Math.max(...mergedTags.map((tag) => tag.confidence)) : sample.confidence,
  };
}

export async function applyLocalVisualAnalysisToSpiritFlixAnalysis(
  analysis: SpiritFlixSmartAnalysis,
  options: SpiritFlixVisualAnalysisOptions = {},
): Promise<SpiritFlixSmartAnalysis> {
  if (options.enabled === false) return analysis;
  const samplesWithFrames = analysis.samples.filter((sample) => sample.cacheKey).slice(0, options.maxSamples ?? MAX_VISUAL_SAMPLES);
  if (samplesWithFrames.length === 0) {
    return {
      ...analysis,
      visualAnalysis: {
        status: "not_run",
        modelName: options.ollamaModel ?? process.env.SPIRITFLIX_SMART_VISION_MODEL ?? DEFAULT_OLLAMA_MODEL,
        analyzedAt: new Date().toISOString(),
        sampledFrameCount: 0,
        analyzedFrameCount: 0,
        tags: [],
        frames: [],
        error: "No sampled frames were available.",
      },
      notes: [analysis.notes, "S9 local visual analysis skipped: no sampled frames were available."].filter(Boolean).join(" | "),
    };
  }

  const modelOptions = {
    ollamaModel: options.ollamaModel ?? process.env.SPIRITFLIX_SMART_VISION_MODEL ?? DEFAULT_OLLAMA_MODEL,
    ollamaUrl: options.ollamaUrl ?? process.env.SPIRITFLIX_SMART_OLLAMA_URL ?? DEFAULT_OLLAMA_URL,
    timeoutMs: options.timeoutMs ?? DEFAULT_TIMEOUT_MS,
  };

  const samples = [...analysis.samples];
  const notes: string[] = [];
  const evidenceTags = new Set<string>();
  const frames: SpiritFlixSmartVisualAnalysisFrame[] = [];
  let analyzedFrames = 0;

  for (const sample of samplesWithFrames) {
    const frameCachePath = await findFramePathForSample(analysis, sample, options.mediaRoot);
    if (!frameCachePath) {
      notes.push(`S9 local visual analysis skipped ${sample.timestampLabel}: cached frame not found.`);
      continue;
    }
    try {
      const response = await postOllamaImage(frameCachePath, promptForFrame(sample), modelOptions);
      const modelTags = Array.isArray(response.tags) ? response.tags as VisualModelTag[] : [];
      const tags = modelTags
        .map((entry) => makeVisualTag(entry, sample.timestampSeconds))
        .filter((tag): tag is SpiritFlixSmartTag => tag != null);
      const normalizedTags = normalizeVisualTags(tags);
      const observations = Array.isArray(response.observations)
        ? response.observations.filter((entry): entry is string => typeof entry === "string" && entry.trim().length > 0).slice(0, 3)
        : [];
      const index = samples.findIndex((entry) => entry.timestampSeconds === sample.timestampSeconds && entry.cacheKey === sample.cacheKey);
      if (index >= 0) {
        samples[index] = mergeSampleTags(
          {
            ...samples[index],
            observations: [...new Set([...samples[index].observations, ...observations.map((entry) => `vlm: ${entry.trim()}`)])],
          },
          normalizedTags,
        );
      }
      normalizedTags.forEach((tag) => evidenceTags.add(tag.id));
      frames.push({
        timestampSeconds: sample.timestampSeconds,
        timestampLabel: sample.timestampLabel,
        cacheKey: sample.cacheKey,
        status: "complete",
        tags: normalizedTags.map((tag) => tag.id),
        observations,
      });
      analyzedFrames += 1;
    } catch (error) {
      const message = error instanceof Error ? error.message : "local visual model failed";
      notes.push(`S9 local visual analysis failed ${sample.timestampLabel}: ${message}`);
      frames.push({
        timestampSeconds: sample.timestampSeconds,
        timestampLabel: sample.timestampLabel,
        cacheKey: sample.cacheKey,
        status: "failed",
        tags: [],
        observations: [],
        error: message,
      });
    }
  }

  const contentTagEvidence = [
    ...(analysis.contentTagEvidence ?? []).filter((entry) => entry.source !== "vlm"),
    {
      source: "vlm" as const,
      tags: [...evidenceTags],
      confidence: evidenceTags.size > 0 ? 0.65 : 0,
      evidenceRef: modelOptions.ollamaModel,
      requiresReview: true,
    },
  ];

  notes.push(`S9 local visual analysis used ${modelOptions.ollamaModel} on ${analyzedFrames}/${samplesWithFrames.length} sampled frames; all VLM tags require review.`);

  return {
    ...analysis,
    analyzerVersion: SPIRITFLIX_SMART_ANALYZER_VERSION_S9,
    samples,
    visualAnalysis: {
      status: evidenceTags.size > 0 ? "complete" : analyzedFrames > 0 ? "partial" : "failed",
      modelName: modelOptions.ollamaModel,
      analyzedAt: new Date().toISOString(),
      sampledFrameCount: samplesWithFrames.length,
      analyzedFrameCount: analyzedFrames,
      tags: [...evidenceTags],
      frames,
      error: evidenceTags.size > 0 ? undefined : notes.find((note) => /failed/i.test(note)),
    },
    contentTagEvidence,
    notes: [analysis.notes, ...notes].filter(Boolean).join(" | ").slice(0, 8_000),
  };
}

async function findFramePathForSample(analysis: SpiritFlixSmartAnalysis, sample: SpiritFlixSmartSample, mediaRoot?: string): Promise<string | null> {
  if (!sample.cacheKey) return null;
  const root = mediaRoot ?? await findMediaRoot(analysis.videoPath);
  const framesRoot = path.join(root, ".spiritflix-admin", "analysis-cache", "frames");
  const expected = path.join(framesRoot, `${sample.cacheKey}.jpg`);
  try {
    const stat = await fs.stat(expected);
    return stat.isFile() && stat.size > 0 ? expected : null;
  } catch {
    return null;
  }
}

async function findMediaRoot(videoPath: string): Promise<string> {
  let current = path.resolve(path.dirname(videoPath));
  while (true) {
    if (path.basename(current) === "media") return current;
    const parent = path.dirname(current);
    if (parent === current) return path.resolve(path.dirname(videoPath));
    current = parent;
  }
}
