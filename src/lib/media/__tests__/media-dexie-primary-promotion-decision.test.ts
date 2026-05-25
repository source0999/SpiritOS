import { describe, expect, it } from "vitest";

import {
  evaluateMediaDexiePrimaryPromotionDecision,
  formatMediaDexiePrimaryPromotionDecision,
} from "@/lib/media/media-dexie-primary-promotion-decision";
import type { MediaIndexedDbManualEvidence } from "@/lib/media/media-indexeddb-manual-evidence";

const acceptedEvidence: MediaIndexedDbManualEvidence = {
  source: "media-indexeddb-manual-evidence",
  status: "accepted",
  blockers: [],
  primaryReadiness: {
    status: "ready",
    blockers: [],
  },
  captured: {
    manualAcceptanceStatus: "passed",
    runtimeReadSourceStatus: "dexie",
    latestProfileWriteStatus: "written",
    indexedDbTablesInspected: true,
    localStorageFallbackPreserved: true,
    skippedEntriesReviewed: true,
  },
};

const blockedEvidence: MediaIndexedDbManualEvidence = {
  ...acceptedEvidence,
  status: "blocked",
  blockers: ["manual-acceptance-not-passed"],
  primaryReadiness: {
    status: "blocked",
    blockers: ["manual-acceptance-not-passed"],
  },
  captured: {
    ...acceptedEvidence.captured,
    manualAcceptanceStatus: "not-run",
  },
};

describe("evaluateMediaDexiePrimaryPromotionDecision", () => {
  it("promotes only when evidence, explicit approval, rollback, fallback, and scope are all clean", () => {
    expect(
      evaluateMediaDexiePrimaryPromotionDecision({
        manualEvidence: acceptedEvidence,
        explicitPromotionApproval: true,
        rollbackPlanConfirmed: true,
        localStorageFallbackPreserved: true,
        scopeExpandedBeyondProfileState: false,
      }),
    ).toEqual({
      source: "media-dexie-primary-promotion-decision",
      status: "promote",
      blockers: [],
      inheritedEvidenceBlockers: [],
    });
  });

  it("blocks promotion by default when explicit approval and rollback are missing", () => {
    expect(
      evaluateMediaDexiePrimaryPromotionDecision({
        manualEvidence: acceptedEvidence,
        explicitPromotionApproval: false,
        rollbackPlanConfirmed: false,
        localStorageFallbackPreserved: true,
        scopeExpandedBeyondProfileState: false,
      }),
    ).toMatchObject({
      status: "do-not-promote",
      blockers: [
        "explicit-promotion-approval-missing",
        "rollback-plan-not-confirmed",
      ],
    });
  });

  it("inherits manual evidence blockers and refuses promotion until evidence is accepted", () => {
    expect(
      evaluateMediaDexiePrimaryPromotionDecision({
        manualEvidence: blockedEvidence,
        explicitPromotionApproval: true,
        rollbackPlanConfirmed: true,
        localStorageFallbackPreserved: true,
        scopeExpandedBeyondProfileState: false,
      }),
    ).toMatchObject({
      status: "do-not-promote",
      blockers: ["manual-evidence-not-accepted"],
      inheritedEvidenceBlockers: ["manual-acceptance-not-passed"],
    });
  });

  it("refuses promotion when fallback is not preserved or scope expands", () => {
    expect(
      evaluateMediaDexiePrimaryPromotionDecision({
        manualEvidence: acceptedEvidence,
        explicitPromotionApproval: true,
        rollbackPlanConfirmed: true,
        localStorageFallbackPreserved: false,
        scopeExpandedBeyondProfileState: true,
      }),
    ).toMatchObject({
      status: "do-not-promote",
      blockers: [
        "localstorage-fallback-not-preserved",
        "promotion-scope-expanded",
      ],
    });
  });

  it("formats the decision for read-only UI display", () => {
    expect(
      formatMediaDexiePrimaryPromotionDecision(
        evaluateMediaDexiePrimaryPromotionDecision({
          manualEvidence: acceptedEvidence,
          explicitPromotionApproval: false,
          rollbackPlanConfirmed: false,
          localStorageFallbackPreserved: true,
          scopeExpandedBeyondProfileState: false,
        }),
      ),
    ).toBe("Do not promote");
  });
});
