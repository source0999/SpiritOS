import { execFile } from "node:child_process";
import { mkdir, appendFile } from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export const runtime = "nodejs";

const execFileAsync = promisify(execFile);
const SAFE_BRANCH_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._/-]{0,119}$/u;

type RouteContext = {
  params: Promise<{
    recommendationId: string;
  }>;
};

export async function POST(request: Request, context: RouteContext) {
  const { recommendationId } = await context.params;
  const requestText = await request.text();
  const response = await sourceProxyFetch(
    `/v1/cartographer/branch-recommendations/${encodeURIComponent(recommendationId)}/approve`,
    {
      body: requestText,
      headers: {
        "content-type": request.headers.get("content-type") ?? "application/json",
      },
      method: "POST",
    },
  );

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
    const approvalRequest = JSON.parse(requestText) as Record<string, unknown>;
    const payload = JSON.parse(responseText) as Record<string, unknown>;
    if (shouldCreateBranchFromRecordedApproval(payload, approvalRequest)) {
      const createdPayload = await createApprovedBranch(payload, recommendationId);
      return Response.json(createdPayload);
    }
  } catch (error) {
    if (error instanceof BranchApprovalRouteError) {
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

function shouldCreateBranchFromRecordedApproval(
  payload: Record<string, unknown>,
  approvalRequest: Record<string, unknown>,
) {
  return (
    approvalRequest.approved === true &&
    payload.status === "approval_recorded" &&
    payload.approval_kind === "branch" &&
    payload.branch_created !== true
  );
}

async function createApprovedBranch(payload: Record<string, unknown>, recommendationId: string) {
  const item = asRecord(payload.item);
  const branchName = String(item?.suggested_branch ?? "");
  validateSafeBranchName(branchName);

  const repoRoot = process.cwd();
  const previousBranch = (await git(repoRoot, ["branch", "--show-current"])).stdout.trim() || null;
  const branchExists = await gitBranchExists(repoRoot, branchName);
  if (branchExists) {
    throw new BranchApprovalRouteError(
      "Recommended branch already exists; Cartographer will not overwrite it.",
      "branch_already_exists",
    );
  }

  await git(repoRoot, ["switch", "-c", branchName]);
  const approvedAt = new Date().toISOString().replace(/\.\d{3}Z$/u, "Z");
  const approvedBy = String(payload.approved_by ?? "cartographer-ui");
  await appendGitApprovalAudit(repoRoot, {
    action_taken: true,
    approval_kind: "branch",
    approved_at: approvedAt,
    approved_by: approvedBy,
    branch: branchName,
    branch_created: true,
    changed_files: Array.isArray(item?.related_files) ? item.related_files : [],
    commit_created: false,
    event: "branch_created",
    item_id: recommendationId,
    previous_branch: previousBranch,
    project_id: String(item?.project_id ?? "spiritos"),
    push_ran: false,
    remote: null,
    result: "branch_created",
  });

  return {
    ...payload,
    status: "branch_created",
    write_actions_enabled: true,
    approved_at: approvedAt,
    branch: branchName,
    previous_branch: previousBranch,
    actions_taken: true,
    branch_created: true,
    commit_created: false,
    push_ran: false,
    committed: false,
    pushed: false,
    next_step: "Branch created; review the dirty tree before approving any commit.",
    safety: {
      approval_recorded: true,
      branch_creation_enabled: true,
      commit_enabled: false,
      push_enabled: false,
    },
  };
}

function validateSafeBranchName(branchName: string) {
  const unsafe =
    !SAFE_BRANCH_PATTERN.test(branchName) ||
    branchName.includes("..") ||
    branchName.includes("@{") ||
    branchName.includes("\\") ||
    branchName.includes("//") ||
    branchName.endsWith("/") ||
    branchName.endsWith(".") ||
    branchName.endsWith(".lock") ||
    branchName.split("/").some((part) => !part || part === "." || part === ".." || part.endsWith(".lock"));
  if (unsafe) {
    throw new BranchApprovalRouteError(
      "Recommended branch name is not a valid safe Git branch name.",
      "unsafe_branch_name",
    );
  }
}

async function gitBranchExists(repoRoot: string, branchName: string) {
  try {
    await git(repoRoot, ["rev-parse", "--verify", "--quiet", `refs/heads/${branchName}`]);
    return true;
  } catch {
    return false;
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
    const message = String(output?.stderr || output?.stdout || "Git branch approval command failed.");
    throw new BranchApprovalRouteError(message.trim(), "git_branch_create_failed");
  }
}

async function appendGitApprovalAudit(repoRoot: string, event: Record<string, unknown>) {
  const auditPath = path.join(repoRoot, "data", "cartographer_git_approvals.audit.jsonl");
  await mkdir(path.dirname(auditPath), { recursive: true });
  await appendFile(auditPath, `${JSON.stringify(event, Object.keys(event).sort())}\n`, "utf8");
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : null;
}

class BranchApprovalRouteError extends Error {
  constructor(
    message: string,
    readonly reasonCode: string,
  ) {
    super(message);
  }
}
