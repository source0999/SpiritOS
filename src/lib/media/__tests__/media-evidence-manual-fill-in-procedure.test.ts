import { describe, expect, it } from "vitest";

import {
  getRequiredMediaEvidenceManualFillInStepIds,
  mediaEvidenceManualFillInProcedure,
} from "@/lib/media/media-evidence-manual-fill-in-procedure";

describe("mediaEvidenceManualFillInProcedure", () => {
  it("defines a manual browser-only procedure that is not persisted by the app", () => {
    expect(mediaEvidenceManualFillInProcedure).toMatchObject({
      title: "Evidence Packet Manual Browser Fill-In Procedure",
      mode: "manual-browser-only",
      storage: "not-persisted",
    });
  });

  it("keeps the required fill-in steps in stable order", () => {
    expect(getRequiredMediaEvidenceManualFillInStepIds()).toEqual([
      "prepare-browser",
      "run-indexeddb-check",
      "inspect-devtools",
      "fill-copy-template",
      "review-blockers",
      "record-location",
    ]);
  });

  it("requires DevTools inspection and manual copy template transcription", () => {
    expect(mediaEvidenceManualFillInProcedure.steps).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "inspect-devtools",
          expectedResult:
            "The human can fill in table inspection notes without attaching media binaries.",
        }),
        expect.objectContaining({
          id: "fill-copy-template",
          expectedResult:
            "Manual evidence, promotion decision, archive packet, and export decision statuses are transcribed.",
        }),
      ]),
    );
  });

  it("blocks automation, persistence, exports, primary promotion, and media binaries", () => {
    expect(mediaEvidenceManualFillInProcedure.blockedWork).toEqual(
      expect.arrayContaining([
        "Clipboard writes",
        "Browser downloads",
        "App file writes",
        "Persisted archive storage",
        "Server export or upload",
        "Browser automation",
        "Dexie primary profile-state promotion",
        "Media binaries",
      ]),
    );
  });
});
