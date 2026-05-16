import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export async function proxyCartographerGet(path: string) {
  let response;
  try {
    response = await sourceProxyFetch(path, {
      method: "GET",
    });
  } catch (error) {
    return Response.json(
      {
        status: "unavailable",
        write_actions_enabled: false,
        configured_roots: [],
        blocked_roots: [],
        projects: [],
        blueprints: [],
        blueprint_count: 0,
        pending_proposals: 0,
        error:
          "The dashboard could not reach the Source Proxy Cartographer endpoint.",
        detail: error instanceof Error ? error.message : "Unknown connection error.",
      },
      { status: 200 },
    );
  }

  return new Response(await response.text(), {
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
    },
    status: response.status,
    statusText: response.statusText,
  });
}
