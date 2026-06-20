import { describe, expect, it } from "vitest";
import {
  createMacWorkerJob,
  createTracedMacWorkerJob,
  macWorkerCapabilityDescriptor,
  macRunSummaryFromResult,
  normalizeMacWorkerResult,
  summarizeMacWorkerResult,
} from "../contract";

describe("Mac worker contract", () => {
  it("creates a Spirit Mac Mini job with the shared fields", () => {
    const job = createMacWorkerJob("trial_context_assist", { prompt: "fix the coding trial" }, "job-1");

    expect(job).toMatchObject({
      job_id: "job-1",
      job_type: "trial_context_assist",
      node_id: "spirit-mac-mini",
      input: { prompt: "fix the coding trial" },
    });
    expect(job.created_at).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    expect(job.job_envelope_version).toBe("source-proxy-mac-worker-job-v1");
  });

  it("creates a traced Mac assignment for the Plan 1 causal seam", () => {
    const job = createTracedMacWorkerJob(
      "system_status",
      { cwd: "$HOME/spiritos-worker/SpiritOS" },
      {
        trace_id: "trace_123",
        invocation_event_id: "invocation_123",
        consumer_event_id: "consumer_123",
        consumer_subsystem: "cartographer_mac_assignment_consumer",
        task_id: "task_123",
      },
      "job-traced",
    );

    expect(job).toMatchObject({
      job_id: "job-traced",
      task_id: "task_123",
      trace_id: "trace_123",
      invocation_event_id: "invocation_123",
      consumer_event_id: "consumer_123",
      consumer_subsystem: "cartographer_mac_assignment_consumer",
    });
  });

  it("reports Mac capability while preserving first-write human stop", () => {
    const capability = macWorkerCapabilityDescriptor("AVAILABLE", "2026-06-20T00:00:00.000Z");

    expect(capability).toMatchObject({
      worker: "mac",
      status: "AVAILABLE",
      write_capable: true,
      requires_human_first_write: true,
      job_envelope_version: "source-proxy-mac-worker-job-v1",
      result_envelope_version: "source-proxy-mac-worker-result-v1",
    });
    expect(capability.capabilities).toContain("run_safe_check");
  });

  it("normalizes candidate files and recommended checks from Mac JSON", () => {
    const job = createMacWorkerJob("repo_context_search", {}, "job-2");
    const result = normalizeMacWorkerResult(
      {
        job_id: "job-2",
        job_type: "repo_context_search",
        node_id: "spirit-mac-mini",
        success: true,
        result: { summary: "searched" },
        candidate_files: ["src/lib/coding/agent-trials-ui.ts"],
        recommended_checks: ["git diff --check"],
      },
      job,
    );

    expect(result.success).toBe(true);
    expect(result.candidate_files).toEqual(["src/lib/coding/agent-trials-ui.ts"]);
    expect(result.recommended_checks).toEqual(["git diff --check"]);
    expect(summarizeMacWorkerResult(result)).toContain("1 candidate file");
  });

  it("does not fake success for unavailable Mac results", () => {
    const job = createMacWorkerJob("system_status", {}, "job-3");
    const result = normalizeMacWorkerResult({ error: "ssh failed" }, job);
    const summary = macRunSummaryFromResult(result);

    expect(result.success).toBe(false);
    expect(summary.mac_used).toBe(true);
    expect(summary.mac_node_status).toBe("offline");
    expect(summary.mac_error).toBe("ssh failed");
  });

  it("preserves structured blocked safe-check failures", () => {
    const job = createMacWorkerJob("run_safe_check", { check_command: "rm -rf ." }, "job-4");
    const result = normalizeMacWorkerResult(
      {
        job_id: "job-4",
        job_type: "run_safe_check",
        node_id: "spirit-mac-mini",
        success: false,
        result: {
          reason_code: "safe_check_command_not_allowlisted",
          blocked_command: "rm -rf .",
          recommended_checks: ["git diff --check"],
        },
        error: "check_command is not allowlisted: rm -rf .",
        recommended_checks: ["git diff --check"],
      },
      job,
    );

    expect(result.success).toBe(false);
    expect(result.result).toMatchObject({
      reason_code: "safe_check_command_not_allowlisted",
      blocked_command: "rm -rf .",
    });
    expect(result.error).toContain("not allowlisted");
    expect(result.recommended_checks).toEqual(["git diff --check"]);
  });

  it("preserves structured scout research packet success fields", () => {
    const job = createMacWorkerJob(
      "scout_research_packet",
      { query: "Mac worker Scout proof", mode: "local_only" },
      "job-5",
    );
    const result = normalizeMacWorkerResult(
      {
        job_id: "job-5",
        job_type: "scout_research_packet",
        node_id: "spirit-mac-mini",
        success: true,
        result: {
          summary: "Local Scout advisory packet searched repo context",
          query: "Mac worker Scout proof",
          mode: "local_only",
          sources: [{ type: "repo_file", file: "scripts/mac-worker/spirit_mac_worker.py" }],
          candidate_files: ["scripts/mac-worker/spirit_mac_worker.py"],
          snippets: [{ file: "scripts/mac-worker/spirit_mac_worker.py", snippets: [] }],
          confidence: "medium",
          limitations: ["Local-only packet; no public web search was performed."],
          recommended_next_checks: ["git diff --check"],
          unsafe_or_untrusted_content_warning: "Advisory packet only.",
        },
        candidate_files: ["scripts/mac-worker/spirit_mac_worker.py"],
        recommended_checks: ["git diff --check"],
      },
      job,
    );

    expect(result.success).toBe(true);
    expect(result.result).toMatchObject({
      query: "Mac worker Scout proof",
      mode: "local_only",
      confidence: "medium",
      unsafe_or_untrusted_content_warning: "Advisory packet only.",
    });
    expect(result.candidate_files).toEqual(["scripts/mac-worker/spirit_mac_worker.py"]);
  });

  it("preserves structured scout research packet blocked mode fields", () => {
    const job = createMacWorkerJob(
      "scout_research_packet",
      { query: "Mac worker Scout proof", mode: "web_search_packet" },
      "job-6",
    );
    const result = normalizeMacWorkerResult(
      {
        job_id: "job-6",
        job_type: "scout_research_packet",
        node_id: "spirit-mac-mini",
        success: false,
        result: {
          summary: "scout_research_packet mode is not available",
          query: "Mac worker Scout proof",
          mode: "web_search_packet",
          sources: [],
          candidate_files: [],
          snippets: [],
          confidence: "none",
          limitations: ["Only local_only mode is currently proven for this worker."],
          recommended_next_checks: ["Run provider boundary proof before enabling web_search_packet."],
          unsafe_or_untrusted_content_warning: "Advisory packet only.",
          reason_code: "unsupported_scout_research_mode",
        },
        error: "unsupported_scout_research_mode",
        candidate_files: [],
        recommended_checks: ["Run provider boundary proof before enabling web search."],
      },
      job,
    );

    expect(result.success).toBe(false);
    expect(result.error).toBe("unsupported_scout_research_mode");
    expect(result.result).toMatchObject({
      reason_code: "unsupported_scout_research_mode",
      mode: "web_search_packet",
      confidence: "none",
    });
  });

  it("preserves structured scout web search packet failure fields", () => {
    const job = createMacWorkerJob(
      "scout_research_packet",
      { query: "Next.js docs", mode: "web_search_packet", provider: "local_first" },
      "job-7",
    );
    const result = normalizeMacWorkerResult(
      {
        job_id: "job-7",
        job_type: "scout_research_packet",
        node_id: "spirit-mac-mini",
        success: false,
        result: {
          summary: "No local-first search provider returned JSON results.",
          query: "Next.js docs",
          mode: "web_search_packet",
          sources: [],
          provider: "local_first",
          provider_status: [{ provider: "searxng", status: "failed" }],
          reason_code: "search_provider_unreachable",
          limitations: ["No paid provider was used."],
          recommended_manual_check: "Verify SearXNG is reachable from the Mac.",
          unsafe_or_untrusted_content_warning: "Advisory packet only.",
        },
        error: "search_provider_unreachable",
        candidate_files: [],
        recommended_checks: ["Check local SearXNG health before retrying web_search_packet."],
      },
      job,
    );

    expect(result.success).toBe(false);
    expect(result.error).toBe("search_provider_unreachable");
    expect(result.result).toMatchObject({
      reason_code: "search_provider_unreachable",
      mode: "web_search_packet",
      provider: "local_first",
    });
  });

  it("preserves blocked browser design packet fields without fake screenshot proof", () => {
    const job = createMacWorkerJob(
      "browser_design_check",
      { url: "https://127.0.0.1:3000/coding", viewport: "mobile", check: "layout_readability_and_overlap" },
      "job-8",
    );
    const result = normalizeMacWorkerResult(
      {
        job_id: "job-8",
        job_type: "browser_design_check",
        node_id: "spirit-mac-mini",
        success: true,
        result: {
          summary: "Mac browser/design check packet prepared; screenshot proof unavailable from current worker dependencies.",
          url: "https://127.0.0.1:3000/coding",
          viewport: "mobile",
          findings: [{ severity: "blocked", title: "Screenshot proof unavailable" }],
          severity: "blocked",
          screenshot_artifacts: [],
          limitations: ["No screenshot was captured."],
          recommended_checks: ["Run Playwright screenshot proof when available."],
          no_mutation_confirmed: true,
        },
        artifacts: [],
        candidate_files: [],
        recommended_checks: ["Run Playwright screenshot proof when available."],
      },
      job,
    );

    expect(result.success).toBe(true);
    expect(result.artifacts).toEqual([]);
    expect(result.result).toMatchObject({
      severity: "blocked",
      screenshot_artifacts: [],
      no_mutation_confirmed: true,
    });
  });
});
