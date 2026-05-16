import { readFile } from "node:fs/promises";
import path from "node:path";

import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export const runtime = "nodejs";

export async function GET() {
  let response;
  try {
    response = await sourceProxyFetch("/v1/cartographer/audit-trail", {
      method: "GET",
    });
  } catch (error) {
    return Response.json(
      {
        status: "unavailable",
        write_actions_enabled: false,
        events: [],
        event_count: 0,
        actions_taken: false,
        rollback_enabled: false,
        rollback_hints_present: true,
        explainability_fields_present: true,
        detail: {
          message: "The dashboard could not reach the Source Proxy audit trail endpoint.",
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
    const localRecords = await readLocalGitApprovalRecords();
    const localEvents = localRecords.map(localGitRecordToAuditEvent);
    const proxiedEvents = Array.isArray(payload.events)
      ? payload.events.map((event) => normalizeAuditEvent(event, localRecords))
      : [];
    const events = mergeAuditEvents(proxiedEvents, localEvents);
    return Response.json(
      {
        ...payload,
        events,
        event_count: payload.event_count ?? events.length,
        rollback_hints_present: events.every((event) => Boolean(event.rollback_hint)),
        explainability_fields_present: events.every((event) => {
          return Boolean(event.event_id) && Boolean(event.event) && event.action !== undefined && event.result !== undefined;
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

async function readLocalGitApprovalRecords() {
  const auditPath = path.join(process.cwd(), "data", "cartographer_git_approvals.audit.jsonl");
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

function normalizeAuditEvent(value: unknown, localRecords: Array<Record<string, unknown>> = []): Record<string, unknown> {
  const event = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  const files = Array.isArray(event.files) ? event.files : [];
  const eventName = String(event.event ?? "");
  const result = String(event.result ?? "");
  const localMatch = matchingLocalRecord(event, localRecords);
  return {
    ...event,
    action: event.action ?? actionForEvent(eventName),
    changed_files: Array.isArray(event.changed_files) ? event.changed_files : files,
    reason: event.reason ?? null,
    component: event.component ?? componentFromFiles(files),
    commit_sha: event.commit_sha ?? localMatch?.commit_sha ?? null,
    rollback_hint: rollbackHintForEvent(eventName, result, event.rollback_hint),
  };
}

function localGitRecordToAuditEvent(record: Record<string, unknown>): Record<string, unknown> {
  const files = Array.isArray(record.changed_files) ? record.changed_files : [];
  const eventName = String(record.event ?? "git_approval_recorded");
  const result = String(record.result ?? "");
  return normalizeAuditEvent(
    {
      event_id: `audit-local-${String(record.item_id ?? eventName)}-${String(record.approved_at ?? "")}`,
      project_id: record.project_id ?? "spiritos",
      event: eventName,
      actor: record.approved_by ?? "unknown",
      timestamp: record.approved_at ?? null,
      result: record.result ?? "recorded",
      files,
      changed_files: files,
      branch: record.branch ?? null,
      remote: record.remote ?? null,
      commit_sha: record.commit_sha ?? null,
      source: "git_approval_record",
    },
    [record],
  );
}

function matchingLocalRecord(event: Record<string, unknown>, localRecords: Array<Record<string, unknown>>) {
  const eventName = String(event.event ?? "");
  const branch = String(event.branch ?? "");
  const result = String(event.result ?? "");
  return localRecords
    .slice()
    .reverse()
    .find((record) => {
      return (
        record.event === eventName &&
        (!branch || record.branch === branch) &&
        (!result || record.result === result || eventName === "commit_created")
      );
    });
}

function mergeAuditEvents(proxiedEvents: Array<Record<string, unknown>>, localEvents: Array<Record<string, unknown>>) {
  const events = [...proxiedEvents];
  const seen = new Set(events.map(auditEventKey));
  for (const event of localEvents) {
    const key = auditEventKey(event);
    if (!seen.has(key)) {
      seen.add(key);
      events.push(event);
    }
  }
  return events.sort((left, right) => String(left.timestamp ?? "").localeCompare(String(right.timestamp ?? "")));
}

function auditEventKey(event: Record<string, unknown>) {
  return [
    event.event,
    event.branch,
    event.remote,
    event.commit_sha,
    event.result,
    JSON.stringify(event.changed_files ?? event.files ?? []),
  ].join("|");
}

function actionForEvent(event: string) {
  const actions: Record<string, string> = {
      rejected: "proposal_rejected",
      approved: "proposal_approved",
      drafted: "proposal_drafted",
      detected: "proposal_detected",
      applied: "proposal_applied",
      branch_approved: "record_branch_approval",
      branch_created: "create_branch",
      commit_created: "create_commit",
      push_approved: "push_branch",
      commit_pending: "commit_proposed",
      push_pending: "push_queued",
  };
  return actions[event] ?? event;
}

function rollbackHintForEvent(event: string, result = "", existing: unknown = null) {
  if (event === "push_approved" && result === "pushed") {
    return "Push reached the remote; use a reviewed revert or remote cleanup workflow.";
  }
  if (event === "commit_created") {
    return "Commit is local until pushed; review Git history before reverting.";
  }
  if (event === "branch_created") {
    return "Switch back to the previous branch and delete the created branch only after review.";
  }
  if (typeof existing === "string" && existing.trim()) return existing;
  if (event === "branch_created") return "Switch back to the previous branch and delete the created branch only after review.";
  if (event === "commit_created") return "Commit is local until pushed; review Git history before reverting.";
  if (event === "push_approved") return "Push reached the remote; use a reviewed revert or remote cleanup workflow.";
  if (event === "rejected") return "No rollback needed; rejected proposal should not change files.";
  if (event === "push_pending") return "Push has not run; reject approval to leave remote untouched.";
  if (event === "commit_pending") return "Commit has not run; reject approval to leave Git untouched.";
  return "Review audit context before rollback.";
}

function componentFromFiles(files: unknown[]) {
  const first = String(files[0] ?? "");
  if (first.startsWith("_blueprints/")) return "blueprint-system";
  if (first.startsWith("source_proxy/cartographer/")) return "cartographer";
  if (first.startsWith("source_proxy/")) return "source-proxy";
  if (first.startsWith("src/components/dashboard/")) return "dashboard";
  if (first.startsWith("scout/")) return "scout";
  if (first.startsWith("docs/")) return "docs";
  return files.length ? "unknown" : null;
}
