type ResearchPreviewRequest = {
  allowed_files?: unknown;
  prompt?: unknown;
  research_sources?: unknown;
  target_files?: unknown;
  task_id?: unknown;
};

const dormantRouteHeaders = {
  "x-spiritos-plan4-route-status": "dormant",
  "x-spiritos-plan4-canonical-replacement": "/v1/decisions/prompt-packet",
};

type ResearchSource = {
  kind: "repo" | "web" | "scout";
  snippet: string;
  title: string;
  url: string;
};

function stringArrayValue(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function sourceArrayValue(value: unknown): ResearchSource[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.flatMap((item) => {
    if (typeof item !== "object" || item === null) {
      return [];
    }
    const record = item as Record<string, unknown>;
    const title = typeof record.title === "string" ? record.title : "";
    const url = typeof record.url === "string" ? record.url : "";
    const snippet = typeof record.snippet === "string" ? record.snippet : "";
    const kind =
      record.kind === "web" || record.kind === "scout" || record.kind === "repo"
        ? record.kind
        : url.startsWith("http")
          ? "web"
          : "repo";
    if (!title && !url && !snippet) {
      return [];
    }
    return [
      {
        kind,
        snippet: snippet || "No snippet supplied; source remains advisory only.",
        title: title || "Untitled advisory source",
        url: url || "repo://unresolved-source",
      },
    ];
  });
}

async function requestJson(request: Request): Promise<ResearchPreviewRequest> {
  try {
    const payload = await request.json();
    return typeof payload === "object" && payload !== null ? payload : {};
  } catch {
    return {};
  }
}

export async function POST(request: Request) {
  const payload = await requestJson(request);
  const prompt = typeof payload.prompt === "string" ? payload.prompt.trim() : "";
  const targetFiles = stringArrayValue(payload.target_files);
  const allowedFiles = stringArrayValue(payload.allowed_files);
  const suppliedSources = sourceArrayValue(payload.research_sources);
  const fallbackSource: ResearchSource = {
    kind: "repo",
    snippet: "Local roadmap context only; no live web search or Scout write occurred.",
    title: "Source Proxy preflight roadmap",
    url: "docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md",
  };
  const researchSources = suppliedSources.length > 0 ? suppliedSources : [fallbackSource];
  const blockedReasons = [
    ...(prompt ? [] : ["missing_prompt"]),
    ...(targetFiles.length > 0 ? [] : ["missing_target_files"]),
    ...(allowedFiles.length > 0 ? [] : ["missing_allowed_files"]),
  ];
  const packetStatus = blockedReasons.length > 0 ? "blocked" : "ready";

  return Response.json({
    accepted_research_to_coding_handoff: packetStatus === "ready",
    advisory_only: true,
    allowed_files: allowedFiles,
    apply_authority: false,
    blocked_actions: [
      "autonomous_scout_discovery",
      "hidden_scheduled_search",
      "provider_model_call",
      "mac_service_control",
      "repo_write_from_mac",
      "cart_mutation",
      "approval",
      "apply",
      "commit",
      "push",
      "auto",
    ],
    blocked_reasons: blockedReasons,
    commit_authority: false,
    hidden_execution_started: false,
    human_review_required: true,
    mac_node: {
      adapter: "mac_searxng_advisory",
      health: "unverified",
      reason: "Mac/SearXNG health is display-only until a human verifies JSON search capability.",
      status: "blocked",
    },
    preview_only: true,
    plan4_canonical_replacement: "/v1/decisions/prompt-packet",
    plan4_route_status: "dormant",
    provider_call_made: false,
    push_authority: false,
    queue_worker_started: false,
    research_lane_status: packetStatus,
    research_packet_id:
      typeof payload.task_id === "string" && payload.task_id.trim()
        ? `research-${payload.task_id.trim()}`
        : "research-preview-local",
    research_sources: researchSources,
    scout_bridge: {
      import_mode: "manual_preview_only",
      packet_status: "preview_only",
      sources_visible: researchSources.map((source) => source.url),
    },
    search: {
      capability: "blocked_until_manual_json_health_check",
      sources_required: true,
      status: "blocked",
    },
    shell_command_started: false,
    target_files: targetFiles,
    task: prompt,
  }, { headers: dormantRouteHeaders });
}
