import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export async function POST() {
  const response = await sourceProxyFetch("/v1/cartographer/docs-autopilot/apply", {
    method: "POST",
  });
  const contentType = response.headers.get("content-type") ?? "application/json";
  const text = await response.text();
  return new Response(text, {
    headers: { "content-type": contentType },
    status: response.status,
    statusText: response.statusText,
  });
}
