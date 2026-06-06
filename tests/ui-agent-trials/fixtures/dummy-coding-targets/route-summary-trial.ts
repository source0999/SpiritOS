export type TrialRouteSummaryInput = {
  body?: unknown;
  message?: string;
  status: number;
};

export function summarizeTrialRouteResponse(input: TrialRouteSummaryInput): string {
  if (input.status >= 200 && input.status < 300) {
    return "Request completed.";
  }

  return typeof input.message === "string" && input.message.trim()
    ? input.message.trim()
    : "Request failed.";
}
