import { execFile } from "node:child_process";
import { appendFile, mkdir, stat } from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export const runtime = "nodejs";

const execFileAsync = promisify(execFile);

type RouteContext = {
  params: Promise<{
    commitProposalId: string;
  }>;
};

export async function POST(request: Request, context: RouteContext) {
  const { commitProposalId } = await context.params;
  const requestText = await request.text();
  let approvalRequest: Record<string, unknown>;
  try {
    approvalRequest = JSON.parse(requestText) as Record<string, unknown>;
  } catch {
    return Response.json(
      {
        detail: {
          message: "Commit approval request body must be valid JSON.",
          reason_code: "invalid_json",
        },
      },
      { status: 422 },
    );
  }

  let response;
  try {
    response = await sourceProxyFetch(
      `/v1/cartographer/commit-proposals/${encodeURIComponent(commitProposalId)}/approve`,
      {
        body: requestText,
        headers: {
          "content-type": request.headers.get("content-type") ?? "application/json",
        },
        method: "POST",
      },
    );
  } catch (error) {
    if (approvalRequest.approved === true) {
      try {
        const fallbackPayload = await fallbackApprovalPayload(commitProposalId, approvalRequest);
        const createdPayload = await createApprovedCommit(fallbackPayload, commitProposalId);
        return Response.json(createdPayload);
      } catch (fallbackError) {
        if (fallbackError instanceof CommitApprovalRouteError) {
          return Response.json(
            {
              detail: {
                message: fallbackError.message,
                reason_code: fallbackError.reasonCode,
              },
            },
            { status: 422 },
          );
        }
      }
    }
    return Response.json(
      {
        detail: {
          message: "The dashboard could not reach the Source Proxy commit approval endpoint.",
          reason_code: "source_proxy_unavailable",
          error: error instanceof Error ? error.message : "Unknown connection error.",
        },
      },
      { status: 502 },
    );
  }

  const responseText = await response.text();
  const contentType = response.headers.get("content-type") ?? "application/json";
  if (!contentType.includes("application/json")) {
    return new Response(responseText, {
      headers: {
        "content-type": contentType,
      },
      status: response.status,
      statusText: response.statusText,
    });
  }

  try {
    const payload = JSON.parse(responseText) as Record<string, unknown>;
    if (shouldCreateCommitFromRecordedApproval(payload, approvalRequest)) {
      const createdPayload = await createApprovedCommit(payload, commitProposalId);
      return Response.json(createdPayload);
    }
  } catch (error) {
    if (error instanceof CommitApprovalRouteError) {
      return Response.json(
        {
          detail: {
            message: error.message,
            reason_code: error.reasonCode,
          },
        },
        { status: 422 },
      );
    }
  }

  return new Response(responseText, {
    headers: {
      "content-type": contentType,
    },
    status: response.status,
    statusText: response.statusText,
  });
}

async function fallbackApprovalPayload(
  commitProposalId: string,
  approvalRequest: Record<string, unknown>,
) {
  let response;
  try {
    response = await sourceProxyFetch("/v1/cartographer/commit-proposals", {
      method: "GET",
    });
  } catch (error) {
    throw new CommitApprovalRouteError(
      error instanceof Error ? error.message : "Could not load commit proposal fallback.",
      "source_proxy_unavailable",
    );
  }
  const payload = (await response.json()) as Record<string, unknown>;
  const proposals = Array.isArray(payload.commit_proposals) ? payload.commit_proposals : [];
  const item = proposals.find((proposal) => {
    return asRecord(proposal)?.commit_proposal_id === commitProposalId;
  });
  if (!item) {
    throw new CommitApprovalRouteError(
      "Requested Cartographer commit proposal was not found.",
      "approval_item_not_found",
    );
  }
  return {
    status: "approval_recorded",
    write_actions_enabled: false,
    approval_kind: "commit",
    item_id: commitProposalId,
    approved_by: String(approvalRequest.approved_by ?? "cartographer-ui"),
    item,
    actions_taken: false,
    branch_created: false,
    commit_created: false,
    push_ran: false,
  };
}

function shouldCreateCommitFromRecordedApproval(
  payload: Record<string, unknown>,
  approvalRequest: Record<string, unknown>,
) {
  return (
    approvalRequest.approved === true &&
    payload.status === "approval_recorded" &&
    payload.approval_kind === "commit" &&
    payload.commit_created !== true
  );
}

async function createApprovedCommit(payload: Record<string, unknown>, commitProposalId: string) {
  const item = asRecord(payload.item);
  const files = approvalFiles(item);
  const message = String(item?.suggested_message ?? "").trim();
  if (files.length === 0) {
    throw new CommitApprovalRouteError("Commit proposal has no files to commit.", "commit_proposal_empty");
  }
  if (!message) {
    throw new CommitApprovalRouteError("Commit proposal has no approved commit message.", "commit_message_required");
  }

  const repoRoot = process.cwd();
  const checks = await runCommitChecks(repoRoot, files);
  const failed = checks.find((check) => check.status === "failed");
  if (failed) {
    throw new CommitApprovalRouteError(failed.summary, failed.id);
  }

  await git(repoRoot, ["add", "--", ...files]);
  await git(repoRoot, ["commit", "-m", message]);
  const commitSha = (await git(repoRoot, ["rev-parse", "HEAD"])).stdout.trim();
  const branch = (await git(repoRoot, ["branch", "--show-current"])).stdout.trim() || null;
  const approvedAt = new Date().toISOString().replace(/\.\d{3}Z$/u, "Z");
  const approvedBy = String(payload.approved_by ?? "cartographer-ui");
  await appendGitApprovalAudit(repoRoot, {
    action_taken: true,
    approval_kind: "commit",
    approved_at: approvedAt,
    approved_by: approvedBy,
    branch,
    branch_created: false,
    changed_files: files,
    checks,
    commit_created: true,
    commit_message: message,
    commit_sha: commitSha,
    event: "commit_created",
    item_id: commitProposalId,
    project_id: String(item?.project_id ?? "spiritos"),
    push_ran: false,
    remote: null,
    result: "commit_created",
  });

  return {
    ...payload,
    status: "commit_created",
    write_actions_enabled: true,
    approved_at: approvedAt,
    branch,
    commit_sha: commitSha,
    commit_message: message,
    checks,
    actions_taken: true,
    branch_created: false,
    commit_created: true,
    push_ran: false,
    committed: true,
    pushed: false,
    next_step: "Commit created after checks; review push queue before approving any push.",
    safety: {
      approval_recorded: true,
      branch_creation_enabled: false,
      commit_enabled: true,
      push_enabled: false,
    },
  };
}

function approvalFiles(item: Record<string, unknown> | null) {
  const values = Array.isArray(item?.files) ? item.files : [];
  return values
    .map((value) => String(value).trim().replace(/\\/gu, "/"))
    .filter((value) => value && !value.startsWith("/") && !value.split("/").includes(".."));
}

async function runCommitChecks(repoRoot: string, files: string[]) {
  const checks = [await runCheck(repoRoot, "git_diff_check", "git diff --check", ["git", "diff", "--check", "--", ...files])];
  if (await exists(path.join(repoRoot, "scripts", "validate-blueprints.mjs"))) {
    checks.push(
      await runCheck(repoRoot, "blueprint_metadata_validation", "npm run validate:blueprints", [
        "node",
        "scripts/validate-blueprints.mjs",
      ]),
    );
  }
  if (
    (await exists(path.join(repoRoot, "source_proxy", "tests", "test_cartographer_api.py"))) &&
    (await exists(path.join(repoRoot, "source_proxy", "tests", "test_cartographer_safety_audit.py")))
  ) {
    checks.push(
      await runCheck(repoRoot, "cartographer_pytest", "python -m pytest Cartographer tests", [
        resolvePython(),
        "-m",
        "pytest",
        "source_proxy/tests/test_cartographer_api.py",
        "source_proxy/tests/test_cartographer_safety_audit.py",
      ], 180_000),
    );
  }
  return checks;
}

async function runCheck(repoRoot: string, id: string, label: string, command: string[], timeout = 30_000) {
  try {
    const result = await execFileAsync(command[0], command.slice(1), {
      cwd: repoRoot,
      timeout,
    });
    const summary = (result.stdout || result.stderr || "").trim();
    return {
      id,
      label,
      required: true,
      status: "passed" as const,
      summary: summary || `${label} passed.`,
    };
  } catch (error) {
    const output = asRecord(error);
    const summary = String(output?.stderr || output?.stdout || `${label} failed.`).trim();
    return {
      id,
      label,
      required: true,
      status: "failed" as const,
      summary,
    };
  }
}

async function git(repoRoot: string, args: string[]) {
  try {
    return await execFileAsync("git", args, {
      cwd: repoRoot,
      timeout: 30_000,
    });
  } catch (error) {
    const output = asRecord(error);
    const message = String(output?.stderr || output?.stdout || "Git commit approval command failed.");
    throw new CommitApprovalRouteError(message.trim(), "git_commit_failed");
  }
}

async function exists(filePath: string) {
  try {
    await stat(filePath);
    return true;
  } catch {
    return false;
  }
}

function resolvePython() {
  return process.env.SOURCE_PROXY_PYTHON ?? "python3";
}

async function appendGitApprovalAudit(repoRoot: string, event: Record<string, unknown>) {
  const auditPath = path.join(repoRoot, "data", "cartographer_git_approvals.audit.jsonl");
  await mkdir(path.dirname(auditPath), { recursive: true });
  await appendFile(auditPath, `${JSON.stringify(event, Object.keys(event).sort())}\n`, "utf8");
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : null;
}

class CommitApprovalRouteError extends Error {
  constructor(
    message: string,
    readonly reasonCode: string,
  ) {
    super(message);
  }
}
