import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { NextRequest, NextResponse } from "next/server";
import type {
  FaceOrganizerMetadataResponse,
  FaceOrganizerPerformer,
  FaceOrganizerStatus,
  FaceOrganizerVideoMatch,
} from "@/lib/spiritflix-types";
import { shouldUseSpiritFlixKnownModelIndexEntry } from "@/lib/spiritflix/manual-models";

interface FaceMetadataRequestItem {
  id?: string;
  name?: string;
  path?: string;
}

interface FaceMetadataRequest {
  items?: FaceMetadataRequestItem[];
}

interface SidecarPerformer {
  id?: string;
  name?: string;
  confidence?: number;
  similarity?: number;
  status?: string;
  verification_needed?: boolean;
}

interface FaceMatchDecision {
  decision?: string;
  performer_name?: string;
  performer_id?: string;
  visual_confirmed?: boolean;
}

interface FaceSidecar {
  video_path?: string;
  generated_at?: string;
  verification_needed?: boolean;
  performers?: SidecarPerformer[];
  faces_detected?: number;
  face_match_decisions?: FaceMatchDecision[];
}

// Active media root is /DATA/yes on this install (the SPIRITFLIX_MEDIA_ROOT
// const elsewhere hardcodes /mnt/spirit-8tb/media, but the live mount is /DATA).
// Include both so the route works regardless of which mount is active.
const MEDIA_ROOTS = ["/DATA/yes", "/DATA/other", "/mnt/spirit-8tb/media/yes", "/mnt/spirit-8tb/media/other"];
const KNOWN_PERFORMERS_INDEX = "/home/source/SpiritOS/scripts/media/known_performers/index.json";
const FACE_ENROLLED_GROUPS = "/home/source/SpiritOS/scripts/media/face_enrolled_performers.json";
const MODEL_INDEX = "/home/source/SpiritOS/scripts/media/model_index.json";
const HIGH_CONFIDENCE = 0.8;
const POSSIBLE_CONFIDENCE = 0.55;

function normalizeNameKey(value?: string): string {
  return (value ?? "").toLowerCase().replace(/[^a-z0-9]/g, "");
}

function normalizePathKey(value?: string): string {
  return (value ?? "")
    .replaceAll("\\", "/")
    .replace(/^\/DATA\//, "/mnt/spirit-8tb/media/")
    .replace(/^\/media\//, "/mnt/spirit-8tb/media/")
    .toLowerCase();
}

function basenameKey(value?: string): string {
  return path.basename(normalizePathKey(value)).toLowerCase();
}

function stemPathKey(value?: string): string {
  const normalized = normalizePathKey(value);
  const parsed = path.posix.parse(normalized);
  return path.posix.join(parsed.dir, parsed.name).toLowerCase();
}

function basenameStemKey(value?: string): string {
  return path.posix.parse(basenameKey(value)).name.toLowerCase();
}

function performerKeys(name?: string, id?: string): Set<string> {
  return new Set([name, id].map(normalizeNameKey).filter(Boolean));
}

function latestDecisionForPerformer(sidecar: FaceSidecar | undefined, performer: FaceOrganizerPerformer | undefined): FaceMatchDecision | undefined {
  if (!sidecar || !performer) return undefined;
  const targetKeys = performerKeys(performer.name, performer.id);
  for (const decision of [...(sidecar.face_match_decisions ?? [])].reverse()) {
    const keys = performerKeys(decision.performer_name, decision.performer_id);
    if ([...targetKeys].some((key) => keys.has(key))) return decision;
  }
  return undefined;
}

function toStatus(
  performers: FaceOrganizerPerformer[],
  verificationNeeded: boolean,
  sidecarFound: boolean,
  acceptedByUser: boolean,
): FaceOrganizerStatus {
  if (!sidecarFound) return "unscanned";
  const bestConfidence = Math.max(0, ...performers.map((performer) => performer.confidence ?? 0));
  const best = performers[0];
  if (acceptedByUser && best?.name && best.name !== "unknown performer") return "confirmed";
  if (best?.name && best.name !== "unknown performer" && bestConfidence >= HIGH_CONFIDENCE && !verificationNeeded) return "confirmed";
  if (bestConfidence >= POSSIBLE_CONFIDENCE) return "needs_review";
  return "unknown";
}

async function readKnownPerformers(): Promise<FaceOrganizerPerformer[]> {
  try {
    const parsed = JSON.parse(await readFile(KNOWN_PERFORMERS_INDEX, "utf8")) as {
      performers?: Array<{ id?: string; name?: string; aliases?: string[]; added_at?: string }>;
    };
    return (parsed.performers ?? [])
      .filter((performer) => performer.name)
      .map((performer) => ({
        id: performer.id,
        name: performer.name ?? "Unknown",
        aliases: performer.aliases ?? [],
        status: "verified",
        verificationNeeded: false,
        source: "known_performers",
      }));
  } catch {
    return [];
  }
}

async function readEnrolledSources(): Promise<NonNullable<FaceOrganizerMetadataResponse["enrolledSources"]>> {
  const enrolledSources: NonNullable<FaceOrganizerMetadataResponse["enrolledSources"]> = {};
  try {
    const parsed = JSON.parse(await readFile(FACE_ENROLLED_GROUPS, "utf8")) as {
      groups?: Array<{
        name?: string;
        slug?: string;
        candidate_videos?: number;
        enrolled_samples?: unknown[];
        recommendation_source_videos?: string[];
        recommendations_refreshed_at?: string;
      }>;
    };
    (parsed.groups ?? []).forEach((group) => {
      if (!group.name) return;
      const source = {
        name: group.name,
        slug: group.slug,
        candidateVideos: Math.max(0, group.candidate_videos ?? 0),
        enrolledScreens: Array.isArray(group.enrolled_samples) ? group.enrolled_samples.length : undefined,
        recommendationSourceVideos: group.recommendation_source_videos ?? [],
        refreshedAt: group.recommendations_refreshed_at,
        source: "enrolled" as const,
      };
      enrolledSources[normalizeNameKey(group.name)] = source;
      if (group.slug) enrolledSources[normalizeNameKey(group.slug)] = source;
    });
  } catch {
    // The enrolled page JSON is generated by the review server; SpiritFlix can still use the model index if it is absent.
  }

  try {
    const parsed = JSON.parse(await readFile(MODEL_INDEX, "utf8")) as {
      models?: Array<{ name?: string; slug?: string; aliases?: string[]; status?: string; video_count?: number }>;
    };
    (parsed.models ?? []).forEach((model) => {
      if (!shouldUseSpiritFlixKnownModelIndexEntry(model)) return;
      if (!model.name) return;
      const keySet = new Set([model.name, model.slug, ...(model.aliases ?? [])].filter(Boolean).map((item) => normalizeNameKey(item)));
      const candidateVideos = Math.max(0, model.video_count ?? 0);
      const source = {
        name: model.name,
        slug: model.slug,
        candidateVideos,
        source: "model_index" as const,
      };
      keySet.forEach((key) => {
        if (!key) return;
        const current = enrolledSources[key];
        if (!current || candidateVideos > current.candidateVideos) {
          enrolledSources[key] = source;
        }
      });
    });
  } catch {
    // Keep face metadata usable even if the organizer model index has not been generated.
  }

  return enrolledSources;
}

async function findSidecars(root: string): Promise<string[]> {
  const entries = await readdir(root, { withFileTypes: true }).catch(() => []);
  const files = await Promise.all(
    entries.map(async (entry) => {
      const fullPath = path.join(root, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === ".face-review") return [];
        return findSidecars(fullPath);
      }
      return entry.isFile() && entry.name.endsWith(".face-meta.json") ? [fullPath] : [];
    }),
  );
  return files.flat();
}

async function loadSidecarIndex(): Promise<Map<string, { path: string; data: FaceSidecar }>> {
  const sidecarPaths = (await Promise.all(MEDIA_ROOTS.map(findSidecars))).flat();
  const index = new Map<string, { path: string; data: FaceSidecar }>();

  await Promise.all(
    sidecarPaths.map(async (sidecarPath) => {
      try {
        const data = JSON.parse(await readFile(sidecarPath, "utf8")) as FaceSidecar;
        const videoPath = data.video_path
          ? normalizePathKey(data.video_path)
          : normalizePathKey(sidecarPath.replace(/\.face-meta\.json$/, ""));
        const bySidecarPath = normalizePathKey(sidecarPath.replace(/\.face-meta\.json$/, ""));
        const entry = { path: sidecarPath, data };
        index.set(videoPath, entry);
        index.set(bySidecarPath, entry);
        index.set(stemPathKey(videoPath), entry);
        index.set(stemPathKey(bySidecarPath), entry);
        index.set(basenameKey(videoPath), entry);
        index.set(basenameStemKey(videoPath), entry);
        index.set(basenameStemKey(bySidecarPath), entry);
      } catch {
        // Ignore malformed sidecars; the organizer can regenerate them.
      }
    }),
  );

  return index;
}

function toVideoMatch(item: FaceMetadataRequestItem, sidecar: { path: string; data: FaceSidecar } | undefined): FaceOrganizerVideoMatch {
  const performers = (sidecar?.data.performers ?? [])
    .map((performer): FaceOrganizerPerformer => ({
      id: performer.id,
      name: performer.name ?? "unknown performer",
      confidence: performer.confidence,
      similarity: performer.similarity,
      status: performer.status,
      verificationNeeded: performer.verification_needed,
      source: "sidecar",
    }))
    .sort((left, right) => (right.confidence ?? 0) - (left.confidence ?? 0));

  const verificationNeeded = sidecar?.data.verification_needed ?? performers.some((performer) => performer.verificationNeeded) ?? false;
  const primaryPerformer = performers[0];
  const latestDecision = latestDecisionForPerformer(sidecar?.data, primaryPerformer);
  const acceptedByUser = latestDecision?.decision === "accepted" && latestDecision.visual_confirmed === true;
  const status = toStatus(performers, verificationNeeded, Boolean(sidecar), acceptedByUser);
  const confidence = primaryPerformer?.confidence;
  const label =
    status === "confirmed" && primaryPerformer
      ? `Identified: ${primaryPerformer.name} (${Math.round((confidence ?? 0) * 100)}%)`
      : status === "needs_review" && primaryPerformer
        ? `Needs review: ${primaryPerformer.name} (${Math.round((confidence ?? 0) * 100)}%)`
        : status === "unknown"
          ? "Unknown performer"
          : "Unscanned";

  return {
    itemId: item.id ?? "",
    itemPath: item.path,
    sidecarPath: sidecar?.path,
    videoPath: sidecar?.data.video_path,
    primaryPerformer,
    performers,
    status,
    label,
    confidence,
    verificationNeeded,
    facesDetected: sidecar?.data.faces_detected,
    generatedAt: sidecar?.data.generated_at,
  };
}

export async function POST(request: NextRequest) {
  let payload: FaceMetadataRequest;
  try {
    payload = (await request.json()) as FaceMetadataRequest;
  } catch {
    return NextResponse.json({ error: "Invalid face metadata request." }, { status: 400 });
  }

  const items = (payload.items ?? []).filter((item) => item.id);
  const [knownPerformers, enrolledSources, sidecarIndex] = await Promise.all([
    readKnownPerformers(),
    readEnrolledSources(),
    loadSidecarIndex(),
  ]);
  const videos: FaceOrganizerMetadataResponse["videos"] = {};

  items.forEach((item) => {
    const normalizedPath = normalizePathKey(item.path);
    const match =
      sidecarIndex.get(normalizedPath) ||
      sidecarIndex.get(stemPathKey(item.path)) ||
      sidecarIndex.get(basenameKey(item.path)) ||
      sidecarIndex.get(basenameStemKey(item.path)) ||
      sidecarIndex.get(basenameKey(item.name)) ||
      sidecarIndex.get(basenameStemKey(item.name));
    videos[item.id ?? ""] = toVideoMatch(item, match);
  });

  const response: FaceOrganizerMetadataResponse = {
    knownPerformers,
    enrolledSources,
    videos,
    scannedCount: Object.values(videos).filter((video) => video.status !== "unscanned").length,
    generatedAt: new Date().toISOString(),
  };

  return NextResponse.json(response, {
    headers: {
      "Cache-Control": "no-store",
    },
  });
}
