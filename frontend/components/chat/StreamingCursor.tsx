// ─── Spirit OS · StreamingCursor ─────────────────────────────────────────────
//
// A self-contained blinking cursor component that mounts during streaming and
// unmounts on completion. Implemented as a separate component (not a CSS
// pseudo-element on the text node) so React can cleanly unmount it without
// producing a flash-of-unstyled-cursor when the stream ends and the parent
// re-renders with finalized Markdown content.
//
// Usage:
//   <StreamingCursor />           ← inline, trails live text
//   <StreamingCursor size="lg" /> ← taller cursor for larger font contexts
//
// ─────────────────────────────────────────────────────────────────────────────

interface StreamingCursorProps {
  size?: "sm" | "md" | "lg";
}

const SIZE_MAP: Record<NonNullable<StreamingCursorProps["size"]>, string> = {
  sm: "h-[0.75em] w-[1.5px]",
  md: "h-[1em] w-[2px]",
  lg: "h-[1.25em] w-[2px]",
};

export function StreamingCursor({ size = "md" }: StreamingCursorProps) {
  return (
    <span
      aria-hidden
      className={[
        "ml-[2px] inline-block align-middle",
        "animate-pulse rounded-[1px] bg-violet-400",
        SIZE_MAP[size],
      ].join(" ")}
    />
  );
}
