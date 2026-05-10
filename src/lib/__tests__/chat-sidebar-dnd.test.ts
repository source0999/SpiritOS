import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import {
  computeFolderReorderPlan,
  computeThreadDropPlan,
  fallbackNearestExcludingActive,
  getThreadLocation,
  parseDragId,
  pickThreadCollisionByVerticalMidpoints,
  resetThreadCollisionSticky,
  applyThreadOverHysteresis,
  shouldEnableChatThreadSidebarDnd,
  THREAD_DND_PREFIX,
} from "@/lib/chat-sidebar-dnd";
import type { FolderSidebarSection } from "@/lib/chat-folder-utils";
import type { ChatFolder, ChatThread } from "@/lib/chat-db.types";

function folder(id: string, order = 0, collapsed = false): ChatFolder {
  return {
    id,
    name: id,
    createdAt: 1,
    updatedAt: 1,
    order,
    collapsed,
  };
}

function thread(
  id: string,
  p: Partial<ChatThread> & { folderId?: string | null } = {},
): ChatThread {
  return {
    id,
    title: id,
    createdAt: 1,
    updatedAt: 2,
    ...p,
  };
}

describe("parseDragId", () => {
  it("parses thread ids", () => {
    expect(parseDragId(`${THREAD_DND_PREFIX}a`)).toEqual({
      kind: "thread",
      threadId: "a",
    });
  });
  it("parses root folder drop", () => {
    expect(parseDragId("folder:root")).toEqual({
      kind: "folder",
      folderId: null,
    });
  });
  it("parses nested folder drop", () => {
    expect(parseDragId("folder:f1")).toEqual({
      kind: "folder",
      folderId: "f1",
    });
  });
  it("does not treat folder-sort: as folder: (prefix collision)", () => {
    expect(parseDragId("folder-sort:f1")).toEqual({ kind: "unknown" });
  });
});

describe("getThreadLocation", () => {
  it("finds root", () => {
    const root = [thread("a")];
    const sections: FolderSidebarSection[] = [];
    expect(getThreadLocation("a", root, sections)).toEqual({ bucket: "root" });
  });
  it("finds folder bucket", () => {
    const root: ChatThread[] = [];
    const sections: FolderSidebarSection[] = [
      { folder: folder("f1"), threads: [thread("x")] },
    ];
    expect(getThreadLocation("x", root, sections)).toEqual({
      bucket: "folder",
      folderId: "f1",
    });
  });
});

describe("computeFolderReorderPlan", () => {
  it("moves folder when over id is folder-sort", () => {
    const folderSections: FolderSidebarSection[] = [
      { folder: folder("a"), threads: [] },
      { folder: folder("b"), threads: [] },
      { folder: folder("c"), threads: [] },
    ];
    expect(
      computeFolderReorderPlan({
        activeFolderId: "c",
        overId: "folder-sort:a",
        folderSections,
      }),
    ).toEqual(["c", "a", "b"]);
  });

  it("accepts thread-drop folder id as over target", () => {
    const folderSections: FolderSidebarSection[] = [
      { folder: folder("a"), threads: [] },
      { folder: folder("b"), threads: [] },
    ];
    expect(
      computeFolderReorderPlan({
        activeFolderId: "a",
        overId: "folder:b",
        folderSections,
      }),
    ).toEqual(["b", "a"]);
  });

  it("returns null when over is unrelated", () => {
    expect(
      computeFolderReorderPlan({
        activeFolderId: "a",
        overId: `${THREAD_DND_PREFIX}x`,
        folderSections: [{ folder: folder("a"), threads: [] }],
      }),
    ).toBeNull();
  });
});

describe("computeThreadDropPlan", () => {
  it("same bucket root: drag B over C -> [A,C,B,D]", () => {
    const rootThreads = [thread("A"), thread("B"), thread("C"), thread("D")];
    const ops = computeThreadDropPlan({
      activeThreadId: "B",
      overId: `${THREAD_DND_PREFIX}C`,
      rootThreads,
      folderSections: [],
    });
    expect(ops).toEqual([{ folderId: null, orderedIds: ["A", "C", "B", "D"] }]);
  });

  it("same bucket root: drag B over D -> [A,C,D,B]", () => {
    const rootThreads = [thread("A"), thread("B"), thread("C"), thread("D")];
    const ops = computeThreadDropPlan({
      activeThreadId: "B",
      overId: `${THREAD_DND_PREFIX}D`,
      rootThreads,
      folderSections: [],
    });
    expect(ops).toEqual([{ folderId: null, orderedIds: ["A", "C", "D", "B"] }]);
  });

  it("same bucket root: drag C over B -> [A,C,B,D]", () => {
    const rootThreads = [thread("A"), thread("B"), thread("C"), thread("D")];
    const ops = computeThreadDropPlan({
      activeThreadId: "C",
      overId: `${THREAD_DND_PREFIX}B`,
      rootThreads,
      folderSections: [],
    });
    expect(ops).toEqual([{ folderId: null, orderedIds: ["A", "C", "B", "D"] }]);
  });

  it("same bucket folder: drag down by one within folder list", () => {
    const rootThreads: ChatThread[] = [];
    const folderSections: FolderSidebarSection[] = [
      {
        folder: folder("f1"),
        threads: [thread("a"), thread("b"), thread("c"), thread("d")],
      },
    ];
    const ops = computeThreadDropPlan({
      activeThreadId: "b",
      overId: `${THREAD_DND_PREFIX}c`,
      rootThreads,
      folderSections,
    });
    expect(ops).toEqual([{ folderId: "f1", orderedIds: ["a", "c", "b", "d"] }]);
  });

  it("moves thread from root into empty folder (append)", () => {
    const rootThreads = [thread("a", { folderId: null })];
    const folderSections: FolderSidebarSection[] = [
      { folder: folder("f1"), threads: [] },
    ];
    const ops = computeThreadDropPlan({
      activeThreadId: "a",
      overId: "folder:f1",
      rootThreads,
      folderSections,
    });
    expect(ops).toEqual([
      { folderId: null, orderedIds: [] },
      { folderId: "f1", orderedIds: ["a"] },
    ]);
  });

  it("moves thread from folder to root", () => {
    const rootThreads: ChatThread[] = [];
    const folderSections: FolderSidebarSection[] = [
      { folder: folder("f1"), threads: [thread("a")] },
    ];
    const ops = computeThreadDropPlan({
      activeThreadId: "a",
      overId: "folder:root",
      rootThreads,
      folderSections,
    });
    expect(ops).toEqual([
      { folderId: "f1", orderedIds: [] },
      { folderId: null, orderedIds: ["a"] },
    ]);
  });

  it("uses caller-supplied root order when pinned rows precede unpinned visually but not by Dexie order", () => {
    const P = thread("p", { pinned: true, order: 3000 });
    const U1 = thread("u1", { pinned: false, order: 1000 });
    const U2 = thread("u2", { pinned: false, order: 2000 });
    const visualRoot = [P, U1, U2];
    const ops = computeThreadDropPlan({
      activeThreadId: "u2",
      overId: `${THREAD_DND_PREFIX}u1`,
      rootThreads: visualRoot,
      folderSections: [],
    });
    expect(ops).toEqual([
      { folderId: null, orderedIds: ["p", "u2", "u1"] },
    ]);
  });

  it("moves thread from folder onto root thread (insert before)", () => {
    const rootThreads = [thread("b")];
    const folderSections: FolderSidebarSection[] = [
      { folder: folder("f1"), threads: [thread("a")] },
    ];
    const ops = computeThreadDropPlan({
      activeThreadId: "a",
      overId: `${THREAD_DND_PREFIX}b`,
      rootThreads,
      folderSections,
    });
    expect(ops).toEqual([
      { folderId: "f1", orderedIds: [] },
      { folderId: null, orderedIds: ["a", "b"] },
    ]);
  });

  it("moves thread between folders", () => {
    const rootThreads: ChatThread[] = [];
    const folderSections: FolderSidebarSection[] = [
      { folder: folder("f1"), threads: [thread("a")] },
      { folder: folder("f2"), threads: [thread("b")] },
    ];
    const ops = computeThreadDropPlan({
      activeThreadId: "a",
      overId: `${THREAD_DND_PREFIX}b`,
      rootThreads,
      folderSections,
    });
    expect(ops).toEqual([
      { folderId: "f1", orderedIds: [] },
      { folderId: "f2", orderedIds: ["a", "b"] },
    ]);
  });

  it("reorders within same folder", () => {
    const rootThreads: ChatThread[] = [];
    const folderSections: FolderSidebarSection[] = [
      {
        folder: folder("f1"),
        threads: [thread("a"), thread("b"), thread("c")],
      },
    ];
    const ops = computeThreadDropPlan({
      activeThreadId: "c",
      overId: `${THREAD_DND_PREFIX}a`,
      rootThreads,
      folderSections,
    });
    expect(ops).toEqual([{ folderId: "f1", orderedIds: ["c", "a", "b"] }]);
  });

  it("reorders root list", () => {
    const rootThreads = [thread("a"), thread("b"), thread("c")];
    const ops = computeThreadDropPlan({
      activeThreadId: "c",
      overId: `${THREAD_DND_PREFIX}a`,
      rootThreads,
      folderSections: [],
    });
    expect(ops).toEqual([{ folderId: null, orderedIds: ["c", "a", "b"] }]);
  });

  it("root folder drop target appends within root bucket", () => {
    const rootThreads = [thread("a"), thread("b"), thread("c")];
    const ops = computeThreadDropPlan({
      activeThreadId: "b",
      overId: "folder:root",
      rootThreads,
      folderSections: [],
    });
    expect(ops).toEqual([{ folderId: null, orderedIds: ["a", "c", "b"] }]);
  });

  it("returns null when dropping onto self", () => {
    const rootThreads = [thread("a")];
    expect(
      computeThreadDropPlan({
        activeThreadId: "a",
        overId: `${THREAD_DND_PREFIX}a`,
        rootThreads,
        folderSections: [],
      }),
    ).toBeNull();
  });
});

describe("pickThreadCollisionByVerticalMidpoints", () => {
  function rectsMap(
    entries: { id: string; top: number; height: number }[],
  ): Map<string, DOMRect> {
    const m = new Map<string, DOMRect>();
    for (const e of entries) {
      const left = 0;
      const width = 10;
      const top = e.top;
      const height = e.height;
      m.set(
        e.id,
        {
          top,
          left,
          width,
          height,
          x: left,
          y: top,
          right: left + width,
          bottom: top + height,
          toJSON: () => ({}),
        } as DOMRect,
      );
    }
    return m;
  }

  it("partitions two overlapping rows by Y midpoint (no horizontal jitter flips)", () => {
    const a = `${THREAD_DND_PREFIX}a`;
    const b = `${THREAD_DND_PREFIX}b`;
    const rects = rectsMap([
      { id: a, top: 0, height: 40 },
      { id: b, top: 20, height: 40 },
    ]);
    expect(
      pickThreadCollisionByVerticalMidpoints([{ id: a }, { id: b }], 29, rects).id,
    ).toBe(a);
    expect(
      pickThreadCollisionByVerticalMidpoints([{ id: a }, { id: b }], 30, rects).id,
    ).toBe(b);
  });

  it("returns the only hit unchanged", () => {
    const a = `${THREAD_DND_PREFIX}a`;
    const rects = rectsMap([{ id: a, top: 0, height: 20 }]);
    expect(pickThreadCollisionByVerticalMidpoints([{ id: a }], 5, rects).id).toBe(a);
  });
});

describe("applyThreadOverHysteresis", () => {
  beforeEach(() => {
    resetThreadCollisionSticky();
  });

  it("after midpoint pick flips, hysteresis follows once pointer crosses inter-row boundary", () => {
    const a = `${THREAD_DND_PREFIX}a`;
    const b = `${THREAD_DND_PREFIX}b`;
    const rects = new Map<string, DOMRect>([
      [
        a,
        {
          top: 0,
          left: 0,
          width: 10,
          height: 40,
          x: 0,
          y: 0,
          right: 10,
          bottom: 40,
          toJSON: () => ({}),
        } as DOMRect,
      ],
      [
        b,
        {
          top: 30,
          left: 0,
          width: 10,
          height: 40,
          x: 0,
          y: 30,
          right: 10,
          bottom: 70,
          toJSON: () => ({}),
        } as DOMRect,
      ],
    ]);
    const hits = [{ id: a }, { id: b }];
    const yStart = 34;
    const first = pickThreadCollisionByVerticalMidpoints(hits, yStart, rects);
    expect(String(first.id)).toBe(a);
    applyThreadOverHysteresis(first, hits, yStart, rects, "thread:drag");
    const yMid = 36;
    const secondPick = pickThreadCollisionByVerticalMidpoints(hits, yMid, rects);
    expect(String(secondPick.id)).toBe(b);
    const afterBoundary = applyThreadOverHysteresis(secondPick, hits, yMid, rects, "thread:drag");
    expect(String(afterBoundary.id)).toBe(b);
    const yDeep = 46;
    const deepPick = pickThreadCollisionByVerticalMidpoints(hits, yDeep, rects);
    const moved = applyThreadOverHysteresis(deepPick, hits, yDeep, rects, "thread:drag");
    expect(String(moved.id)).toBe(b);
  });
});

describe("shouldEnableChatThreadSidebarDnd", () => {
  const base = {
    hasCommitHandler: true,
    railLocked: false,
  } as const;

  it("enables on desktop lg regardless of drawer flag", () => {
    expect(
      shouldEnableChatThreadSidebarDnd({
        ...base,
        lgDesktop: true,
        layoutVariant: "default",
        mobileDndEnabled: false,
      }),
    ).toBe(true);
  });

  it("disables mobile rail when not lg and not drawer DnD", () => {
    expect(
      shouldEnableChatThreadSidebarDnd({
        ...base,
        lgDesktop: false,
        layoutVariant: "default",
        mobileDndEnabled: false,
      }),
    ).toBe(false);
  });

  it("enables mobile drawer when mobileDndEnabled", () => {
    expect(
      shouldEnableChatThreadSidebarDnd({
        ...base,
        lgDesktop: false,
        layoutVariant: "drawer",
        mobileDndEnabled: true,
      }),
    ).toBe(true);
  });

  it("disables drawer DnD when mobileDndEnabled is false", () => {
    expect(
      shouldEnableChatThreadSidebarDnd({
        ...base,
        lgDesktop: false,
        layoutVariant: "drawer",
        mobileDndEnabled: false,
      }),
    ).toBe(false);
  });

  it("disables when rail locked or no commit handler", () => {
    expect(
      shouldEnableChatThreadSidebarDnd({
        hasCommitHandler: false,
        railLocked: false,
        lgDesktop: true,
        layoutVariant: "drawer",
        mobileDndEnabled: true,
      }),
    ).toBe(false);
    expect(
      shouldEnableChatThreadSidebarDnd({
        hasCommitHandler: true,
        railLocked: true,
        lgDesktop: true,
        layoutVariant: "default",
        mobileDndEnabled: true,
      }),
    ).toBe(false);
  });
});

describe("fallbackNearestExcludingActive", () => {
  it("returns closest non-active droppable by rect-center distance", () => {
    const idA = `${THREAD_DND_PREFIX}row-a`;
    const idB = `${THREAD_DND_PREFIX}row-b`;
    const args = {
      pointerCoordinates: { x: 50, y: 70 },
      droppableContainers: [{ id: idA }, { id: idB }],
      droppableRects: new Map([
        [idA, { top: 0, left: 0, width: 200, height: 44 } as DOMRect],
        [idB, { top: 48, left: 0, width: 200, height: 44 } as DOMRect],
      ]),
    };
    expect(
      fallbackNearestExcludingActive(
        args as unknown as Parameters<typeof fallbackNearestExcludingActive>[0],
        idA,
      ),
    ).toEqual([{ id: idB }]);
  });
});

describe("chat sidebar DnD components (no debug ingest telemetry)", () => {
  const paths = [
    "src/components/chat/ChatSidebarDndProvider.tsx",
    "src/components/chat/SortableChatThreadItem.tsx",
    "src/components/chat/ChatThreadSidebar.tsx",
    "src/lib/chat-sidebar-dnd.ts",
  ] as const;

  it.each(paths)("%s has no localhost ingest fetch or agentDebugLog", (rel) => {
    const src = readFileSync(resolve(process.cwd(), rel), "utf8");
    expect(src).not.toMatch(/localhost:7644|\/ingest\//);
    expect(src).not.toMatch(/agentDebugLog/);
  });
});
