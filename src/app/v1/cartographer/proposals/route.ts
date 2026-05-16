import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export async function GET() {
  let response;
  try {
    response = await sourceProxyFetch("/v1/cartographer/proposals", {
      method: "GET",
    });
  } catch (error) {
    return Response.json(
      {
        status: "unavailable",
        write_actions_enabled: false,
        proposals: [],
        proposal_count: 0,
        pending_proposals: 0,
        deduped: true,
        duplicate_proposals_present: 0,
        duplicate_proposals_suppressed: 0,
        actions_taken: false,
        error:
          "The dashboard could not reach the Source Proxy Cartographer proposals endpoint.",
        detail: error instanceof Error ? error.message : "Unknown connection error.",
      },
      { status: 200 },
    );
  }

  const contentType = response.headers.get("content-type") ?? "application/json";
  const text = await response.text();
  if (!contentType.includes("application/json")) {
    return new Response(text, {
      headers: { "content-type": contentType },
      status: response.status,
      statusText: response.statusText,
    });
  }

  let payload: unknown;
  try {
    payload = JSON.parse(text);
  } catch {
    return new Response(text, {
      headers: { "content-type": contentType },
      status: response.status,
      statusText: response.statusText,
    });
  }

  if (!payload || typeof payload !== "object") {
    return Response.json(payload, {
      status: response.status,
      statusText: response.statusText,
    });
  }

  const normalized = normalizeProposalDeduping(payload as Record<string, unknown>);
  return Response.json(normalized, {
    status: response.status,
    statusText: response.statusText,
  });
}

function normalizeProposalDeduping(payload: Record<string, unknown>) {
  const proposals = Array.isArray(payload.proposals)
    ? payload.proposals.map((item) =>
        item && typeof item === "object"
          ? { deduped: true, ...(item as Record<string, unknown>) }
          : item,
      )
    : [];
  const duplicateProposalsPresent = countDuplicateProposalKeys(proposals);

  return {
    ...payload,
    proposals,
    deduped: payload.deduped ?? duplicateProposalsPresent === 0,
    duplicate_proposals_present:
      payload.duplicate_proposals_present ?? duplicateProposalsPresent,
    duplicate_proposals_suppressed: payload.duplicate_proposals_suppressed ?? 0,
  };
}

function countDuplicateProposalKeys(proposals: unknown[]) {
  const seen = new Set<string>();
  let duplicates = 0;
  for (const item of proposals) {
    if (!item || typeof item !== "object") {
      continue;
    }
    const proposal = item as Record<string, unknown>;
    const key =
      typeof proposal.fingerprint === "string" && proposal.fingerprint
        ? `fingerprint:${proposal.fingerprint}`
        : typeof proposal.proposal_id === "string" && proposal.proposal_id
          ? `proposal:${proposal.proposal_id}`
          : "";
    if (!key) {
      continue;
    }
    if (seen.has(key)) {
      duplicates += 1;
    } else {
      seen.add(key);
    }
  }
  return duplicates;
}
