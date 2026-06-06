export type TrialRouteResponse = {
  ok: boolean;
  message: string;
};

export function buildTrialRouteResponse(message: string): TrialRouteResponse {
  return {
    ok: true,
    message,
  };
}
