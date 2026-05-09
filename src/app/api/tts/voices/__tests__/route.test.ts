import { afterEach, describe, expect, it, vi } from "vitest";

import { GET } from "@/app/api/tts/voices/route";

describe("GET /api/tts/voices (Prompt 9L allowlist)", () => {
  const origFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = origFetch;
    delete process.env.ELEVENLABS_API_KEY;
    delete process.env.ELEVENLABS_DEFAULT_VOICE_ID;
    delete process.env.ELEVENLABS_VOICE_ID;
    delete process.env.ELEVENLABS_VOICE_ALLOWLIST;
    delete process.env.ELEVENLABS_VOICE_ALLOWLIST_JSON;
    vi.restoreAllMocks();
  });

  it("returns 503 when no allowlist and no API key", async () => {
    delete process.env.ELEVENLABS_API_KEY;
    const res = await GET();
    expect(res.status).toBe(503);
    const j = (await res.json()) as { ok: boolean };
    expect(j.ok).toBe(false);
  });

  it("returns 200 env-allowlist without API key (explicit ids)", async () => {
    process.env.ELEVENLABS_VOICE_ALLOWLIST =
      "Paige:pppppppppppp,Clarice:cccccccccccc";
    delete process.env.ELEVENLABS_API_KEY;
    const res = await GET();
    expect(res.status).toBe(200);
    const j = (await res.json()) as {
      ok: boolean;
      source?: string;
      allowlistMode?: string;
      voices: { voice_id: string; name: string }[];
      defaultVoiceId: string | null;
      warnings?: string[];
    };
    expect(j.ok).toBe(true);
    expect(j.source).toBe("env-allowlist");
    expect(j.allowlistMode).toBe("explicit-id");
    expect(j.voices).toHaveLength(2);
    expect(j.defaultVoiceId).toBe("cccccccccccc");
    expect(j.warnings?.some((w) => /catalog disabled/i.test(w))).toBe(true);
  });

  it("returns allowlist on catalog 401 with warning (explicit ids)", async () => {
    process.env.ELEVENLABS_API_KEY = "k";
    process.env.ELEVENLABS_VOICE_ALLOWLIST = "Clarice:cccccccccccc";
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "nope" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const res = await GET();
    expect(res.status).toBe(200);
    const j = (await res.json()) as {
      ok: boolean;
      source: string;
      warnings?: string[];
      voices: unknown[];
    };
    expect(j.ok).toBe(true);
    expect(j.source).toBe("env-allowlist");
    expect(j.voices).toHaveLength(1);
    expect(j.warnings?.some((w) => /catalog unavailable/i.test(w))).toBe(true);
  });

  it("returns mixed when catalog succeeds (explicit allowlist)", async () => {
    process.env.ELEVENLABS_API_KEY = "k";
    process.env.ELEVENLABS_VOICE_ALLOWLIST = "Clarice:cccccccccccc";
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          voices: [
            { voice_id: "cccccccccccc", name: "Clarice Remote", category: "premade" },
          ],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    const res = await GET();
    expect(res.status).toBe(200);
    const j = (await res.json()) as {
      ok: boolean;
      source: string;
      voices: { voice_id: string; name: string; category?: string }[];
    };
    expect(j.ok).toBe(true);
    expect(j.source).toBe("mixed");
    expect(j.voices[0]!.name).toBe("Clarice");
    expect(j.voices[0]!.category).toBe("premade");
  });

  it("returns catalog when no allowlist and key present", async () => {
    process.env.ELEVENLABS_API_KEY = "k";
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          voices: [{ voice_id: "vvvvvvvvvvvv", name: "Clarice" }],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    const res = await GET();
    expect(res.status).toBe(200);
    const j = (await res.json()) as {
      ok: boolean;
      source: string;
      allowlistMode?: string;
      defaultVoiceId: string | null;
      warnings?: string[];
    };
    expect(j.source).toBe("elevenlabs-api");
    expect(j.allowlistMode).toBe("none");
    expect(j.defaultVoiceId).toBe("vvvvvvvvvvvv");
    expect(j.warnings).toEqual([]);
  });

  it("name-only allowlist + catalog returns only resolved voices in order", async () => {
    process.env.ELEVENLABS_API_KEY = "k";
    process.env.ELEVENLABS_VOICE_ALLOWLIST = "Paige,Clarice,Zed";
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          voices: [
            { voice_id: "cccccccccccc", name: "Clarice" },
            { voice_id: "pppppppppppp", name: "Paige" },
            { voice_id: "zzzzzzzzzzzz", name: "Zed" },
            { voice_id: "strangerstran", name: "Nobody" },
          ],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    const res = await GET();
    const j = (await res.json()) as {
      ok: boolean;
      source: string;
      allowlistMode?: string;
      voices: { voice_id: string; name: string }[];
      warnings?: string[];
    };
    expect(res.status).toBe(200);
    expect(j.ok).toBe(true);
    expect(j.source).toBe("env-name-allowlist");
    expect(j.allowlistMode).toBe("name-only");
    expect(j.voices.map((v) => v.voice_id)).toEqual([
      "pppppppppppp",
      "cccccccccccc",
      "zzzzzzzzzzzz",
    ]);
    expect(j.voices.some((v) => v.voice_id === "strangerstran")).toBe(false);
    expect(j.warnings?.length ?? 0).toBe(0);
  });

  it("name-only allowlist + catalog failure returns empty voices, no catalog spill", async () => {
    process.env.ELEVENLABS_API_KEY = "k";
    process.env.ELEVENLABS_VOICE_ALLOWLIST = "Charlotte,Clarice";
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({}), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const res = await GET();
    const j = (await res.json()) as {
      ok: boolean;
      voices: unknown[];
      warnings?: string[];
      source?: string;
    };
    expect(res.status).toBe(200);
    expect(j.ok).toBe(true);
    expect(j.voices).toHaveLength(0);
    expect(j.warnings?.some((w) => /names only/i.test(w) && /voice_id/i.test(w))).toBe(true);
  });
});
