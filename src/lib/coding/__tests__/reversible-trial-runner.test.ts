import { describe, expect, it } from "vitest";

import type { DurableCodingRun } from "@/lib/coding/durable-run-types";
import {
  betweenPromptsStaleSummary,
  buildTrialPromptQuickLinks,
  classifyCurrentSuiteAgentLabFiles,
  classifyEditReversibleAlreadySatisfied,
  downgradePassWithoutReversalProof,
  durableRunHasStaleBetweenPromptsGap,
  durableRunHasStalePostApplyVerification,
  evaluateAgentLabBaseline,
  inferAgentLabPageHref,
  postApplyStaleReasonCode,
  trialRunnerRunBlocked,
} from "@/lib/coding/reversible-trial-runner";

describe("reversible trial runner helpers", () => {
  it("blocks suite start while cleanup/reverse is active", () => {
    expect(
      trialRunnerRunBlocked({
        suiteStatus: "idle",
        isReverting: true,
      }),
    ).toMatchObject({
      blocked: true,
      reason: "cleanup_reverse_active",
    });
    expect(
      trialRunnerRunBlocked({
        backgroundCleanupActive: true,
        suiteStatus: "idle",
      }),
    ).toMatchObject({
      blocked: true,
      reason: "background_cleanup_active",
    });
  });

  it("downgrades edit_reversible already satisfied without expected noop proof", () => {
    expect(
      classifyEditReversibleAlreadySatisfied({
        expectedOutcome: "edit_reversible",
        promptPacketReasonCode: "coder_no_changes_needed",
        providerCallMade: true,
        proposedDiff: "",
      }),
    ).toEqual({
      kind: "needs_fix",
      reason_code: "already_satisfied_without_expected_noop",
      visible_result_label: "NEEDS FIX",
    });
  });

  it("flags dirty baseline already satisfied", () => {
    expect(
      classifyEditReversibleAlreadySatisfied({
        baselineCleanForFreshSuite: false,
        expectedOutcome: "edit_reversible",
        promptPacketReasonCode: "coder_no_changes_needed",
        providerCallMade: true,
        proposedDiff: "",
      }).kind,
    ).toBe("needs_fix");
  });

  it("evaluates agent-lab baseline dirty state from leftovers", () => {
    const snapshot = evaluateAgentLabBaseline({
      agentLabFiles: ["src/app/agent-lab/cards/page.tsx"],
      unrevertedReceiptTargets: ["src/app/agent-lab/cards/page.tsx"],
    });
    expect(snapshot.baseline_clean_for_fresh_suite).toBe(false);
    expect(snapshot.baseline_dirty_agent_lab_files).toContain("src/app/agent-lab/cards/page.tsx");
  });

  it("separates current-suite expected agent-lab files from stale leftovers", () => {
    expect(
      classifyCurrentSuiteAgentLabFiles({
        completedPromptChangedFiles: ["src/app/agent-lab/page.tsx"],
        dirtyAgentLabFiles: [
          "src/app/agent-lab/page.tsx",
          "src/app/agent-lab/calculator/page.tsx",
        ],
      }),
    ).toEqual({
      expectedCurrentSuiteFiles: ["src/app/agent-lab/page.tsx"],
      staleLeftoverFiles: ["src/app/agent-lab/calculator/page.tsx"],
    });
  });

  it("builds quick links for agent-lab page targets", () => {
    expect(inferAgentLabPageHref("src/app/agent-lab/notes/page.tsx")).toBe("/agent-lab/notes");
    expect(
      buildTrialPromptQuickLinks({
        quickFindPaths: ["src/app/agent-lab/notes/page.tsx"],
        selectedTarget: "src/app/agent-lab/notes/page.tsx",
      }).map((link) => link.href),
    ).toEqual(["/agent-lab", "/agent-lab/notes"]);
  });

  it("detects stale post-apply verification after execute-approved 200", () => {
    const run: DurableCodingRun = {
      benchmark_name: "Messy Coder 10",
      completed_count: 7,
      created_at: new Date(Date.now() - 120_000).toISOString(),
      current_prompt_id: "coder-008",
      current_step_started_at: new Date(Date.now() - 120_000).toISOString(),
      disk_changed_files: [],
      endpoint_statuses: ["/v1/actions/execute-approved:200"],
      final_summary: "Editing files",
      frontend_url: "https://example/coding",
      generated_diff_present: true,
      lane: "coder",
      last_error: null,
      model: "qwen",
      model_called_for_generation: "qwen",
      preview_changed_files: ["src/app/agent-lab/notes/page.tsx"],
      provider: "ollama",
      provider_call_made: true,
      proxy_url: "https://example/proxy",
      reason_code: "",
      requested_count: 10,
      reversal_available: false,
      reversal_status: "none",
      rows: [
        {
          applied_changed_files: [],
          checks_result: "",
          checks_run: [],
          disk_changed_files: [],
          endpoint_statuses: ["/v1/actions/execute-approved:200"],
          error_summary: "",
          generated_diff_present: true,
          model_called_for_generation: "qwen",
          preview_changed_files: ["src/app/agent-lab/notes/page.tsx"],
          prompt_excerpt: "notes",
          prompt_id: "coder-008",
          prompt_text: "notes",
          provider_call_made: true,
          reason_code: "",
          result_label: "RUNNING",
          reversal_available: false,
          reversal_status: "none",
          started_at: new Date(Date.now() - 120_000).toISOString(),
          status: "running",
          updated_at: new Date(Date.now() - 120_000).toISOString(),
        },
      ],
      run_id: "suite-mq2yjssl",
      started_by_surface: "coding",
      status: "running",
      suite_id: "suite-mq2yjssl",
      updated_at: new Date().toISOString(),
      applied_changed_files: [],
      checks_result: "",
      checks_run: [],
    };
    expect(durableRunHasStalePostApplyVerification(run, Date.now(), 60_000)).toBe(true);
    expect(postApplyStaleReasonCode(run)).toBe("apply_ack_no_disk_proof");
  });

  it("distinguishes a lost execute-approved body read from missing disk proof", () => {
    const run: DurableCodingRun = {
      benchmark_name: "Messy Coder 10",
      completed_count: 0,
      created_at: new Date(Date.now() - 120_000).toISOString(),
      current_prompt_id: "coder-001",
      current_step_started_at: new Date(Date.now() - 120_000).toISOString(),
      disk_changed_files: [],
      endpoint_statuses: ["/v1/actions/execute-approved:200"],
      final_summary: "Apply route returned; reading execute-approved proof",
      frontend_url: "https://example/coding",
      generated_diff_present: true,
      lane: "coder",
      last_error: null,
      model: "qwen2.5-coder:7b",
      model_called_for_generation: "ollama_chat/qwen2.5-coder:7b",
      preview_changed_files: ["src/app/agent-lab/page.tsx"],
      provider: "Local / Ollama",
      provider_call_made: true,
      proxy_url: "https://example/proxy",
      reason_code: "",
      requested_count: 10,
      reversal_available: false,
      reversal_status: "none",
      rows: [
        {
          applied_changed_files: [],
          checks_result: "",
          checks_run: [],
          disk_changed_files: [],
          endpoint_statuses: ["/v1/actions/execute-approved:200"],
          error_summary: "",
          generated_diff_present: true,
          model_called_for_generation: "ollama_chat/qwen2.5-coder:7b",
          preview_changed_files: ["src/app/agent-lab/page.tsx"],
          prompt_excerpt: "make a new isolated test",
          prompt_id: "coder-001",
          prompt_text: "make a new isolated test",
          provider_call_made: true,
          reason_code: "",
          result_label: "RUNNING",
          reversal_available: false,
          reversal_status: "none",
          started_at: new Date(Date.now() - 120_000).toISOString(),
          status: "running",
          step_instrumentation: {
            execute_approved_body_read_started_at: new Date(Date.now() - 120_000).toISOString(),
            execute_approved_completed_at: new Date(Date.now() - 120_000).toISOString(),
            execute_approved_http_status: "200",
            last_progress_reason_code: "execute_approved_http_200_body_pending",
          },
          updated_at: new Date(Date.now() - 120_000).toISOString(),
        },
      ],
      run_id: "suite-body-read-lost",
      started_by_surface: "coding",
      status: "running",
      suite_id: "suite-body-read-lost",
      updated_at: new Date(Date.now() - 120_000).toISOString(),
      applied_changed_files: [],
      checks_result: "",
      checks_run: [],
    };

    expect(durableRunHasStalePostApplyVerification(run, Date.now(), 60_000)).toBe(true);
    expect(postApplyStaleReasonCode(run)).toBe("execute_approved_body_read_missing");
  });

  it("detects stale between-prompts gap when runner dies after a completed row", () => {
    const run: DurableCodingRun = {
      benchmark_name: "Messy Coder 10",
      completed_count: 1,
      created_at: new Date(Date.now() - 120_000).toISOString(),
      current_prompt_id: "coder-001",
      current_step_started_at: new Date(Date.now() - 120_000).toISOString(),
      disk_changed_files: ["src/app/agent-lab/page.tsx"],
      endpoint_statuses: [],
      final_summary: "Ready for review",
      frontend_url: "https://example/coding",
      generated_diff_present: true,
      lane: "coder",
      last_error: null,
      model: "qwen2.5-coder:7b",
      model_called_for_generation: "ollama_chat/qwen2.5-coder:7b",
      preview_changed_files: ["src/app/agent-lab/page.tsx"],
      provider: "Local / Ollama",
      provider_call_made: true,
      proxy_url: "https://example/proxy",
      reason_code: "",
      requested_count: 10,
      reversal_available: true,
      reversal_status: "available",
      rows: [
        {
          applied_changed_files: ["src/app/agent-lab/page.tsx"],
          checks_result: "git diff --check recorded",
          checks_run: ["git diff --check"],
          disk_changed_files: ["src/app/agent-lab/page.tsx"],
          endpoint_statuses: ["/v1/actions/execute-approved:200"],
          error_summary: "",
          generated_diff_present: true,
          model_called_for_generation: "ollama_chat/qwen2.5-coder:7b",
          preview_changed_files: ["src/app/agent-lab/page.tsx"],
          prompt_excerpt: "",
          prompt_id: "coder-001",
          prompt_text: "",
          provider_call_made: true,
          reason_code: "",
          result_label: "PASS",
          reversal_available: true,
          reversal_status: "available",
          run_id: "task_1",
          status: "completed",
          started_at: new Date(Date.now() - 120_000).toISOString(),
          updated_at: new Date(Date.now() - 120_000).toISOString(),
        },
      ],
      run_id: "suite-mq32syem",
      started_by_surface: "coding",
      status: "running",
      suite_id: "suite-mq32syem",
      updated_at: new Date(Date.now() - 120_000).toISOString(),
      applied_changed_files: ["src/app/agent-lab/page.tsx"],
      checks_result: "git diff --check recorded",
      checks_run: ["git diff --check"],
    };
    expect(durableRunHasStaleBetweenPromptsGap(run, Date.now(), 45_000)).toBe(true);
    expect(betweenPromptsStaleSummary(run)).toContain("resume from prompt 2");
  });

  it("downgrades PASS without reversal proof", () => {
    expect(
      downgradePassWithoutReversalProof({
        appliedChangedFiles: ["src/app/agent-lab/cards/page.tsx"],
        diskChangedFiles: [],
        expectedOutcome: "edit_reversible",
        reversalAvailable: false,
        reverseDiff: "",
        visibleResultLabel: "PASS",
      }).downgraded,
    ).toBe(true);
  });
});
