import { describe, expect, it } from "vitest";
import {
  cartographerMapApprovalTokenFields,
  cartographerMapAuthorityDenials,
  cartographerMapLiveStateFields,
  cartographerMapOperationalSections,
  cartographerMapOperatorQuestions,
  cartographerMapQueuePanelFields,
  cartographerMapReceiptEvidenceFields,
  cartographerMapStopControlFields,
  cartographerMapWorkflowPanelFields,
} from "../map-information-architecture";

describe("Cartographer map information architecture", () => {
  it("uses simple operational sections for Plan 7 Phase 1", () => {
    expect(cartographerMapOperationalSections.map((section) => section.id)).toEqual([
      "current-state",
      "approvals",
      "queue",
      "workflows",
      "receipts",
      "verify",
      "debug",
    ]);
  });

  it("keeps operator review questions visible", () => {
    expect(cartographerMapOperatorQuestions).toContain("What is Cartographer doing?");
    expect(cartographerMapOperatorQuestions).toContain("What is blocked?");
    expect(cartographerMapOperatorQuestions).toContain("What is approved?");
    expect(cartographerMapOperatorQuestions).toContain("What ran?");
    expect(cartographerMapOperatorQuestions).toContain("What does Britton need to verify?");
  });

  it("locks the Plan 7 Phase 2 live state panel fields", () => {
    expect(cartographerMapLiveStateFields).toEqual([
      "Branch",
      "HEAD",
      "Dirty state",
      "Protected-lane state",
      "Recommendation",
    ]);
  });

  it("locks the Plan 7 Phase 3 approval token panel fields", () => {
    expect(cartographerMapApprovalTokenFields).toEqual([
      "Runtime status",
      "Validation status",
      "Consumption preview",
      "Blocked reasons",
      "Safe next action",
    ]);
  });

  it("locks the Plan 7 Phase 4 queue panel fields", () => {
    expect(cartographerMapQueuePanelFields).toEqual([
      "Queue status",
      "Run-next status",
      "One-task selection",
      "Execution blocked",
      "Safe next action",
    ]);
  });

  it("locks the Plan 7 Phase 5 workflow run panel fields", () => {
    expect(cartographerMapWorkflowPanelFields).toEqual([
      "Active runs",
      "Recent runs",
      "Workflow status",
      "Step status",
      "Blocked reasons",
    ]);
  });

  it("locks the Plan 7 Phase 6 kill switch and stop control fields", () => {
    expect(cartographerMapStopControlFields).toEqual([
      "Kill switch state",
      "Pause control",
      "Cancel control",
      "Timeout control",
      "Retry control",
    ]);
  });

  it("locks the Plan 7 Phase 7 receipt and evidence browser fields", () => {
    expect(cartographerMapReceiptEvidenceFields).toEqual([
      "Receipt journal",
      "Evidence artifacts",
      "Approved docs paths",
      "Missing evidence",
      "Write blocked",
    ]);
  });

  it("does not present authority-granting dashboard actions", () => {
    expect(cartographerMapAuthorityDenials).toContain("No approval minting");
    expect(cartographerMapAuthorityDenials).toContain("No self-approval");
    expect(cartographerMapAuthorityDenials).toContain("No source writes");
    expect(cartographerMapAuthorityDenials).toContain("No command execution");
    expect(cartographerMapAuthorityDenials).toContain(
      "No commit, push, branch, checkout, reset, clean, or stash",
    );
  });
});
