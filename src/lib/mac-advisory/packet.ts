import { MAC_ADVISORY_JOB_TYPES, type MacAdvisoryJobType, type MacAdvisoryPacket } from "./types";

export function isMacAdvisoryJobType(value: string): value is MacAdvisoryJobType {
  return MAC_ADVISORY_JOB_TYPES.includes(value as MacAdvisoryJobType);
}

export function normalizeMacAdvisoryJobType(value: unknown): MacAdvisoryJobType | null {
  return typeof value === "string" && isMacAdvisoryJobType(value) ? value : null;
}

export function buildMacAdvisoryPacket(input: {
  citations_or_evidence?: string[];
  completed_at?: string;
  input_summary: string;
  job_id: string;
  job_type: MacAdvisoryJobType;
  mac_host: string;
  result: string;
  started_at?: string;
  status: MacAdvisoryPacket["status"];
}): MacAdvisoryPacket {
  const now = new Date().toISOString();

  return {
    job_id: input.job_id,
    job_type: input.job_type,
    input_summary: input.input_summary,
    mac_host: input.mac_host,
    started_at: input.started_at ?? now,
    completed_at: input.completed_at ?? now,
    status: input.status,
    result: input.result,
    citations_or_evidence: input.citations_or_evidence ?? [],
    safety_boundary:
      "Mac advisory jobs are one-shot, preview-only, and have no repo write/apply/commit/push authority. Source Proxy remains the authority gate.",
    repo_write_authority: false,
  };
}

export function validateMacAdvisoryPacket(packet: MacAdvisoryPacket): string[] {
  const missing = [
    packet.job_id ? null : "job_id",
    packet.job_type ? null : "job_type",
    packet.input_summary ? null : "input_summary",
    packet.mac_host ? null : "mac_host",
    packet.started_at ? null : "started_at",
    packet.completed_at ? null : "completed_at",
    packet.status ? null : "status",
    packet.result ? null : "result",
    Array.isArray(packet.citations_or_evidence) ? null : "citations_or_evidence",
    packet.safety_boundary ? null : "safety_boundary",
    packet.repo_write_authority === false ? null : "repo_write_authority",
  ].filter((field): field is string => Boolean(field));

  return missing;
}

