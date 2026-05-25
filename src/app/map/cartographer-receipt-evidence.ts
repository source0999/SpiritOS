const RECEIPT_JOURNAL_ENDPOINT = "/v1/cartographer/level-8-receipt-journal";
const V1_EVIDENCE_ENDPOINT = "/v1/cartographer/v1-evidence";

export type CartographerReceiptEvidenceItem = {
  id: string;
  label: string;
  status: string;
  paths: string[];
};

export type CartographerReceiptEvidenceStatus = {
  available: boolean;
  receiptJournalStatus: string;
  receiptJournalWriteAllowed: boolean;
  hiddenReceiptWritesAllowed: boolean;
  evidenceCollectionMode: string;
  evidenceArtifactCount: number;
  proofGateRecordCount: number;
  missingEvidence: string[];
  approvedDocsArtifacts: CartographerReceiptEvidenceItem[];
  evidenceItems: CartographerReceiptEvidenceItem[];
  safeNextAction: string;
  detail: string;
};

const unavailableReceiptEvidenceStatus: CartographerReceiptEvidenceStatus = {
  available: false,
  receiptJournalStatus: "unavailable",
  receiptJournalWriteAllowed: false,
  hiddenReceiptWritesAllowed: false,
  evidenceCollectionMode: "unavailable",
  evidenceArtifactCount: 0,
  proofGateRecordCount: 0,
  missingEvidence: ["receipt_evidence_browser_unavailable"],
  approvedDocsArtifacts: [],
  evidenceItems: [],
  safeNextAction:
    "Stop and manually verify receipt/evidence sources before trusting the browser.",
  detail: "Receipt/evidence browser data could not be read.",
};

export async function getCartographerReceiptEvidenceStatus(
  origin: string | null,
): Promise<CartographerReceiptEvidenceStatus> {
  if (!origin) {
    return {
      ...unavailableReceiptEvidenceStatus,
      detail:
        "Request origin was unavailable, so receipt/evidence browser data was not fetched.",
    };
  }

  try {
    const [receiptResponse, evidenceResponse] = await Promise.all([
      fetch(`${origin}${RECEIPT_JOURNAL_ENDPOINT}`, {
        method: "GET",
        cache: "no-store",
      }),
      fetch(`${origin}${V1_EVIDENCE_ENDPOINT}`, {
        method: "GET",
        cache: "no-store",
      }),
    ]);

    if (!receiptResponse.ok || !evidenceResponse.ok) {
      return {
        ...unavailableReceiptEvidenceStatus,
        detail: `Receipt/evidence endpoint returned HTTP ${receiptResponse.status}/${evidenceResponse.status}.`,
      };
    }

    return normalizeReceiptEvidenceStatus(
      await receiptResponse.json(),
      await evidenceResponse.json(),
    );
  } catch (error) {
    return {
      ...unavailableReceiptEvidenceStatus,
      detail:
        error instanceof Error
          ? `Receipt/evidence browser request failed: ${error.message}`
          : "Receipt/evidence browser request failed.",
    };
  }
}

function normalizeReceiptEvidenceStatus(
  receiptPayload: unknown,
  evidencePayload: unknown,
): CartographerReceiptEvidenceStatus {
  if (!isRecord(receiptPayload) || !isRecord(evidencePayload)) {
    return {
      ...unavailableReceiptEvidenceStatus,
      detail: "Receipt/evidence endpoints returned unexpected payload shapes.",
    };
  }

  const journal = isRecord(receiptPayload.journal) ? receiptPayload.journal : {};
  const receiptEntries = itemArray(receiptPayload.entries, "receipt");
  const cleanDiagnostics = artifactArray(
    evidencePayload.latest_clean_diagnostics,
    "diagnostic",
  );
  const cleanSoak = artifactArray(
    evidencePayload.latest_clean_soak_snapshots,
    "soak",
  );

  return {
    available: true,
    receiptJournalStatus: stringValue(journal.status) ?? stringValue(receiptPayload.status) ?? "unknown",
    receiptJournalWriteAllowed:
      booleanValue(receiptPayload.receipt_journal_write_allowed) ?? false,
    hiddenReceiptWritesAllowed:
      booleanValue(receiptPayload.hidden_receipt_writes_allowed) ?? false,
    evidenceCollectionMode:
      stringValue(evidencePayload.evidence_collection_mode) ?? "unknown",
    evidenceArtifactCount: numberValue(evidencePayload.artifact_count) ?? 0,
    proofGateRecordCount: numberValue(evidencePayload.proof_gate_record_count) ?? 0,
    missingEvidence: stringArray(evidencePayload.missing_evidence),
    approvedDocsArtifacts: receiptEntries
      .concat(cleanDiagnostics, cleanSoak)
      .filter((item) => item.paths.some((path) => path.startsWith("docs/")))
      .slice(0, 8),
    evidenceItems: receiptEntries.concat(cleanDiagnostics, cleanSoak).slice(0, 12),
    safeNextAction:
      "Review existing docs artifacts only; do not create evidence, receipts, or audit records from /map.",
    detail:
      "Receipt/evidence browser reads existing approved artifacts and keeps write authority blocked.",
  };
}

function itemArray(value: unknown, fallbackPrefix: string): CartographerReceiptEvidenceItem[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter(isRecord).map((item, index) => ({
    id:
      stringValue(item.event_id) ??
      stringValue(item.id) ??
      `${fallbackPrefix}-${index + 1}`,
    label:
      stringValue(item.event_type) ??
      stringValue(item.label) ??
      `${fallbackPrefix} item`,
    status: stringValue(item.status) ?? "unknown",
    paths: stringArray(item.evidence),
  }));
}

function artifactArray(value: unknown, fallbackPrefix: string): CartographerReceiptEvidenceItem[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter(isRecord).map((item, index) => ({
    id:
      stringValue(item.path) ??
      stringValue(item.artifact_id) ??
      `${fallbackPrefix}-${index + 1}`,
    label:
      stringValue(item.profile) ??
      stringValue(item.kind) ??
      `${fallbackPrefix} artifact`,
    status: booleanValue(item.clean) === false ? "needs_review" : "clean",
    paths: stringValue(item.path) ? [stringValue(item.path) as string] : [],
  }));
}

function booleanValue(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function stringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is string => typeof item === "string");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
