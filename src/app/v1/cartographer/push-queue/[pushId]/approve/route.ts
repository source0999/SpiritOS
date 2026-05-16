import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { appendFile, mkdir } from "node:fs/promises";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export const runtime = "nodejs";

const execFileAsync = promisify(execFile);
const SAFE_BRANCH_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._/-]{0,119}$/u;

type RouteContext = {
  params: Promise<{
    pushId: string;
  }>;
};

export async function POST(request: Request, context: RouteContext) {
  const { pushId } = await context.params;
  const requestText = await request.text();
  let approvalRequest: Record<string, unknown>;
  try {
    approvalRequest = JSON.parse(requestText) as Record<string, unknown>;
  } catch {
    return Response.json(
      {
        detail: {
          message: "Push approval request body must be valid JSON.",
          reason_code: "invalid_json",
        },
      },
      { status: 422 },
    );
  }

  let response;
  try {
    response = await sourceProxyFetch(
      `/v1/cartographer/push-queue/${encodeURIComponent(pushId)}/approve`,
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
        const fallbackPayload = await fallbackApprovalPayload(pushId, approvalRequest);
        const pushedPayload = await runApprovedPush(fallbackPayload, pushId);
        return Response.json(pushedPayload);
      } catch (fallbackError) {
        if (fallbackError instanceof PushApprovalRouteError) {
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
          message: "The dashboard could not reach the Source Proxy push approval endpoint.",
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
    if (shouldPushFromRecordedApproval(payload, approvalRequest)) {
      const pushedPayload = await runApprovedPush(payload, pushId);
      return Response.json(pushedPayload);
    }
    if (approvalRequest.approved === true && isApprovalItemNotFound(payload)) {
      const fallbackPayload = await fallbackApprovalPayload(pushId, approvalRequest);
      const pushedPayload = await runApprovedPush(fallbackPayload, pushId);
      return Response.json(pushedPayload);
    }
  } catch (error) {
    if (error instanceof PushApprovalRouteError) {
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

function isApprovalItemNotFound(payload: Record<string, unknown>) {
  const detail = asRecord(payload.detail);
  return detail?.reason_code === "approval_item_not_found";
}

function shouldPushFromRecordedApproval(
  payload: Record<string, unknown>,
  approvalRequest: Record<string, unknown>,
) {
  return (
    approvalRequest.approved === true &&
    payload.status === "approval_recorded" &&
    payload.approval_kind === "push" &&
    payload.push_ran !== true
  );
}

async function fallbackApprovalPayload(pushId: string, approvalRequest: Record<string, unknown>) {
  let response;
  try {
    response = await sourceProxyFetch("/v1/cartographer/push-queue", {
      method: "GET",
    });
  } catch (error) {
    throw new PushApprovalRouteError(
      error instanceof Error ? error.message : "Could not load push queue fallback.",
      "source_proxy_unavailable",
    );
  }
  const payload = (await response.json()) as Record<string, unknown>;
  const queue = Array.isArray(payload.push_queue) ? payload.push_queue : [];
  const item = queue.find((candidate) => asRecord(candidate)?.push_id === pushId);
  const fallbackItem = item ?? (await localPushItem(pushId));
  if (!fallbackItem) {
    throw new PushApprovalRouteError(
      "Requested Cartographer push item was not found.",
      "approval_item_not_found",
    );
  }
  return {
    status: "approval_recorded",
    write_actions_enabled: false,
    approval_kind: "push",
    item_id: pushId,
    approved_by: String(approvalRequest.approved_by ?? "cartographer-ui"),
    item: fallbackItem,
    actions_taken: false,
    branch_created: false,
    commit_created: false,
    push_ran: false,
  };
}

async function localPushItem(pushId: string) {
  const repoRoot = process.cwd();
  const branch = (await optionalGit(repoRoot, ["branch", "--show-current"])).trim();
  const upstream = (await optionalGit(repoRoot, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])).trim();
  const baseRef = upstream || (await branchCreationBase(repoRoot, branch));
  const remote = remoteForUpstream(upstream) || (await firstRemote(repoRoot));
  if (!branch || !baseRef || !remote) {
    return null;
  }
  const commitsAheadText = (await git(repoRoot, ["rev-list", "--count", `${baseRef}..HEAD`])).stdout.trim();
  const commitsAhead = Number.parseInt(commitsAheadText, 10);
  if (!Number.isFinite(commitsAhead) || commitsAhead <= 0) {
    return null;
  }
  const expectedPushId = computedPushId("spiritos", upstream, branch, commitsAhead);
  if (expectedPushId !== pushId) {
    return null;
  }
  const files = (await git(repoRoot, ["diff", "--name-only", `${baseRef}..HEAD`])).stdout
    .split(/\r?\n/u)
    .map((line) => line.trim().replace(/\\/gu, "/"))
    .filter(Boolean)
    .slice(0, 50);
  return {
    push_id: expectedPushId,
    project_id: "spiritos",
    remote,
    branch,
    upstream: upstream || null,
    commits_ahead: commitsAhead,
    files,
    status: "push_pending",
    requires_approval: true,
    push_enabled: false,
    action_taken: false,
  };
}

async function branchCreationBase(repoRoot: string, branch: string) {
  const auditPath = path.join(repoRoot, "data", "cartographer_git_approvals.audit.jsonl");
  let text = "";
  try {
    text = await readFile(auditPath, "utf8");
  } catch {
    return "";
  }
  for (const line of text.split(/\r?\n/u).filter(Boolean).reverse()) {
    try {
      const record = JSON.parse(line) as Record<string, unknown>;
      if (record.event === "branch_created" && record.branch === branch && record.previous_branch) {
        return String(record.previous_branch);
      }
    } catch {
      continue;
    }
  }
  return "";
}

function remoteForUpstream(upstream: string) {
  const [remote, upstreamBranch] = upstream.split("/", 2);
  return remote && upstreamBranch ? remote : "";
}

async function firstRemote(repoRoot: string) {
  const output = await optionalGit(repoRoot, ["remote"]);
  return output.split(/\r?\n/u).find(Boolean) ?? "";
}

function computedPushId(projectId: string, upstream: string, branch: string, commitsAhead: number) {
  const key = [projectId, upstream, branch, String(commitsAhead)].join("|");
  return `push-${createHash("sha256").update(key).digest("hex").slice(0, 12)}`;
}

async function runApprovedPush(payload: Record<string, unknown>, pushId: string) {
  const item = asRecord(payload.item);
  const remote = String(item?.remote ?? "").trim();
  const branch = String(item?.branch ?? "").trim();
  validateSafeBranchName(branch);
  if (!remote) {
    throw new PushApprovalRouteError("Push item is missing a remote.", "push_target_required");
  }
  const repoRoot = process.cwd();
  const upstream = item?.upstream;
  await git(repoRoot, upstream ? ["push", remote, branch] : ["push", "-u", remote, branch]);
  const approvedAt = new Date().toISOString().replace(/\.\d{3}Z$/u, "Z");
  const approvedBy = String(payload.approved_by ?? "cartographer-ui");
  await appendGitApprovalAudit(repoRoot, {
    action_taken: true,
    approval_kind: "push",
    approved_at: approvedAt,
    approved_by: approvedBy,
    branch,
    branch_created: false,
    changed_files: Array.isArray(item?.files) ? item.files : [],
    commit_created: false,
    commits_ahead: item?.commits_ahead ?? null,
    event: "push_approved",
    item_id: pushId,
    project_id: String(item?.project_id ?? "spiritos"),
    push_ran: true,
    remote,
    result: "pushed",
    upstream: item?.upstream ?? null,
  });

  return {
    ...payload,
    status: "pushed",
    write_actions_enabled: true,
    approved_at: approvedAt,
    remote,
    branch,
    actions_taken: true,
    branch_created: false,
    commit_created: false,
    push_ran: true,
    committed: false,
    pushed: true,
    next_step: "Push completed; review merge readiness before merging.",
    safety: {
      approval_recorded: true,
      branch_creation_enabled: false,
      commit_enabled: false,
      push_enabled: true,
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
    throw new PushApprovalRouteError(
      "Push branch name is not a valid safe Git branch name.",
      "unsafe_branch_name",
    );
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
    const message = String(output?.stderr || output?.stdout || "Git push approval command failed.");
    throw new PushApprovalRouteError(message.trim(), "git_push_failed");
  }
}

async function optionalGit(repoRoot: string, args: string[]) {
  try {
    return (await git(repoRoot, args)).stdout.trim();
  } catch {
    return "";
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

class PushApprovalRouteError extends Error {
  constructor(
    message: string,
    readonly reasonCode: string,
  ) {
    super(message);
  }
}
