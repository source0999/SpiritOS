export const MAC_ADVISORY_JOB_TYPES = [
  "search_packet",
  "screenshot_packet",
  "design_review_packet",
  "test_scribe_packet",
  "docs_summary_packet",
] as const;

export type MacAdvisoryJobType = (typeof MAC_ADVISORY_JOB_TYPES)[number];

export type MacAdvisoryStatus = "completed" | "blocked" | "failed";

export type MacAdvisoryPacket = {
  job_id: string;
  job_type: MacAdvisoryJobType;
  input_summary: string;
  mac_host: string;
  started_at: string;
  completed_at: string;
  status: MacAdvisoryStatus;
  result: string;
  citations_or_evidence: string[];
  safety_boundary: string;
  repo_write_authority: false;
};

export type MacAdvisoryRequest = {
  job_id?: string;
  job_type?: string;
  input_summary?: string;
  query?: string;
  url?: string;
};

export type MacCommandResult = {
  stdout: string;
  stderr: string;
};

export type MacCommandRunner = (command: string) => Promise<MacCommandResult>;

