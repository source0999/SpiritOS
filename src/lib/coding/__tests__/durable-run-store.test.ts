import { createHash } from "node:crypto";

import { beforeEach, describe, expect, it, vi } from "vitest";

import { sourceProxyFetch } from "@/lib/source-proxy-origin";
import {
  NonAuthoritativeCodingRunMutationError,
  createCodingRun,
  listRecentCodingRuns,
  patchCodingRun,
  projectSourceProxyTaskEnvelope,
  upsertCodingRunRow,
} from "@/lib/coding/durable-run-store";

vi.mock("@/lib/source-proxy-origin", () => ({ sourceProxyFetch: vi.fn() }));

const mockedSourceProxyFetch = vi.mocked(sourceProxyFetch);
const sourceResponse = (
  body: BodyInit | null,
  init?: ResponseInit,
): Awaited<ReturnType<typeof sourceProxyFetch>> =>
  new Response(body, init) as unknown as Awaited<ReturnType<typeof sourceProxyFetch>>;
const participantRoles = [
  "coding-executor",
  "coding-reviewer",
  "coding-verifier",
  "coding-anti-cheat",
  "evidence-recorder",
];
const laneIds = [
  "context-broker",
  "planner",
  "coder",
  "reviewer",
  "verifier",
  "anti-cheat",
  "repair",
  "evidence-recorder",
];

function canonicalJson(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value) ?? "null";
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  const record = value as Record<string, unknown>;
  return `{${Object.keys(record)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${canonicalJson(record[key])}`)
    .join(",")}}`;
}

function sha256Json(value: unknown): string {
  return `sha256:${createHash("sha256").update(canonicalJson(value), "utf8").digest("hex")}`;
}

function taskEnvelope(
  status: string,
  options: { completeEvidence?: boolean; taskId?: string; description?: string } = {},
) {
  const taskId = options.taskId ?? "task-authoritative-1";
  const complete = options.completeEvidence === true;
  const runId = `coding-run-${taskId}`;
  const approvalId = `approval-${taskId}`;
  const artifactSha256 = `sha256:${"a".repeat(64)}`;
  const proofBody = {
    schema_version: "coding.production-proof/v1",
    task_id: taskId,
    run_id: runId,
    source_head: "b".repeat(40),
    target_plugin_proposal_sha256: `sha256:${"c".repeat(64)}`,
    model_invocation_id: "model-invocation-1",
    model_output_id: "model-output-1",
    cartographer_proposal_id: "proposal-1",
    cartographer_selection_id: "selection-1",
    cartographer_transfer_event_id: "transfer-1",
    recovery_id: null,
    participant_invocation_ids: participantRoles.map((_role, index) => `invocation-${index}`),
    artifact_sha256: artifactSha256,
    approval_id: approvalId,
    failures: [],
    terminal_proof_eligible: true,
    claim_ceiling: "model_authored_applied_diff_verified",
  };
  const productionProof = { ...proofBody, proof_sha256: sha256Json(proofBody) };
  const outputs = participantRoles.map((role, index) => ({
    output_id: `output-${index}`,
    producer: role,
  }));
  return {
    access_scope: "read_only_task_status_tracking",
    task: {
      id: taskId,
      status,
      created_at: "2026-07-17T10:00:00Z",
      updated_at: "2026-07-17T10:01:00Z",
      description: options.description ?? "Apply the bounded coding change",
      next_action: status === "completed" ? "Done" : "Continue through backend gates",
      post_apply_verification: {
        status: complete ? "verified" : "verification_ready",
        changed_files: ["src/example.ts"],
        checks: [{ id: "typecheck", required: true, status: complete ? "passed" : "pending" }],
      },
      ast_snapshot: {
        coding_artifact: {
          model: "qwen-coder",
          provider: "ollama",
          artifact_sha256: artifactSha256,
          approval_id: approvalId,
        },
        coding_orchestrator: {
          schema_version: complete ? "coding-orchestrator/v2" : "coding-orchestrator/v1",
          authoritative: complete,
          run_id: runId,
          summary: "Backend-authored summary",
          lane_states: Object.fromEntries(
            laneIds.map((lane) => [lane, complete ? (lane === "repair" ? "skipped" : "completed") : "running"]),
          ),
        },
        campaign_2_approval: {
          approval_id: approvalId,
          state: complete ? "consumed" : "consuming",
        },
        approved_execution_evidence: {
          final_truth_status: complete ? "GO" : "PENDING_PARTICIPANTS",
          commit_safe: complete,
          terminal_proof_eligible: complete,
          production_proof_sha256: complete ? productionProof.proof_sha256 : null,
          audit: { changed_files: ["src/example.ts"] },
        },
        coding_production_proof: complete ? productionProof : {},
        coding_participant_records: complete
          ? participantRoles.map((role, index) => ({
              role,
              passed: true,
              invocation_id: `invocation-${index}`,
              output_id: `participant-output-${index}`,
              consumer_acknowledgement_id: `ack-${index}`,
            }))
          : [],
        coding_runtime_outputs: complete ? outputs : [],
        coding_runtime_consumptions: complete
          ? outputs.map((output, index) => ({ consumption_id: `consume-${index}`, output_id: output.output_id }))
          : [],
      },
    },
  };
}

describe("Source Proxy coding-run projection", () => {
  beforeEach(() => {
    mockedSourceProxyFetch.mockReset();
  });

  it("never promotes apply-only backend state to PASS or completed", () => {
    const run = projectSourceProxyTaskEnvelope(taskEnvelope("applied_needs_verification"));

    expect(run).toMatchObject({
      status: "running",
      completed_count: 0,
      reason_code: "post_apply_verification_required",
      backend_authority: {
        owner: "source_proxy",
        projection: "read_only",
        source_status: "applied_needs_verification",
        terminal_success: false,
      },
    });
    expect(run?.rows[0]).toMatchObject({ status: "running", result_label: "PENDING" });
  });

  it("projects completed only when verification, approval, participants, lanes, and consumption all agree", () => {
    const incomplete = projectSourceProxyTaskEnvelope(taskEnvelope("completed"));
    const complete = projectSourceProxyTaskEnvelope(
      taskEnvelope("completed", { completeEvidence: true }),
    );

    expect(incomplete).toMatchObject({
      status: "failed",
      reason_code: "backend_terminal_evidence_incomplete",
      backend_authority: { terminal_success: false },
    });
    expect(complete).toMatchObject({
      status: "completed",
      completed_count: 1,
      reason_code: null,
      backend_authority: { terminal_success: true },
    });
    expect(complete?.rows[0].result_label).toBe("PASS");
  });

  it("fails closed when terminal production proof is absent or re-sealed incorrectly", () => {
    const missing = taskEnvelope("completed", { completeEvidence: true });
    missing.task.ast_snapshot.coding_production_proof = {};
    const tampered = taskEnvelope("completed", { completeEvidence: true });
    (tampered.task.ast_snapshot.coding_production_proof as Record<string, unknown>).claim_ceiling =
      "forged_terminal_claim";

    for (const envelope of [missing, tampered]) {
      expect(projectSourceProxyTaskEnvelope(envelope)).toMatchObject({
        status: "failed",
        reason_code: "backend_terminal_evidence_incomplete",
        backend_authority: { terminal_success: false },
      });
    }
  });

  it("discards mutation-shaped PASS/completed input and returns backend truth", async () => {
    mockedSourceProxyFetch.mockImplementation(async () =>
      sourceResponse(JSON.stringify(taskEnvelope("applied_needs_verification")), { status: 200 }),
    );

    const patched = await patchCodingRun("task-authoritative-1", {
      status: "completed",
      completed_count: 99,
    });
    const rowUpsert = await upsertCodingRunRow("task-authoritative-1", "forged-prompt", {
      status: "completed",
      result_label: "PASS",
    });

    expect(patched?.status).toBe("running");
    expect(rowUpsert?.status).toBe("running");
    expect(rowUpsert?.rows[0].result_label).toBe("PENDING");
    expect(mockedSourceProxyFetch).toHaveBeenCalledTimes(2);
  });

  it("fails closed instead of creating a local JSON run", async () => {
    await expect(createCodingRun({ status: "completed" })).rejects.toBeInstanceOf(
      NonAuthoritativeCodingRunMutationError,
    );
    expect(mockedSourceProxyFetch).not.toHaveBeenCalled();
  });

  it("bounds the requested run count, detail fanout, strings, and output rows", async () => {
    const taskIds = Array.from({ length: 60 }, (_, index) => `task-${index}`);
    mockedSourceProxyFetch.mockImplementation(async (path) => {
      if (path.startsWith("/v1/tasks/long-running?")) {
        return sourceResponse(
          JSON.stringify({ tasks: taskIds.map((task_id) => ({ task_id })) }),
          { status: 200 },
        );
      }
      const taskId = decodeURIComponent(path.split("/").at(-1) ?? "");
      return sourceResponse(
        JSON.stringify(taskEnvelope("running", { taskId, description: "x".repeat(10_000) })),
        { status: 200 },
      );
    });

    const runs = await listRecentCodingRuns(999);

    expect(mockedSourceProxyFetch.mock.calls[0][0]).toContain("limit=50");
    expect(mockedSourceProxyFetch).toHaveBeenCalledTimes(51);
    expect(runs).toHaveLength(50);
    expect(runs.every((run) => run.rows.length === 1)).toBe(true);
    expect(runs.every((run) => run.benchmark_name.length <= 160)).toBe(true);
  });
});
