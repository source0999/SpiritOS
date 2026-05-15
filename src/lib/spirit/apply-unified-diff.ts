// ── apply-unified-diff ───────────────────────────────────────────────────────
// Minimal unified-diff application for coder-generated git-style hunks.
// Used when the approval gate has a patch but no full replacement `content` yet.

/** Apply a unified diff to `original` text. Returns null if the patch cannot be applied safely. */
export function applyUnifiedDiffToText(original: string, diffText: string): string | null {
  const trimmed = diffText.trim();
  if (!trimmed || !trimmed.includes("@@")) {
    return null;
  }

  const oldLines = original === "" ? [] : original.split(/\r?\n/);
  const lines = diffText.split(/\r?\n/);
  let i = 0;
  while (i < lines.length && !lines[i]!.startsWith("@@")) {
    i++;
  }
  if (i >= lines.length) {
    return null;
  }

  const out: string[] = [];
  let oi = 0;

  while (i < lines.length) {
    const h = lines[i]!;
    if (!h.startsWith("@@")) {
      i++;
      continue;
    }
    const m = /^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@/.exec(h);
    if (!m) {
      return null;
    }
    const oldStart0 = Math.max(0, parseInt(m[1]!, 10) - 1);
    while (oi < oldStart0) {
      out.push(oldLines[oi] ?? "");
      oi++;
    }
    i++;
    while (i < lines.length && !lines[i]!.startsWith("@@")) {
      const l = lines[i]!;
      if (l.startsWith("---") || l.startsWith("+++")) {
        i++;
        continue;
      }
      if (l === "") {
        i++;
        continue;
      }
      const tag = l[0]!;
      if (tag === "\\") {
        i++;
        continue;
      }
      if (tag !== " " && tag !== "+" && tag !== "-") {
        return null;
      }
      const text = l.slice(1);
      if (tag === " ") {
        if (oi >= oldLines.length || oldLines[oi] !== text) {
          return null;
        }
        out.push(text);
        oi++;
      } else if (tag === "-") {
        if (oi >= oldLines.length || oldLines[oi] !== text) {
          return null;
        }
        oi++;
      } else if (tag === "+") {
        out.push(text);
      }
      i++;
    }
  }

  while (oi < oldLines.length) {
    out.push(oldLines[oi] ?? "");
    oi++;
  }

  return out.join("\n");
}
