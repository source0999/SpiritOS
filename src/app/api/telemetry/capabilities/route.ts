import { getCapabilityRegistry } from "@/lib/server/capabilities/get-capabilities";

export const dynamic = "force-dynamic";

export async function GET() {
  const body = await getCapabilityRegistry();
  return Response.json(body, { headers: { "Cache-Control": "no-store" } });
}
