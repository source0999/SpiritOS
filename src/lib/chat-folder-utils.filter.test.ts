import { describe, expect, it } from "vitest";

import {
  filterFolderSidebarModel,
  type FolderSidebarModel,
} from "@/lib/chat-folder-utils";

describe("filterFolderSidebarModel", () => {
  const model: FolderSidebarModel = {
    rootThreads: [
      { id: "a", title: "A", createdAt: 1, updatedAt: 3 },
      { id: "b", title: "B", createdAt: 1, updatedAt: 2 },
    ],
    folderSections: [
      {
        folder: {
          id: "f1",
          name: "F",
          createdAt: 1,
          updatedAt: 1,
          order: 1,
        },
        threads: [{ id: "c", title: "C", createdAt: 1, updatedAt: 1, folderId: "f1" }],
      },
    ],
  };

  it("returns unchanged when allowed null", () => {
    expect(filterFolderSidebarModel(model, null)).toEqual(model);
  });

  it("filters roots and folder threads", () => {
    const out = filterFolderSidebarModel(model, new Set(["b", "c"]));
    expect(out.rootThreads.map((t) => t.id)).toEqual(["b"]);
    expect(out.folderSections).toHaveLength(1);
    expect(out.folderSections[0]!.threads.map((t) => t.id)).toEqual(["c"]);
  });

  it("drops empty folder sections", () => {
    const out = filterFolderSidebarModel(model, new Set(["a"]));
    expect(out.folderSections).toEqual([]);
  });
});
