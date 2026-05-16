// ── Explicit task target (approval pipeline) ────────────────────────────────
// Parses "Target file: …" from the *current* user task so we never treat proxy /
// memory echoes as the source of truth for where edits land.

const EXPLICIT_TARGET_FILE_LINE_RE = /^\s*target\s+file\s*:\s*(.+?)\s*$/gim;

let explicitTargetParserWarningShown = false;

/**
 * @deprecated Backend route decisions now own explicit target parsing. Prefer
 * `decision.resolved_target.path` / `decision.resolvedTarget.path`.
 */
export function parseExplicitTargetFileLine(text: string): string {
  if (!explicitTargetParserWarningShown && typeof console !== "undefined") {
    explicitTargetParserWarningShown = true;
    console.warn(
      "parseExplicitTargetFileLine is deprecated; use backend decision.resolved_target.path instead.",
    );
  }
  EXPLICIT_TARGET_FILE_LINE_RE.lastIndex = 0;
  let last = "";
  let match: RegExpExecArray | null;
  while ((match = EXPLICIT_TARGET_FILE_LINE_RE.exec(text)) !== null) {
    const raw = match[1]?.trim().replace(/^["'`]|["'`]$/g, "") ?? "";
    if (raw) {
      last = raw.replace(/\\/g, "/").replace(/^\.\/+/, "");
    }
  }
  return last;
}

export function normalizeRepoRelativePath(p: string): string {
  return p.replace(/\\/g, "/").replace(/^\.\/+/, "").trim();
}
