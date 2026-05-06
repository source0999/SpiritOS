import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { OracleMemoryEvent } from "@/lib/chat-db.types";

// ── db mock - defined with vi.hoisted so it exists before vi.mock hoisting ──────
const { mockTable, mockEvents } = vi.hoisted(() => {
  const mockEvents: OracleMemoryEvent[] = [];
  const mockTable = {
    add: vi.fn(async (e: OracleMemoryEvent) => {
      mockEvents.push(e);
      return e.id;
    }),
    orderBy: vi.fn().mockReturnThis(),
    reverse: vi.fn().mockReturnThis(),
    limit: vi.fn().mockReturnThis(),
    toArray: vi.fn(async () => [...mockEvents].reverse()),
    clear: vi.fn(async () => {
      mockEvents.length = 0;
    }),
  };
  return { mockTable, mockEvents };
});

vi.mock("@/lib/chat-db", () => ({
  db: { oracleMemoryEvents: mockTable },
}));

import {
  appendOracleMemoryEvent,
  clearOracleMemoryEvents,
  getRecentOracleMemoryEvents,
  isOracleMemoryEnabled,
  summarizeOracleMemoryForPrompt,
} from "@/lib/oracle/oracle-memory";

describe("isOracleMemoryEnabled", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("returns false by default (env unset)", () => {
    vi.stubEnv("NEXT_PUBLIC_SPIRIT_ENABLE_ORACLE_MEMORY", "");
    expect(isOracleMemoryEnabled()).toBe(false);
  });

  it("returns true when env is exactly 'true'", () => {
    vi.stubEnv("NEXT_PUBLIC_SPIRIT_ENABLE_ORACLE_MEMORY", "true");
    expect(isOracleMemoryEnabled()).toBe(true);
  });

  it("returns false for '1', 'yes', or 'TRUE'", () => {
    for (const v of ["1", "yes", "TRUE"]) {
      vi.stubEnv("NEXT_PUBLIC_SPIRIT_ENABLE_ORACLE_MEMORY", v);
      expect(isOracleMemoryEnabled(), `value: ${v}`).toBe(false);
    }
  });
});

describe("summarizeOracleMemoryForPrompt", () => {
  it("returns null for empty event array", () => {
    expect(summarizeOracleMemoryForPrompt([])).toBeNull();
  });

  it("returns [ORACLE MEMORY CONTEXT] block for one event", () => {
    const events: OracleMemoryEvent[] = [
      { id: "1", createdAt: 1000, summary: "Asked about Python generators" },
    ];
    const result = summarizeOracleMemoryForPrompt(events);
    expect(result).not.toBeNull();
    expect(result).toContain("[ORACLE MEMORY CONTEXT]");
    expect(result).toContain("Asked about Python generators");
    expect(result).toContain("1.");
  });

  it("numbers each event in order", () => {
    const events: OracleMemoryEvent[] = [
      { id: "1", createdAt: 1000, summary: "First topic" },
      { id: "2", createdAt: 2000, summary: "Second topic" },
    ];
    const result = summarizeOracleMemoryForPrompt(events)!;
    expect(result.indexOf("1. First topic")).toBeLessThan(result.indexOf("2. Second topic"));
  });

  it("includes the background-only usage note", () => {
    const events: OracleMemoryEvent[] = [{ id: "1", createdAt: 1000, summary: "Test" }];
    const result = summarizeOracleMemoryForPrompt(events)!;
    expect(result).toMatch(/lightweight background context/i);
  });

  it("appends surface/source metadata when present", () => {
    const events: OracleMemoryEvent[] = [
      {
        id: "1",
        createdAt: 1000,
        summary: "Asked about generators",
        runtimeSurface: "oracle",
        source: "oracle-voice-surface",
      },
    ];
    const result = summarizeOracleMemoryForPrompt(events)!;
    expect(result).toContain("1. Asked about generators (surface=oracle, source=oracle-voice-surface)");
  });

  it("truncates result at 3000 chars", () => {
    const longSummary = "x".repeat(200);
    const events: OracleMemoryEvent[] = Array.from({ length: 20 }, (_, i) => ({
      id: String(i),
      createdAt: i * 1000,
      summary: longSummary,
    }));
    const result = summarizeOracleMemoryForPrompt(events)!;
    expect(result.length).toBeLessThanOrEqual(3000);
  });
});

describe("appendOracleMemoryEvent", () => {
  beforeEach(() => {
    mockEvents.length = 0;
    vi.clearAllMocks();
    vi.stubEnv("NEXT_PUBLIC_SPIRIT_ENABLE_ORACLE_MEMORY", "true");
  });
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("no-ops when oracle memory is disabled", async () => {
    vi.stubEnv("NEXT_PUBLIC_SPIRIT_ENABLE_ORACLE_MEMORY", "false");
    await appendOracleMemoryEvent({ summary: "test" });
    expect(mockTable.add).not.toHaveBeenCalled();
  });

  it("calls db.oracleMemoryEvents.add when enabled", async () => {
    await appendOracleMemoryEvent({ summary: "hello" });
    expect(mockTable.add).toHaveBeenCalledOnce();
    const added = mockTable.add.mock.calls[0]?.[0] as OracleMemoryEvent;
    expect(added.summary).toBe("hello");
    expect(typeof added.id).toBe("string");
    expect(typeof added.createdAt).toBe("number");
  });

  it("passes through optional fields", async () => {
    await appendOracleMemoryEvent({
      summary: "test",
      userText: "what is recursion",
      assistantText: "A function calling itself",
      modelProfileId: "teacher",
      source: "oracle-voice-surface",
      runtimeSurface: "oracle",
    });
    const added = mockTable.add.mock.calls[0]?.[0] as OracleMemoryEvent;
    expect(added.userText).toBe("what is recursion");
    expect(added.assistantText).toBe("A function calling itself");
    expect(added.modelProfileId).toBe("teacher");
    expect(added.source).toBe("oracle-voice-surface");
    expect(added.runtimeSurface).toBe("oracle");
  });
});

describe("getRecentOracleMemoryEvents", () => {
  beforeEach(() => {
    mockEvents.length = 0;
    vi.clearAllMocks();
  });
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("returns [] when disabled", async () => {
    vi.stubEnv("NEXT_PUBLIC_SPIRIT_ENABLE_ORACLE_MEMORY", "false");
    const result = await getRecentOracleMemoryEvents();
    expect(result).toEqual([]);
    expect(mockTable.orderBy).not.toHaveBeenCalled();
  });

  it("calls orderBy('createdAt').reverse().limit(12) by default when enabled", async () => {
    vi.stubEnv("NEXT_PUBLIC_SPIRIT_ENABLE_ORACLE_MEMORY", "true");
    await getRecentOracleMemoryEvents();
    expect(mockTable.orderBy).toHaveBeenCalledWith("createdAt");
    expect(mockTable.reverse).toHaveBeenCalled();
    expect(mockTable.limit).toHaveBeenCalledWith(12);
  });

  it("respects custom limit argument", async () => {
    vi.stubEnv("NEXT_PUBLIC_SPIRIT_ENABLE_ORACLE_MEMORY", "true");
    await getRecentOracleMemoryEvents(5);
    expect(mockTable.limit).toHaveBeenCalledWith(5);
  });
});

describe("clearOracleMemoryEvents", () => {
  beforeEach(() => {
    mockEvents.length = 0;
    vi.clearAllMocks();
  });
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("calls db.oracleMemoryEvents.clear() regardless of flag", async () => {
    vi.stubEnv("NEXT_PUBLIC_SPIRIT_ENABLE_ORACLE_MEMORY", "false");
    await clearOracleMemoryEvents();
    expect(mockTable.clear).toHaveBeenCalledOnce();
  });
});

describe("Dexie v5 schema: OracleMemoryEvent type contract", () => {
  it("OracleMemoryEvent type has required fields", () => {
    const event: OracleMemoryEvent = {
      id: "test-id",
      createdAt: Date.now(),
      summary: "test summary",
    };
    expect(event.id).toBe("test-id");
    expect(event.userText).toBeUndefined();
    expect(event.assistantText).toBeUndefined();
    expect(event.modelProfileId).toBeUndefined();
    expect(event.source).toBeUndefined();
    expect(event.runtimeSurface).toBeUndefined();
  });

  it("OracleMemoryEvent accepts optional fields", () => {
    const event: OracleMemoryEvent = {
      id: "x",
      createdAt: 0,
      summary: "s",
      userText: "u",
      assistantText: "a",
      modelProfileId: "normal-peer",
      source: "oracle-voice-surface",
      runtimeSurface: "oracle",
    };
    expect(event.userText).toBe("u");
    expect(event.modelProfileId).toBe("normal-peer");
    expect(event.source).toBe("oracle-voice-surface");
    expect(event.runtimeSurface).toBe("oracle");
  });
});
