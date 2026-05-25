import type {
  MediaIndexedDbManualEvidence,
  MediaIndexedDbManualEvidenceBlocker,
} from "@/lib/media/media-indexeddb-manual-evidence";

export type MediaDexiePrimaryPromotionDecisionStatus =
  | "promote"
  | "do-not-promote";

export type MediaDexiePrimaryPromotionDecisionBlocker =
  | "manual-evidence-not-accepted"
  | "explicit-promotion-approval-missing"
  | "rollback-plan-not-confirmed"
  | "localstorage-fallback-not-preserved"
  | "promotion-scope-expanded";

export type MediaDexiePrimaryPromotionDecisionInput = {
  manualEvidence: MediaIndexedDbManualEvidence;
  explicitPromotionApproval: boolean;
  rollbackPlanConfirmed: boolean;
  localStorageFallbackPreserved: boolean;
  scopeExpandedBeyondProfileState: boolean;
};

export type MediaDexiePrimaryPromotionDecision = {
  source: "media-dexie-primary-promotion-decision";
  status: MediaDexiePrimaryPromotionDecisionStatus;
  blockers: MediaDexiePrimaryPromotionDecisionBlocker[];
  inheritedEvidenceBlockers: MediaIndexedDbManualEvidenceBlocker[];
};

export function evaluateMediaDexiePrimaryPromotionDecision(
  input: MediaDexiePrimaryPromotionDecisionInput,
): MediaDexiePrimaryPromotionDecision {
  const blockers: MediaDexiePrimaryPromotionDecisionBlocker[] = [];

  if (input.manualEvidence.status !== "accepted") {
    blockers.push("manual-evidence-not-accepted");
  }

  if (!input.explicitPromotionApproval) {
    blockers.push("explicit-promotion-approval-missing");
  }

  if (!input.rollbackPlanConfirmed) {
    blockers.push("rollback-plan-not-confirmed");
  }

  if (!input.localStorageFallbackPreserved) {
    blockers.push("localstorage-fallback-not-preserved");
  }

  if (input.scopeExpandedBeyondProfileState) {
    blockers.push("promotion-scope-expanded");
  }

  return {
    source: "media-dexie-primary-promotion-decision",
    status: blockers.length ? "do-not-promote" : "promote",
    blockers,
    inheritedEvidenceBlockers: input.manualEvidence.blockers,
  };
}

export function formatMediaDexiePrimaryPromotionDecision(
  decision: MediaDexiePrimaryPromotionDecision,
): string {
  return decision.status === "promote" ? "Promote" : "Do not promote";
}
