import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

const IMAGE_EXTENSIONS = new Set([".jpg", ".jpeg", ".png", ".webp", ".gif"]);
const GALLERY_DIR_NAME = "model_gallery";

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

function contentTypeFor(fileName: string): string {
  const ext = path.extname(fileName).toLowerCase();
  if (ext === ".jpg" || ext === ".jpeg") return "image/jpeg";
  if (ext === ".png") return "image/png";
  if (ext === ".webp") return "image/webp";
  if (ext === ".gif") return "image/gif";
  return "application/octet-stream";
}

function isSafeModelSlug(value: string): boolean {
  return /^[a-z0-9][a-z0-9-]*$/.test(value);
}

export async function GET(request: NextRequest) {
  const model = request.nextUrl.searchParams.get("model") ?? "";
  const file = request.nextUrl.searchParams.get("file") ?? "";
  if (!isSafeModelSlug(model) || !file || file !== path.basename(file) || !IMAGE_EXTENSIONS.has(path.extname(file).toLowerCase())) {
    return NextResponse.json({ error: "Invalid gallery image path." }, { status: 400 });
  }

  const galleryRoot = await findGalleryRoot();
  const modelRoot = path.resolve(galleryRoot, model);
  const target = path.resolve(modelRoot, file);
  if (target !== modelRoot && !target.startsWith(`${modelRoot}${path.sep}`)) {
    return NextResponse.json({ error: "Invalid gallery image path." }, { status: 400 });
  }

  try {
    const payload = await readFile(target);
    return new NextResponse(payload, {
      headers: {
        "Cache-Control": "no-store",
        "Content-Type": contentTypeFor(file),
      },
    });
  } catch {
    return NextResponse.json({ error: "Gallery image not found." }, { status: 404 });
  }
}
