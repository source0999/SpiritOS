import { describe, expect, it, vi, beforeEach } from "vitest";

const mockThreadsUpdate = vi.fn();
const mockThreadsToArray = vi.fn();
const mockMessagesFilter = vi.fn();

vi.mock("@/lib/chat-db", () => ({
  isBrowserChatDbAvailable: () => true,
  db: {
    threads: {
      update: (...a: unknown[]) => mockThreadsUpdate(...a),
      toArray: () => mockThreadsToArray(),
    },
    messages: {
      filter: (fn: (m: { text: string }) => boolean) => ({
        toArray: async () => {
          const all = await mockMessagesFilter();
          return all.filter(fn);
        },
      }),
    },
  },
}));

import { pinThread, searchThreadsAndMessages, unpinThread } from "@/lib/chat-persistence";

describe("chat-persistence pins", () => {
  beforeEach(() => {
    mockThreadsUpdate.mockClear();
  });

  it("pinThread sets pinned true and pinnedAt", async () => {
    await pinThread("abc");
    expect(mockThreadsUpdate).toHaveBeenCalledTimes(1);
    const [id, patch] = mockThreadsUpdate.mock.calls[0]!;
    expect(id).toBe("abc");
    expect(patch).toMatchObject({ pinned: true });
    expect(typeof (patch as { pinnedAt: number }).pinnedAt).toBe("number");
  });

  it("unpinThread clears pinned", async () => {
    await unpinThread("abc");
    expect(mockThreadsUpdate).toHaveBeenCalledWith(
      "abc",
      expect.objectContaining({ pinned: false, pinnedAt: undefined }),
    );
  });
});

describe("searchThreadsAndMessages", () => {
  beforeEach(() => {
    mockThreadsToArray.mockReset();
    mockMessagesFilter.mockReset();
  });

  it("returns [] for empty query", async () => {
    expect(await searchThreadsAndMessages("   ")).toEqual([]);
  });

  it("matches title case-insensitively", async () => {
    mockThreadsToArray.mockResolvedValue([
      {
        id: "t1",
        title: "Hello WORLD",
        createdAt: 1,
        updatedAt: 10,
        archived: false,
      },
    ]);
    mockMessagesFilter.mockResolvedValue([]);
    const hits = await searchThreadsAndMessages("world");
    expect(hits).toHaveLength(1);
    expect(hits[0]!.thread.id).toBe("t1");
  });

  it("matches message text with snippet", async () => {
    mockThreadsToArray.mockResolvedValue([
      {
        id: "t1",
        title: "Other",
        createdAt: 1,
        updatedAt: 10,
        archived: false,
      },
    ]);
    mockMessagesFilter.mockResolvedValue([
      { threadId: "t1", text: "The quick brown Fox jumps", role: "user" },
    ]);
    const hits = await searchThreadsAndMessages("fox");
    expect(hits).toHaveLength(1);
    expect(hits[0]!.thread.id).toBe("t1");
    expect(hits[0]!.snippet?.toLowerCase()).toContain("fox");
  });

  it("returns empty when nothing matches", async () => {
    mockThreadsToArray.mockResolvedValue([
      {
        id: "t1",
        title: "Zed",
        createdAt: 1,
        updatedAt: 2,
        archived: false,
      },
    ]);
    mockMessagesFilter.mockResolvedValue([]);
    expect(await searchThreadsAndMessages("nope")).toEqual([]);
  });
});
