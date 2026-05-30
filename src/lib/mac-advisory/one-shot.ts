import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { buildMacAdvisoryPacket, normalizeMacAdvisoryJobType } from "./packet";
import type { MacAdvisoryPacket, MacAdvisoryRequest, MacCommandResult, MacCommandRunner } from "./types";

const execFileAsync = promisify(execFile);

const DEFAULT_MAC_HOST = "spirit-mac-mini";

function shellQuote(value: string): string {
  return `'${value.replace(/'/g, "'\\''")}'`;
}

function advisoryCommandFor(request: Required<Pick<MacAdvisoryRequest, "job_type" | "input_summary">> & MacAdvisoryRequest) {
  switch (request.job_type) {
    case "search_packet": {
      const query = request.query || request.input_summary;
      return [
        "python3",
        "-c",
        shellQuote(
          [
            "import json, urllib.parse",
            `query=${JSON.stringify(query)}`,
            "print(json.dumps({'kind':'search_packet','query':query,'status':'blocked_if_searxng_unavailable','citation':'searxng-json-if-configured','safe':'no_repo_write'}))",
          ].join("; "),
        ),
      ].join(" ");
    }
    case "screenshot_packet": {
      const url = request.url || "https://localhost:3000/coding/design-demo";
      return [
        "python3",
        "-c",
        shellQuote(
          [
            "import json",
            `url=${JSON.stringify(url)}`,
            "print(json.dumps({'kind':'screenshot_packet','url':url,'status':'metadata_only','safe':'no_repo_write'}))",
          ].join("; "),
        ),
      ].join(" ");
    }
    case "design_review_packet":
    case "test_scribe_packet":
    case "docs_summary_packet":
      return [
        "python3",
        "-c",
        shellQuote(
          [
            "import json, platform",
            `summary=${JSON.stringify(request.input_summary)}`,
            `kind=${JSON.stringify(request.job_type)}`,
            "print(json.dumps({'kind':kind,'summary':summary[:280],'host':platform.node(),'safe':'no_repo_write'}))",
          ].join("; "),
        ),
      ].join(" ");
    default:
      return "";
  }
}

export async function defaultSshCommandRunner(command: string, macHost = DEFAULT_MAC_HOST): Promise<MacCommandResult> {
  const { stderr, stdout } = await execFileAsync("ssh", ["-o", "BatchMode=yes", macHost, command], {
    timeout: 15_000,
  });

  return {
    stderr: String(stderr ?? ""),
    stdout: String(stdout ?? ""),
  };
}

export async function runMacAdvisoryJob(
  request: MacAdvisoryRequest,
  options: {
    macHost?: string;
    runner?: MacCommandRunner;
  } = {},
): Promise<MacAdvisoryPacket> {
  const startedAt = new Date().toISOString();
  const jobType = normalizeMacAdvisoryJobType(request.job_type);
  const inputSummary =
    typeof request.input_summary === "string" && request.input_summary.trim()
      ? request.input_summary.trim()
      : "";
  const macHost = options.macHost ?? DEFAULT_MAC_HOST;
  const jobId =
    typeof request.job_id === "string" && request.job_id.trim()
      ? request.job_id.trim()
      : `mac-advisory-${Date.now()}`;

  if (!jobType || !inputSummary) {
    return buildMacAdvisoryPacket({
      completed_at: new Date().toISOString(),
      input_summary: inputSummary || "missing input summary",
      job_id: jobId,
      job_type: jobType ?? "docs_summary_packet",
      mac_host: macHost,
      result: !jobType ? "Blocked: unsupported Mac advisory job type." : "Blocked: missing input_summary.",
      started_at: startedAt,
      status: "blocked",
    });
  }

  const command = advisoryCommandFor({ ...request, input_summary: inputSummary, job_type: jobType });
  const runner = options.runner ?? ((oneShotCommand: string) => defaultSshCommandRunner(oneShotCommand, macHost));

  try {
    const result = await runner(command);
    const evidence = [result.stdout.trim(), result.stderr.trim()].filter(Boolean);

    return buildMacAdvisoryPacket({
      citations_or_evidence: evidence,
      completed_at: new Date().toISOString(),
      input_summary: inputSummary,
      job_id: jobId,
      job_type: jobType,
      mac_host: macHost,
      result: result.stdout.trim() || "Mac advisory one-shot completed without stdout.",
      started_at: startedAt,
      status: "completed",
    });
  } catch (error) {
    return buildMacAdvisoryPacket({
      citations_or_evidence: [error instanceof Error ? error.message : String(error)],
      completed_at: new Date().toISOString(),
      input_summary: inputSummary,
      job_id: jobId,
      job_type: jobType,
      mac_host: macHost,
      result: "Blocked: Mac advisory one-shot command failed. No worker or daemon was started.",
      started_at: startedAt,
      status: "blocked",
    });
  }
}

