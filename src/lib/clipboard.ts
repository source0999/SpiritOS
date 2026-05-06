// ── clipboard - SpiritMessage copy without assuming secure context (10B) ─────────

export type CopyTextResult = { ok: true } | { ok: false; reason: "unavailable" | "denied" };

/** Best-effort copy; never throws. */
export async function copyTextToClipboard(text: string): Promise<CopyTextResult> {
  const t = text;
  try {
    const w = typeof navigator !== "undefined" ? navigator : undefined;
    const clip = w?.clipboard;
    const write = clip?.writeText;
    if (typeof write === "function") {
      await write.call(clip, t);
      return { ok: true };
    }
  } catch {
    return { ok: false, reason: "denied" };
  }

  if (typeof document === "undefined") {
    return { ok: false, reason: "unavailable" };
  }

  try {
    const ta = document.createElement("textarea");
    ta.value = t;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    ta.style.top = "0";
    document.body.appendChild(ta);
    ta.select();
    const legacyOk = document.execCommand?.("copy");
    document.body.removeChild(ta);
    if (legacyOk) return { ok: true };
  } catch {
    /* fall through */
  }

  return { ok: false, reason: "unavailable" };
}
