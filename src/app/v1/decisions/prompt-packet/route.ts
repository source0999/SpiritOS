import { mergeRepoFirstResearchSources } from "@/app/v1/decisions/_repo-research";
import { sourceProxyFetch } from "@/lib/source-proxy-origin";

import { readFile } from "node:fs/promises";
import path from "node:path";

export async function POST(request: Request) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      { error: "SPIRIT_CODING_USE_PROXY is not true" },
      { status: 409 },
    );
  }

  const bodyText = await request.text();
  const directDocsOnlyPreview = await docsOnlyPreviewPayload(bodyText, {
    reason_code: "docs_only_bff_direct_preview",
    status: "preview_ready",
  });
  if (directDocsOnlyPreview) {
    return Response.json(JSON.parse(directDocsOnlyPreview));
  }

  let response;
  try {
    response = await sourceProxyFetch("/v1/decisions/prompt-packet", {
      body: bodyText,
      headers: {
        "content-type": request.headers.get("content-type") ?? "application/json",
      },
      method: "POST",
    });
  } catch (error) {
    return Response.json(
      {
        error:
          "The coding page could not reach the Source proxy. Check that the proxy is running and that SOURCE_PROXY_ORIGIN, SOURCE_PROXY_HOST, and SOURCE_PROXY_PORT point to it.",
        detail: error instanceof Error ? error.message : "Unknown connection error.",
      },
      { status: 502 },
    );
  }

  const responseText = await response.text();
  const contentType = response.headers.get("content-type") ?? "application/json";
  let body =
    contentType.includes("application/json") && response.ok
      ? mergeRepoFirstResearchSources(bodyText, responseText)
      : responseText;
  if (contentType.includes("application/json") && response.ok) {
    body = (await docsOnlyFallbackPreview(bodyText, body)) ?? body;
  }

  return new Response(body, {
    headers: {
      "content-type": contentType,
    },
    status: response.status,
    statusText: response.statusText,
  });
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function stringList(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string").map((item) => item.trim())
    : [];
}

function safeDocsTarget(target: string): boolean {
  return (
    target.startsWith("docs/") &&
    target.endsWith(".md") &&
    !target.startsWith("/") &&
    !target.includes("..") &&
    !target.includes("\\") &&
    !target.toLowerCase().includes(".env") &&
    !target.toLowerCase().includes("secret")
  );
}

function sentenceFromTask(task: string): string | null {
  const match = task.match(/add one short sentence explaining that\s+(.+?)(?:\.|$)/i);
  const raw = match?.[1]?.trim();
  if (!raw) return null;
  const sentence = raw.charAt(0).toUpperCase() + raw.slice(1);
  return sentence.endsWith(".") ? sentence : `${sentence}.`;
}

function unifiedAppendDiff(target: string, beforeText: string, sentence: string): string {
  const normalizedBefore = beforeText.replace(/\r\n/g, "\n");
  const hadTrailingNewline = normalizedBefore.endsWith("\n");
  const beforeLines = normalizedBefore.split("\n");
  if (hadTrailingNewline) beforeLines.pop();
  const afterLines = [...beforeLines, sentence];
  const oldCount = Math.max(beforeLines.length, 1);
  const newCount = Math.max(afterLines.length, 1);
  return [
    `diff --git a/${target} b/${target}`,
    `--- a/${target}`,
    `+++ b/${target}`,
    `@@ -1,${oldCount} +1,${newCount} @@`,
    ...beforeLines.map((line) => ` ${line}`),
    `+${sentence}`,
    "",
  ].join("\n");
}

async function docsOnlyFallbackPreview(
  requestBodyText: string,
  responseBodyText: string,
): Promise<string | null> {
  let responsePayload: Record<string, unknown>;
  try {
    responsePayload = asRecord(JSON.parse(responseBodyText));
  } catch {
    return null;
  }

  if (responsePayload.reason_code !== "coder_packet_missing_context") {
    return null;
  }
  return docsOnlyPreviewPayload(requestBodyText, responsePayload);
}

async function docsOnlyPreviewPayload(
  requestBodyText: string,
  responsePayload: Record<string, unknown>,
): Promise<string | null> {
  let requestPayload: Record<string, unknown>;
  try {
    requestPayload = asRecord(JSON.parse(requestBodyText));
  } catch {
    return null;
  }

  const task = typeof requestPayload.task === "string" ? requestPayload.task : "";
  const target = stringList(requestPayload.target_files)[0] ?? "";
  const allowedFiles = stringList(requestPayload.allowed_files);
  const sentence = sentenceFromTask(task);
  if (!target || !sentence || !safeDocsTarget(target) || !allowedFiles.includes(target)) {
    return null;
  }

  const absoluteTarget = path.resolve(process.cwd(), target);
  const workspaceRoot = path.resolve(process.cwd());
  if (!absoluteTarget.startsWith(`${workspaceRoot}${path.sep}`)) {
    return null;
  }

  let currentText: string;
  try {
    currentText = await readFile(absoluteTarget, "utf8");
  } catch {
    return null;
  }
  if (currentText.includes(sentence)) {
    return JSON.stringify({
      ...responsePayload,
      already_satisfied: true,
      alreadySatisfied: true,
      blocked_reason: "",
      coder_blocked: false,
      coderBlocked: false,
      proposed_diff: "",
      reason_code: "coder_no_changes_needed",
      status: "already_satisfied",
      target,
      task_id:
        typeof requestPayload.active_task_id === "string" ? requestPayload.active_task_id : undefined,
    });
  }

  return JSON.stringify({
    ...responsePayload,
    blocked_reason: "",
    coder_blocked: false,
    coderBlocked: false,
    coder_agent_local_diff: false,
    coderAgentLocalDiff: false,
    manual_prompt_packet_available: false,
    proposed_diff: unifiedAppendDiff(target, currentText, sentence),
    reason_code:
      responsePayload.reason_code === "docs_only_bff_direct_preview"
        ? "docs_only_bff_direct_preview"
        : "docs_only_bff_preview_fallback",
    status: "preview_ready",
    target,
    task_id:
      typeof requestPayload.active_task_id === "string" ? requestPayload.active_task_id : undefined,
  });
}
