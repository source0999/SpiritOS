export type TrialRouteResponse = {
  ok: boolean;
  message: string;
};

export function buildTrialRouteResponse(message: string, ok = true): TrialRouteResponse {
  return {
    ok,
    message,
  };
}
