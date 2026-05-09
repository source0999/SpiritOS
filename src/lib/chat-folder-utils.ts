// ── chat-folder-utils - pure sidebar grouping + order-aware sorts (Prompt 6) ───
import type { ChatFolder, ChatThread } from "@/lib/chat-db.types";

export type FolderSidebarSection = {
  folder: ChatFolder;
  threads: ChatThread[];
};

export type FolderSidebarModel = {
  rootThreads: ChatThread[];
  folderSections: FolderSidebarSection[];
};

export type MoveSelectOption = { value: string; label: string };

export function sortFoldersByOrderThenUpdated(
  folders: ChatFolder[],
): ChatFolder[] {
  return [...folders].sort(
    (a, b) => a.order - b.order || b.updatedAt - a.updatedAt,
  );
}

/** If any row has numeric `order`, sort by order asc then updatedAt; else updatedAt desc only. */
export function sortThreadsWithOrderFallback(threads: ChatThread[]): ChatThread[] {
  const anyOrder = threads.some(
    (t) => typeof t.order === "number" && !Number.isNaN(t.order),
  );
  if (!anyOrder) {
    return [...threads].sort((a, b) => b.updatedAt - a.updatedAt);
  }
  return [...threads].sort((a, b) => {
    const ao =
      typeof a.order === "number" && !Number.isNaN(a.order) ? a.order : 1e15;
    const bo =
      typeof b.order === "number" && !Number.isNaN(b.order) ? b.order : 1e15;
    if (ao !== bo) return ao - bo;
    return b.updatedAt - a.updatedAt;
  });
}

/** When `allowed` is set, keep only threads whose id is in the set (search filter). */
export function filterFolderSidebarModel(
  model: FolderSidebarModel,
  allowed: Set<string> | null,
): FolderSidebarModel {
  if (!allowed) return model;
  return {
    rootThreads: model.rootThreads.filter((t) => allowed.has(t.id)),
    folderSections: model.folderSections
      .map((section) => ({
        ...section,
        threads: section.threads.filter((t) => allowed.has(t.id)),
      }))
      .filter((s) => s.threads.length > 0),
  };
}

export function buildFolderSidebarModel(
  threads: ChatThread[],
  folders: ChatFolder[],
): FolderSidebarModel {
  const orderedFolders = sortFoldersByOrderThenUpdated(folders);
  const folderIds = new Set(orderedFolders.map((f) => f.id));

  const rootThreads = sortThreadsWithOrderFallback(
    threads.filter((t) => {
      const fid = t.folderId ?? null;
      if (fid == null || fid === "") return true;
      return !folderIds.has(fid);
    }),
  );

  const folderSections: FolderSidebarSection[] = orderedFolders.map(
    (folder) => ({
      folder,
      threads: sortThreadsWithOrderFallback(
        threads.filter((t) => (t.folderId ?? null) === folder.id),
      ),
    }),
  );

  return { rootThreads, folderSections };
}

/** Full move dropdown: Chats + every folder; value matches current bucket. */
export function buildMoveSelectModel(
  thread: ChatThread,
  allFolders: ChatFolder[],
): { show: boolean; value: string; options: MoveSelectOption[] } {
  const sortedFolders = sortFoldersByOrderThenUpdated(allFolders);
  const options: MoveSelectOption[] = [
    { value: "__root__", label: "Chats" },
    ...sortedFolders.map((f) => ({ value: f.id, label: f.name })),
  ];
  const cur = thread.folderId ?? null;
  const inKnownFolder = cur != null && sortedFolders.some((f) => f.id === cur);
  const value = inKnownFolder ? cur! : "__root__";
  const show = sortedFolders.length > 0;
  return { show, value, options };
}

/** Trim + lowercase for duplicate folder detection (case-insensitive). */
export function normalizeFolderName(name: string): string {
  return name.trim().toLowerCase();
}

export function isDuplicateFolderName(
  name: string,
  folders: Pick<ChatFolder, "id" | "name">[],
  ignoreId?: string,
): boolean {
  const key = normalizeFolderName(name);
  if (!key) return false;
  return folders.some(
    (f) => (ignoreId == null || f.id !== ignoreId) && normalizeFolderName(f.name) === key,
  );
}

/** @deprecated Prefer buildMoveSelectModel - kept for tests referencing old API */
export function buildMoveTargetsForThread(
  thread: ChatThread,
  allFolders: ChatFolder[],
): { folderId: string | null; label: string }[] {
  const cur = thread.folderId ?? null;
  const targets: { folderId: string | null; label: string }[] = [];
  if (cur !== null) {
    targets.push({ folderId: null, label: "Chats" });
  }
  for (const f of allFolders) {
    if (f.id !== cur) targets.push({ folderId: f.id, label: f.name });
  }
  return targets;
}
