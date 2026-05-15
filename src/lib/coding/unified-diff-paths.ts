import { normalizeRepoRelativePath } from "@/lib/coding/explicit-task-target";

/**
 * Paths touched by a unified diff, de-duplicated, order preserved.
 * Supports both git-style diffs and standard unified diffs.
 */
export function collectPathsFromUnifiedDiff(diff: string): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  const lines = diff.replace(/\r\n/g, "\n").split("\n");
  const addPath = (rawPath: string) => {
    const path = normalizeDiffHeaderPath(rawPath);
    if (path && !seen.has(path)) {
      seen.add(path);
      out.push(path);
    }
  };
  for (const raw of lines) {
    const line = raw.trimEnd();
    if (line.startsWith("diff --git ")) {
      const parts = line.split(/\s+/);
      if (parts.length >= 4) {
        addPath(parts[3]);
      }
      continue;
    }
    if (line.startsWith("--- ") || line.startsWith("+++ ")) {
      addPath(line.slice(4));
    }
  }
  return out;
}

function normalizeDiffHeaderPath(rawPath: string): string {
  let path = rawPath.trim();
  if (!path || path === "/dev/null") {
    return "";
  }
  path = unquoteDiffPath(path);
  path = stripDiffHeaderTimestamp(path);
  path = path.replace(/^(?:a|b)\//, "");
  if (path === "/dev/null") {
    return "";
  }
  return normalizeRepoRelativePath(path);
}

function unquoteDiffPath(path: string): string {
  const quote = path[0];
  if ((quote !== `"` && quote !== "'") || path.length < 2) {
    return path;
  }
  let escaped = false;
  for (let i = 1; i < path.length; i += 1) {
    const char = path[i];
    if (escaped) {
      escaped = false;
      continue;
    }
    if (char === "\\") {
      escaped = true;
      continue;
    }
    if (char === quote) {
      return path.slice(1, i);
    }
  }
  return path.replace(/^["']|["']$/g, "");
}

function stripDiffHeaderTimestamp(path: string): string {
  return path
    .replace(/\t.*$/, "")
    .replace(/\s+\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:\s+[+-]\d{4})?)?$/, "")
    .trim();
}

export function diffTouchesExplicitTarget(diff: string, explicitTarget: string): boolean {
  const want = normalizeRepoRelativePath(explicitTarget);
  if (!want || !diff.trim()) {
    return true;
  }
  const paths = collectPathsFromUnifiedDiff(diff);
  if (paths.length === 0) {
    return false;
  }
  return paths.some((p) => normalizeRepoRelativePath(p) === want);
}
