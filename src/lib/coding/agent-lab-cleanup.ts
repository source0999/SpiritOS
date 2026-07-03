function normalizeRepoPath(path: string): string {
  const trimmed = path.trim().replace(/\\/g, "/");
  if (trimmed.endsWith("/") && /\.[A-Za-z0-9]+$/.test(trimmed.slice(0, -1))) {
    return trimmed.slice(0, -1);
  }
  return trimmed;
}

export function isAgentLabTrialPath(path: string): boolean {
  const normalized = normalizeRepoPath(path);
  return (
    normalized.startsWith("src/app/agent-lab/") ||
    normalized.startsWith("src/components/agent-lab/") ||
    normalized.startsWith("src/lib/agent-lab/") ||
    normalized.startsWith("src/app/api/agent-lab/") ||
    normalized.startsWith("tests/agent-lab/")
  );
}

export const DUMMY_PRODUCT_SITE_TRIAL_ROOT = "tests/ui-agent-trials/fixtures/dummy-product-site/";

export const DUMMY_PRODUCT_SITE_TRIAL_FILES = [
  `${DUMMY_PRODUCT_SITE_TRIAL_ROOT}README.md`,
  `${DUMMY_PRODUCT_SITE_TRIAL_ROOT}package.json`,
  `${DUMMY_PRODUCT_SITE_TRIAL_ROOT}index.html`,
  `${DUMMY_PRODUCT_SITE_TRIAL_ROOT}src/main.js`,
  `${DUMMY_PRODUCT_SITE_TRIAL_ROOT}src/products.js`,
  `${DUMMY_PRODUCT_SITE_TRIAL_ROOT}src/styles.css`,
] as const;

export function isDummyProductSiteTrialPath(path: string): boolean {
  return normalizeRepoPath(path).startsWith(DUMMY_PRODUCT_SITE_TRIAL_ROOT);
}

export function isCoderTrialCleanupPath(path: string): boolean {
  return isAgentLabTrialPath(path) || isDummyProductSiteTrialPath(path);
}

export function pathIsAllowedForTrialReverse(filePath: string, allowedFiles: string[]): boolean {
  const normalized = normalizeRepoPath(filePath);
  return allowedFiles.some((allowed) => {
    const pattern = normalizeRepoPath(allowed);
    if (pattern.endsWith("/**")) {
      return normalized.startsWith(pattern.slice(0, -3));
    }
    return normalized === pattern;
  });
}

export function buildDeleteFileReverseDiff(target: string, fileContent: string): string {
  const normalized = normalizeRepoPath(target);
  const lines = fileContent.split("\n");
  const trailingNewline = lines.length > 0 && lines[lines.length - 1] === "";
  const bodyLines = trailingNewline ? lines.slice(0, -1) : lines;
  const hunkOldCount = Math.max(1, bodyLines.length);
  return [
    `diff --git a/${normalized} b/${normalized}`,
    "deleted file mode 100644",
    `--- a/${normalized}`,
    "+++ /dev/null",
    `@@ -1,${hunkOldCount} +0,0 @@`,
    ...bodyLines.map((line) => `-${line}`),
    "",
  ].join("\n");
}

export function allUnrevertedSuiteResultsInReversePromptOrder<
  T extends {
    prompt: { id: string };
    reversal_available: boolean;
    reverted: boolean;
    reverse_diff: string;
  },
>(results: T[]): T[] {
  return results
    .filter((result) => result.reversal_available && !result.reverted && result.reverse_diff.trim())
    .sort((left, right) => right.prompt.id.localeCompare(left.prompt.id));
}

export function uniqueAgentLabTargetsFromResults<
  T extends {
    applied_changed_files: string[];
    disk_changed_files: string[];
    preview_changed_files: string[];
    reversal_available: boolean;
    reverted: boolean;
  },
>(results: T[]): string[] {
  const targets = new Set<string>();
  for (const result of results) {
    if (!result.reversal_available || result.reverted) continue;
    for (const file of [
      ...result.applied_changed_files,
      ...result.disk_changed_files,
      ...result.preview_changed_files,
    ]) {
      if (isCoderTrialCleanupPath(file)) {
        targets.add(normalizeRepoPath(file));
      }
    }
  }
  return [...targets];
}
