import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { NextRequest, NextResponse } from "next/server";
import type {
  FaceOrganizerMetadataResponse,
  FaceOrganizerPerformer,
  FaceOrganizerStatus,
  FaceOrganizerVideoMatch,
} from "@/lib/spiritflix-types";

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

interface FaceSidecar {
  video_path?: string;
  generated_at?: string;
  verification_needed?: boolean;
  performers?: SidecarPerformer[];
  faces_detected?: number;
}

const MEDIA_ROOTS = ["/mnt/spirit-8tb/media/yes", "/mnt/spirit-8tb/media/other"];
const KNOWN_PERFORMERS_INDEX = "/home/source/SpiritOS/scripts/media/known_performers/index.json";
const HIGH_CONFIDENCE = 0.8;
const POSSIBLE_CONFIDENCE = 0.55;

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

function toStatus(performers: FaceOrganizerPerformer[], verificationNeeded: boolean, sidecarFound: boolean): FaceOrganizerStatus {
  if (!sidecarFound) return "unscanned";
  const bestConfidence = Math.max(0, ...performers.map((performer) => performer.confidence ?? 0));
  const best = performers[0];
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
        index.set(basenameKey(videoPath), entry);
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
  const status = toStatus(performers, verificationNeeded, Boolean(sidecar));
  const primaryPerformer = performers[0];
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
  const [knownPerformers, sidecarIndex] = await Promise.all([readKnownPerformers(), loadSidecarIndex()]);
  const videos: FaceOrganizerMetadataResponse["videos"] = {};

  items.forEach((item) => {
    const normalizedPath = normalizePathKey(item.path);
    const match =
      sidecarIndex.get(normalizedPath) ||
      sidecarIndex.get(basenameKey(item.path)) ||
      sidecarIndex.get(basenameKey(item.name));
    videos[item.id ?? ""] = toVideoMatch(item, match);
  });

  const response: FaceOrganizerMetadataResponse = {
    knownPerformers,
    videos,
    scannedCount: Object.values(videos).filter((video) => video.status !== "unscanned").length,
    generatedAt: new Date().toISOString(),
  };

  return NextResponse.json(response, {
    headers: {
      "Cache-Control": "private, max-age=60",
    },
  });
}
