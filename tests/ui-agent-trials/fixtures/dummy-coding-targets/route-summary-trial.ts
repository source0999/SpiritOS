export type TrialRouteSummaryInput = {
  body?: unknown;
  message?: string;
  status: number;
};

export function summarizeTrialRouteResponse(input: TrialRouteSummaryInput): string {
  if (input.status >= 200 && input.status < 300) {
    return "Request completed.";
  }

  const message = typeof input.body === 'string' ? input.body.trim() : input.message?.trim() || '';
  const safeMessage = message.length > 50 ? message.substring(0, 50) + '...' : message;

  return safeMessage
    ? `Request failed with status ${input.status}: ${safeMessage}`
    : `Request failed with status ${input.status}`;
}
