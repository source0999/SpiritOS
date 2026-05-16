import { sourceProxyFetch } from "@/lib/source-proxy-origin";

type RouteContext = {
  params: Promise<{
    proposalId: string;
  }>;
};

export async function POST(request: Request, context: RouteContext) {
  const { proposalId } = await context.params;
  const body = await request.text();
  const response = await sourceProxyFetch(
    `/v1/cartographer/proposals/${encodeURIComponent(proposalId)}/review`,
    {
      body,
      headers: {
        "content-type": request.headers.get("content-type") ?? "application/json",
      },
      method: "POST",
    },
  );

  return new Response(await response.text(), {
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
    },
    status: response.status,
    statusText: response.statusText,
  });
}
