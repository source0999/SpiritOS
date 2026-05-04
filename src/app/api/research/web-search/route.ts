import { NextResponse } from "next/server";

import { runOpenAiWebSearch } from "@/lib/server/openai-web-search";
import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
import { isModelProfileId } from "@/lib/spirit/model-profiles";

// ── /api/research/web-search — OpenAI proof-of-search (Prompt 10B) ───────────────
// > Isolated from Hermes; UI can call to preview sources without streaming chat.

export const dynamic = "force-dynamic";
export const maxDuration = 120;

type Body = {
  query?: unknown;
  mode?: unknown;
  maxResults?: unknown;
};

export async function POST(req: Request) {
  let json: unknown;
  try {
    json = await req.json();
  } catch {
    return NextResponse.json(
      { ok: false, provider: "openai", searched: false, error: "invalid_json", detail: "Body must be JSON" },
      { status: 400 },
    );
  }

  if (!json || typeof json !== "object") {
    return NextResponse.json(
      { ok: false, provider: "openai", searched: false, error: "bad_body", detail: "Expected object" },
      { status: 400 },
    );
  }

  const b = json as Body;
  if (typeof b.query !== "string" || !b.query.trim()) {
    return NextResponse.json(
      { ok: false, provider: "openai", searched: false, error: "missing_query", detail: "query string required" },
      { status: 400 },
    );
  }

  const modeRaw = b.mode;
  let mode: ModelProfileId | undefined;
  if (modeRaw !== undefined && modeRaw !== null) {
    if (typeof modeRaw !== "string") {
      return NextResponse.json(
        {
          ok: false,
          provider: "openai",
          searched: false,
          error: "bad_mode",
          detail: "mode must be a string",
        },
        { status: 400 },
      );
    }
    const normalized = modeRaw === "peer" ? "normal-peer" : modeRaw;
    if (!isModelProfileId(normalized)) {
      return NextResponse.json(
        {
          ok: false,
          provider: "openai",
          searched: false,
          error: "bad_mode",
          detail: "mode must be researcher | teacher | peer (ModelProfileId subset)",
        },
        { status: 400 },
      );
    }
    mode = normalized;
    if (mode !== "researcher" && mode !== "teacher" && mode !== "normal-peer") {
      return NextResponse.json(
        {
          ok: false,
          provider: "openai",
          searched: false,
          error: "bad_mode",
          detail: "mode must be researcher | teacher | peer for this route",
        },
        { status: 400 },
      );
    }
  }

  let maxResults: number | undefined;
  if (typeof b.maxResults === "number" && Number.isFinite(b.maxResults)) {
    maxResults = Math.min(Math.max(Math.floor(b.maxResults), 1), 12);
  }

  const result = await runOpenAiWebSearch({
    query: b.query.trim(),
    maxResults,
  });

  if (!result.ok) {
    const status =
      result.error === "missing_key" ? 503 : result.error === "disabled" ? 403 : 502;
    return NextResponse.json(result, { status });
  }

  return NextResponse.json(result);
}
