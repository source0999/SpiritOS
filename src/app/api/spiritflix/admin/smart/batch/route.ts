import { NextRequest, NextResponse } from "next/server";
import { isSpiritFlixAdminPathError } from "@/lib/spiritflix/admin/paths";
import { previewSpiritFlixSmartBatch, runSpiritFlixSmartBatch } from "@/lib/spiritflix/admin/smart";

export const runtime = "nodejs";

function numberParam(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value !== "string" || !value.trim()) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function boolParam(value: unknown): boolean {
  return value === true || value === "true";
}

function jsonError(error: unknown, fallbackStatus = 500) {
  if (isSpiritFlixAdminPathError(error)) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Invalid path." }, { status: 400 });
  }
  const message = error instanceof Error ? error.message : "Smart batch analysis failed.";
  const status = /requires a folder|path|outside|traversal|not allowed|selection/i.test(message) ? 400 : fallbackStatus;
  return NextResponse.json({ error: message.slice(0, 500) }, { status });
}

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  try {
    const payload = await previewSpiritFlixSmartBatch({
      path: url.searchParams.get("path") ?? undefined,
      recursive: boolParam(url.searchParams.get("recursive")),
      maxItems: numberParam(url.searchParams.get("maxItems")),
    });
    return NextResponse.json(payload, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return jsonError(error);
  }
}

export async function POST(request: NextRequest) {
  let body: {
    path?: string;
    paths?: string[];
    action?: string;
    recursive?: boolean;
    maxItems?: number;
    force?: boolean;
  };
  try {
    body = (await request.json()) as typeof body;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const action = body.action?.trim() || "run";
  if (action !== "preview" && action !== "run") {
    return NextResponse.json({ error: "Unsupported smart batch action." }, { status: 400 });
  }

  try {
    const options = {
      path: body.path,
      paths: Array.isArray(body.paths) ? body.paths : undefined,
      recursive: Boolean(body.recursive),
      maxItems: numberParam(body.maxItems),
      force: Boolean(body.force),
    };
    const payload = action === "preview"
      ? await previewSpiritFlixSmartBatch(options)
      : await runSpiritFlixSmartBatch(options);
    return NextResponse.json(payload, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return jsonError(error);
  }
}
