import { describe, expect, it } from "vitest";

import {
  computeThreadDropPlan,
  getThreadLocation,
  parseDragId,
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

describe("computeThreadDropPlan", () => {
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
