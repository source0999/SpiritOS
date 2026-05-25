export type CodingAlertKind =
  | "done"
  | "blocked"
  | "needs-review"
  | "waiting-for-approval"
  | "failed"
  | "browser-title-badge"
  | "desktop-notification-gate"
  | "background-autonomy-gate";

export type CodingAlertState = "active" | "waiting" | "gated" | "unavailable";

export type CodingAlertRow = {
  authority: string;
  cooldown: string;
  display: string;
  evidence: string;
  id: CodingAlertKind;
  state: CodingAlertState;
  title: string;
  trigger: string;
};

export type CodingAlertInput = {
  activeRunState: "idle" | "queued" | "running" | "blocked" | "complete" | "failed";
  canApprovePreview: boolean;
  canMarkPreviewReviewed: boolean;
  closeoutBlockersText: string;
  previewAlreadySatisfied: boolean;
  previewStatus: "idle" | "loading" | "ready" | "blocked" | "error";
  receiptReadinessText: string;
  safeNextAction: string;
  verificationStatus: "not_started" | "required" | "running" | "passed" | "failed" | "unavailable";
};

export function buildCodingAlertRows(input: CodingAlertInput): CodingAlertRow[] {
  const needsReviewActive = input.canApprovePreview || input.canMarkPreviewReviewed;
  const waitingForApprovalActive =
    needsReviewActive ||
    (input.previewStatus === "ready" &&
      !input.previewAlreadySatisfied &&
      input.verificationStatus !== "passed");
  const blockedActive =
    input.previewStatus === "blocked" ||
    input.activeRunState === "blocked" ||
    input.closeoutBlockersText.includes("preview evidence missing") ||
    input.closeoutBlockersText.includes("local approval missing");
  const doneActive =
    input.previewAlreadySatisfied ||
    input.verificationStatus === "passed" ||
    input.receiptReadinessText.startsWith("Receipt ready");
  const failedActive = input.previewStatus === "error" || input.verificationStatus === "failed" || input.activeRunState === "failed";

  return [
    {
      authority: "In-app status only; no apply, commit, push, provider, queue, worker, or shell authority.",
      cooldown: "Resets when the active chat/run state changes.",
      display: doneActive ? input.receiptReadinessText : "Waiting for verification or no-op receipt evidence.",
      evidence: doneActive ? input.receiptReadinessText : "No done evidence active.",
      id: "done",
      state: doneActive ? "active" : "waiting",
      title: "Done alert",
      trigger: "Verification passed, no-op receipt ready, or receipt ready.",
    },
    {
      authority: "In-app status only; no automatic repair or background continuation.",
      cooldown: "Resets when preview evidence changes or blocker text changes.",
      display: blockedActive
        ? "Blocked safely; review Task State, Progress, or receipt for exact blocker."
        : "No active blocker alert.",
      evidence: blockedActive ? input.closeoutBlockersText : "No blocker evidence active.",
      id: "blocked",
      state: blockedActive ? "active" : "waiting",
      title: "Blocked alert",
      trigger: "Preview blocked, run blocked, or required receipt evidence missing.",
    },
    {
      authority: "In-app status only; review does not imply approval, apply, commit, or push.",
      cooldown: "Resets after local review/approval state changes.",
      display: needsReviewActive
        ? "Preview evidence needs human review."
        : "No preview is awaiting human review.",
      evidence: needsReviewActive
        ? "Preview review evidence is ready; inspect changed files and allowed files before approval."
        : "No needs-review evidence active.",
      id: "needs-review",
      state: needsReviewActive ? "active" : "waiting",
      title: "Needs-review alert",
      trigger: "Preview is ready with changed files and review/approval is available.",
    },
    {
      authority: "In-app status only; approval remains an explicit local action.",
      cooldown: "Resets when approval is recorded or preview state changes.",
      display: waitingForApprovalActive
        ? "Waiting for local review/approval."
        : "No task is waiting for approval.",
      evidence: waitingForApprovalActive
        ? "Preview is ready and local review/approval has not been recorded."
        : "No waiting-for-approval evidence active.",
      id: "waiting-for-approval",
      state: waitingForApprovalActive ? "active" : "waiting",
      title: "Waiting-for-approval alert",
      trigger: "Preview is ready and approval/review has not been recorded.",
    },
    {
      authority: "In-app status only; no automatic retry, repair, provider call, queue, worker, or shell run.",
      cooldown: "Resets after the failed preview/run state changes.",
      display: failedActive
        ? "Failed safely; review Task State, Progress, or receipt for exact failure."
        : "No failed run alert.",
      evidence: failedActive ? input.closeoutBlockersText : "No failed-run evidence active.",
      id: "failed",
      state: failedActive ? "active" : "waiting",
      title: "Failed alert",
      trigger: "Preview error, failed verification, or failed diagnostic.",
    },
    {
      authority: "Optional future browser title/badge display only; no OS notification permission.",
      cooldown: "Would follow visible active chat/run state only.",
      display: "Optional later; not implemented in PR-6.",
      evidence: "Roadmap allows browser title/badge as optional.",
      id: "browser-title-badge",
      state: "gated",
      title: "Browser title/badge",
      trigger: "Separate UI decision after in-app alerts prove useful.",
    },
    {
      authority: "Desktop notifications, sound, and permission prompts require separate Britton approval.",
      cooldown: "Not applicable; not active.",
      display: "Gated; no Notification API permission prompt.",
      evidence: "PR-6 notification permission gate.",
      id: "desktop-notification-gate",
      state: "gated",
      title: "Desktop/sound notification gate",
      trigger: "Separate approval only.",
    },
    {
      authority: "No background watcher, service worker, queue, worker, or autonomous continuation.",
      cooldown: "Not applicable; not active.",
      display: "Gated; no background autonomy.",
      evidence: "PR-6 no-background-autonomy boundary.",
      id: "background-autonomy-gate",
      state: "gated",
      title: "Background autonomy gate",
      trigger: "Separate approval only.",
    },
  ];
}

export function codingAlertsReceiptLines(rows: CodingAlertRow[]): string[] {
  return [
    "Alerts receipt",
    "in_app_alerts: true",
    "desktop_permission_prompted: false",
    "sound_notification_started: false",
    "background_watcher_started: false",
    ...rows.map(
      (row) =>
        `${row.title}: ${row.state}; display=${row.display}; trigger=${row.trigger}; evidence=${row.evidence}; cooldown=${row.cooldown}; authority=${row.authority}`,
    ),
  ];
}
