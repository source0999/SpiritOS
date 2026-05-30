import { runMacAdvisoryJob } from "@/lib/mac-advisory/one-shot";
import type { MacAdvisoryRequest } from "@/lib/mac-advisory/types";

export const runtime = "nodejs";

async function requestJson(request: Request): Promise<MacAdvisoryRequest> {
  try {
    const payload = await request.json();
    return typeof payload === "object" && payload !== null ? (payload as MacAdvisoryRequest) : {};
  } catch {
    return {};
  }
}

export async function POST(request: Request) {
  const payload = await requestJson(request);
  const packet = await runMacAdvisoryJob(payload);

  return Response.json({
    advisory_only: true,
    apply_authority: false,
    commit_authority: false,
    hidden_worker_started: false,
    mac_repo_write_authority: false,
    packet,
    persistent_daemon_started: false,
    preview_only: true,
    provider_call_made: false,
    push_authority: false,
    source_proxy_authority_gate: true,
  });
}
