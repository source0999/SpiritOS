import "server-only";

// ── ElevenLabs voice list — GET /v1/voices for UI + defaults (Prompt 9L allowlist) ─
// > Name-only allowlist needs catalog; explicit Name:voice_id does not need voices_read.

export type ElevenLabsVoiceRow = {
  voice_id: string;
  name: string;
  category?: string;
  labels?: Record<string, string>;
  preview_url?: string | null;
};

type ElevenLabsVoicesApiVoice = {
  voice_id?: string;
  name?: string;
  category?: string;
  labels?: Record<string, string>;
  preview_url?: string | null;
};

type ElevenLabsVoicesApi = {
  voices?: ElevenLabsVoicesApiVoice[];
  data?: { voices?: ElevenLabsVoicesApiVoice[] };
};

const FETCH_TIMEOUT_MS = 25_000;

/** RHS after `:` must look like a real ElevenLabs voice_id (not "Paige"). */
const VOICE_ID_LIKE = /^[a-zA-Z0-9_-]{10,64}$/;

export type ElevenLabsVoicesFetchErrorCode =
  | "elevenlabs_missing_key"
  | "elevenlabs_unauthorized"
  | "elevenlabs_forbidden"
  | "elevenlabs_rate_limited"
  | "elevenlabs_upstream"
  | "elevenlabs_bad_json"
  | "elevenlabs_network";

export class ElevenLabsVoicesFetchError extends Error {
  readonly name = "ElevenLabsVoicesFetchError";

  constructor(
    message: string,
    public readonly httpStatus: number,
    public readonly code: ElevenLabsVoicesFetchErrorCode,
    public readonly safeDetail?: string,
  ) {
    super(message);
  }
}

function abortTimeout(): AbortSignal {
  try {
    return AbortSignal.timeout(FETCH_TIMEOUT_MS);
  } catch {
    const c = new AbortController();
    const t = setTimeout(() => c.abort(), FETCH_TIMEOUT_MS);
    void t.unref?.();
    return c.signal;
  }
}

function normalizeRow(v: ElevenLabsVoicesApiVoice): ElevenLabsVoiceRow | null {
  const id = typeof v.voice_id === "string" ? v.voice_id.trim() : "";
  const name = typeof v.name === "string" ? v.name.trim() : "";
  if (!id || !name) return null;
  return {
    voice_id: id,
    name,
    category: typeof v.category === "string" ? v.category.trim() : undefined,
    labels: v.labels && typeof v.labels === "object" ? v.labels : undefined,
    preview_url:
      typeof v.preview_url === "string" && v.preview_url.trim()
        ? v.preview_url.trim()
        : null,
  };
}

function safeUpstreamSnippet(text: string, max = 240): string {
  const t = text.replace(/\s+/g, " ").trim();
  if (!t) return "";
  return t.length > max ? `${t.slice(0, max)}…` : t;
}

function extractVoicesArray(json: unknown): ElevenLabsVoicesApiVoice[] {
  if (!json || typeof json !== "object") return [];
  const root = json as ElevenLabsVoicesApi;
  if (Array.isArray(root.voices)) return root.voices;
  const nested = root.data?.voices;
  if (Array.isArray(nested)) return nested;
  return [];
}

/** Sort: Clarice first (case-insensitive), then name A–Z. */
export function sortElevenLabsVoicesForUi(rows: ElevenLabsVoiceRow[]): ElevenLabsVoiceRow[] {
  return [...rows].sort((a, b) => {
    const ac = a.name.toLowerCase() === "clarice" ? 0 : 1;
    const bc = b.name.toLowerCase() === "clarice" ? 0 : 1;
    if (ac !== bc) return ac - bc;
    return a.name.localeCompare(b.name, undefined, { sensitivity: "base" });
  });
}

export type PickDefaultElevenLabsVoiceResult = {
  defaultVoiceId: string | null;
  defaultVoiceName: string | null;
  /** When env default id is set but absent from fetched catalog (non-empty list). */
  warning?: string;
};

/**
 * Default pick order:
 * 1) ELEVENLABS_DEFAULT_VOICE_ID (in list → name from row; empty list → env name / "Configured voice"; not in list → warning)
 * 2) Clarice by name
 * 3) ELEVENLABS_VOICE_ID
 * 4) first sorted row
 */
export function pickDefaultElevenLabsVoice(
  sortedRows: ElevenLabsVoiceRow[],
): PickDefaultElevenLabsVoiceResult {
  const envDefaultId = process.env.ELEVENLABS_DEFAULT_VOICE_ID?.trim();
  const envDefaultName = process.env.ELEVENLABS_DEFAULT_VOICE_NAME?.trim();

  if (envDefaultId) {
    const hit = sortedRows.find((r) => r.voice_id === envDefaultId);
    if (sortedRows.length === 0) {
      return {
        defaultVoiceId: envDefaultId,
        defaultVoiceName: envDefaultName ?? "Configured voice",
      };
    }
    if (!hit) {
      return {
        defaultVoiceId: envDefaultId,
        defaultVoiceName: envDefaultName ?? "Configured voice",
        warning: "default_voice_id_not_in_catalog",
      };
    }
    return {
      defaultVoiceId: envDefaultId,
      defaultVoiceName: hit.name,
    };
  }

  const clarice = sortedRows.find((r) => r.name.toLowerCase() === "clarice");
  if (clarice) {
    return { defaultVoiceId: clarice.voice_id, defaultVoiceName: clarice.name };
  }

  const legacy = process.env.ELEVENLABS_VOICE_ID?.trim();
  if (legacy) {
    const hit = sortedRows.find((r) => r.voice_id === legacy);
    return { defaultVoiceId: legacy, defaultVoiceName: hit?.name ?? null };
  }

  const first = sortedRows[0];
  if (first) return { defaultVoiceId: first.voice_id, defaultVoiceName: first.name };
  return { defaultVoiceId: null, defaultVoiceName: null };
}

// ── Env allowlist — explicit ids OR name-only (Prompt 9L) ─────────────────────────

export type ElevenLabsAllowlistMode = "explicit-id" | "name-only" | "mixed" | "json" | "none";

export type AllowlistOrderedSegment =
  | { kind: "explicit"; row: ElevenLabsVoiceRow }
  | { kind: "name"; name: string };

export type ParsedElevenLabsAllowlist = {
  orderedSegments: AllowlistOrderedSegment[];
  explicitVoices: ElevenLabsVoiceRow[];
  nameOnly: string[];
  hasAllowlist: boolean;
  invalidEntries: string[];
  allowlistMode: ElevenLabsAllowlistMode;
};

export const WARN_NAME_ONLY_CATALOG_FAILED =
  "Voice allowlist uses names only, but ElevenLabs catalog lookup failed. Use Name:voice_id pairs to avoid voices_read permission.";

function parseCommaToken(token: string): AllowlistOrderedSegment | "invalid" | null {
  const t = token.trim();
  if (!t) return null;
  const lastColon = t.lastIndexOf(":");
  if (lastColon <= 0) {
    return { kind: "name", name: t };
  }
  if (lastColon >= t.length - 1) {
    return "invalid";
  }
  const name = t.slice(0, lastColon).trim();
  const voice_id = t.slice(lastColon + 1).trim();
  if (!name || !voice_id) return "invalid";
  if (VOICE_ID_LIKE.test(voice_id)) {
    return { kind: "explicit", row: { voice_id, name } };
  }
  /* Colon present but RHS is not a plausible voice_id — treat whole token as a display name (catalog match). */
  return { kind: "name", name: t };
}

/**
 * `ELEVENLABS_VOICE_ALLOWLIST_JSON` wins over comma env when both are set.
 * JSON: `[{"name":"Clarice","voice_id":"abc"},…]` — always explicit-id mode.
 * Comma: `Name:voice_id` (id must match VOICE_ID_LIKE) OR `Charlotte,Clarice` name-only.
 */
export function parseElevenLabsVoiceAllowlistFromEnv(): ParsedElevenLabsAllowlist {
  const jsonRaw = process.env.ELEVENLABS_VOICE_ALLOWLIST_JSON?.trim();
  if (jsonRaw) {
    try {
      const parsed = JSON.parse(jsonRaw) as unknown;
      if (!Array.isArray(parsed)) {
        return {
          orderedSegments: [],
          explicitVoices: [],
          nameOnly: [],
          hasAllowlist: false,
          invalidEntries: [],
          allowlistMode: "none",
        };
      }
      const orderedSegments: AllowlistOrderedSegment[] = [];
      const explicitVoices: ElevenLabsVoiceRow[] = [];
      const invalidEntries: string[] = [];
      for (const row of parsed) {
        if (!row || typeof row !== "object") continue;
        const o = row as Record<string, unknown>;
        const voice_id = typeof o.voice_id === "string" ? o.voice_id.trim() : "";
        const name = typeof o.name === "string" ? o.name.trim() : "";
        if (!voice_id || !name) {
          invalidEntries.push(JSON.stringify(row).slice(0, 80));
          continue;
        }
        const r = { voice_id, name };
        explicitVoices.push(r);
        orderedSegments.push({ kind: "explicit", row: r });
      }
      const hasAllowlist = orderedSegments.length > 0;
      return {
        orderedSegments,
        explicitVoices,
        nameOnly: [],
        hasAllowlist,
        invalidEntries,
        allowlistMode: hasAllowlist ? "json" : "none",
      };
    } catch {
      return {
        orderedSegments: [],
        explicitVoices: [],
        nameOnly: [],
        hasAllowlist: false,
        invalidEntries: [],
        allowlistMode: "none",
      };
    }
  }

  const comma = process.env.ELEVENLABS_VOICE_ALLOWLIST?.trim();
  if (!comma) {
    return {
      orderedSegments: [],
      explicitVoices: [],
      nameOnly: [],
      hasAllowlist: false,
      invalidEntries: [],
      allowlistMode: "none",
    };
  }

  const orderedSegments: AllowlistOrderedSegment[] = [];
  const explicitVoices: ElevenLabsVoiceRow[] = [];
  const nameOnly: string[] = [];
  const invalidEntries: string[] = [];

  for (const part of comma.split(",")) {
    const seg = parseCommaToken(part);
    if (seg === null) continue;
    if (seg === "invalid") {
      invalidEntries.push(part.trim());
      continue;
    }
    orderedSegments.push(seg);
    if (seg.kind === "explicit") {
      explicitVoices.push(seg.row);
    } else {
      nameOnly.push(seg.name);
    }
  }

  const hasAllowlist = orderedSegments.length > 0;
  let allowlistMode: ElevenLabsAllowlistMode = "none";
  if (hasAllowlist) {
    if (explicitVoices.length > 0 && nameOnly.length > 0) allowlistMode = "mixed";
    else if (explicitVoices.length > 0) allowlistMode = "explicit-id";
    else allowlistMode = "name-only";
  }

  return {
    orderedSegments,
    explicitVoices,
    nameOnly,
    hasAllowlist,
    invalidEntries,
    allowlistMode,
  };
}

export type ResolveElevenLabsVoiceAllowlistInput = {
  parsed: ParsedElevenLabsAllowlist;
  catalog: ElevenLabsVoiceRow[];
};

export type ResolveElevenLabsVoiceAllowlistResult = {
  voices: ElevenLabsVoiceRow[];
  warnings: string[];
  missingNames: string[];
};

/**
 * Resolves allowlist segments against catalog (case-insensitive name match).
 * Preserves env order. Does not append unrelated catalog voices.
 */
export function resolveElevenLabsVoiceAllowlist(
  input: ResolveElevenLabsVoiceAllowlistInput,
): ResolveElevenLabsVoiceAllowlistResult {
  const { parsed, catalog } = input;
  const warnings: string[] = [];
  const missingNames: string[] = [];
  const voices: ElevenLabsVoiceRow[] = [];

  if (!parsed.hasAllowlist) {
    return { voices: [...catalog], warnings, missingNames };
  }

  const byLower = new Map<string, ElevenLabsVoiceRow>();
  for (const r of catalog) {
    byLower.set(r.name.toLowerCase().trim(), r);
  }

  for (const seg of parsed.orderedSegments) {
    if (seg.kind === "explicit") {
      voices.push({ ...seg.row });
      continue;
    }
    const key = seg.name.toLowerCase().trim();
    const hit = byLower.get(key);
    if (hit) {
      voices.push({
        ...hit,
        name: seg.name.trim(),
      });
    } else {
      missingNames.push(seg.name.trim());
    }
  }

  if (missingNames.length > 0) {
    warnings.push(
      `Some allowlist names could not be resolved in the ElevenLabs catalog: ${missingNames.join(", ")}.`,
    );
  }

  return { voices, warnings, missingNames };
}

/** Merge catalog metadata into allowlisted rows (same `voice_id` only). */
export function enrichAllowlistWithCatalog(
  allowlist: ElevenLabsVoiceRow[],
  catalog: ElevenLabsVoiceRow[],
): ElevenLabsVoiceRow[] {
  const byId = new Map(catalog.map((r) => [r.voice_id, r]));
  return allowlist.map((a) => {
    const hit = byId.get(a.voice_id);
    if (!hit) return { ...a };
    return {
      voice_id: a.voice_id,
      name: a.name,
      category: hit.category ?? a.category,
      labels: hit.labels ?? a.labels,
      preview_url: hit.preview_url ?? a.preview_url,
    };
  });
}

export function hasElevenLabsApiKey(): boolean {
  return Boolean(process.env.ELEVENLABS_API_KEY?.trim());
}

export async function fetchElevenLabsVoicesNormalized(): Promise<ElevenLabsVoiceRow[]> {
  const key = process.env.ELEVENLABS_API_KEY?.trim();
  if (!key) {
    throw new ElevenLabsVoicesFetchError(
      "ElevenLabs API key missing",
      503,
      "elevenlabs_missing_key",
    );
  }

  let res: Response;
  try {
    res = await fetch("https://api.elevenlabs.io/v1/voices", {
      method: "GET",
      headers: {
        "xi-api-key": key,
        Accept: "application/json",
      },
      signal: abortTimeout(),
    });
  } catch (e) {
    const detail = e instanceof Error ? e.message : String(e);
    const isAbort =
      (e instanceof DOMException && e.name === "AbortError") ||
      (e instanceof Error && /abort/i.test(e.message));
    throw new ElevenLabsVoicesFetchError(
      isAbort ? "ElevenLabs voices request timed out or aborted" : "ElevenLabs voices network error",
      503,
      "elevenlabs_network",
      safeUpstreamSnippet(detail, 200),
    );
  }

  const ct = res.headers.get("content-type") ?? "";
  const rawText = await res.text().catch(() => res.statusText);

  if (!res.ok) {
    const detail = safeUpstreamSnippet(rawText, 280);
    if (res.status === 401) {
      throw new ElevenLabsVoicesFetchError("Unauthorized", res.status, "elevenlabs_unauthorized", detail);
    }
    if (res.status === 403) {
      throw new ElevenLabsVoicesFetchError("Forbidden", res.status, "elevenlabs_forbidden", detail);
    }
    if (res.status === 429) {
      throw new ElevenLabsVoicesFetchError("Rate limited", res.status, "elevenlabs_rate_limited", detail);
    }
    throw new ElevenLabsVoicesFetchError(
      "ElevenLabs voices request failed",
      res.status >= 400 && res.status < 600 ? res.status : 502,
      "elevenlabs_upstream",
      detail || res.statusText,
    );
  }

  if (!ct.includes("json")) {
    throw new ElevenLabsVoicesFetchError(
      "Unexpected ElevenLabs response (not JSON)",
      502,
      "elevenlabs_bad_json",
      safeUpstreamSnippet(rawText, 120),
    );
  }

  let json: unknown;
  try {
    json = JSON.parse(rawText) as unknown;
  } catch {
    throw new ElevenLabsVoicesFetchError(
      "Invalid JSON from ElevenLabs",
      502,
      "elevenlabs_bad_json",
      safeUpstreamSnippet(rawText, 120),
    );
  }

  const raw = extractVoicesArray(json);
  const rows: ElevenLabsVoiceRow[] = [];
  for (const v of raw) {
    const n = normalizeRow(v);
    if (n) rows.push(n);
  }
  return sortElevenLabsVoicesForUi(rows);
}

export async function getElevenLabsVoiceDetails(
  voiceId: string,
): Promise<ElevenLabsVoiceRow | null> {
  const id = voiceId.trim();
  if (!id) return null;
  const key = process.env.ELEVENLABS_API_KEY?.trim();
  if (!key) return null;
  const url = `https://api.elevenlabs.io/v1/voices/${encodeURIComponent(id)}`;
  const res = await fetch(url, {
    method: "GET",
    headers: {
      "xi-api-key": key,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    signal: abortTimeout(),
  });
  if (!res.ok) return null;
  let json: unknown;
  try {
    json = (await res.json()) as unknown;
  } catch {
    return null;
  }
  return normalizeRow(json as ElevenLabsVoicesApiVoice);
}
