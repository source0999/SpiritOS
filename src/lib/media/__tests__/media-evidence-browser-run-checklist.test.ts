import { describe, expect, it } from "vitest";

import {
  getRequiredMediaEvidenceBrowserRunChecklistItemIds,
  mediaEvidenceBrowserRunChecklist,
} from "@/lib/media/media-evidence-browser-run-checklist";

describe("mediaEvidenceBrowserRunChecklist", () => {
  it("defines a manual browser-only checklist that is not persisted by the app", () => {
    expect(mediaEvidenceBrowserRunChecklist).toMatchObject({
      title: "Evidence Packet Browser Manual Run Checklist",
      mode: "manual-browser-only",
      storage: "not-persisted",
    });
  });

  it("keeps the browser run checklist items in stable order", () => {
    expect(getRequiredMediaEvidenceBrowserRunChecklistItemIds()).toEqual([
      "open-media-browser",
      "create-local-state",
      "run-manual-indexeddb-check",
      "inspect-devtools",
      "verify-localstorage-fallback",
      "review-evidence-panels",
      "fill-manual-copy-template",
      "record-archive-location",
      "confirm-blocked-work",
    ]);
  });

  it("requires DevTools, fallback, copy template, and archive-location checks", () => {
    expect(mediaEvidenceBrowserRunChecklist.items).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "inspect-devtools",
          detail:
            "Confirm seeded metadata and migrated profile-state records directly in browser DevTools.",
        }),
        expect.objectContaining({
          id: "verify-localstorage-fallback",
          detail:
            "Confirm localStorage profile state remains intact and remains the primary state source.",
        }),
        expect.objectContaining({
          id: "fill-manual-copy-template",
          detail:
            "Transcribe the on-page packet template outside the app; the app does not copy, download, or export it.",
        }),
        expect.objectContaining({
          id: "record-archive-location",
          detail:
            "Write down where the externally maintained evidence packet lives without storing that location in the app.",
        }),
      ]),
    );
  });

  it("blocks automation, exports, file writes, primary promotion, and media binaries", () => {
    expect(mediaEvidenceBrowserRunChecklist.stopCriteria).toEqual(
      expect.arrayContaining([
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
      ]),
    );
  });
});
