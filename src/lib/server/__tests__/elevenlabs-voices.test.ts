import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ElevenLabsVoicesFetchError,
  enrichAllowlistWithCatalog,
  fetchElevenLabsVoicesNormalized,
  parseElevenLabsVoiceAllowlistFromEnv,
  pickDefaultElevenLabsVoice,
  resolveElevenLabsVoiceAllowlist,
  sortElevenLabsVoicesForUi,
  type ElevenLabsVoiceRow,
} from "@/lib/server/elevenlabs-voices";

const origFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = origFetch;
  delete process.env.ELEVENLABS_API_KEY;
  delete process.env.ELEVENLABS_DEFAULT_VOICE_ID;
  delete process.env.ELEVENLABS_DEFAULT_VOICE_NAME;
  delete process.env.ELEVENLABS_VOICE_ID;
  delete process.env.ELEVENLABS_VOICE_ALLOWLIST;
  delete process.env.ELEVENLABS_VOICE_ALLOWLIST_JSON;
  vi.restoreAllMocks();
});

describe("sortElevenLabsVoicesForUi", () => {
  it("bubbles Clarice first then sorts A–Z", () => {
    const rows: ElevenLabsVoiceRow[] = [
      { voice_id: "b", name: "Beta" },
      { voice_id: "c", name: "Clarice" },
      { voice_id: "a", name: "Alpha" },
    ];
    const s = sortElevenLabsVoicesForUi(rows);
    expect(s[0]!.name).toBe("Clarice");
    expect(s.map((r) => r.name)).toEqual(["Clarice", "Alpha", "Beta"]);
  });
});

describe("pickDefaultElevenLabsVoice", () => {
  const rows: ElevenLabsVoiceRow[] = [
    { voice_id: "x1", name: "Zed" },
    { voice_id: "cl", name: "Clarice" },
  ];

  it("prefers ELEVENLABS_DEFAULT_VOICE_ID when set", () => {
    process.env.ELEVENLABS_DEFAULT_VOICE_ID = "x1";
    const r = pickDefaultElevenLabsVoice(sortElevenLabsVoicesForUi(rows));
    expect(r.defaultVoiceId).toBe("x1");
    expect(r.defaultVoiceName).toBe("Zed");
  });

  it("falls back to Clarice by name", () => {
    const r = pickDefaultElevenLabsVoice(sortElevenLabsVoicesForUi(rows));
    expect(r.defaultVoiceId).toBe("cl");
    expect(r.defaultVoiceName).toBe("Clarice");
  });

  it("uses ELEVENLABS_VOICE_ID when Clarice missing", () => {
    process.env.ELEVENLABS_VOICE_ID = "x1";
    const onlyZed: ElevenLabsVoiceRow[] = [{ voice_id: "x1", name: "Zed" }];
    const r = pickDefaultElevenLabsVoice(sortElevenLabsVoicesForUi(onlyZed));
    expect(r.defaultVoiceId).toBe("x1");
  });

  it("warns when default env id is absent from non-empty catalog", () => {
    process.env.ELEVENLABS_DEFAULT_VOICE_ID = "ghost";
    process.env.ELEVENLABS_DEFAULT_VOICE_NAME = "Ghost label";
    const r = pickDefaultElevenLabsVoice(sortElevenLabsVoicesForUi(rows));
    expect(r.warning).toBe("default_voice_id_not_in_catalog");
    expect(r.defaultVoiceId).toBe("ghost");
    expect(r.defaultVoiceName).toBe("Ghost label");
  });

  it("uses env name when catalog empty but default id configured", () => {
    process.env.ELEVENLABS_DEFAULT_VOICE_ID = "only-env";
    process.env.ELEVENLABS_DEFAULT_VOICE_NAME = "Solo";
    const r = pickDefaultElevenLabsVoice([]);
    expect(r.defaultVoiceId).toBe("only-env");
    expect(r.defaultVoiceName).toBe("Solo");
  });
});

describe("fetchElevenLabsVoicesNormalized", () => {
  it("normalizes data.voices when present", async () => {
    process.env.ELEVENLABS_API_KEY = "k";
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          data: { voices: [{ voice_id: "z1", name: "Zora" }] },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    const rows = await fetchElevenLabsVoicesNormalized();
    expect(rows).toHaveLength(1);
    expect(rows[0]!.voice_id).toBe("z1");
  });

  it("throws ElevenLabsVoicesFetchError on 401", async () => {
    process.env.ELEVENLABS_API_KEY = "k";
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({}), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await expect(fetchElevenLabsVoicesNormalized()).rejects.toBeInstanceOf(
      ElevenLabsVoicesFetchError,
    );
  });
});

describe("parseElevenLabsVoiceAllowlistFromEnv", () => {
  afterEach(() => {
    delete process.env.ELEVENLABS_VOICE_ALLOWLIST;
    delete process.env.ELEVENLABS_VOICE_ALLOWLIST_JSON;
  });

  it("parses explicit Name:voice_id pairs (id must look like ElevenLabs id)", () => {
    process.env.ELEVENLABS_VOICE_ALLOWLIST =
      "Minerva Nightshade:midmidmidmidmid,Paige:pppppppppppp,Charlotte – Warm:charcharcharch";
    const p = parseElevenLabsVoiceAllowlistFromEnv();
    expect(p.allowlistMode).toBe("explicit-id");
    expect(p.explicitVoices).toHaveLength(3);
    expect(p.explicitVoices[0]!.name).toBe("Minerva Nightshade");
    expect(p.explicitVoices[0]!.voice_id).toBe("midmidmidmidmid");
    expect(p.nameOnly).toHaveLength(0);
  });

  it("parses name-only comma list", () => {
    process.env.ELEVENLABS_VOICE_ALLOWLIST = "Charlotte,Clarice,Minerva Nightshade,Paige";
    const p = parseElevenLabsVoiceAllowlistFromEnv();
    expect(p.allowlistMode).toBe("name-only");
    expect(p.nameOnly).toEqual(["Charlotte", "Clarice", "Minerva Nightshade", "Paige"]);
    expect(p.explicitVoices).toHaveLength(0);
    expect(p.orderedSegments).toHaveLength(4);
  });

  it("prefers JSON when both env vars are set", () => {
    process.env.ELEVENLABS_VOICE_ALLOWLIST = "Wrong:bbbbbbbbbbbb";
    process.env.ELEVENLABS_VOICE_ALLOWLIST_JSON = JSON.stringify([
      { name: "Clarice", voice_id: "goodvoiceid12" },
    ]);
    const p = parseElevenLabsVoiceAllowlistFromEnv();
    expect(p.allowlistMode).toBe("json");
    expect(p.explicitVoices).toEqual([{ voice_id: "goodvoiceid12", name: "Clarice" }]);
  });

  it("treats only-invalid comma env as no allowlist", () => {
    process.env.ELEVENLABS_VOICE_ALLOWLIST = "alsobad:";
    const p = parseElevenLabsVoiceAllowlistFromEnv();
    expect(p.hasAllowlist).toBe(false);
    expect(p.invalidEntries.length).toBeGreaterThan(0);
  });

  it("returns empty allowlist on malformed JSON", () => {
    process.env.ELEVENLABS_VOICE_ALLOWLIST_JSON = "{";
    const p = parseElevenLabsVoiceAllowlistFromEnv();
    expect(p.hasAllowlist).toBe(false);
    expect(p.allowlistMode).toBe("none");
  });
});

describe("resolveElevenLabsVoiceAllowlist", () => {
  afterEach(() => {
    delete process.env.ELEVENLABS_VOICE_ALLOWLIST;
  });

  it("matches name-only entries case-insensitively and preserves order", () => {
    process.env.ELEVENLABS_VOICE_ALLOWLIST = "paige,charlotte";
    const parsed = parseElevenLabsVoiceAllowlistFromEnv();
    const cat: ElevenLabsVoiceRow[] = [
      { voice_id: "cidcidcidcid", name: "Charlotte" },
      { voice_id: "pidpidpidpid", name: "Paige" },
    ];
    const r = resolveElevenLabsVoiceAllowlist({ parsed, catalog: cat });
    expect(r.voices.map((v) => v.voice_id)).toEqual(["pidpidpidpid", "cidcidcidcid"]);
    expect(r.voices[0]!.name).toBe("paige");
  });

  it("does not append unrelated catalog voices", () => {
    process.env.ELEVENLABS_VOICE_ALLOWLIST = "Clarice:claricevoice1";
    const parsed = parseElevenLabsVoiceAllowlistFromEnv();
    const cat: ElevenLabsVoiceRow[] = [
      { voice_id: "claricevoice1", name: "Clarice" },
      { voice_id: "otherotherot", name: "Stranger" },
    ];
    const r = resolveElevenLabsVoiceAllowlist({ parsed, catalog: cat });
    expect(r.voices).toHaveLength(1);
    expect(r.voices[0]!.voice_id).toBe("claricevoice1");
  });

  it("reports missing names", () => {
    process.env.ELEVENLABS_VOICE_ALLOWLIST = "GhostName";
    const parsed = parseElevenLabsVoiceAllowlistFromEnv();
    const r = resolveElevenLabsVoiceAllowlist({ parsed, catalog: [] });
    expect(r.voices).toHaveLength(0);
    expect(r.missingNames).toEqual(["GhostName"]);
    expect(r.warnings.some((w) => /could not be resolved/i.test(w))).toBe(true);
  });
});

describe("enrichAllowlistWithCatalog", () => {
  it("merges category from catalog by voice_id", () => {
    const allow = [{ voice_id: "a", name: "Local" }];
    const cat = [{ voice_id: "a", name: "Remote", category: "premade" }];
    const out = enrichAllowlistWithCatalog(allow, cat);
    expect(out[0]!.name).toBe("Local");
    expect(out[0]!.category).toBe("premade");
  });
});
