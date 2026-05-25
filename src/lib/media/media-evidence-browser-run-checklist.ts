export type MediaEvidenceBrowserRunChecklistItemId =
  | "open-media-browser"
  | "create-local-state"
  | "run-manual-indexeddb-check"
  | "inspect-devtools"
  | "verify-localstorage-fallback"
  | "review-evidence-panels"
  | "fill-manual-copy-template"
  | "record-archive-location"
  | "confirm-blocked-work";

export type MediaEvidenceBrowserRunChecklistItem = {
  id: MediaEvidenceBrowserRunChecklistItemId;
  label: string;
  detail: string;
  required: true;
};

export type MediaEvidenceBrowserRunChecklist = {
  title: "Evidence Packet Browser Manual Run Checklist";
  mode: "manual-browser-only";
  storage: "not-persisted";
  items: MediaEvidenceBrowserRunChecklistItem[];
  stopCriteria: string[];
};

export const mediaEvidenceBrowserRunChecklist: MediaEvidenceBrowserRunChecklist =
  {
    title: "Evidence Packet Browser Manual Run Checklist",
    mode: "manual-browser-only",
    storage: "not-persisted",
    items: [
      {
        id: "open-media-browser",
        label: "Open /media in a real browser",
        detail:
          "Use the real browser surface so IndexedDB, localStorage, and DevTools evidence are all browser-native.",
        required: true,
      },
      {
        id: "create-local-state",
        label: "Create local sample state",
        detail:
          "Add a Watchlist item, save curation evidence, and record playback acceptance for one profile.",
        required: true,
      },
      {
        id: "run-manual-indexeddb-check",
        label: "Run manual IndexedDB check",
        detail:
          "Use only the explicit on-page manual harness control; no automatic migration runs on page load.",
        required: true,
      },
      {
        id: "inspect-devtools",
        label: "Inspect DevTools SpiritMediaDB tables",
        detail:
          "Confirm seeded metadata and migrated profile-state records directly in browser DevTools.",
        required: true,
      },
      {
        id: "verify-localstorage-fallback",
        label: "Verify localStorage fallback",
        detail:
          "Confirm localStorage profile state remains intact and remains the primary state source.",
        required: true,
      },
      {
        id: "review-evidence-panels",
        label: "Review read-only evidence panels",
        detail:
          "Check manual evidence, promotion, archive, export, and readiness panels without accepting a primary-state flip.",
        required: true,
      },
      {
        id: "fill-manual-copy-template",
        label: "Fill manual copy template",
        detail:
          "Transcribe the on-page packet template outside the app; the app does not copy, download, or export it.",
        required: true,
      },
      {
        id: "record-archive-location",
        label: "Record archive location",
        detail:
          "Write down where the externally maintained evidence packet lives without storing that location in the app.",
        required: true,
      },
      {
        id: "confirm-blocked-work",
        label: "Confirm no media binaries or blocked work",
        detail:
          "Stop if the run would require media binaries, browser automation, server export, app file writes, or Dexie primary promotion.",
        required: true,
      },
    ],
    stopCriteria: [
      "Browser automation",
      "Fake IndexedDB",
      "Clipboard writes",
      "Browser downloads",
      "App file writes",
      "Server export or upload",
      "Persisted archive storage",
      "Media binaries",
      "Dexie primary profile-state promotion",
      "Automatic migration on /media load",
      "localStorage fallback removal",
    ],
  };

export function getRequiredMediaEvidenceBrowserRunChecklistItemIds(
  checklist: MediaEvidenceBrowserRunChecklist = mediaEvidenceBrowserRunChecklist,
): MediaEvidenceBrowserRunChecklistItemId[] {
  return checklist.items.map((item) => item.id);
}
