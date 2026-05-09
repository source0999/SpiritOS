import { describe, expect, it } from "vitest";

import {
  buildFolderSidebarModel,
  buildMoveSelectModel,
  buildMoveTargetsForThread,
  isDuplicateFolderName,
  normalizeFolderName,
  sortFoldersByOrderThenUpdated,
  sortThreadsWithOrderFallback,
} from "@/lib/chat-folder-utils";
import type { ChatFolder, ChatThread } from "@/lib/chat-db.types";

function folder(p: Partial<ChatFolder> & Pick<ChatFolder, "id">): ChatFolder {
  return {
    name: "F",
    createdAt: 1,
    updatedAt: 1,
    order: 0,
    collapsed: false,
    ...p,
  };
}

function thread(p: Partial<ChatThread> & Pick<ChatThread, "id">): ChatThread {
  return {
    title: "T",
    createdAt: 1,
    updatedAt: 2,
    ...p,
  };
}

describe("chat-folder-utils", () => {
  it("normalizeFolderName trims and lowercases", () => {
    expect(normalizeFolderName("  Test  ")).toBe("test");
    expect(normalizeFolderName("")).toBe("");
  });

  it("isDuplicateFolderName is case-insensitive and ignores folder by id", () => {
    const folders = [folder({ id: "a", name: "Work" }), folder({ id: "b", name: "play" })];
    expect(isDuplicateFolderName("work", folders)).toBe(true);
    expect(isDuplicateFolderName("WORK ", folders)).toBe(true);
    expect(isDuplicateFolderName("work", folders, "a")).toBe(false);
    expect(isDuplicateFolderName("Work", folders, "a")).toBe(false);
    expect(isDuplicateFolderName("new", folders)).toBe(false);
    expect(isDuplicateFolderName("   ", folders)).toBe(false);
  });

  it("rename can keep the same name on the same folder (case-insensitive)", () => {
    const folders = [folder({ id: "a", name: "Work" }), folder({ id: "b", name: "play" })];
    expect(isDuplicateFolderName("WORK", folders, "a")).toBe(false);
  });

  it("sortFoldersByOrderThenUpdated orders by order then newer updatedAt", () => {
    const a = folder({ id: "a", order: 1, updatedAt: 100 });
    const b = folder({ id: "b", order: 1, updatedAt: 200 });
    const c = folder({ id: "c", order: 0, updatedAt: 50 });
    expect(sortFoldersByOrderThenUpdated([a, b, c]).map((f) => f.id)).toEqual([
      "c",
      "b",
      "a",
    ]);
  });

  it("sortThreadsWithOrderFallback prefers numeric order when any row has order", () => {
    const threads: ChatThread[] = [
      thread({ id: "a", order: 3000, updatedAt: 50 }),
      thread({ id: "b", order: 1000, updatedAt: 99 }),
    ];
    expect(sortThreadsWithOrderFallback(threads).map((t) => t.id)).toEqual([
      "b",
      "a",
    ]);
  });

  it("buildMoveSelectModel hides move when no folders exist", () => {
    const t = thread({ id: "x", folderId: null, updatedAt: 1 });
    const m = buildMoveSelectModel(t, []);
    expect(m.show).toBe(false);
  });

  it("buildMoveSelectModel includes Chats and folders with current value", () => {
    const folders = [
      folder({ id: "a", name: "Alpha", order: 0 }),
      folder({ id: "b", name: "Beta", order: 1 }),
    ];
    const t = thread({ id: "x", folderId: "b", updatedAt: 1 });
    const m = buildMoveSelectModel(t, folders);
    expect(m.show).toBe(true);
    expect(m.value).toBe("b");
    expect(m.options.map((o) => o.value)).toEqual(["__root__", "a", "b"]);
  });

  it("buildFolderSidebarModel buckets root vs folders and drops orphan folderIds to root", () => {
    const f1 = folder({ id: "f1", order: 0, name: "Work" });
    const threads: ChatThread[] = [
      thread({ id: "r1", folderId: null, updatedAt: 10 }),
      thread({ id: "in1", folderId: "f1", updatedAt: 5 }),
      thread({ id: "orphan", folderId: "missing", updatedAt: 99 }),
    ];
    const { rootThreads, folderSections } = buildFolderSidebarModel(threads, [
      f1,
    ]);
    expect(rootThreads.map((t) => t.id)).toEqual(["orphan", "r1"]);
    expect(folderSections).toHaveLength(1);
    expect(folderSections[0]!.threads.map((t) => t.id)).toEqual(["in1"]);
  });

  it("buildFolderSidebarModel orders filed threads by order when set", () => {
    const f1 = folder({ id: "f1", order: 0, name: "Work" });
    const threads: ChatThread[] = [
      thread({ id: "t2", folderId: "f1", order: 2000, updatedAt: 1 }),
      thread({ id: "t1", folderId: "f1", order: 1000, updatedAt: 99 }),
    ];
    const { folderSections } = buildFolderSidebarModel(threads, [f1]);
    expect(folderSections[0]!.threads.map((t) => t.id)).toEqual(["t1", "t2"]);
  });

  it("buildMoveTargetsForThread lists sibling folders and root when filed", () => {
    const folders = [
      folder({ id: "a", name: "Alpha", order: 0 }),
      folder({ id: "b", name: "Beta", order: 1 }),
    ];
    const t = thread({ id: "x", folderId: "a", updatedAt: 1 });
    const targets = buildMoveTargetsForThread(t, folders);
    expect(targets).toEqual([
      { folderId: null, label: "Chats" },
      { folderId: "b", label: "Beta" },
    ]);
  });

  it("buildMoveTargetsForThread at root only lists folders", () => {
    const folders = [folder({ id: "a", name: "Alpha", order: 0 })];
    const t = thread({ id: "x", folderId: null, updatedAt: 1 });
    expect(buildMoveTargetsForThread(t, folders)).toEqual([
      { folderId: "a", label: "Alpha" },
    ]);
  });
});
