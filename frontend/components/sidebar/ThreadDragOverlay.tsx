// ─── Spirit OS · ThreadDragOverlay ───────────────────────────────────────────
//
// The ghost card that floats under the cursor during a drag operation.
// Rendered inside @dnd-kit/core's <DragOverlay> portal — it paints on top of
// everything at the correct cursor position automatically.
//
// Design decision: this is NOT a SortableThreadItem clone. Cloning would
// re-instantiate the ThreadItem state machine (rename/menu/confirming) inside
// a portal, which causes React warnings and subtle state bugs. Instead we
// render a lightweight read-only card that matches the idle ThreadItem visual
// with a violet glow to signal "in flight."
//
// ─────────────────────────────────────────────────────────────────────────────

import type { Thread } from "@/lib/db.types";

interface ThreadDragOverlayProps {
  thread: Thread;
}

export function ThreadDragOverlay({ thread }: ThreadDragOverlayProps) {
  return (
    <div
      className={[
        "flex w-full items-center rounded-xl px-3 py-2.5",
        "border border-violet-500/30 bg-zinc-900",
        "shadow-[0_8px_32px_rgba(139,92,246,0.25)]",
        "cursor-grabbing",
      ].join(" ")}
      style={{ width: "232px" }} // matches sidebar inner width (256px - 2*px-2)
    >
      <div className="min-w-0 flex-1">
        <p className="truncate text-[12px] font-medium text-zinc-100">
          {thread.title}
        </p>
        {thread.preview && (
          <p className="mt-0.5 truncate text-[11px] text-zinc-500">
            {thread.preview}
          </p>
        )}
      </div>
    </div>
  );
}
