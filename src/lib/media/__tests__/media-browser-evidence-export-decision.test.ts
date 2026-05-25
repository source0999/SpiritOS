import { describe, expect, it } from "vitest";

import type { MediaBrowserEvidenceArchivePacket } from "@/lib/media/media-browser-evidence-archive-packet";
import {
  evaluateMediaBrowserEvidenceExportDecision,
  formatMediaBrowserEvidenceExportDecision,
} from "@/lib/media/media-browser-evidence-export-decision";

const readyArchivePacket: MediaBrowserEvidenceArchivePacket = {
  source: "media-browser-evidence-archive-packet",
  status: "ready",
  blockers: [],
  includes: {
    manualEvidenceStatus: "blocked",
    promotionDecisionStatus: "do-not-promote",
    browserRunNotes: true,
    archiveLocation: true,
    localOnlyScope: true,
    mediaBinaries: "excluded",
  },
};

describe("evaluateMediaBrowserEvidenceExportDecision", () => {
  it("allows manual export only when packet, approval, location, and no-binary rules are clean", () => {
    expect(
      evaluateMediaBrowserEvidenceExportDecision({
        archivePacket: readyArchivePacket,
        manualExportApproval: true,
        exportLocationSelected: true,
        mediaBinariesExcluded: true,
        appFileWriteRequested: false,
        serverExportRequested: false,
      }),
    ).toEqual({
      source: "media-browser-evidence-export-decision",
      status: "export-ready",
      blockers: [],
      archivePacketStatus: "ready",
    });
  });

  it("blocks export while the archive packet is still draft", () => {
    expect(
      evaluateMediaBrowserEvidenceExportDecision({
        archivePacket: {
          ...readyArchivePacket,
          status: "draft",
          blockers: ["browser-run-notes-not-captured"],
        },
        manualExportApproval: true,
        exportLocationSelected: true,
        mediaBinariesExcluded: true,
        appFileWriteRequested: false,
        serverExportRequested: false,
      }),
    ).toMatchObject({
      status: "do-not-export",
      blockers: ["archive-packet-not-ready"],
      archivePacketStatus: "draft",
    });
  });

  it("blocks export by default without manual approval or location", () => {
    expect(
      evaluateMediaBrowserEvidenceExportDecision({
        archivePacket: readyArchivePacket,
        manualExportApproval: false,
        exportLocationSelected: false,
        mediaBinariesExcluded: true,
        appFileWriteRequested: false,
        serverExportRequested: false,
      }),
    ).toMatchObject({
      status: "do-not-export",
      blockers: [
        "manual-export-approval-missing",
        "export-location-not-selected",
      ],
    });
  });

  it("blocks app file writes, server export, or media binary inclusion", () => {
    expect(
      evaluateMediaBrowserEvidenceExportDecision({
        archivePacket: readyArchivePacket,
        manualExportApproval: true,
        exportLocationSelected: true,
        mediaBinariesExcluded: false,
        appFileWriteRequested: true,
        serverExportRequested: true,
      }),
    ).toMatchObject({
      status: "do-not-export",
      blockers: [
        "media-binaries-not-excluded",
        "app-file-write-requested",
        "server-export-requested",
      ],
    });
  });

  it("formats export decisions for read-only UI", () => {
    expect(
      formatMediaBrowserEvidenceExportDecision(
        evaluateMediaBrowserEvidenceExportDecision({
          archivePacket: readyArchivePacket,
          manualExportApproval: false,
          exportLocationSelected: false,
          mediaBinariesExcluded: true,
          appFileWriteRequested: false,
          serverExportRequested: false,
        }),
      ),
    ).toBe("Do not export");
  });
});
