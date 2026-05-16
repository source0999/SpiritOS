import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export const runtime = "nodejs";

const execFileAsync = promisify(execFile);

export async function GET() {
  let response;
  try {
    response = await sourceProxyFetch("/v1/cartographer/project-health", {
      method: "GET",
    });
  } catch (error) {
    const fallback = await localProjectHealth();
    return Response.json(
      {
        status: "observing",
        write_actions_enabled: false,
        projects: [fallback],
        project_count: 1,
        actions_taken: false,
        detail: {
          message: "The dashboard could not reach the Source Proxy project health endpoint.",
          reason_code: "source_proxy_unavailable",
          error: error instanceof Error ? error.message : "Unknown connection error.",
        },
      },
      { status: 200 },
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
    const projects = Array.isArray(payload.projects) ? payload.projects : [];
    const readiness = await localMergeReadiness();
    return Response.json(
      {
        ...payload,
        projects: projects.map((project, index) => {
          const record = project && typeof project === "object" ? (project as Record<string, unknown>) : {};
          if (index > 0 || record.merge_ready !== undefined) {
            return record;
          }
          return {
            ...record,
            ...readiness,
          };
        }),
      },
      {
        status: response.status,
        statusText: response.statusText,
      },
    );
  } catch {
    return new Response(text, {
      headers: { "content-type": contentType },
      status: response.status,
      statusText: response.statusText,
    });
  }
}

async function localProjectHealth() {
  const readiness = await localMergeReadiness();
  return {
    project_id: "spiritos",
    name: "SpiritOS",
    root: process.cwd(),
    status: "active",
    blueprint_health: "healthy",
    markers: [".git", "package.json", "_blueprints"],
    filters: readiness.merge_ready ? ["active", "merge_ready"] : ["active", ...(readiness.dirty ? ["dirty"] : [])],
    action_taken: false,
    ...readiness,
  };
}

async function localMergeReadiness() {
  const repoRoot = process.cwd();
  const branch = await optionalGit(repoRoot, ["branch", "--show-current"]);
  const upstream = await optionalGit(repoRoot, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"]);
  const status = await optionalGit(repoRoot, ["status", "--porcelain=v1"]);
  const aheadBehind = upstream ? await aheadBehindCounts(repoRoot, upstream) : { ahead: 0, behind: 0 };
  const audit = await readAudit(repoRoot);
  const pushed = audit.some(
    (record) =>
      record.event === "push_approved" &&
      record.result === "pushed" &&
      record.branch === branch,
  );
  const checks_passed = latestCommitChecksPassed(audit, branch);
  const blockers = [];
  const dirty = status.trim().length > 0;
  if (dirty) blockers.push("working tree has uncommitted changes");
  if (aheadBehind.ahead > 0) blockers.push("branch has unpushed commits");
  if (aheadBehind.behind > 0) blockers.push("branch is behind upstream");
  if (!upstream) blockers.push("merge target unknown");
  if (!branch || ["main", "master", "trunk"].includes(branch)) blockers.push("work is not on a review branch");
  if (!pushed) blockers.push("push audit missing");
  if (!checks_passed) blockers.push("required checks not recorded as passed");

  return {
    merge_ready: blockers.length === 0,
    merge_blockers: blockers,
    recommended_next_step: recommendedNextStep(blockers),
    merge_target: upstream || null,
    pushed,
    checks_passed,
    dirty,
    branch: branch || null,
  };
}

async function aheadBehindCounts(repoRoot: string, upstream: string) {
  const output = await optionalGit(repoRoot, ["rev-list", "--left-right", "--count", `${upstream}...HEAD`]);
  const [behindText, aheadText] = output.split(/\s+/u);
  return {
    ahead: Number.parseInt(aheadText ?? "0", 10) || 0,
    behind: Number.parseInt(behindText ?? "0", 10) || 0,
  };
}

async function readAudit(repoRoot: string) {
  const auditPath = path.join(repoRoot, "data", "cartographer_git_approvals.audit.jsonl");
  try {
    const text = await readFile(auditPath, "utf8");
    return text
      .split(/\r?\n/u)
      .filter(Boolean)
      .map((line) => JSON.parse(line) as Record<string, unknown>);
  } catch {
    return [];
  }
}

function latestCommitChecksPassed(records: Array<Record<string, unknown>>, branch: string) {
  for (const record of [...records].reverse()) {
    if (record.event !== "commit_created" || record.branch !== branch) continue;
    const checks = Array.isArray(record.checks) ? record.checks : [];
    const passed = new Set(
      checks
        .filter((check) => {
          const item = check as Record<string, unknown>;
          return item.status === "passed";
        })
        .map((check) => String((check as Record<string, unknown>).id)),
    );
    return ["git_diff_check", "blueprint_metadata_validation", "cartographer_pytest"].every((id) =>
      passed.has(id),
    );
  }
  return false;
}

function recommendedNextStep(blockers: string[]) {
  if (blockers.length === 0) return "open merge review";
  if (blockers.includes("working tree has uncommitted changes")) return "commit or discard remaining local changes";
  if (blockers.includes("branch has unpushed commits")) return "push branch after approval";
  if (blockers.includes("required checks not recorded as passed")) return "run required checks before merge review";
  if (blockers.includes("merge target unknown")) return "set upstream or merge target";
  return "resolve merge blockers";
}

async function optionalGit(repoRoot: string, args: string[]) {
  try {
    return (await execFileAsync("git", args, { cwd: repoRoot, timeout: 30_000 })).stdout.trim();
  } catch {
    return "";
  }
}
