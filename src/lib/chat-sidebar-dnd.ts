// ── chat-sidebar-dnd - pure drop math (oldSpiritOS rules, Dexie-agnostic) ───────
// > parseDragId + getThreadLocation + computeThreadDropPlan - no DOM geometry.
import {
  closestCenter,
  pointerWithin,
  type Collision,
  type CollisionDetection,
} from "@dnd-kit/core";
import type { UniqueIdentifier } from "@dnd-kit/core";

import type { FolderSidebarSection } from "@/lib/chat-folder-utils";
import type { ChatThread } from "@/lib/chat-db.types";

export const THREAD_DND_PREFIX = "thread:";
export const FOLDER_DROP_PREFIX = "folder:";
/** Sortable folder row id — distinct from `folder:` thread-drop droppable on the same card. */
export const FOLDER_SORT_PREFIX = "folder-sort:";

export const CHAT_SIDEBAR_ROOT_DROP_ID = `${FOLDER_DROP_PREFIX}root` as const;

type CollisionArgs = Parameters<CollisionDetection>[0];

/** Survives pointerWithin membership jitter at row boundaries (see debug-eafb6b L217–228). */
let threadOverSticky: { activeId: string; overId: string } | null = null;

/** Call on thread drag start — activeId can match a prior drag; sticky must not leak. */
export function resetThreadCollisionSticky(): void {
  threadOverSticky = null;
}

type NearestFallbackArgs = Pick<
  CollisionArgs,
  "pointerCoordinates" | "droppableContainers" | "droppableRects"
>;

/**
 * When pointer sits in the gap between rects or closestCenter is dominated by the active item,
 * pick the nearest *other* droppable by rect-center distance (fixes flaky downward drags).
 */
/** @internal exported for unit tests */
export function fallbackNearestExcludingActive(
  args: NearestFallbackArgs,
  activeId: string,
): Collision[] {
  const pc = args.pointerCoordinates;
  if (!pc) return [];
  let best: Collision | null = null;
  let bestD = Number.POSITIVE_INFINITY;
  for (const cont of args.droppableContainers) {
    const sid = String(cont.id);
    if (sid === activeId) continue;
    const rect = args.droppableRects.get(cont.id);
    if (!rect) continue;
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = pc.x - cx;
    const dy = pc.y - cy;
    const d = dx * dx + dy * dy;
    if (d < bestD) {
      bestD = d;
      best = { id: cont.id };
    }
  }
  return best ? [best] : [];
}

/**
 * When the pointer sits in overlapping / adjacent thread row rects, Euclidean “nearest center”
 * flips on tiny moves (runtime: onDragOver oscillates between two ids — Spirit debug log lines
 * 121–135). Partition vertically by midpoints between row centers so the active target is stable.
 */
/** @internal exported for unit tests */
export function pickThreadCollisionByVerticalMidpoints(
  threadHits: Collision[],
  pointerY: number,
  droppableRects: CollisionArgs["droppableRects"],
): Collision {
  if (threadHits.length === 1) return threadHits[0]!;

  const withCy = threadHits
    .map((h) => {
      const rect = droppableRects.get(h.id as UniqueIdentifier);
      const cy = rect ? rect.top + rect.height / 2 : pointerY;
      return { h, cy };
    })
    .sort((a, b) => a.cy - b.cy);

  if (withCy.length === 0) return threadHits[0]!;
  if (withCy.length === 1) return withCy[0]!.h;

  if (pointerY < (withCy[0]!.cy + withCy[1]!.cy) / 2) {
    return withCy[0]!.h;
  }
  for (let i = 1; i < withCy.length - 1; i++) {
    const midUp = (withCy[i - 1]!.cy + withCy[i]!.cy) / 2;
    const midDown = (withCy[i]!.cy + withCy[i + 1]!.cy) / 2;
    if (pointerY >= midUp && pointerY < midDown) {
      return withCy[i]!.h;
    }
  }
  return withCy[withCy.length - 1]!.h;
}

/** Sticky hand-off between midpoint-picked rows; exported for unit tests only. */
export function applyThreadOverHysteresis(
  picked: Collision,
  threadHits: Collision[],
  pointerY: number,
  droppableRects: CollisionArgs["droppableRects"],
  activeId: string,
): Collision {
  const pickedId = String(picked.id);
  if (threadHits.length < 2) {
    threadOverSticky = { activeId, overId: pickedId };
    return picked;
  }
  if (!threadOverSticky || threadOverSticky.activeId !== activeId) {
    threadOverSticky = { activeId, overId: pickedId };
    return picked;
  }
  const sid = threadOverSticky.overId;
  if (sid === pickedId) {
    return picked;
  }
  const stickyHit = threadHits.find((h) => String(h.id) === sid);
  if (!stickyHit) {
    threadOverSticky = { activeId, overId: pickedId };
    return picked;
  }
  const sr = droppableRects.get(stickyHit.id as UniqueIdentifier);
  const pr = droppableRects.get(picked.id as UniqueIdentifier);
  if (!sr || !pr) {
    threadOverSticky = { activeId, overId: pickedId };
    return picked;
  }
  const sMid = sr.top + sr.height / 2;
  const pMid = pr.top + pr.height / 2;
  if (Math.abs(sMid - pMid) < 1) {
    threadOverSticky = { activeId, overId: pickedId };
    return picked;
  }
  const boundary = (sMid + pMid) / 2;
  // Hand off exactly at row mid-boundary so `overId` tracks the midpoint pick (no +h stickiness).
  if (sMid < pMid) {
    if (pointerY < boundary) {
      return stickyHit;
    }
  } else {
    if (pointerY > boundary) {
      return stickyHit;
    }
  }
  threadOverSticky = { activeId, overId: pickedId };
  return picked;
}

/**
 * Prefer pointer hit targets so `folder:root` wins over ghost `closestCenter` folder grabs
 * when dragging a thread back to Chats - still picks nearest thread when hovering a row.
 */
export const chatSidebarThreadCollisionDetection: CollisionDetection = (args) => {
  const activeId = String(args.active.id);

  // Folder reorder: `closestCenter` after notSelf still picks thread rows under the pointer
  // (runtime debug-5a2791: overId thread:… while active folder-sort:… → reorder plan null).
  // Prefer other folder-sort rects, then folder: droppables — never thread:* for this drag type.
  if (activeId.startsWith(FOLDER_SORT_PREFIX)) {
    threadOverSticky = null;
    const idStr = (c: Collision) => String(c.id);
    const notSelf = (c: Collision) => idStr(c) !== activeId;
    const isThread = (c: Collision) => idStr(c).startsWith(THREAD_DND_PREFIX);
    const isFolderSort = (c: Collision) => idStr(c).startsWith(FOLDER_SORT_PREFIX);
    const isFolderDrop = (c: Collision) => {
      const s = idStr(c);
      return (
        s.startsWith(FOLDER_DROP_PREFIX) &&
        !s.startsWith(FOLDER_SORT_PREFIX) &&
        s !== CHAT_SIDEBAR_ROOT_DROP_ID
      );
    };

    const candidates = closestCenter(args).filter(notSelf);
    const folderSortHits = candidates.filter(isFolderSort);
    if (folderSortHits.length) return folderSortHits;

    const folderDropHits = candidates.filter(isFolderDrop);
    if (folderDropHits.length) return folderDropHits;

    const nonThread = candidates.filter((c) => !isThread(c));
    if (nonThread.length) return nonThread;

    // closestCenter can be thread-only when the pointer sits over expanded thread lists; still pick
    // the nearest folder card by rect so reorder doesn't die with over=null / thread steal.
    const fb = fallbackNearestExcludingActive(args, activeId).filter((c) => {
      if (isThread(c)) return false;
      if (isFolderSort(c)) return true;
      return isFolderDrop(c);
    });
    return fb.length ? fb : [];
  }

  if (!activeId.startsWith(THREAD_DND_PREFIX)) {
    threadOverSticky = null;
    return closestCenter(args);
  }

  const idStr = (c: Collision) => String(c.id);

  /** Never treat the dragged thread as the drop target — self-drop makes computeThreadDropPlan return null. */
  const notSelf = (c: Collision) => idStr(c) !== activeId;

  const pw = pointerWithin(args).filter(notSelf);
  if (pw.length === 0) {
    threadOverSticky = null;
    const cc = closestCenter(args).filter(notSelf);
    if (cc.length) return cc;
    const fb = fallbackNearestExcludingActive(args, activeId);
    return fb.length ? fb : [];
  }

  const threadHits = pw.filter((c) => idStr(c).startsWith(THREAD_DND_PREFIX));
  if (threadHits.length > 0) {
    const pc = args.pointerCoordinates;
    if (!pc || threadHits.length === 1) return [threadHits[0]!];

    const midpointPick = pickThreadCollisionByVerticalMidpoints(
      threadHits,
      pc.y,
      args.droppableRects,
    );
    const stabilized = applyThreadOverHysteresis(
      midpointPick,
      threadHits,
      pc.y,
      args.droppableRects,
      activeId,
    );
    return [stabilized];
  }

  const root = pw.find((c) => idStr(c) === CHAT_SIDEBAR_ROOT_DROP_ID);
  if (root) return [root];

  const folderHits = pw.filter((c) => {
    const s = idStr(c);
    return (
      s.startsWith(FOLDER_DROP_PREFIX) &&
      !s.startsWith(FOLDER_SORT_PREFIX) &&
      s !== CHAT_SIDEBAR_ROOT_DROP_ID
    );
  });
  if (folderHits.length > 0) return [folderHits[folderHits.length - 1]!];

  const cc = closestCenter(args).filter(notSelf);
  if (cc.length) return cc;
  const fb = fallbackNearestExcludingActive(args, activeId);
  return fb.length ? fb : [];
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
  if (id.startsWith(FOLDER_SORT_PREFIX)) {
    return { kind: "unknown" };
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

/** dnd-kit-style move: indices are positions in the *original* list before the move. */
function arrayMoveLocal<T>(items: T[], from: number, to: number): T[] {
  const next = [...items];
  const [item] = next.splice(from, 1);
  next.splice(to, 0, item);
  return next;
}

/** Reorder sidebar folders (Dexie `folders.order`) after a folder card drag. */
export function computeFolderReorderPlan(args: {
  activeFolderId: string;
  overId: string;
  folderSections: FolderSidebarSection[];
}): string[] | null {
  const { activeFolderId, overId, folderSections } = args;
  const order = folderSections.map((s) => s.folder.id);
  const activeIdx = order.indexOf(activeFolderId);
  if (activeIdx < 0) return null;

  let overFolderId: string | null = null;
  if (overId.startsWith(FOLDER_SORT_PREFIX)) {
    overFolderId = overId.slice(FOLDER_SORT_PREFIX.length);
  } else if (
    overId.startsWith(FOLDER_DROP_PREFIX) &&
    overId !== CHAT_SIDEBAR_ROOT_DROP_ID
  ) {
    overFolderId = overId.slice(FOLDER_DROP_PREFIX.length);
  } else {
    return null;
  }

  const overIdx = order.indexOf(overFolderId);
  if (overIdx < 0 || activeIdx === overIdx) return null;

  return arrayMoveLocal(order, activeIdx, overIdx);
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
  let overThreadId: string | null = null;

  if (overParsed.kind === "folder") {
    destKey = overParsed.folderId;
  } else {
    overThreadId = overParsed.threadId;
    const overLoc = getThreadLocation(overThreadId, rootThreads, folderSections);
    if (!overLoc) return null;
    destKey = bucketKey(overLoc);
  }

  // Same bucket + hovering another thread: arrayMove on original order. Remove+insertBefore
  // was wrong for downward drags (remove B then insert before C → noop).
  if (overThreadId != null && srcKey === destKey) {
    const originalIds = cloneBuckets(rootThreads, folderSections)
      .get(srcKey)!
      .map((t) => t.id);
    const activeIdx = originalIds.indexOf(activeThreadId);
    const overIdx = originalIds.indexOf(overThreadId);
    if (activeIdx < 0 || overIdx < 0 || activeIdx === overIdx) return null;
    const orderedIds = arrayMoveLocal(originalIds, activeIdx, overIdx);
    return [{ folderId: srcKey, orderedIds }];
  }

  let insertBeforeThreadId: string | null = null;
  if (overParsed.kind === "thread") {
    insertBeforeThreadId = overParsed.threadId;
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
  /** Thread bucket reorder and/or folder reorder — either arms the sidebar DnD shell. */
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
