import { proxyCartographerGet } from "@/app/v1/cartographer/_proxy";

export async function GET() {
  return proxyCartographerGet("/v1/cartographer/docs-autopilot/soak");
}
