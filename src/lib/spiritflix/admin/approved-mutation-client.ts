export type SpiritFlixAdminApprovalWriter =
  | "admin-action"
  | "face-learning"
  | "library-smart-rescan"
  | "manual-model"
  | "manual-tags"
  | "smart-analysis"
  | "smart-batch";

type ApprovalErrorBody = { error?: string; message?: string; reason_code?: string };

async function errorMessage(response: Response, fallback: string): Promise<string> {
  const body = await response.clone().json().catch(() => null) as ApprovalErrorBody | null;
  return body?.reason_code ?? body?.error ?? body?.message ?? `${fallback} (HTTP ${response.status})`;
}

export async function issueSpiritFlixAdminMutationApproval(
  writer: SpiritFlixAdminApprovalWriter,
  mutation: Record<string, unknown>,
): Promise<string> {
  const previewResponse = await fetch("/v1/operator/spiritflix-admin-approval", {
    body: JSON.stringify({ action: "preview", mutation, writer }),
    credentials: "same-origin",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    method: "POST",
  });
  if (!previewResponse.ok) throw new Error(await errorMessage(previewResponse, "SpiritFlix approval preview failed"));
  const previewBody = await previewResponse.json() as {
    preview?: { generation?: unknown; preview_id?: unknown };
  };
  const previewId = typeof previewBody.preview?.preview_id === "string" ? previewBody.preview.preview_id : "";
  const generation = Number(previewBody.preview?.generation);
  if (!previewId || !Number.isInteger(generation)) throw new Error("spiritflix_admin_preview_response_invalid");

  const approvalResponse = await fetch("/v1/operator/spiritflix-admin-approval", {
    body: JSON.stringify({ action: "approve", generation, preview_id: previewId }),
    credentials: "same-origin",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    method: "POST",
  });
  if (!approvalResponse.ok) throw new Error(await errorMessage(approvalResponse, "SpiritFlix approval issuance failed"));
  const approvalBody = await approvalResponse.json() as {
    approval?: { value?: { approval_id?: unknown } };
  };
  const approvalId = typeof approvalBody.approval?.value?.approval_id === "string"
    ? approvalBody.approval.value.approval_id
    : "";
  if (!approvalId) throw new Error("spiritflix_admin_approval_response_invalid");
  return approvalId;
}

export async function fetchApprovedSpiritFlixAdminMutation(
  writer: SpiritFlixAdminApprovalWriter,
  url: string,
  mutation: Record<string, unknown>,
  init: Omit<RequestInit, "body" | "method"> & { method?: "POST" | "PUT" } = {},
): Promise<Response> {
  const approvalId = await issueSpiritFlixAdminMutationApproval(writer, mutation);
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  headers.set("Content-Type", "application/json");
  return fetch(url, {
    ...init,
    body: JSON.stringify({ ...mutation, approval_id: approvalId }),
    credentials: init.credentials ?? "same-origin",
    headers,
    method: init.method ?? "POST",
  });
}
