export type TrialResultCardState = "success" | "failed" | "pending";

export type TrialResultCardProps = {
  detail: string;
  state: TrialResultCardState;
  title: string;
};

export function trialResultCardView(props: TrialResultCardProps) {
  return {
    detail: props.detail,
    state: props.state,
    title: props.title,
  };
}
