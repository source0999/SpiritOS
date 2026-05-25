export type MediaIndexedDbBrowserRunNoteFieldId =
  | "browser-and-version"
  | "media-route-url"
  | "manual-report-status"
  | "runtime-read-source"
  | "profile-write-path"
  | "indexeddb-table-inspection"
  | "localstorage-fallback-check"
  | "skipped-entry-review"
  | "stop-condition-notes";

export type MediaIndexedDbBrowserRunNoteField = {
  id: MediaIndexedDbBrowserRunNoteFieldId;
  label: string;
  prompt: string;
  source: "manual-note" | "media-ui" | "browser-devtools";
  required: boolean;
};

export type MediaIndexedDbBrowserRunNotesTemplate = {
  title: "Browser IndexedDB Manual Run Notes";
  mode: "manual-notes-only";
  storage: "not-persisted";
  fields: MediaIndexedDbBrowserRunNoteField[];
  stopCriteria: string[];
};

export const mediaIndexedDbBrowserRunNotesTemplate: MediaIndexedDbBrowserRunNotesTemplate =
  {
    title: "Browser IndexedDB Manual Run Notes",
    mode: "manual-notes-only",
    storage: "not-persisted",
    fields: [
      {
        id: "browser-and-version",
        label: "Browser and version",
        prompt: "Record the browser used for the manual IndexedDB run.",
        source: "manual-note",
        required: true,
      },
      {
        id: "media-route-url",
        label: "Route URL",
        prompt: "Record the /media URL and confirm it loaded without route errors.",
        source: "manual-note",
        required: true,
      },
      {
        id: "manual-report-status",
        label: "Manual report",
        prompt: "Record the Manual IndexedDB acceptance harness status.",
        source: "media-ui",
        required: true,
      },
      {
        id: "runtime-read-source",
        label: "Runtime source",
        prompt: "Record whether the readiness summary reports Dexie or local fallback.",
        source: "media-ui",
        required: true,
      },
      {
        id: "profile-write-path",
        label: "Profile write path",
        prompt: "Record the latest profile-state side-write status after a local action.",
        source: "media-ui",
        required: true,
      },
      {
        id: "indexeddb-table-inspection",
        label: "IndexedDB tables",
        prompt: "Inspect SpiritMediaDB tables in DevTools and record any missing records.",
        source: "browser-devtools",
        required: true,
      },
      {
        id: "localstorage-fallback-check",
        label: "Fallback check",
        prompt: "Record that localStorage-backed state still renders after fallback testing.",
        source: "manual-note",
        required: true,
      },
      {
        id: "skipped-entry-review",
        label: "Skipped entries",
        prompt: "Record whether skipped migration entries were absent or reviewed.",
        source: "media-ui",
        required: true,
      },
      {
        id: "stop-condition-notes",
        label: "Stop conditions",
        prompt:
          "Record any condition that blocks promotion, including automation or server work pressure.",
        source: "manual-note",
        required: false,
      },
    ],
    stopCriteria: [
      "The run requires browser automation.",
      "The run requires fake IndexedDB dependencies.",
      "The run requires server, API, auth, scanner, manifest import, or media-serving work.",
      "localStorage fallback no longer renders the media page.",
      "Any skipped migration entry is not understood.",
    ],
  };

export function getRequiredMediaIndexedDbBrowserRunNoteFields(
  template: MediaIndexedDbBrowserRunNotesTemplate = mediaIndexedDbBrowserRunNotesTemplate,
): MediaIndexedDbBrowserRunNoteField[] {
  return template.fields.filter((field) => field.required);
}
