import { buildTrialRouteResponse } from "./backend-route-trial";

export function assertTrialRouteSuccessResponse() {
  const response = buildTrialRouteResponse("Ready");
  return response.ok === true && response.message === "Ready";
}
