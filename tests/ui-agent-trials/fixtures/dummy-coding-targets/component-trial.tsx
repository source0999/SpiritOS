export type TrialBadgeProps = {
  label: string;
  tone: "neutral" | "success";
};

export function TrialBadge({ label, tone }: TrialBadgeProps) {
  return {
    label,
    tone,
  };
}

