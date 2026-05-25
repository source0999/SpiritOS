import { describe, expect, it } from "vitest";

import { mediaIndexedDbAcceptanceRunbook } from "@/lib/media/media-indexeddb-acceptance-runbook";

describe("mediaIndexedDbAcceptanceRunbook", () => {
  it("defines a manual browser-only acceptance scope", () => {
    expect(mediaIndexedDbAcceptanceRunbook).toMatchObject({
      title: "Browser IndexedDB Acceptance Runbook",
      mode: "manual-browser-only",
      scope: {
        automation: "not-included",
        primaryProfileState: "not-enabled",
        localStorageFallback: "must-remain",
      },
    });
  });

  it("covers manual setup, harness run, IndexedDB inspection, and fallback verification", () => {
    expect(mediaIndexedDbAcceptanceRunbook.steps.map((step) => step.id)).toEqual([
      "open-media",
      "seed-local-state",
      "run-manual-panel",
      "inspect-indexeddb",
      "verify-fallback",
    ]);
  });

  it("keeps primary profile-state gated behind browser evidence", () => {
    expect(mediaIndexedDbAcceptanceRunbook.passCriteria).toEqual(
      expect.arrayContaining([
        "Manual report status is Passed.",
        "Runtime read source can report Dexie in the browser after seeding.",
        "Latest profile write path can report Dexie written after a user action.",
        "Primary profile-state readiness can become Ready only after the other evidence is true.",
        "localStorage fallback remains available.",
      ]),
    );
  });

  it("stops if the path requires automation, server code, or media serving", () => {
    expect(mediaIndexedDbAcceptanceRunbook.stopCriteria).toContain(
      "The test requires browser automation, fake IndexedDB, API routes, server DB, or media-serving code.",
    );
  });
});
