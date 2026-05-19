import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export const runtime = "nodejs";

const execFileAsync = promisify(execFile);

export async function GET() {
  let response;
  try {
    response = await sourceProxyFetch("/v1/cartographer/push-queue", {
      method: "GET",
    });
  } catch (error) {
    const fallback = await buildLocalPushQueue();
    if (fallback.push_count > 0) {
      return Response.json(fallback);
    }
    return Response.json(
      {
        status: "unavailable",
        write_actions_enabled: false,
        push_queue: [],
        push_count: 0,
        actions_taken: false,
        push_enabled: false,
        detail: {
          message: "The dashboard could not reach the Source Proxy push queue endpoint.",
          reason_code: "source_proxy_unavailable",
          error: error instanceof Error ? error.message : "Unknown connection error.",
        },
      },
      { status: 502 },
    );
  }

  const text = await response.text();
  const contentType = response.headers.get("content-type") ?? "application/json";
  if (!contentType.includes("application/json")) {
    return new Response(text, {
      headers: { "content-type": contentType },
      status: response.status,
      statusText: response.statusText,
    });
  }

  try {
    const payload = JSON.parse(text) as Record<string, unknown>;
    const existing = Array.isArray(payload.push_queue) ? payload.push_queue : [];
    if (existing.length > 0) {
      return Response.json(payload, {
        status: response.status,
        statusText: response.statusText,
      });
    }
    const fallback = await buildLocalPushQueue();
    if (fallback.push_count > 0) {
      return Response.json(fallback);
    }
  } catch {
    return new Response(text, {
      headers: { "content-type": contentType },
      status: response.status,
      statusText: response.statusText,
    });
  }

  return new Response(text, {
    headers: { "content-type": contentType },
    status: response.status,
    statusText: response.statusText,
  });
}

async function buildLocalPushQueue() {
  const repoRoot = process.cwd();
  const branch = (await git(repoRoot, ["branch", "--show-current"])).stdout.trim();
  const upstream = await optionalGit(repoRoot, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"]);
  const baseRef = upstream || (await branchCreationBase(repoRoot, branch));
  const remote = remoteForUpstream(upstream) || (await firstRemote(repoRoot));
  if (!branch || !baseRef || !remote) {
    return pushQueuePayload([]);
  }
  const commitsAheadText = (await git(repoRoot, ["rev-list", "--count", `${baseRef}..HEAD`])).stdout.trim();
  const commitsAhead = Number.parseInt(commitsAheadText, 10);
  if (!Number.isFinite(commitsAhead) || commitsAhead <= 0) {
    return pushQueuePayload([]);
  }
  const files = (await git(repoRoot, ["diff", "--name-only", `${baseRef}..HEAD`])).stdout
    .split(/\r?\n/u)
    .map((line) => line.trim().replace(/\\/gu, "/"))
    .filter(Boolean)
    .slice(0, 50);
  const item = {
    push_id: pushId("spiritos", upstream, branch, commitsAhead),
    project_id: "spiritos",
    remote,
    branch,
    upstream: upstream || null,
    ahead: commitsAhead,
    behind: 0,
    commits_ahead: commitsAhead,
    files,
    reason_codes: [
      "push_requires_separate_approval",
      "push_disabled_until_approved",
    ],
    push_blockers: [
      "push_requires_separate_approval",
      "commit_audit_status_unavailable_in_frontend_fallback",
    ],
    branch_protection_warnings: branchProtectionWarnings(branch, upstream),
    remote_status: {
      remote,
      branch,
      upstream: upstream || null,
      ahead: commitsAhead,
      behind: 0,
    },
    status: "push_pending",
    requires_approval: true,
    push_enabled: false,
    action_taken: false,
  };
  return pushQueuePayload([item]);
}

function pushQueuePayload(pushQueue: Array<Record<string, unknown>>) {
  return {
    status: "observing",
    write_actions_enabled: false,
    push_queue: pushQueue,
    push_count: pushQueue.length,
    approval_type: "push",
    approval_endpoint_template: "/v1/cartographer/push-queue/{push_id}/approve",
    push_enabled: false,
    actions_taken: false,
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
  const records = text.split(/\r?\n/u).filter(Boolean).reverse();
  for (const line of records) {
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

function pushId(projectId: string, upstream: string, branch: string, commitsAhead: number) {
  const key = [projectId, upstream, branch, String(commitsAhead)].join("|");
  return `push-${createHash("sha256").update(key).digest("hex").slice(0, 12)}`;
}

function branchProtectionWarnings(branch: string, upstream: string) {
  const warnings = ["review_remote_branch_protection_before_push"];
  if (["main", "master", "trunk"].includes(branch)) {
    warnings.push("base_branch_push_requires_extra_review");
  }
  if (!upstream) {
    warnings.push("new_remote_branch_may_not_have_protection_rules");
  }
  return warnings;
}

async function optionalGit(repoRoot: string, args: string[]) {
  try {
    return (await git(repoRoot, args)).stdout.trim();
  } catch {
    return "";
  }
}

async function git(repoRoot: string, args: string[]) {
  return execFileAsync("git", args, {
    cwd: repoRoot,
    timeout: 30_000,
  });
}
