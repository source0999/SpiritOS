import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  createCodingRun,
  getActiveCodingRun,
  getCodingRun,
  listRecentCodingRuns,
  patchCodingRun,
  upsertCodingRunRow,
} from "@/lib/coding/durable-run-store";

describe("durable coding run store", () => {
  let tempDir = "";
  let previousStore: string | undefined;

  beforeEach(async () => {
    previousStore = process.env.SPIRIT_CODING_RUNS_STORE;
    tempDir = await mkdtemp(path.join(os.tmpdir(), "spirit-coding-runs-"));
    process.env.SPIRIT_CODING_RUNS_STORE = path.join(tempDir, "coding-runs.json");
  });

  afterEach(async () => {
    if (previousStore === undefined) {
      delete process.env.SPIRIT_CODING_RUNS_STORE;
    } else {
      process.env.SPIRIT_CODING_RUNS_STORE = previousStore;
    }
    await rm(tempDir, { force: true, recursive: true });
  });

  it("creates a durable run id and rehydrates active/completed rows", async () => {
    const created = await createCodingRun({
      benchmark_name: "Messy Coder 10",
      requested_count: 1,
      run_id: "suite-sync-1",
      status: "running",
    });

    expect(created.run_id).toBe("suite-sync-1");
    expect(await getActiveCodingRun()).toMatchObject({ run_id: "suite-sync-1" });

    await upsertCodingRunRow("suite-sync-1", "coder-001", {
      applied_changed_files: ["src/app/agent-lab/page.tsx"],
      checks_result: "git diff --check recorded",
      checks_run: ["git diff --check"],
      disk_changed_files: ["src/app/agent-lab/page.tsx"],
      model_called_for_generation: "ollama_chat/qwen2.5-coder:7b",
      preview_changed_files: ["src/app/agent-lab/page.tsx"],
      provider_call_made: true,
      result_label: "PASS",
      reversal_available: true,
      reversal_status: "available",
      run_id: "task-row-1",
      status: "completed",
      step_instrumentation: {
        execute_approved_completed_at: "2026-06-07T00:00:00.000Z",
        last_progress_reason_code: "server_apply_proof_recorded",
        result_finalized_at: "2026-06-07T00:00:01.000Z",
      },
    });

    const withRow = await getCodingRun("suite-sync-1");
    expect(withRow?.rows[0]).toMatchObject({
      prompt_id: "coder-001",
      run_id: "task-row-1",
      provider_call_made: true,
      reversal_available: true,
      step_instrumentation: {
        execute_approved_completed_at: "2026-06-07T00:00:00.000Z",
        last_progress_reason_code: "server_apply_proof_recorded",
        result_finalized_at: "2026-06-07T00:00:01.000Z",
      },
    });

    await patchCodingRun("suite-sync-1", {
      completed_count: 1,
      final_summary: "Finished",
      status: "completed",
    });
    expect(await getActiveCodingRun()).toBeNull();
    expect((await listRecentCodingRuns(1))[0]).toMatchObject({
      completed_count: 1,
      run_id: "suite-sync-1",
      status: "completed",
    });
  });

  it("marks the current running row terminal when a first prompt abort is patched without result rows", async () => {
    await createCodingRun({
      benchmark_name: "Messy Coder 10",
      current_prompt_id: "coder-001",
      requested_count: 10,
      run_id: "suite-timeout-1",
      status: "running",
    });
    await upsertCodingRunRow("suite-timeout-1", "coder-001", {
      model_called_for_generation: "qwen2.5-coder:7b",
      prompt_text: "make a new isolated test",
      prompt_excerpt: "make a new isolated test",
      provider_call_made: false,
      result_label: "RUNNING",
      run_id: "suite-timeout-1:coder-001",
      status: "running",
    });

    await patchCodingRun("suite-timeout-1", {
      final_summary: "Backend failed - model sync timed out",
      last_error: "timeout_source: /v1/decisions/prompt-packet",
      reason_code: "coder_sync_timeout",
      status: "timed_out",
    });

    const run = await getCodingRun("suite-timeout-1");
    expect(run).toMatchObject({
      reason_code: "coder_sync_timeout",
      status: "timed_out",
    });
    expect(run?.rows[0]).toMatchObject({
      error_summary: "timeout_source: /v1/decisions/prompt-packet",
      prompt_id: "coder-001",
      reason_code: "coder_sync_timeout",
      result_label: "NEEDS FIX",
      status: "timed_out",
    });
    expect(await getActiveCodingRun()).toBeNull();
  });

  it("does not let late frontend stale writes downgrade server apply proof", async () => {
    await createCodingRun({
      benchmark_name: "Messy Coder 10",
      current_prompt_id: "coder-001",
      requested_count: 10,
      run_id: "suite-server-proof-race",
      status: "running",
    });
    await upsertCodingRunRow("suite-server-proof-race", "coder-001", {
      applied_changed_files: ["src/app/agent-lab/page.tsx"],
      checks_result: "server apply proof recorded",
      checks_run: ["git diff --check"],
      disk_changed_files: ["src/app/agent-lab/page.tsx"],
      endpoint_statuses: [
        "/v1/actions/execute-approved:200",
        "/v1/actions/execute-approved:server_apply_proof_recorded",
      ],
      preview_changed_files: ["src/app/agent-lab/page.tsx"],
      provider_call_made: true,
      result_label: "PASS",
      reversal_available: true,
      reversal_status: "available",
      run_id: "task-server-proof",
      status: "completed",
      step_instrumentation: {
        last_progress_reason_code: "server_apply_proof_recorded",
        result_finalized_at: "2026-06-07T00:00:00.000Z",
      },
    });

    await upsertCodingRunRow("suite-server-proof-race", "coder-001", {
      endpoint_statuses: [
        "/v1/actions/execute-approved:200",
        "/v1/actions/execute-approved:stale_no_completion",
      ],
      error_summary: "Prompt 1 reached execute-approved without disk/applied proof before the stale deadline.",
      reason_code: "execute_approved_body_read_missing",
      result_label: "NEEDS FIX",
      status: "failed",
      step_instrumentation: {
        last_progress_reason_code: "execute_approved_body_read_missing",
      },
    });

    const run = await getCodingRun("suite-server-proof-race");
    expect(run?.rows[0]).toMatchObject({
      applied_changed_files: ["src/app/agent-lab/page.tsx"],
      disk_changed_files: ["src/app/agent-lab/page.tsx"],
      reason_code: "",
      result_label: "PASS",
      status: "completed",
      step_instrumentation: {
        last_progress_reason_code: "server_apply_proof_recorded",
      },
    });
    expect(run?.rows[0].endpoint_statuses).toContain("/v1/actions/execute-approved:stale_no_completion");
  });

  it("deduplicates patched rows and does not count completed RUNNING placeholders", async () => {
    await createCodingRun({
      benchmark_name: "Messy Coder 10",
      requested_count: 10,
      run_id: "suite-duplicate-rows",
      status: "running",
    });

    await patchCodingRun("suite-duplicate-rows", {
      rows: [
        {
          applied_changed_files: [],
          checks_result: "",
          checks_run: [],
          disk_changed_files: [],
          endpoint_statuses: ["/v1/decisions/prompt-packet:started"],
          error_summary: "",
          generated_diff_present: false,
          model_called_for_generation: "qwen",
          preview_changed_files: [],
          prompt_excerpt: "counter",
          prompt_id: "coder-006",
          prompt_text: "counter",
          provider_call_made: false,
          reason_code: "",
          result_label: "RUNNING",
          reversal_available: false,
          reversal_status: "none",
          run_id: "suite-duplicate-rows:coder-006",
          started_at: "2026-06-07T00:00:00.000Z",
          status: "completed",
          updated_at: "2026-06-07T00:00:00.000Z",
        },
        {
          applied_changed_files: [],
          checks_result: "already_satisfied_without_expected_noop",
          checks_run: ["git diff --check"],
          disk_changed_files: [],
          endpoint_statuses: ["/v1/decisions/prompt-packet:200"],
          error_summary: "reason_code=already_satisfied_without_expected_noop",
          generated_diff_present: false,
          model_called_for_generation: "qwen",
          preview_changed_files: [],
          prompt_excerpt: "counter",
          prompt_id: "coder-006",
          prompt_text: "counter",
          provider_call_made: true,
          reason_code: "already_satisfied_without_expected_noop",
          result_label: "NEEDS FIX",
          reversal_available: false,
          reversal_status: "none",
          run_id: "task-counter",
          started_at: "2026-06-07T00:00:01.000Z",
          status: "failed",
          updated_at: "2026-06-07T00:00:01.000Z",
        },
        {
          applied_changed_files: [],
          checks_result: "",
          checks_run: [],
          disk_changed_files: [],
          endpoint_statuses: ["/v1/decisions/prompt-packet:started"],
          error_summary: "",
          generated_diff_present: false,
          model_called_for_generation: "qwen",
          preview_changed_files: [],
          prompt_excerpt: "notes",
          prompt_id: "coder-008",
          prompt_text: "notes",
          provider_call_made: false,
          reason_code: "",
          result_label: "RUNNING",
          reversal_available: false,
          reversal_status: "none",
          run_id: "suite-duplicate-rows:coder-008",
          started_at: "2026-06-07T00:00:02.000Z",
          status: "completed",
          updated_at: "2026-06-07T00:00:02.000Z",
        },
      ],
    });

    const run = await getCodingRun("suite-duplicate-rows");
    expect(run?.completed_count).toBe(1);
    expect(run?.rows.map((row) => `${row.prompt_id}:${row.status}:${row.result_label}`)).toEqual([
      "coder-006:failed:NEEDS FIX",
      "coder-008:running:RUNNING",
    ]);
  });

  it("does not let late shorter suite patches move progress backward", async () => {
    await createCodingRun({
      benchmark_name: "Messy Coder 10",
      completed_count: 3,
      requested_count: 10,
      run_id: "suite-progress-race",
      status: "running",
    });

    for (const promptId of ["coder-001", "coder-002", "coder-003"]) {
      await upsertCodingRunRow("suite-progress-race", promptId, {
        checks_result: "recorded",
        checks_run: ["git diff --check"],
        model_called_for_generation: "qwen",
        prompt_excerpt: promptId,
        prompt_text: promptId,
        provider_call_made: true,
        result_label: "NEEDS FIX",
        run_id: `suite-progress-race:${promptId}`,
        status: "failed",
      });
    }

    await patchCodingRun("suite-progress-race", {
      completed_count: 2,
      rows: [
        {
          applied_changed_files: [],
          checks_result: "recorded",
          checks_run: ["git diff --check"],
          disk_changed_files: [],
          endpoint_statuses: ["/v1/decisions/prompt-packet:200"],
          error_summary: "no diff",
          generated_diff_present: false,
          model_called_for_generation: "qwen",
          preview_changed_files: [],
          prompt_excerpt: "coder-001",
          prompt_id: "coder-001",
          prompt_text: "coder-001",
          provider_call_made: true,
          reason_code: "",
          result_label: "NEEDS FIX",
          reversal_available: false,
          reversal_status: "none",
          run_id: "suite-progress-race:coder-001",
          started_at: "2026-06-07T00:00:00.000Z",
          status: "failed",
          updated_at: "2026-06-07T00:00:01.000Z",
        },
        {
          applied_changed_files: [],
          checks_result: "recorded",
          checks_run: ["git diff --check"],
          disk_changed_files: [],
          endpoint_statuses: ["/v1/decisions/prompt-packet:200"],
          error_summary: "no diff",
          generated_diff_present: false,
          model_called_for_generation: "qwen",
          preview_changed_files: [],
          prompt_excerpt: "coder-002",
          prompt_id: "coder-002",
          prompt_text: "coder-002",
          provider_call_made: true,
          reason_code: "",
          result_label: "NEEDS FIX",
          reversal_available: false,
          reversal_status: "none",
          run_id: "suite-progress-race:coder-002",
          started_at: "2026-06-07T00:00:02.000Z",
          status: "failed",
          updated_at: "2026-06-07T00:00:03.000Z",
        },
      ],
    });

    const run = await getCodingRun("suite-progress-race");
    expect(run?.completed_count).toBe(3);
    expect(run?.rows.map((row) => row.prompt_id).sort()).toEqual([
      "coder-001",
      "coder-002",
      "coder-003",
    ]);
  });

  it("does not let a late terminal suite patch stop an in-flight next prompt", async () => {
    await createCodingRun({
      benchmark_name: "Messy Coder 10",
      completed_count: 4,
      current_prompt_id: "coder-005",
      requested_count: 10,
      run_id: "suite-terminal-race",
      status: "running",
    });
    await upsertCodingRunRow("suite-terminal-race", "coder-005", {
      model_called_for_generation: "qwen",
      prompt_excerpt: "form",
      prompt_text: "form",
      provider_call_made: false,
      result_label: "RUNNING",
      run_id: "suite-terminal-race:coder-005",
      status: "running",
    });

    await patchCodingRun("suite-terminal-race", {
      completed_count: 4,
      final_summary: "Finished",
      rows: [],
      status: "failed",
    });

    const run = await getCodingRun("suite-terminal-race");
    expect(run).toMatchObject({
      completed_count: 4,
      current_prompt_id: "coder-005",
      status: "running",
    });
    expect(run?.rows[0]).toMatchObject({
      prompt_id: "coder-005",
      result_label: "RUNNING",
      status: "running",
    });

    await patchCodingRun("suite-terminal-race", {
      final_summary: "Cleared by user",
      reason_code: "user_cleared_synced_run",
      status: "cleared",
    });

    expect(await getCodingRun("suite-terminal-race")).toMatchObject({
      completed_count: 4,
      current_prompt_id: null,
      reason_code: "user_cleared_synced_run",
      last_write_decision: "accepted_clear_wins",
      invariant_violations: [],
      status: "cleared",
    });
  });

  it("classifies and demotes duplicate running rows instead of leaving two active prompts", async () => {
    await createCodingRun({
      benchmark_name: "Messy Coder 10",
      current_prompt_id: "coder-006",
      requested_count: 10,
      run_id: "suite-duplicate-running-debug",
      status: "running",
    });
    await upsertCodingRunRow("suite-duplicate-running-debug", "coder-006", {
      model_called_for_generation: "qwen",
      prompt_excerpt: "older",
      prompt_text: "older",
      result_label: "RUNNING",
      status: "running",
    });
    await upsertCodingRunRow("suite-duplicate-running-debug", "coder-008", {
      model_called_for_generation: "qwen",
      prompt_excerpt: "newer",
      prompt_text: "newer",
      result_label: "RUNNING",
      status: "running",
    });

    const run = await getCodingRun("suite-duplicate-running-debug");
    expect(run?.rows.map((row) => `${row.prompt_id}:${row.status}:${row.reason_code}`).sort()).toEqual([
      "coder-006:failed:rejected_duplicate_running_row",
      "coder-008:running:",
    ]);
    expect(run?.invariant_violations).toEqual([]);
    expect(run?.last_write_decision).toBe("accepted_duplicate_running_demoted:coder-006");
    expect(run?.write_debug?.at(-1)).toMatchObject({
      accepted: true,
      decision: "accepted_duplicate_running_demoted:coder-006",
      prompt_id: "coder-008",
      source: "row_upsert",
    });
  });

  it("records rejected late row reopen attempts on terminal runs", async () => {
    await createCodingRun({
      benchmark_name: "Messy Coder 10",
      completed_count: 10,
      current_prompt_id: "coder-010",
      requested_count: 10,
      run_id: "suite-terminal-debug",
      status: "completed",
    });

    await upsertCodingRunRow("suite-terminal-debug", "coder-010", {
      model_called_for_generation: "qwen",
      prompt_excerpt: "late",
      prompt_text: "late",
      result_label: "RUNNING",
      status: "running",
    });

    const run = await getCodingRun("suite-terminal-debug");
    expect(run).toMatchObject({
      completed_count: 10,
      last_write_decision: "rejected_terminal_row_reopen",
      status: "completed",
    });
    expect(run?.write_debug?.at(-1)).toMatchObject({
      accepted: false,
      decision: "rejected_terminal_row_reopen",
      prompt_id: "coder-010",
      source: "row_upsert",
    });
  });

  it("blocks completed terminal patches before the requested count", async () => {
    await createCodingRun({
      benchmark_name: "Messy Coder 10",
      current_prompt_id: "coder-001",
      requested_count: 10,
      run_id: "suite-completed-before-full-count",
      status: "running",
    });
    await upsertCodingRunRow("suite-completed-before-full-count", "coder-001", {
      error_summary: "user_clicked_stop_suite",
      model_called_for_generation: "qwen",
      prompt_excerpt: "first",
      prompt_text: "first",
      provider_call_made: false,
      reason_code: "user_clicked_stop_suite",
      result_label: "FAILED",
      status: "failed",
    });

    await patchCodingRun("suite-completed-before-full-count", {
      completed_count: 0,
      final_summary: "Finished",
      status: "completed",
    });

    const run = await getCodingRun("suite-completed-before-full-count");
    expect(run).toMatchObject({
      completed_count: 1,
      invariant_violations: [],
      last_write_decision: "accepted_completed_terminal_blocked_before_full_count",
      reason_code: "completed_before_requested_count_blocked",
      status: "failed",
    });
  });

  it("keeps the current prompt on the newest in-flight row when an older row finishes late", async () => {
    await createCodingRun({
      benchmark_name: "Messy Coder 10",
      completed_count: 5,
      current_prompt_id: "coder-007",
      requested_count: 10,
      run_id: "suite-current-pointer-race",
      status: "running",
    });
    await upsertCodingRunRow("suite-current-pointer-race", "coder-007", {
      model_called_for_generation: "qwen",
      prompt_excerpt: "newer",
      prompt_text: "newer",
      provider_call_made: false,
      result_label: "RUNNING",
      run_id: "suite-current-pointer-race:coder-007",
      status: "running",
    });

    await upsertCodingRunRow("suite-current-pointer-race", "coder-006", {
      checks_result: "recorded",
      checks_run: ["git diff --check"],
      model_called_for_generation: "qwen",
      prompt_excerpt: "older",
      prompt_text: "older",
      provider_call_made: true,
      result_label: "NEEDS FIX",
      run_id: "suite-current-pointer-race:coder-006",
      status: "failed",
    });

    const run = await getCodingRun("suite-current-pointer-race");
    expect(run).toMatchObject({
      completed_count: 1,
      current_prompt_id: "coder-007",
      status: "running",
    });
    expect(run?.rows.map((row) => `${row.prompt_id}:${row.status}`).sort()).toEqual([
      "coder-006:failed",
      "coder-007:running",
    ]);
  });

  it("does not move current prompt backward when the previous current row finishes after the next prompt starts", async () => {
    await createCodingRun({
      benchmark_name: "Messy Coder 10",
      completed_count: 2,
      current_prompt_id: "coder-003",
      requested_count: 10,
      run_id: "suite-current-previous-finishes-late",
      status: "running",
    });
    await upsertCodingRunRow("suite-current-previous-finishes-late", "coder-004", {
      model_called_for_generation: "qwen",
      prompt_excerpt: "new prompt",
      prompt_text: "new prompt",
      provider_call_made: false,
      result_label: "RUNNING",
      run_id: "suite-current-previous-finishes-late:coder-004",
      status: "running",
    });
    await upsertCodingRunRow("suite-current-previous-finishes-late", "coder-003", {
      checks_result: "recorded",
      checks_run: ["git diff --check"],
      model_called_for_generation: "qwen",
      prompt_excerpt: "previous prompt",
      prompt_text: "previous prompt",
      provider_call_made: true,
      result_label: "PASS",
      run_id: "suite-current-previous-finishes-late:coder-003",
      status: "completed",
    });

    const run = await getCodingRun("suite-current-previous-finishes-late");
    expect(run).toMatchObject({
      current_prompt_id: "coder-004",
      invariant_violations: [],
      status: "running",
    });
    expect(run?.rows.map((row) => `${row.prompt_id}:${row.status}`).sort()).toEqual([
      "coder-003:completed",
      "coder-004:running",
    ]);
  });

  it("does not reopen a terminal run from a late running suite patch", async () => {
    await createCodingRun({
      benchmark_name: "Messy Coder 10",
      completed_count: 10,
      current_prompt_id: "coder-010",
      final_summary: "Finished",
      requested_count: 10,
      run_id: "suite-terminal-reopen-patch",
      status: "failed",
    });
    await patchCodingRun("suite-terminal-reopen-patch", {
      completed_count: 10,
      rows: Array.from({ length: 10 }, (_, index) => {
        const promptId = `coder-${String(index + 1).padStart(3, "0")}`;
        return {
          applied_changed_files: [],
          checks_result: "not run",
          checks_run: [],
          disk_changed_files: [],
          endpoint_statuses: ["/v1/decisions/prompt-packet:200"],
          error_summary: "",
          generated_diff_present: false,
          model_called_for_generation: "qwen",
          preview_changed_files: [],
          prompt_excerpt: "done",
          prompt_id: promptId,
          prompt_text: "done",
          provider_call_made: true,
          reason_code: "",
          result_label: "NEEDS FIX",
          reversal_available: false,
          reversal_status: "none",
          run_id: `suite-terminal-reopen-patch:${promptId}`,
          started_at: "2026-06-07T00:00:00.000Z",
          status: "failed" as const,
          updated_at: "2026-06-07T00:00:01.000Z",
        };
      }),
    });

    await patchCodingRun("suite-terminal-reopen-patch", {
      completed_count: 9,
      current_prompt_id: "coder-010",
      final_summary: "Running prompt-packet",
      rows: [
        {
          applied_changed_files: [],
          checks_result: "",
          checks_run: [],
          disk_changed_files: [],
          endpoint_statuses: ["/v1/decisions/prompt-packet:started"],
          error_summary: "",
          generated_diff_present: false,
          model_called_for_generation: "qwen",
          preview_changed_files: [],
          prompt_excerpt: "late",
          prompt_id: "coder-010",
          prompt_text: "late",
          provider_call_made: false,
          reason_code: "",
          result_label: "RUNNING",
          reversal_available: false,
          reversal_status: "none",
          run_id: "suite-terminal-reopen-patch:coder-010-late",
          started_at: "2026-06-07T00:00:10.000Z",
          status: "running",
          updated_at: "2026-06-07T00:00:11.000Z",
        },
      ],
      status: "running",
    });

    const run = await getCodingRun("suite-terminal-reopen-patch");
    expect(run).toMatchObject({
      completed_count: 10,
      current_prompt_id: "coder-010",
      final_summary: "Finished",
      status: "failed",
    });
    expect(run?.rows.at(-1)).toMatchObject({ prompt_id: "coder-010", status: "failed" });
  });

  it("does not reopen a terminal run from a late running row upsert", async () => {
    await createCodingRun({
      benchmark_name: "Messy Coder 10",
      completed_count: 10,
      current_prompt_id: "coder-010",
      final_summary: "Finished",
      requested_count: 10,
      run_id: "suite-terminal-reopen-row",
      status: "failed",
    });
    await patchCodingRun("suite-terminal-reopen-row", {
      completed_count: 10,
      rows: Array.from({ length: 10 }, (_, index) => {
        const promptId = `coder-${String(index + 1).padStart(3, "0")}`;
        return {
          applied_changed_files: [],
          checks_result: "not run",
          checks_run: [],
          disk_changed_files: [],
          endpoint_statuses: ["/v1/decisions/prompt-packet:200"],
          error_summary: "",
          generated_diff_present: false,
          model_called_for_generation: "qwen",
          preview_changed_files: [],
          prompt_excerpt: "done",
          prompt_id: promptId,
          prompt_text: "done",
          provider_call_made: true,
          reason_code: "",
          result_label: "NEEDS FIX",
          reversal_available: false,
          reversal_status: "none",
          run_id: `suite-terminal-reopen-row:${promptId}`,
          started_at: "2026-06-07T00:00:00.000Z",
          status: "failed" as const,
          updated_at: "2026-06-07T00:00:01.000Z",
        };
      }),
    });

    await upsertCodingRunRow("suite-terminal-reopen-row", "coder-010", {
      model_called_for_generation: "qwen",
      prompt_excerpt: "late",
      prompt_text: "late",
      provider_call_made: false,
      result_label: "RUNNING",
      run_id: "suite-terminal-reopen-row:coder-010-late",
      status: "running",
    });

    const run = await getCodingRun("suite-terminal-reopen-row");
    expect(run).toMatchObject({
      completed_count: 10,
      current_prompt_id: "coder-010",
      final_summary: "Finished",
      status: "failed",
    });
    expect(run?.rows.at(-1)).toMatchObject({ prompt_id: "coder-010", status: "failed" });
  });

  it("treats cleared runs as terminal so another device does not attach to them", async () => {
    await createCodingRun({
      benchmark_name: "Messy Coder 10",
      requested_count: 10,
      run_id: "suite-cleared-1",
      status: "running",
    });

    await patchCodingRun("suite-cleared-1", {
      final_summary: "Run cleared from synced coding cloud.",
      reason_code: "user_cleared_synced_run",
      status: "cleared",
    });

    expect(await getActiveCodingRun()).toBeNull();
    expect((await listRecentCodingRuns(1))[0]).toMatchObject({
      reason_code: "user_cleared_synced_run",
      run_id: "suite-cleared-1",
      status: "cleared",
    });
  });

  it("preserves row progress when a run patch and row upsert happen concurrently", async () => {
    await createCodingRun({
      benchmark_name: "Messy Coder 10",
      current_prompt_id: "coder-001",
      requested_count: 10,
      run_id: "suite-race-1",
      status: "running",
    });
    await upsertCodingRunRow("suite-race-1", "coder-001", {
      model_called_for_generation: "qwen2.5-coder:7b",
      prompt_text: "make a new isolated test",
      prompt_excerpt: "make a new isolated test",
      provider_call_made: false,
      result_label: "RUNNING",
      run_id: "suite-race-1:coder-001",
      status: "running",
    });

    await Promise.all([
      upsertCodingRunRow("suite-race-1", "coder-001", {
        endpoint_statuses: ["/v1/tasks/long-running:200"],
        model_called_for_generation: "ollama_chat/qwen2.5-coder:7b",
        provider_call_made: false,
        result_label: "RUNNING",
        status: "running",
      }),
      patchCodingRun("suite-race-1", {
        endpoint_statuses: ["/v1/tasks/long-running:200"],
        final_summary: "Reading request",
        model_called_for_generation: "ollama_chat/qwen2.5-coder:7b",
        status: "running",
      }),
    ]);

    const run = await getCodingRun("suite-race-1");
    expect(run).toMatchObject({
      endpoint_statuses: ["/v1/tasks/long-running:200"],
      final_summary: "Reading request",
      status: "running",
    });
    expect(run?.rows[0]).toMatchObject({
      endpoint_statuses: ["/v1/tasks/long-running:200"],
      model_called_for_generation: "ollama_chat/qwen2.5-coder:7b",
      prompt_id: "coder-001",
      status: "running",
    });
  });
});
