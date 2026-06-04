import {
  routeSummaryTrialHasSatisfiedApplyShape,
  routeSummaryTrialHasStatusPrefix,
} from "@/lib/coding/agent-trials-ui";

export type TrialRunReceipt = {
  allowedFiles?: string[];
  changedFiles: string[];
  diff: string;
  id: string;
  revertedAt: string | null;
  staleResolvedAt?: string | null;
  target: string;
};

export type TrialReceiptReconcileStatus =
  | "active"
  | "reverted"
  | "stale_resolved"
  | "unknown";

export function isTrialRunReceiptPath(path: string): boolean {
  return (
    path.startsWith("tests/ui-agent-trials/") ||
    path.startsWith("src/lib/coding/__tests__/") ||
    path === "src/lib/coding/agent-trials-ui.ts"
  );
}

export function isTrialRunReceipt(receipt: Pick<TrialRunReceipt, "changedFiles"> & {
  allowedFiles?: string[];
}): boolean {
  const files =
    receipt.changedFiles.length > 0
      ? receipt.changedFiles
      : receipt.allowedFiles ?? [];
  return files.some((path) => isTrialRunReceiptPath(path));
}

function addedLinesFromUnifiedDiff(diff: string): string[] {
  return diff
    .split("\n")
    .filter((line) => line.startsWith("+") && !line.startsWith("+++"))
    .map((line) => line.slice(1).trim())
    .filter(Boolean);
}

function removedLinesFromUnifiedDiff(diff: string): string[] {
  return diff
    .split("\n")
    .filter((line) => line.startsWith("-") && !line.startsWith("---"))
    .map((line) => line.slice(1).trim())
    .filter(Boolean);
}

/** Added lines that identify the trial edit, not unchanged context still present after a partial apply. */
export function distinctiveAddedMarkersFromDiff(diff: string): string[] {
  const added = addedLinesFromUnifiedDiff(diff);
  const removed = new Set(removedLinesFromUnifiedDiff(diff));
  return added.filter((line) => {
    const trimmed = line.trim();
    if (!trimmed || removed.has(trimmed)) {
      return false;
    }
    if (trimmed === "}" || trimmed === "{" || trimmed === "};") {
      return false;
    }
    if (/^export function /.test(trimmed)) {
      return true;
    }
    if (/^export (type|const|enum) /.test(trimmed)) {
      return true;
    }
    if (/assertTrialBadgeWarningState|safeMessage|Status: \$\{input\.status\}/.test(trimmed)) {
      return true;
    }
    return trimmed.length >= 28;
  });
}

export function reconcileTrialReceiptWithContent(
  receipt: TrialRunReceipt,
  currentFileContent: string | null | undefined,
): TrialReceiptReconcileStatus {
  if (receipt.revertedAt || receipt.staleResolvedAt) {
    return receipt.staleResolvedAt ? "stale_resolved" : "reverted";
  }
  if (currentFileContent === null || currentFileContent === undefined) {
    return "unknown";
  }

  const addedLines = addedLinesFromUnifiedDiff(receipt.diff);
  const removedLines = removedLinesFromUnifiedDiff(receipt.diff);
  const distinctiveMarkers = distinctiveAddedMarkersFromDiff(receipt.diff);

  if (!addedLines.length && !removedLines.length) {
    return "unknown";
  }

  const normalizedTarget = receipt.target.replace(/\\/g, "/");
  if (normalizedTarget.endsWith("/route-summary-trial.ts")) {
    return routeSummaryTrialHasStatusPrefix(currentFileContent) ||
      routeSummaryTrialHasSatisfiedApplyShape(currentFileContent)
      ? "active"
      : "stale_resolved";
  }

  if (distinctiveMarkers.length > 0) {
    const hasDistinctiveEvidence = distinctiveMarkers.some((marker) =>
      currentFileContent.includes(marker),
    );
    return hasDistinctiveEvidence ? "active" : "stale_resolved";
  }

  const hasAddedEvidence = addedLines.some((line) => currentFileContent.includes(line));
  const hasRemovedEvidence = removedLines.some((line) => !currentFileContent.includes(line));

  if (hasAddedEvidence || hasRemovedEvidence) {
    return "active";
  }

  return "stale_resolved";
}

export function applyTrialReceiptReconciliation<T extends TrialRunReceipt>(
  receipts: T[],
  fileContentsByTarget: Record<string, string | null | undefined>,
  resolvedAt = new Date().toISOString(),
): T[] {
  return receipts.map((receipt) => {
    if (receipt.revertedAt || receipt.staleResolvedAt) {
      return receipt;
    }
    const status = reconcileTrialReceiptWithContent(
      receipt,
      fileContentsByTarget[receipt.target],
    );
    if (status !== "stale_resolved") {
      return receipt;
    }
    return {
      ...receipt,
      staleResolvedAt: resolvedAt,
    };
  });
}

export function countActiveUnrevertedTrialReceipts(
  receipts: Array<TrialRunReceipt & { allowedFiles?: string[] }>,
): number {
  return receipts.filter(
    (receipt) =>
      !receipt.revertedAt &&
      !receipt.staleResolvedAt &&
      isTrialRunReceipt(receipt),
  ).length;
}

export function countStaleResolvedTrialReceipts(receipts: TrialRunReceipt[]): number {
  return receipts.filter((receipt) => Boolean(receipt.staleResolvedAt)).length;
}
