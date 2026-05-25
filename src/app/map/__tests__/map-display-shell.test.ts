import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const simplePageSource = () =>
  readFileSync(resolve(process.cwd(), "src/app/map/page.tsx"), "utf8");

const rawPageSource = () =>
  readFileSync(resolve(process.cwd(), "src/app/map/raw/page.tsx"), "utf8");

describe("Cartographer simple controller shell", () => {
  it("renders the simplified controller language for /map", () => {
    const src = simplePageSource();

    expect(src).toContain("Cartographer");
    expect(src).toContain(
      "Command center for repo status, blockers, dirty groups, and safe next steps.",
    );
    expect(src).toContain("Cartographer status strip");
    expect(src).toContain("Cartographer status");
    expect(src).toContain("Short hash");
    expect(src).toContain("Dirty count");
    expect(src).toContain("Protected warnings");
    expect(src).toContain("Can Cartographer act?");
    expect(src).toContain("What Britton does next");
    expect(src).toContain("Open manual check");
    expect(src).toContain("Evidence links");
    expect(src).toContain("truthEvidenceLinks.length");
    expect(src).toContain("review-only link(s)");
    expect(src).toContain("No truth-packet evidence links reported.");
    expect(src).toContain("getCartographerReceiptEvidenceStatus");
    expect(src).toContain("Receipt browser");
    expect(src).toContain("visibleReceiptItems.length");
    expect(src).toContain("No receipt/evidence items are visible.");
    expect(src).toContain("This browser does not");
    expect(src).toContain("Control cards");
    expect(src).toContain("disabled until scoped token authority exists");
    expect(src).toContain("Show detailed diagnostics and proof");
    expect(src).toContain("Truth Packet");
    expect(src).toContain("Packet status");
    expect(src).toContain("Decision default");
    expect(src).toContain("Unknown fields");
    expect(src).toContain("Stale fields");
    expect(src).toContain("Blockers");
    expect(src).toContain("Approval missing");
    expect(src).toContain("Lane Ownership");
    expect(src).toContain("Active lane");
    expect(src).toContain("Registry state");
    expect(src).toContain("Conflict state");
    expect(src).toContain("Allowed paths");
    expect(src).toContain("Forbidden paths");
    expect(src).toContain("Protected zones");
    expect(src).toContain("Ownership blocked actions");
    expect(src).toContain("blocked until dirty overlaps are clear");
    expect(src).toContain("Approval Gate");
    expect(src).toContain("Approval status");
    expect(src).toContain("Validation");
    expect(src).toContain("Consumption preview");
    expect(src).toContain("Event preview");
    expect(src).toContain("Self-approval");
    expect(src).toContain("Approval lane");
    expect(src).toContain("Single action");
    expect(src).toContain("Human issued");
    expect(src).toContain("Reason codes");
    expect(src).toContain("Queue/action blocked");
    expect(src).toContain("Kill switch status");
    expect(src).toContain("Dirty Tree Groups");
    expect(src).toContain("Commit And Push Readiness");
    expect(src).toContain("Project Tracker");
    expect(src).toContain("Daily Driver Proof");
    expect(src).toContain("Daily-driver checklist");
    expect(src).toContain("10 supervised safe-task receipts require approval");
    expect(src).toContain("24-hour and 72-hour soak samples record drift");
    expect(src).toContain("Promotion decision remains a human record only");
    expect(src).toContain("Passing proof does not create full auto");
    expect(src).toContain("Trust Tier Gate");
    expect(src).toContain("Current tier");
    expect(src).toContain("tier-1");
    expect(src).toContain("Next decision gate");
    expect(src).toContain("Plan 10/10 trust-tier decision packet");
    expect(src).toContain("Blocked authorities");
    expect(src).toContain("advance, hold, or demote");
    expect(src).toContain("Advisory Fleet");
    expect(src).toContain("Manual Check");
    expect(src).toContain("Next safe step");
  });

  it("keeps the advisory helper fleet compact without helper execution controls", () => {
    const src = simplePageSource();

    [
      "Component Mapper",
      "Safety Reviewer",
      "Test Scribe",
      "Change Scribe",
      "Runbook Scribe",
      "Blueprint Scribe",
      "Commit Scribe",
      "Release Steward",
    ].forEach((helperName) => {
      expect(src).toContain(helperName);
    });
    expect(src).toContain("<details");
    expect(src).not.toContain("<details open");
    expect(src).toContain("Show advisory helper summaries");
    expect(src).toContain("advisory_only");
    expect(src).toContain("Watching:");
    expect(src).toContain("Blocked:");
    expect(src).toContain("cannot");
    expect(src).toContain("mutate state, start workers, run queues, call providers");
    expect(src).not.toContain("Start helper");
    expect(src).not.toContain("Run helper");
    expect(src).not.toContain("Apply helper");
    expect(src).not.toContain("Start worker");
    expect(src).not.toContain("Run queue");
  });

  it("keeps /map in NO-GO, read-only, review-only state", () => {
    const src = simplePageSource();

    expect(src).toContain("NO-GO");
    expect(src).toContain("Read-only");
    expect(src).toContain(">No<");
    expect(src).toContain(
      "Cartographer is review-only. It can show what it sees, but cannot change files,",
    );
    expect(src).toContain(
      "Real operator actions still need a separate plan and explicit approval.",
    );
    expect(src).toContain("Unknown or stale packet fields keep /map at NO-GO.");
    expect(src).toContain("Clear facts still do not");
    expect(src).toContain(
      "grant apply, commit, push, queue, approval, or worker authority.",
    );
    expect(src).toContain("validation only, no execution approval");
    expect(src).toContain("automatic tier advancement");
    expect(src).toContain("full auto");
    expect(src).toContain("push promotion");
    expect(src).toContain(
      "Missing, invalid, stale, or self-approved",
    );
    expect(src).toContain("lane-scoped");
    expect(src).toContain("single-action");
    expect(src).toContain("human-issued");
    expect(src).toContain(
      "valid preview still grants no apply, commit, push, queue,",
    );
    expect(src).toContain("Lane ownership is display-only");
    expect(src).toContain("Lock proposals cannot acquire locks");
    expect(src).toContain("No lock acquisition");
    expect(src).toContain("No lock release");
    expect(src).toContain("No active-lane mutation");
    expect(src).toContain("No worker dispatch");
    expect(src).toContain("No filesystem enforcement");
    expect(src).toContain("Verification Runner");
    expect(src).toContain("exact argv allowlist");
    expect(src).toContain("pass/fail summaries required");
    expect(src).toContain("shell strings and metacharacters");
    expect(src).toContain("Verification status is display-only on /map");
    expect(src).toContain("Queue And Workflow Runtime");
    expect(src).toContain("Queue status");
    expect(src).toContain("Run-next");
    expect(src).toContain("One task");
    expect(src).toContain("Workflow status");
    expect(src).toContain("Stop controls");
    expect(src).toContain("Queue and workflow state is display-only");
    expect(src).toContain("cannot run queues, resume work, start background loops");
    expect(src).toContain("Worker Control");
    expect(src).toContain("Required identity fields");
    expect(src).toContain("Worker blocked actions");
    expect(src).toContain("exact non-overlapping zones only");
    expect(src).toContain("operator review required");
    expect(src).toContain("Worker state is display-only on /map");
    expect(src).toContain("Cartographer-visible queue state before");
    expect(src).toContain("Cartographer Integrated Control Master Plan 9/10");
    expect(src).toContain("Commit gate");
    expect(src).toContain("exact human-approved local commit only");
    expect(src).toContain("Staging");
    expect(src).toContain("exact file list only");
    expect(src).toContain("Branch/worktree");
    expect(src).toContain("proposal-only");
    expect(src).toContain("Push boundary");
    expect(src).toContain("dedicated branch, exact sha, human approval required");
    expect(src).toContain("Auto push");
    expect(src).toContain("blocked pending later promotion");
    expect(src).toContain("Rollback");
    expect(src).toContain("git revert guidance required");
    expect(src).toContain("Git operator blocked actions");
    expect(src).toContain("git add .");
    expect(src).toContain("force push");
    expect(src).toContain("push to main/master/trunk");
    expect(src).toContain("Commit, push, branch, worktree, and rollback state is display-only");
    expect(src).toContain("do not grant broad staging");
  });

  it("shows approval gate status and reason codes without authority controls", () => {
    const src = simplePageSource();

    expect(src).toContain("approvalTokenStatus.approvalState");
    expect(src).toContain("approvalTokenStatus.validationStatus");
    expect(src).toContain("approvalTokenStatus.consumptionStatus");
    expect(src).toContain("approvalTokenStatus.eventPreviewType");
    expect(src).toContain("approvalTokenStatus.selfApprovalBlocked");
    expect(src).toContain("approvalTokenStatus.laneId");
    expect(src).toContain("approvalTokenStatus.singleAction");
    expect(src).toContain("approvalTokenStatus.issuedByHuman");
    expect(src).toContain("approvalReasonCodes");
    expect(src).toContain("No approval reason codes reported");
    expect(src).not.toContain("Mint approval");
    expect(src).not.toContain("Approve token");
    expect(src).not.toContain("Consume approval");
    expect(src).not.toContain("Execute approval");
  });

  it("uses the shared route shell and nav without a route-owned desktop rail slab", () => {
    const src = simplePageSource();

    expect(src).toContain("dashboard-demo-v4-route-shell-map");
    expect(src).toContain("dashboard-demo-v4-route-main");
    expect(src).toContain("DashboardDemoV4FloatingNav");
    expect(src).toContain("--shell-mobile-bottom-reserved-height");
    expect(src).toContain("max-w-[92rem]");
    expect(src).toContain(
      "xl:grid-cols-[minmax(0,0.72fr)_minmax(0,0.8fr)_minmax(0,1.2fr)]",
    );
    expect(src).toContain(
      "xl:grid-cols-[minmax(0,1.14fr)_minmax(0,0.86fr)]",
    );
    expect(src).toContain(
      "xl:grid-cols-[minmax(0,1.12fr)_minmax(0,0.88fr)]",
    );
    expect(src).not.toContain("fixed inset-y-0 left-0");
    expect(src).not.toContain("md:pl-[14rem]");
  });

  it("has no POST/action controls on /map", () => {
    const src = simplePageSource();

    expect(src).not.toMatch(new RegExp("<" + "button\\b"));
    expect(src).not.toMatch(/<form\b/);
    expect(src).not.toContain("on" + "Click=");
    expect(src).not.toContain("on" + "Submit=");
    expect(src).not.toContain("method: " + '"POST"');
    expect(src).not.toContain("method: " + "'POST'");
    expect(src).not.toContain("apply" + "-approved");
    expect(src).not.toContain("execute-approved");
    expect(src).not.toContain("Acquire lock");
    expect(src).not.toContain("Release lock");
    expect(src).not.toContain("Change active lane");
    expect(src).not.toContain("Enforce lock");
    expect(src).not.toContain("Run verification");
    expect(src).not.toContain("Execute command");
    expect(src).not.toContain("/verification/run\",");
    expect(src).not.toContain("Start queue");
    expect(src).not.toContain("Run next task");
    expect(src).not.toContain("Resume workflow");
    expect(src).not.toContain("Cancel workflow");
    expect(src).not.toContain("Start worker");
    expect(src).not.toContain("Dispatch worker");
    expect(src).not.toContain("Create worktree");
    expect(src).not.toContain("Commit changes");
    expect(src).not.toContain("Push branch");
    expect(src).not.toContain("Create branch");
    expect(src).not.toContain("Run rollback");
  });

  it("keeps only safe navigation links and one manual command block", () => {
    const src = simplePageSource();

    expect(src).toContain("Open raw diagnostics");
    expect(src).toContain("Open raw dirty details");
    expect(src).toContain("Review blockers");
    expect(src).toContain("Preview next step");
    expect(src).not.toContain("Copy manual check");
    expect(src).not.toContain("Refresh page");
    expect(src).not.toContain("Preview cleanup plan");
    expect(src).not.toContain("Copy manual commit checklist");
    expect(src).not.toContain("Copy branch check commands");
    expect(src).not.toContain("Copy push preflight checklist");
    expect(src).not.toContain("View project details");
    expect(src.match(/<CommandBlock value=\{manualCheck\}/g)).toHaveLength(1);
    expect(src).toContain("href=\"/map/raw\"");
    expect(src).toContain("href=\"#attention\"");
    expect(src).toContain("href=\"#next-safe-step\"");
  });

  it("keeps fallback behavior visible on /map", () => {
    const src = simplePageSource();

    expect(src).toContain("getReadOnlyMapData(origin)");
    expect(src).toContain("getCartographerLiveState(origin)");
    expect(src).toContain("safe fallback view");
    expect(src).toContain("fallback is showing");
  });
});

describe("Cartographer raw backend diagnostic shell", () => {
  it("renders the raw backend diagnostic language at /map/raw", () => {
    const src = rawPageSource();

    expect(src).toContain("Raw backend view");
    expect(src).toContain("Back to simple controller");
    expect(src).toContain("Live Read-Only Packet");
    expect(src).toContain("Read-Only Sources");
    expect(src).toContain("Trust / Audit Summary");
    expect(src).toContain("Authority Boundary Audit");
    expect(src).toContain("Advanced safety/debug");
  });

  it("preserves read-only diagnostics on /map/raw", () => {
    const src = rawPageSource();

    expect(src).toContain("Six endpoint status");
    expect(src).toContain("Endpoint");
    expect(src).toContain("Diagnostics");
    expect(src).toContain("HTTP");
    expect(src).toContain("risky read-only");
    expect(src).toContain("Approval/Token State");
    expect(src).toContain("Queue/Workflow State");
    expect(src).toContain("Evidence/Receipts");
    expect(src).toContain("Manual Checks");
  });

  it("keeps fallback behavior visible on /map/raw", () => {
    const src = rawPageSource();

    expect(src).toContain("Live Cartographer data is unavailable");
    expect(src).toContain("fallbackEndpointCount");
    expect(src).toContain("fallbackProof");
    expect(src).toContain("Showing safe fallback");
  });
});
