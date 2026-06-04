import { normalizeAppliedRunReceiptFromJson } from "@/lib/coding/normalize-applied-run-receipt";
import { sourceProxyFetch } from "@/lib/source-proxy-origin";
import {
  applyTrialReceiptReconciliation,
  isTrialRunReceipt,
  type TrialRunReceipt,
} from "@/lib/coding/trial-receipt-reconciliation";

type JsonRecord = Record<string, unknown>;

function asRecord(value: unknown): JsonRecord {
  return value && typeof value === "object" ? (value as JsonRecord) : {};
}

async function readWorkspaceFile(path: string): Promise<string | null> {
  try {
    const response = await sourceProxyFetch("/v1/workspace/read", {
      body: JSON.stringify({ path, max_bytes: 64000 }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    if (!response.ok) return null;
    const payload = await response.json() as unknown;
    const record = asRecord(payload);
    return typeof record.excerpt === "string"
      ? record.excerpt
      : typeof record.content === "string"
        ? record.content
        : null;
  } catch {
    return null;
  }
}

export async function POST(request: Request) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      { error: "SPIRIT_CODING_USE_PROXY is not true" },
      { status: 409 },
    );
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const record = asRecord(body);
  const receiptsRaw = Array.isArray(record.receipts) ? record.receipts : [];
  const receipts = receiptsRaw
    .map((item) => normalizeAppliedRunReceiptFromJson(asRecord(item)))
    .filter((item): item is NonNullable<typeof item> => item !== null);

  const trialReceipts = receipts.filter((receipt) => isTrialRunReceipt(receipt));
  const fileContentsByTarget: Record<string, string | null> = {};
  for (const receipt of trialReceipts) {
    if (!receipt.target || fileContentsByTarget[receipt.target] !== undefined) continue;
    fileContentsByTarget[receipt.target] = await readWorkspaceFile(receipt.target);
  }

  const reconciled = applyTrialReceiptReconciliation(receipts, fileContentsByTarget);
  const activeUnreverted = reconciled.filter(
    (receipt) =>
      isTrialRunReceipt(receipt) &&
      !receipt.revertedAt &&
      !receipt.staleResolvedAt,
  ).length;
  const staleResolved = reconciled.filter((receipt) => Boolean(receipt.staleResolvedAt)).length;

  return Response.json({
    active_unreverted_trial_receipts: activeUnreverted,
    receipts: reconciled,
    stale_resolved_count: staleResolved,
    trial_fixtures_clean: activeUnreverted === 0 ? "yes" : "no",
  });
}
