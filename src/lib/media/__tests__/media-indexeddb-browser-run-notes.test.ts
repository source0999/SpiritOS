import { describe, expect, it } from "vitest";

import {
  getRequiredMediaIndexedDbBrowserRunNoteFields,
  mediaIndexedDbBrowserRunNotesTemplate,
} from "@/lib/media/media-indexeddb-browser-run-notes";

describe("mediaIndexedDbBrowserRunNotesTemplate", () => {
  it("defines manual notes that are not persisted by the app", () => {
    expect(mediaIndexedDbBrowserRunNotesTemplate).toMatchObject({
      title: "Browser IndexedDB Manual Run Notes",
      mode: "manual-notes-only",
      storage: "not-persisted",
    });
  });

  it("captures the browser run evidence needed before a primary-state decision", () => {
    expect(mediaIndexedDbBrowserRunNotesTemplate.fields.map((field) => field.id)).toEqual([
      "browser-and-version",
      "media-route-url",
      "manual-report-status",
      "runtime-read-source",
      "profile-write-path",
      "indexeddb-table-inspection",
      "localstorage-fallback-check",
      "skipped-entry-review",
      "stop-condition-notes",
    ]);
  });

  it("marks every required evidence field except optional stop-condition notes", () => {
    expect(
      getRequiredMediaIndexedDbBrowserRunNoteFields().map((field) => field.id),
    ).toEqual([
      "browser-and-version",
      "media-route-url",
      "manual-report-status",
      "runtime-read-source",
      "profile-write-path",
      "indexeddb-table-inspection",
      "localstorage-fallback-check",
      "skipped-entry-review",
    ]);
  });

  it("keeps automation, fake IndexedDB, server work, and fallback loss as stop criteria", () => {
    expect(mediaIndexedDbBrowserRunNotesTemplate.stopCriteria).toEqual(
      expect.arrayContaining([
        "The run requires browser automation.",
        "The run requires fake IndexedDB dependencies.",
        "The run requires server, API, auth, scanner, manifest import, or media-serving work.",
        "localStorage fallback no longer renders the media page.",
      ]),
    );
  });
});
