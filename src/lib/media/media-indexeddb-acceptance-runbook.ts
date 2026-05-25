export type MediaIndexedDbAcceptanceRunbookStep = {
  id: string;
  title: string;
  action: string;
  expectedEvidence: string;
};

export type MediaIndexedDbAcceptanceRunbook = {
  title: "Browser IndexedDB Acceptance Runbook";
  mode: "manual-browser-only";
  scope: {
    automation: "not-included";
    primaryProfileState: "not-enabled";
    localStorageFallback: "must-remain";
  };
  steps: MediaIndexedDbAcceptanceRunbookStep[];
  passCriteria: string[];
  stopCriteria: string[];
};

export const mediaIndexedDbAcceptanceRunbook: MediaIndexedDbAcceptanceRunbook = {
  title: "Browser IndexedDB Acceptance Runbook",
  mode: "manual-browser-only",
  scope: {
    automation: "not-included",
    primaryProfileState: "not-enabled",
    localStorageFallback: "must-remain",
  },
  steps: [
    {
      id: "open-media",
      title: "Open the media route",
      action: "Open /media in a real browser with IndexedDB enabled.",
      expectedEvidence:
        "The page renders, shows Runtime read source, and keeps localStorage fallback available.",
    },
    {
      id: "seed-local-state",
      title: "Create representative local profile state",
      action:
        "Add Local Lights to Watchlist, save one curation check, and record playback acceptance for one profile.",
      expectedEvidence:
        "Continue Watching, Watchlist, curation, and playback evidence remain profile-local.",
    },
    {
      id: "run-manual-panel",
      title: "Run the manual IndexedDB check",
      action: "Click Run Manual IndexedDB Check in the /media manual harness panel.",
      expectedEvidence:
        "The manual report returns Passed, or any Blocked state lists skipped entries for review.",
    },
    {
      id: "inspect-indexeddb",
      title: "Inspect browser IndexedDB",
      action:
        "Use browser DevTools to inspect SpiritMediaDB tables for metadata seed and migrated profile-state records.",
      expectedEvidence:
        "Catalog metadata and profile-state tables contain the expected records without committed media binaries.",
    },
    {
      id: "verify-fallback",
      title: "Verify fallback preservation",
      action:
        "Refresh the page and confirm localStorage-backed state still renders if IndexedDB is cleared or unavailable.",
      expectedEvidence:
        "The page remains usable and reports the local fallback/readiness state instead of failing.",
    },
  ],
  passCriteria: [
    "Manual report status is Passed.",
    "No skipped migration entries remain unreviewed.",
    "Runtime read source can report Dexie in the browser after seeding.",
    "Latest profile write path can report Dexie written after a user action.",
    "Primary profile-state readiness can become Ready only after the other evidence is true.",
    "localStorage fallback remains available.",
  ],
  stopCriteria: [
    "Manual report status is Blocked.",
    "Any skipped migration entry is not understood.",
    "IndexedDB seed or profile-state records are missing after the manual run.",
    "localStorage fallback no longer renders the media page.",
    "The test requires browser automation, fake IndexedDB, API routes, server DB, or media-serving code.",
  ],
};
