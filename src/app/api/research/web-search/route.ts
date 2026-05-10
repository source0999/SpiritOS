import { NextResponse } from "next/server";

import { runWebSearch } from "@/lib/server/web-search/provider-router";
import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
import { isModelProfileId } from "@/lib/spirit/model-profiles";

// /api/research/web-search - provider-neutral proof-of-search.
// Isolated from Hermes; UI can call to preview sources without streaming chat.

export const dynamic = "force-dynamic";
export const maxDuration = 120;

type Body = {
  query?: unknown;
  mode?: unknown;
  maxResults?: unknown;
  paidFallbackApproved?: unknown;
};

function failureStatus(error: string): number {
  if (error === "disabled") return 403;
  if (error === "missing_key") return 503;
  if (error === "empty_query" || error === "no_local_provider_available") return 422;
  return 502;
}

export async function POST(req: Request) {
  let json: unknown;
  try {
    json = await req.json();
  } catch {
    return NextResponse.json(
      { ok: false, provider: "manual", searched: false, error: "invalid_json", detail: "Body must be JSON" },
      { status: 400 },
    );
  }

  if (!json || typeof json !== "object") {
    return NextResponse.json(
      { ok: false, provider: "manual", searched: false, error: "bad_body", detail: "Expected object" },
      { status: 400 },
    );
  }

  const b = json as Body;
  if (typeof b.query !== "string" || !b.query.trim()) {
    return NextResponse.json(
      { ok: false, provider: "manual", searched: false, error: "missing_query", detail: "query string required" },
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
          provider: "manual",
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
          provider: "manual",
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
          provider: "manual",
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

  const result = await runWebSearch({
    query: b.query.trim(),
    maxResults,
    paidFallbackApproved: b.paidFallbackApproved === true,
  });

  if (!result.ok) {
    return NextResponse.json(result, { status: failureStatus(result.error) });
  }

  return NextResponse.json(result);
}
