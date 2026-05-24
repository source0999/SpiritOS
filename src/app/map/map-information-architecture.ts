export const cartographerMapOperationalSections = [
  {
    id: "current-state",
    label: "Current State",
    purpose: "What Cartographer sees right now.",
  },
  {
    id: "approvals",
    label: "Approvals",
    purpose: "What is approved, missing, or blocked.",
  },
  {
    id: "queue",
    label: "Queue",
    purpose: "What can be selected and why it may be blocked.",
  },
  {
    id: "workflows",
    label: "Workflows",
    purpose: "What ran, what stopped, and what is waiting.",
  },
  {
    id: "receipts",
    label: "Receipts",
    purpose: "Evidence Britton can review.",
  },
  {
    id: "verify",
    label: "Verify",
    purpose: "What Britton should manually check next.",
  },
  {
    id: "debug",
    label: "Debug",
    purpose: "Read-only source health and fallback state.",
  },
] as const;

export const cartographerMapAuthorityDenials = [
  "No approval minting",
  "No self-approval",
  "No broad full auto",
  "No source writes",
  "No command execution",
  "No commit, push, branch, checkout, reset, clean, or stash",
] as const;

export const cartographerMapOperatorQuestions = [
  "What is Cartographer doing?",
  "What is blocked?",
  "What is approved?",
  "What ran?",
  "What does Britton need to verify?",
] as const;

export const cartographerMapLiveStateFields = [
  "Branch",
  "HEAD",
  "Dirty state",
  "Protected-lane state",
  "Recommendation",
] as const;

export const cartographerMapApprovalTokenFields = [
  "Runtime status",
  "Validation status",
  "Consumption preview",
  "Blocked reasons",
  "Safe next action",
] as const;

export const cartographerMapQueuePanelFields = [
  "Queue status",
  "Run-next status",
  "One-task selection",
  "Execution blocked",
  "Safe next action",
] as const;

export const cartographerMapWorkflowPanelFields = [
  "Active runs",
  "Recent runs",
  "Workflow status",
  "Step status",
  "Blocked reasons",
] as const;

export const cartographerMapStopControlFields = [
  "Kill switch state",
  "Pause control",
  "Cancel control",
  "Timeout control",
  "Retry control",
] as const;

export const cartographerMapReceiptEvidenceFields = [
  "Receipt journal",
  "Evidence artifacts",
  "Approved docs paths",
  "Missing evidence",
  "Write blocked",
] as const;
