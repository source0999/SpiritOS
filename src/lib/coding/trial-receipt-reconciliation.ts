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
  const hasAddedEvidence = addedLines.some((line) => currentFileContent.includes(line));
  const hasRemovedEvidence = removedLines.some((line) => !currentFileContent.includes(line));

  if (!addedLines.length && !removedLines.length) {
    return "unknown";
  }

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
