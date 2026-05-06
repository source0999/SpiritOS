import { NextResponse } from "next/server";

import {
  ElevenLabsVoicesFetchError,
  enrichAllowlistWithCatalog,
  fetchElevenLabsVoicesNormalized,
  hasElevenLabsApiKey,
  parseElevenLabsVoiceAllowlistFromEnv,
  pickDefaultElevenLabsVoice,
  resolveElevenLabsVoiceAllowlist,
  sortElevenLabsVoicesForUi,
  WARN_NAME_ONLY_CATALOG_FAILED,
} from "@/lib/server/elevenlabs-voices";

// ── GET /api/tts/voices - allowlist-only + name resolution (Prompt 9L) ────────────
export const dynamic = "force-dynamic";

function httpStatusForVoicesError(e: ElevenLabsVoicesFetchError): number {
  if (e.code === "elevenlabs_missing_key" || e.code === "elevenlabs_network") return 503;
  if (e.httpStatus === 401 || e.httpStatus === 403 || e.httpStatus === 429) return e.httpStatus;
  return 502;
}

function defaultFromEnvWhenEmptyVoices(): {
  defaultVoiceId: string | null;
  defaultVoiceName: string | null;
} {
  const id = process.env.ELEVENLABS_DEFAULT_VOICE_ID?.trim();
  const name = process.env.ELEVENLABS_DEFAULT_VOICE_NAME?.trim();
  if (id) return { defaultVoiceId: id, defaultVoiceName: name ?? null };
  const legacy = process.env.ELEVENLABS_VOICE_ID?.trim();
  if (legacy) return { defaultVoiceId: legacy, defaultVoiceName: name ?? null };
  return { defaultVoiceId: null, defaultVoiceName: name ?? null };
}

export async function GET() {
  const parsed = parseElevenLabsVoiceAllowlistFromEnv();
  const hasAllowlist = parsed.hasAllowlist;
  const hasKey = hasElevenLabsApiKey();

  const baseWarnings: string[] = [];
  if (parsed.invalidEntries.length > 0) {
    baseWarnings.push(`Ignored invalid allowlist entries: ${parsed.invalidEntries.join("; ")}.`);
  }

  /** Hard fail: no allowlist and no way to load catalog. */
  if (!hasAllowlist && !hasKey) {
    return NextResponse.json(
      {
        ok: false as const,
        provider: "elevenlabs" as const,
        error: "ElevenLabs API key missing and no ELEVENLABS_VOICE_ALLOWLIST configured",
        status: 503 as const,
      },
      { status: 503 },
    );
  }

  if (hasAllowlist && !hasKey) {
    if (parsed.nameOnly.length > 0 && parsed.explicitVoices.length === 0) {
      const envDef = defaultFromEnvWhenEmptyVoices();
      return NextResponse.json(
        {
          ok: true as const,
          provider: "elevenlabs" as const,
          source: "env-name-allowlist" as const,
          allowlistMode: parsed.allowlistMode,
          voices: [] as const,
          defaultVoiceId: envDef.defaultVoiceId,
          defaultVoiceName: envDef.defaultVoiceName,
          warnings: [
            ...baseWarnings,
            "Name-only allowlist requires ELEVENLABS_API_KEY so the catalog can resolve names. Use Name:voice_id pairs (e.g. Clarice:abc…) to skip the catalog.",
          ],
        },
        { status: 200, headers: { "Cache-Control": "no-store" } },
      );
    }

    const voices = parsed.explicitVoices;
    const picked = pickDefaultElevenLabsVoice(sortElevenLabsVoicesForUi(voices));
    return NextResponse.json(
      {
        ok: true as const,
        provider: "elevenlabs" as const,
        source: "env-allowlist" as const,
        allowlistMode: parsed.allowlistMode,
        voices,
        defaultVoiceId: picked.defaultVoiceId,
        defaultVoiceName: picked.defaultVoiceName,
        warnings: [
          ...baseWarnings,
          "ElevenLabs API key missing; catalog disabled. Explicit voice IDs from env still work.",
        ],
        ...(picked.warning ? { pickWarning: picked.warning } : {}),
      },
      { status: 200, headers: { "Cache-Control": "no-store" } },
    );
  }

  if (hasAllowlist && hasKey) {
    let catalog: Awaited<ReturnType<typeof fetchElevenLabsVoicesNormalized>> = [];
    let catalogErr: ElevenLabsVoicesFetchError | null = null;
    try {
      catalog = await fetchElevenLabsVoicesNormalized();
    } catch (e) {
      if (e instanceof ElevenLabsVoicesFetchError) {
        catalogErr = e;
        console.warn(
          "[api/tts/voices] catalog failed",
          e.code,
          e.safeDetail ?? e.message,
        );
      } else {
        throw e;
      }
    }

    if (catalogErr) {
      const detail = catalogErr.safeDetail?.slice(0, 400);
      if (parsed.explicitVoices.length > 0) {
        const enriched = enrichAllowlistWithCatalog(parsed.explicitVoices, []);
        const picked = pickDefaultElevenLabsVoice(sortElevenLabsVoicesForUi(enriched));
        const warnings = [
          ...baseWarnings,
          "ElevenLabs catalog unavailable; using allowlist voice IDs only.",
        ];
        if (parsed.nameOnly.length > 0) {
          warnings.push(WARN_NAME_ONLY_CATALOG_FAILED);
        }
        return NextResponse.json(
          {
            ok: true as const,
            provider: "elevenlabs" as const,
            source: "env-allowlist" as const,
            allowlistMode: parsed.allowlistMode,
            voices: enriched,
            defaultVoiceId: picked.defaultVoiceId,
            defaultVoiceName: picked.defaultVoiceName,
            warnings,
            ...(detail ? { detail } : {}),
            ...(picked.warning ? { pickWarning: picked.warning } : {}),
          },
          { status: 200, headers: { "Cache-Control": "no-store" } },
        );
      }

      const envDef = defaultFromEnvWhenEmptyVoices();
      return NextResponse.json(
        {
          ok: true as const,
          provider: "elevenlabs" as const,
          source: "env-name-allowlist" as const,
          allowlistMode: parsed.allowlistMode,
          voices: [],
          defaultVoiceId: envDef.defaultVoiceId,
          defaultVoiceName: envDef.defaultVoiceName,
          warnings: [...baseWarnings, WARN_NAME_ONLY_CATALOG_FAILED],
          ...(detail ? { detail } : {}),
        },
        { status: 200, headers: { "Cache-Control": "no-store" } },
      );
    }

    const resolved = resolveElevenLabsVoiceAllowlist({ parsed, catalog });
    const warnings = [...baseWarnings, ...resolved.warnings];
    const voices = enrichAllowlistWithCatalog(resolved.voices, catalog);

    let source: "env-allowlist" | "env-name-allowlist" | "mixed" | "elevenlabs-api" =
      "env-allowlist";
    if (parsed.allowlistMode === "name-only") {
      source = "env-name-allowlist";
    } else if (catalog.length > 0) {
      source = "mixed";
    }

    const picked = pickDefaultElevenLabsVoice(sortElevenLabsVoicesForUi(voices));
    return NextResponse.json(
      {
        ok: true as const,
        provider: "elevenlabs" as const,
        source,
        allowlistMode: parsed.allowlistMode,
        voices,
        defaultVoiceId: picked.defaultVoiceId,
        defaultVoiceName: picked.defaultVoiceName,
        warnings,
        ...(picked.warning ? { pickWarning: picked.warning } : {}),
      },
      { status: 200, headers: { "Cache-Control": "no-store" } },
    );
  }

  /* No allowlist - full catalog */
  try {
    const voices = await fetchElevenLabsVoicesNormalized();
    const picked = pickDefaultElevenLabsVoice(voices);
    return NextResponse.json(
      {
        ok: true as const,
        provider: "elevenlabs" as const,
        source: "elevenlabs-api" as const,
        allowlistMode: "none" as const,
        voices,
        defaultVoiceId: picked.defaultVoiceId,
        defaultVoiceName: picked.defaultVoiceName,
        warnings: [] as string[],
        ...(picked.warning ? { pickWarning: picked.warning } : {}),
      },
      { status: 200, headers: { "Cache-Control": "no-store" } },
    );
  } catch (e) {
    if (e instanceof ElevenLabsVoicesFetchError) {
      const status = httpStatusForVoicesError(e);
      console.warn("[api/tts/voices]", e.code, "upstreamStatus=", e.httpStatus, "detail=", e.safeDetail ?? e.message);
      if (e.code === "elevenlabs_missing_key") {
        return NextResponse.json(
          {
            ok: false as const,
            provider: "elevenlabs" as const,
            error: "ElevenLabs API key missing",
            status: 503 as const,
            detail: e.safeDetail,
          },
          { status: 503 },
        );
      }
      const human =
        e.code === "elevenlabs_unauthorized"
          ? "Unauthorized"
          : e.code === "elevenlabs_forbidden"
            ? "Forbidden"
            : e.code === "elevenlabs_rate_limited"
              ? "Rate limited"
              : e.code === "elevenlabs_network"
                ? "Network error reaching ElevenLabs"
                : e.code === "elevenlabs_bad_json"
                  ? "Invalid response from ElevenLabs"
                  : "ElevenLabs voices request failed";
      return NextResponse.json(
        {
          ok: false as const,
          provider: "elevenlabs" as const,
          error: human,
          status: e.httpStatus,
          detail: e.safeDetail?.slice(0, 400),
        },
        { status },
      );
    }
    const msg = e instanceof Error ? e.message : String(e);
    console.error("[api/tts/voices] unexpected", msg);
    return NextResponse.json(
      {
        ok: false as const,
        provider: "elevenlabs" as const,
        error: "Could not load voices",
        status: 502,
        detail: msg.slice(0, 200),
      },
      { status: 502 },
    );
  }
}
