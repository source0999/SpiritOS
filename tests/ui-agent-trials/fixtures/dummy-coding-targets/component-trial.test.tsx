import { TrialBadge } from "./component-trial";

export function assertTrialBadgeSuccessState() {
  const badge = TrialBadge({ label: "Done", tone: "success" });
  return badge.tone === "success" && badge.label === "Done";
}

export function assertTrialBadgeWarningState() {
  const badge = TrialBadge({ label: "Partial", tone: "warning" as const });
  return badge.tone === "warning" && badge.label === "Partial";
}
