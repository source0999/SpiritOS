import { describe, expect, it } from "vitest";

import {
  durableRunInvariantViolations,
  enforceSingleRunningRow,
  promptOrdinal,
} from "@/lib/coding/durable-run-invariants";
import type { DurableCodingRun, DurableCodingRunRow } from "@/lib/coding/durable-run-types";

function row(promptId: string, status: DurableCodingRunRow["status"], resultLabel = ""): DurableCodingRunRow {
  return {
    applied_changed_files: [],
    checks_result: "",
    checks_run: [],
    disk_changed_files: [],
    endpoint_statuses: [],
    error_summary: "",
    generated_diff_present: false,
    model_called_for_generation: "qwen",
    preview_changed_files: [],
    prompt_excerpt: promptId,
    prompt_id: promptId,
    prompt_text: promptId,
    provider_call_made: false,
    reason_code: "",
    result_label: resultLabel,
    reversal_available: false,
    reversal_status: "none",
    started_at: "2026-06-07T00:00:00.000Z",
    status,
    updated_at: "2026-06-07T00:00:00.000Z",
  };
}

function run(overrides: Partial<DurableCodingRun>): DurableCodingRun {
  return {
    applied_changed_files: [],
    benchmark_name: "Messy Coder 10",
    checks_result: "",
    checks_run: [],
    completed_count: 0,
    created_at: "2026-06-07T00:00:00.000Z",
    current_prompt_id: null,
    disk_changed_files: [],
    endpoint_statuses: [],
    final_summary: "",
    frontend_url: "https://10.0.0.186:3000/coding",
    generated_diff_present: false,
    lane: "coder",
    last_error: null,
    model: "qwen",
    model_called_for_generation: "qwen",
    preview_changed_files: [],
    provider: "ollama",
    provider_call_made: false,
    proxy_url: "https://10.0.0.186:8787",
    reason_code: null,
    requested_count: 10,
    reversal_available: false,
    reversal_status: "none",
    rows: [],
    run_id: "suite-invariant",
    started_by_surface: "coding",
    status: "running",
    suite_id: "suite-invariant",
    updated_at: "2026-06-07T00:00:00.000Z",
    ...overrides,
  };
}

describe("durable run invariants", () => {
  it("extracts prompt ordinals from coder prompt ids", () => {
    expect(promptOrdinal("coder-001")).toBe(1);
    expect(promptOrdinal("coder-010")).toBe(10);
    expect(promptOrdinal("custom")).toBeNull();
  });

  it("reports impossible active/terminal states", () => {
    const violations = durableRunInvariantViolations(
      run({
        completed_count: 0,
        current_prompt_id: "coder-001",
        rows: [row("coder-001", "running", "RUNNING"), row("coder-002", "running", "RUNNING")],
        status: "completed",
      }),
    );

    expect(violations).toEqual([
      "multiple_running_rows:coder-001,coder-002",
      "terminal_run_has_running_row:completed:coder-001,coder-002",
      "completed_status_before_full_count:0/10",
    ]);
  });

  it("demotes duplicate running rows and keeps the chosen owner row", () => {
    const enforced = enforceSingleRunningRow(
      [row("coder-006", "running", "RUNNING"), row("coder-008", "running", "RUNNING")],
      "coder-008",
      "2026-06-07T00:01:00.000Z",
    );

    expect(enforced.changed).toBe(true);
    expect(enforced.demoted).toEqual(["coder-006"]);
    expect(enforced.rows.map((item) => `${item.prompt_id}:${item.status}:${item.reason_code}`)).toEqual([
      "coder-006:failed:rejected_duplicate_running_row",
      "coder-008:running:",
    ]);
  });
});
