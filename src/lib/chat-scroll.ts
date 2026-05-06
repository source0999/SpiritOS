// ── chat-scroll - near-bottom detection for SpiritChat stickiness (Prompt 9H) ───

export const DEFAULT_SCROLL_NEAR_BOTTOM_PX = 160;

/** True when the user is within `threshold` px of the scroll bottom. */
export function isNearBottom(
  el: HTMLElement | null | undefined,
  threshold: number = DEFAULT_SCROLL_NEAR_BOTTOM_PX,
): boolean {
  if (!el) return true;
  const gap = el.scrollHeight - el.scrollTop - el.clientHeight;
  return gap < threshold;
}
