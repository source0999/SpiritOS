import { sourceProxyFetch } from "@/lib/source-proxy-origin";

type Context = {
  params: Promise<{ proposalId: string }>;
};

export async function POST(request: Request, context: Context) {
  const { proposalId } = await context.params;
  const body = await request.text();
  const response = await sourceProxyFetch(
    `/v1/cartographer/starter-blueprints/${encodeURIComponent(proposalId)}/approve`,
    {
      method: "POST",
      body,
      headers: {
        "content-type": request.headers.get("content-type") ?? "application/json",
      },
    },
  );
  const contentType = response.headers.get("content-type") ?? "application/json";
  const text = await response.text();
  return new Response(text, {
    headers: { "content-type": contentType },
    status: response.status,
    statusText: response.statusText,
  });
}
