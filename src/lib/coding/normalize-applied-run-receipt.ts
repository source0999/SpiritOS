/** Normalize client-stored applied-run receipts from JSON (camelCase or snake_case). */
export type NormalizedAppliedRunReceipt = {
  allowedFiles: string[];
  appliedAt: string;
  backupManifest?: string | null;
  changedFiles: string[];
  diff: string;
  finalTruthStatus?: string | null;
  hermesUsedForThisRun: boolean | null;
  id: string;
  model: string | null;
  prompt: string;
  provider: string | null;
  providerModelSource: string;
  providerModelStatus: string;
  revertedAt: string | null;
  reversalModel: string | null;
  reversalProvider: string | null;
  reversalProviderModelSource: string | null;
  reverseDiff: string;
  staleResolvedAt?: string | null;
  target: string;
  taskId: string;
  undoReceiptId?: string | null;
  undoReceiptPath?: string | null;
  postApplyVerificationStatus?: string | null;
};

function stringField(record: Record<string, unknown>, ...keys: string[]): string {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) return value;
  }
  return "";
}

function nullableString(record: Record<string, unknown>, ...keys: string[]): string | null {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "string") return value;
    if (value === null) return null;
  }
  return null;
}

function stringList(record: Record<string, unknown>, ...keys: string[]): string[] {
  for (const key of keys) {
    const value = record[key];
    if (Array.isArray(value)) {
      return value.filter((item): item is string => typeof item === "string");
    }
  }
  return [];
}

function nullableBoolean(record: Record<string, unknown>, ...keys: string[]): boolean | null {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "boolean") return value;
    if (value === null) return null;
  }
  return null;
}

export function normalizeAppliedRunReceiptFromJson(
  item: Record<string, unknown>,
): NormalizedAppliedRunReceipt | null {
  const id = stringField(item, "id");
  const diff = stringField(item, "diff");
  const reverseDiff = stringField(item, "reverseDiff", "reverse_diff");
  if (!id || !diff || !reverseDiff) return null;

  return {
    allowedFiles: stringList(item, "allowedFiles", "allowed_files"),
    appliedAt: stringField(item, "appliedAt", "applied_at"),
    backupManifest: nullableString(item, "backupManifest", "backup_manifest"),
    changedFiles: stringList(item, "changedFiles", "changed_files"),
    diff,
    finalTruthStatus: nullableString(item, "finalTruthStatus", "final_truth_status"),
    hermesUsedForThisRun: nullableBoolean(item, "hermesUsedForThisRun", "hermes_used_for_this_run"),
    id,
    model: nullableString(item, "model"),
    prompt: stringField(item, "prompt"),
    provider: nullableString(item, "provider"),
    providerModelSource:
      stringField(item, "providerModelSource", "provider_model_source") || "unknown",
    providerModelStatus:
      stringField(item, "providerModelStatus", "provider_model_status") || "unknown",
    revertedAt: nullableString(item, "revertedAt", "reverted_at"),
    reversalModel: nullableString(item, "reversalModel", "reversal_model"),
    reversalProvider: nullableString(item, "reversalProvider", "reversal_provider"),
    reversalProviderModelSource: nullableString(
      item,
      "reversalProviderModelSource",
      "reversal_provider_model_source",
    ),
    reverseDiff,
    staleResolvedAt: nullableString(item, "staleResolvedAt", "stale_resolved_at"),
    target: stringField(item, "target"),
    taskId: stringField(item, "taskId", "task_id"),
    undoReceiptId: nullableString(item, "undoReceiptId", "undo_receipt_id"),
    undoReceiptPath: nullableString(item, "undoReceiptPath", "undo_receipt_path"),
    postApplyVerificationStatus: nullableString(
      item,
      "postApplyVerificationStatus",
      "post_apply_verification_status",
    ),
  };
}
