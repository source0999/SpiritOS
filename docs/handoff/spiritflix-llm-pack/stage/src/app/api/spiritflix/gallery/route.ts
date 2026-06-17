import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";
import type { SpiritFlixGalleryItem, SpiritFlixGalleryResponse } from "@/lib/spiritflix-types";

export const runtime = "nodejs";

const IMAGE_EXTENSIONS = new Set([".jpg", ".jpeg", ".png", ".webp", ".gif"]);
const GALLERY_DIR_NAME = "model_gallery";
const GALLERY_SIDECAR_SUFFIX = ".gallery.json";

interface EnrolledGroup {
  name?: string;
  slug?: string;
  model_slug?: string;
}

interface EnrolledPayload {
  groups?: EnrolledGroup[];
}

interface GallerySidecar {
  model_name?: string;
  model_key?: string;
  model_slug?: string;
  collection?: string;
  uploaded_at?: string;
  content_type?: string;
  size_bytes?: number;
}

function normalizeNameKey(value = ""): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function slugToName(slug: string): string {
  return slug
    .split("-")
    .filter(Boolean)
    .map((part) => part.slice(0, 1).toUpperCase() + part.slice(1))
    .join(" ") || "Gallery";
}

function galleryRootCandidates(): string[] {
  return [
    process.env.SPIRITFLIX_GALLERY_ROOT,
    "/home/source/SpiritOS/scripts/media/model_gallery",
    path.join(process.cwd(), "scripts", "media", GALLERY_DIR_NAME),
  ].filter((value): value is string => Boolean(value));
}

async function exists(target: string): Promise<boolean> {
  try {
    await stat(target);
    return true;
  } catch {
    return false;
  }
}

async function findGalleryRoot(): Promise<string> {
  for (const candidate of galleryRootCandidates()) {
    if (await exists(candidate)) return candidate;
  }
  return galleryRootCandidates()[0] ?? path.join(process.cwd(), "scripts", "media", GALLERY_DIR_NAME);
}

async function readJson<T>(target: string, fallback: T): Promise<T> {
  try {
    return JSON.parse(await readFile(target, "utf8")) as T;
  } catch {
    return fallback;
  }
}

async function readModelNames(galleryRoot: string): Promise<Map<string, string>> {
  const mediaDir = path.dirname(galleryRoot);
  const enrolled = await readJson<EnrolledPayload>(path.join(mediaDir, "face_enrolled_performers.json"), { groups: [] });
  const names = new Map<string, string>();
  for (const group of enrolled.groups ?? []) {
    const name = group.name?.trim();
    const slug = (group.model_slug ?? group.slug)?.trim();
    if (name && slug) names.set(slug, name);
  }
  return names;
}

async function readGallerySidecar(imagePath: string): Promise<GallerySidecar> {
  return readJson<GallerySidecar>(`${imagePath}${GALLERY_SIDECAR_SUFFIX}`, {});
}

function contentTypeFor(fileName: string, sidecar: GallerySidecar): string {
  if (sidecar.content_type?.startsWith("image/")) return sidecar.content_type;
  const ext = path.extname(fileName).toLowerCase();
  if (ext === ".jpg" || ext === ".jpeg") return "image/jpeg";
  if (ext === ".png") return "image/png";
  if (ext === ".webp") return "image/webp";
  if (ext === ".gif") return "image/gif";
  return "application/octet-stream";
}

async function scanGallery(): Promise<SpiritFlixGalleryResponse> {
  const galleryRoot = await findGalleryRoot();
  const modelNames = await readModelNames(galleryRoot);
  const entries = await readdir(galleryRoot, { withFileTypes: true }).catch(() => []);
  const items: SpiritFlixGalleryItem[] = [];

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const modelSlug = entry.name;
    const modelDir = path.join(galleryRoot, modelSlug);
    const files = await readdir(modelDir, { withFileTypes: true }).catch(() => []);
    for (const file of files) {
      if (!file.isFile()) continue;
      if (!IMAGE_EXTENSIONS.has(path.extname(file.name).toLowerCase())) continue;
      if (file.name.endsWith(GALLERY_SIDECAR_SUFFIX)) continue;
      const imagePath = path.join(modelDir, file.name);
      const [fileStat, sidecar] = await Promise.all([stat(imagePath), readGallerySidecar(imagePath)]);
      const modelName = sidecar.model_name ?? modelNames.get(modelSlug) ?? slugToName(modelSlug);
      const src = `/api/spiritflix/gallery/image?model=${encodeURIComponent(modelSlug)}&file=${encodeURIComponent(file.name)}`;
      items.push({
        id: `${modelSlug}/${file.name}`,
        modelName,
        modelKey: sidecar.model_key ?? normalizeNameKey(modelName),
        modelSlug,
        fileName: file.name,
        src,
        thumbnailSrc: src,
        collection: sidecar.collection ?? "",
        uploadedAt: sidecar.uploaded_at ?? fileStat.mtime.toISOString(),
        sizeBytes: sidecar.size_bytes ?? fileStat.size,
        contentType: contentTypeFor(file.name, sidecar),
      });
    }
  }

  items.sort((left, right) => (right.uploadedAt ?? "").localeCompare(left.uploadedAt ?? ""));
  const groups = Array.from(
    items.reduce((map, item) => {
      const current = map.get(item.modelSlug) ?? {
        name: item.modelName,
        modelKey: item.modelKey,
        modelSlug: item.modelSlug,
        itemCount: 0,
      };
      current.itemCount += 1;
      map.set(item.modelSlug, current);
      return map;
    }, new Map<string, SpiritFlixGalleryResponse["groups"][number]>()),
  ).map(([, group]) => group);

  return {
    schema: "spiritflix-model-gallery/v1",
    generatedAt: new Date().toISOString(),
    items,
    groups: groups.sort((left, right) => left.name.localeCompare(right.name)),
    summary: {
      galleryItems: items.length,
      modelsWithGallery: groups.length,
    },
  };
}

export async function GET() {
  const payload = await scanGallery();
  return NextResponse.json(payload, {
    headers: {
      "Cache-Control": "no-store",
    },
  });
}
