// ── chat-sidebar-dnd - pure drop math (oldSpiritOS rules, Dexie-agnostic) ───────
// > parseDragId + getThreadLocation + computeThreadDropPlan - no DOM geometry.
import { closestCenter, pointerWithin, type Collision, type CollisionDetection } from "@dnd-kit/core";
import type { UniqueIdentifier } from "@dnd-kit/core";

import type { FolderSidebarSection } from "@/lib/chat-folder-utils";
import type { ChatThread } from "@/lib/chat-db.types";

export const THREAD_DND_PREFIX = "thread:";
export const FOLDER_DROP_PREFIX = "folder:";

export const CHAT_SIDEBAR_ROOT_DROP_ID = `${FOLDER_DROP_PREFIX}root` as const;

/**
 * Prefer pointer hit targets so `folder:root` wins over ghost `closestCenter` folder grabs
 * when dragging a thread back to Chats - still picks nearest thread when hovering a row.
 */
export const chatSidebarThreadCollisionDetection: CollisionDetection = (args) => {
  const activeId = String(args.active.id);
  if (!activeId.startsWith(THREAD_DND_PREFIX)) {
    return closestCenter(args);
  }

  const pw = pointerWithin(args);
  if (pw.length === 0) return closestCenter(args);

  const idStr = (c: Collision) => String(c.id);
  const threadHits = pw.filter((c) => idStr(c).startsWith(THREAD_DND_PREFIX));
  if (threadHits.length > 0) {
    const pc = args.pointerCoordinates;
    if (!pc || threadHits.length === 1) return [threadHits[0]!];

    let best = threadHits[0]!;
    let bestD = Number.POSITIVE_INFINITY;
    for (const h of threadHits) {
      const rect = args.droppableRects.get(h.id as UniqueIdentifier);
      if (!rect) continue;
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = pc.x - cx;
      const dy = pc.y - cy;
      const d = dx * dx + dy * dy;
      if (d < bestD) {
        bestD = d;
        best = h;
      }
    }
    return [best];
  }

  const root = pw.find((c) => idStr(c) === CHAT_SIDEBAR_ROOT_DROP_ID);
  if (root) return [root];

  const folderHits = pw.filter(
    (c) => idStr(c).startsWith(FOLDER_DROP_PREFIX) && idStr(c) !== CHAT_SIDEBAR_ROOT_DROP_ID,
  );
  if (folderHits.length > 0) return [folderHits[folderHits.length - 1]!];

  return closestCenter(args);
};

export type ThreadReorderOp = { folderId: string | null; orderedIds: string[] };

export type ParsedDragId =
  | { kind: "thread"; threadId: string }
  | { kind: "folder"; folderId: string | null }
  | { kind: "unknown" };

export function parseDragId(id: string): ParsedDragId {
  if (id.startsWith(THREAD_DND_PREFIX)) {
    return { kind: "thread", threadId: id.slice(THREAD_DND_PREFIX.length) };
  }
  if (id === CHAT_SIDEBAR_ROOT_DROP_ID) {
    return { kind: "folder", folderId: null };
  }
  if (id.startsWith(FOLDER_DROP_PREFIX)) {
    return {
      kind: "folder",
      folderId: id.slice(FOLDER_DROP_PREFIX.length),
    };
  }
  return { kind: "unknown" };
}

export type ThreadLocation =
  | { bucket: "root" }
  | { bucket: "folder"; folderId: string };

export function getThreadLocation(
  threadId: string,
  rootThreads: ChatThread[],
  folderSections: FolderSidebarSection[],
): ThreadLocation | undefined {
  if (rootThreads.some((t) => t.id === threadId)) return { bucket: "root" };
  for (const s of folderSections) {
    if (s.threads.some((t) => t.id === threadId)) {
      return { bucket: "folder", folderId: s.folder.id };
    }
  }
  return undefined;
}

function bucketKey(loc: ThreadLocation): string | null {
  return loc.bucket === "root" ? null : loc.folderId;
}

function cloneBuckets(
  rootThreads: ChatThread[],
  folderSections: FolderSidebarSection[],
): Map<string | null, ChatThread[]> {
  const m = new Map<string | null, ChatThread[]>();
  m.set(null, [...rootThreads]);
  for (const s of folderSections) {
    m.set(s.folder.id, [...s.threads]);
  }
  return m;
}

/** Dexie reorder writes after a thread drag (root = null bucket). */
export function computeThreadDropPlan(args: {
  activeThreadId: string;
  overId: string;
  rootThreads: ChatThread[];
  folderSections: FolderSidebarSection[];
}): ThreadReorderOp[] | null {
  const { activeThreadId, overId, rootThreads, folderSections } = args;
  if (!activeThreadId) return null;

  const overParsed = parseDragId(overId);
  if (overParsed.kind === "unknown") return null;
  if (
    overParsed.kind === "thread" &&
    overParsed.threadId === activeThreadId
  ) {
    return null;
  }

  const srcLoc = getThreadLocation(activeThreadId, rootThreads, folderSections);
  if (!srcLoc) return null;
  const srcKey = bucketKey(srcLoc);

  let destKey: string | null;
  let insertBeforeThreadId: string | null = null;

  if (overParsed.kind === "folder") {
    destKey = overParsed.folderId;
  } else {
    const overThreadId = overParsed.threadId;
    const overLoc = getThreadLocation(overThreadId, rootThreads, folderSections);
    if (!overLoc) return null;
    destKey = bucketKey(overLoc);
    insertBeforeThreadId = overThreadId;
  }

  const buckets = cloneBuckets(rootThreads, folderSections);
  const srcList = buckets.get(srcKey)!;
  const activeIdx = srcList.findIndex((t) => t.id === activeThreadId);
  if (activeIdx < 0) return null;
  const [moving] = srcList.splice(activeIdx, 1);

  const dstList = buckets.get(destKey)!;

  if (insertBeforeThreadId) {
    const ins = dstList.findIndex((t) => t.id === insertBeforeThreadId);
    if (ins >= 0) dstList.splice(ins, 0, moving);
    else dstList.push(moving);
  } else {
    dstList.push(moving);
  }

  if (srcKey === destKey) {
    return [{ folderId: srcKey, orderedIds: dstList.map((t) => t.id) }];
  }
  return [
    { folderId: srcKey, orderedIds: srcList.map((t) => t.id) },
    { folderId: destKey, orderedIds: dstList.map((t) => t.id) },
  ];
}

/** @deprecated use computeThreadDropPlan */
export const computeThreadDragOps = computeThreadDropPlan;

/** Pure gate: desktop rail vs mobile drawer-only DnD (Prompt 9F). */
export function shouldEnableChatThreadSidebarDnd(opts: {
  hasCommitHandler: boolean;
  railLocked: boolean;
  lgDesktop: boolean;
  layoutVariant: "default" | "drawer";
  mobileDndEnabled: boolean;
}): boolean {
  return Boolean(
    opts.hasCommitHandler &&
      !opts.railLocked &&
      (opts.lgDesktop || (opts.layoutVariant === "drawer" && opts.mobileDndEnabled)),
  );
}
