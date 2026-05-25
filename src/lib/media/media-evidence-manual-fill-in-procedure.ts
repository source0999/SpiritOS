export type MediaEvidenceManualFillInStepId =
  | "prepare-browser"
  | "run-indexeddb-check"
  | "inspect-devtools"
  | "fill-copy-template"
  | "review-blockers"
  | "record-location";

export type MediaEvidenceManualFillInStep = {
  id: MediaEvidenceManualFillInStepId;
  title: string;
  action: string;
  expectedResult: string;
};

export type MediaEvidenceManualFillInProcedure = {
  title: "Evidence Packet Manual Browser Fill-In Procedure";
  mode: "manual-browser-only";
  storage: "not-persisted";
  steps: MediaEvidenceManualFillInStep[];
  blockedWork: string[];
};

export const mediaEvidenceManualFillInProcedure: MediaEvidenceManualFillInProcedure =
  {
    title: "Evidence Packet Manual Browser Fill-In Procedure",
    mode: "manual-browser-only",
    storage: "not-persisted",
    steps: [
      {
        id: "prepare-browser",
        title: "Prepare browser state",
        action:
          "Open /media in a real browser and create representative local profile state.",
        expectedResult:
          "Watchlist, curation, playback evidence, and fallback state are visible.",
      },
      {
        id: "run-indexeddb-check",
        title: "Run manual IndexedDB check",
        action: "Use the explicit Manual IndexedDB acceptance harness button.",
        expectedResult:
          "The manual report status is visible and any skipped entries are known.",
      },
      {
        id: "inspect-devtools",
        title: "Inspect DevTools tables",
        action:
          "Open browser DevTools and inspect SpiritMediaDB metadata and profile-state tables.",
        expectedResult:
          "The human can fill in table inspection notes without attaching media binaries.",
      },
      {
        id: "fill-copy-template",
        title: "Fill copy template",
        action:
          "Use the on-page manual copy template as a source for the evidence packet.",
        expectedResult:
          "Manual evidence, promotion decision, archive packet, and export decision statuses are transcribed.",
      },
      {
        id: "review-blockers",
        title: "Review blockers",
        action:
          "Record unresolved blockers before any future storage promotion or export plan.",
        expectedResult:
          "Blocked work remains explicit and no hidden promotion is implied.",
      },
      {
        id: "record-location",
        title: "Record archive location",
        action:
          "Record where the manually filled packet lives outside the app.",
        expectedResult:
          "The app still does not write, download, upload, or persist the packet.",
      },
    ],
    blockedWork: [
      "Clipboard writes",
      "Browser downloads",
      "App file writes",
      "Persisted archive storage",
      "Server export or upload",
      "Browser automation",
      "Fake IndexedDB",
      "Dexie primary profile-state promotion",
      "Automatic migration on /media load",
      "localStorage key deletion",
      "Media binaries",
    ],
  };

export function getRequiredMediaEvidenceManualFillInStepIds(
  procedure: MediaEvidenceManualFillInProcedure = mediaEvidenceManualFillInProcedure,
): MediaEvidenceManualFillInStepId[] {
  return procedure.steps.map((step) => step.id);
}
