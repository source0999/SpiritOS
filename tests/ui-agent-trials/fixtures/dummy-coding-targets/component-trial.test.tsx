import { TrialBadge } from "./component-trial";

export function assertTrialBadgeSuccessState() {
  const badge = TrialBadge({ label: "Done", tone: "success" });
  return badge.tone === "success" && badge.label === "Done";
}
