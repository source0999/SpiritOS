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

function approvalIdForApprovedDiff({
  approvedDiff,
  target,
  taskId,
}: {
  approvedDiff: string;
  target: string;
  taskId: string;
}) {
  const diffHash = createHash("sha256").update(approvedDiff).digest("hex");
  const key = [taskId.trim(), target.trim(), diffHash].join("|");
  return `approval-${createHash("sha256").update(key).digest("hex").slice(0, 16)}`;
}
