export type TrialBadgeProps = {
  label: string;
  tone: "neutral" | "success" | "warning";
};

export function TrialBadge({ label, tone }: TrialBadgeProps) {
  return {
    label,
    tone,
  };
}

