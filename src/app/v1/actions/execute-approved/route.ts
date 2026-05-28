import { sourceProxyFetch } from "@/lib/source-proxy-origin";
import { createHash } from "crypto";

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  if (!body || typeof body !== "object") {
    return Response.json({ error: "Request body must be an object" }, { status: 400 });
  }

  const record = body as Record<string, unknown>;
  const action = typeof record.action === "string" ? record.action : "";
  const target = typeof record.target === "string" ? record.target : "";
  const approved = record.approved === true;
  const approvedDiff =
    typeof record.approved_diff === "string"
      ? record.approved_diff
      : typeof record.approvedDiff === "string"
        ? record.approvedDiff
        : "";
  const taskId =
    typeof record.task_id === "string"
      ? record.task_id
      : typeof record.taskId === "string"
        ? record.taskId
        : "";
  const approvalId =
    typeof record.approval_id === "string"
      ? record.approval_id
      : typeof record.approvalId === "string"
        ? record.approvalId
        : "";
  const allowedFiles = stringArrayValue(record.allowed_files ?? record.allowedFiles);
  const changedFiles = changedFilesFromApprovedDiff(approvedDiff);

  if (!approved) {
    return Response.json(
      { error: "approved must be true before execution" },
      { status: 403 },
    );
  }
  if (!action.trim() || !target.trim()) {
    return Response.json(
      { error: "action and target are required" },
      { status: 400 },
    );
  }

  if (!taskId.trim()) {
    return Response.json(
      {
        error:
          "execute-approved requires task_id so Source Proxy can re-run verification before apply.",
      },
      { status: 400 },
    );
  }
  if (!approvedDiff.trim()) {
    return Response.json(
      {
        error:
          "execute-approved requires approved_diff so Source Proxy can re-run verification before apply.",
      },
      { status: 400 },
    );
  }
  if (allowedFiles.length === 0) {
    return Response.json(
      {
        error:
          "execute-approved requires allowed_files so Source Proxy can scope-match the approved diff before apply.",
      },
      { status: 400 },
    );
  }
  if (changedFiles.length === 0) {
    return Response.json(
      {
        error:
          "execute-approved requires approved_diff changed files so exact apply scope can be verified.",
      },
      { status: 400 },
    );
  }
  if (changedFiles.some((file) => isProtectedApplyPath(file))) {
    return Response.json(
      {
        changed_files: changedFiles,
        error: "execute-approved rejected protected path in approved_diff.",
      },
      { status: 403 },
    );
  }
  if (target.trim() && !changedFiles.includes(target.trim())) {
    return Response.json(
      {
        changed_files: changedFiles,
        error: "execute-approved target does not match approved_diff changed files.",
        target,
      },
      { status: 409 },
    );
  }
  const unexpectedFiles = changedFiles.filter((file) => !allowedFiles.includes(file));
  if (unexpectedFiles.length > 0) {
    return Response.json(
      {
        allowed_files: allowedFiles,
        changed_files: changedFiles,
        error: "execute-approved approved_diff changed files are outside allowed_files.",
        unexpected_files: unexpectedFiles,
      },
      { status: 409 },
    );
  }
  const expectedApprovalId = approvalIdForApprovedDiff({
    approvedDiff,
    target,
    taskId,
  });
  if (approvalId.trim() && approvalId !== expectedApprovalId) {
    return Response.json(
      {
        error:
          "execute-approved approval_id does not match task_id, target, and approved_diff.",
        expected_approval_id: expectedApprovalId,
      },
      { status: 409 },
    );
  }

  // Approved real diffs execute through Source proxy's long-running task layer.
  // That keeps diff verification, workspace writes, progress, and audit logging
  // behind a single explicit approval boundary.
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      { error: "SPIRIT_CODING_USE_PROXY is not true" },
      { status: 409 },
    );
  }

  const response = await sourceProxyFetch(
    `/v1/tasks/long-running/${encodeURIComponent(taskId)}/execute-approved`,
    {
      body: JSON.stringify({
        action,
        approved: true,
        approval_id: expectedApprovalId,
        approved_by: "coding-ui",
        approved_diff: approvedDiff,
        allowed_files: allowedFiles,
        changed_files: changedFiles,
        diff_hash: diffHashForApprovedDiff(approvedDiff),
        commit_authority: false,
        push_authority: false,
        target,
      }),
      headers: {
        "content-type": "application/json",
      },
      method: "POST",
    },
  );

  return new Response(await response.text(), {
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
    },
    status: response.status,
    statusText: response.statusText,
  });
}

function stringArrayValue(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function changedFilesFromApprovedDiff(diff: string): string[] {
  const files = new Set<string>();
  for (const line of diff.split(/\r?\n/)) {
    if (!line.startsWith("+++ b/")) {
      continue;
    }
    const file = line.slice("+++ b/".length).trim();
    if (file && file !== "/dev/null") {
      files.add(file);
    }
  }
  return [...files];
}

function isProtectedApplyPath(path: string) {
  return (
    path === ".env" ||
    path.startsWith(".env.") ||
    path.includes("/.env") ||
    path.endsWith(".pem") ||
    path.endsWith(".key") ||
    path.startsWith("source_proxy/") ||
    path.startsWith("config/") ||
    path === "package.json" ||
    path === "package-lock.json" ||
    path === "pnpm-lock.yaml" ||
    path === "yarn.lock"
  );
}

function diffHashForApprovedDiff(approvedDiff: string) {
  return createHash("sha256").update(approvedDiff).digest("hex");
}

function approvalIdForApprovedDiff({
  approvedDiff,
  target,
  taskId,
}: {
  approvedDiff: string;
  target: string;
  taskId: string;
}) {
  const diffHash = diffHashForApprovedDiff(approvedDiff);
  const key = [taskId.trim(), target.trim(), diffHash].join("|");
  return `approval-${createHash("sha256").update(key).digest("hex").slice(0, 16)}`;
}
