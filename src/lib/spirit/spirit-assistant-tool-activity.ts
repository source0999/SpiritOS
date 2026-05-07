// ── spirit-assistant-tool-activity - merge stream metadata + tool UI parts into cards ─
// > Client-safe: mirrors server telemetry shapes without importing workspace roots or secrets.

import type { UIMessage } from "ai";

import {
  createSpiritToolActivityCard,
  type SpiritAssistantMessageMetadata,
  type SpiritToolActivityCard,
  type SpiritToolActivityKind,
  type SpiritToolActivityStatus,
} from "@/lib/spirit/spirit-activity-events";

function isRecord(x: unknown): x is Record<string, unknown> {
  return Boolean(x && typeof x === "object");
}

export function readSpiritAssistantMessageMetadata(
  message: UIMessage,
): SpiritAssistantMessageMetadata | undefined {
  const m = message.metadata;
  if (!m || typeof m !== "object") return undefined;
  const spirit = (m as SpiritAssistantMessageMetadata).spiritToolActivity;
  if (!Array.isArray(spirit)) return undefined;
  return m as SpiritAssistantMessageMetadata;
}

function toolNameFromPart(part: UIMessage["parts"][number]): string | null {
  if (!isRecord(part)) return null;
  if ("toolName" in part && typeof (part as { toolName?: string }).toolName === "string") {
    return (part as { toolName: string }).toolName;
  }
  const t = (part as { type?: unknown }).type;
  if (typeof t === "string" && t.startsWith("tool-")) {
    return t.slice("tool-".length);
  }
  return null;
}

function statusLabel(s: SpiritToolActivityStatus): string {
  switch (s) {
    case "pending":
      return "Pending";
    case "completed":
      return "Completed";
    case "failed":
      return "Failed";
    case "blocked":
      return "Blocked";
    case "confirmation_required":
      return "Confirmation required";
    default:
      return s;
  }
}

/** Human-readable action title for tool parts (matches direct-fallback labels where possible). */
export function spiritToolKindDisplay(kind: SpiritToolActivityKind): string {
  switch (kind) {
    case "workspace_list":
      return "List workspace files";
    case "workspace_read":
      return "Read workspace file";
    case "workspace_tail":
      return "Tail log file";
    case "file_edit_proposed":
      return "Propose file edit";
    case "file_edit_applied":
      return "Apply file edit";
    case "dev_command_started":
      return "Dev command";
    case "dev_command_completed":
      return "Dev command";
    case "dev_command_failed":
      return "Dev command";
    case "tool_blocked":
      return "Blocked";
    case "tool_unavailable":
      return "Tool unavailable";
    default:
      return "Tool";
  }
}

export { statusLabel };

function cardsFromListWorkspace(
  out: unknown,
  id: string,
  input: unknown,
): SpiritToolActivityCard[] {
  if (!isRecord(out)) return [];
  const inp = isRecord(input) ? input : {};
  const dir =
    typeof inp.directory === "string" ? inp.directory : typeof inp.path === "string" ? inp.path : ".";

  if (out.ok === true) {
    return [
      createSpiritToolActivityCard({
        id,
        kind: "workspace_list",
        label: "List workspace files",
        status: "completed",
        target: typeof out.directory === "string" ? out.directory : dir,
        summary: out.truncated === true ? "truncated" : undefined,
      }),
    ];
  }
  return [
    createSpiritToolActivityCard({
      id,
      kind: "tool_blocked",
      label: "List workspace files",
      status: "blocked",
      target: dir,
      safeMessage: typeof out.message === "string" ? out.message : "blocked",
    }),
  ];
}

function cardsFromReadFile(out: unknown, id: string, input: unknown): SpiritToolActivityCard[] {
  if (!isRecord(out)) return [];
  const inp = isRecord(input) ? input : {};
  const fp = typeof inp.filePath === "string" ? inp.filePath : undefined;

  if (out.ok === true) {
    return [
      createSpiritToolActivityCard({
        id,
        kind: "workspace_read",
        label: "Read workspace file",
        status: "completed",
        target: typeof out.filePath === "string" ? out.filePath : fp,
        summary: out.truncated === true ? "truncated" : undefined,
      }),
    ];
  }
  return [
    createSpiritToolActivityCard({
      id,
      kind: "tool_blocked",
      label: "Read workspace file",
      status: "blocked",
      target: fp,
      safeMessage: typeof out.message === "string" ? out.message : "blocked",
    }),
  ];
}

function cardsFromTail(out: unknown, id: string, input: unknown): SpiritToolActivityCard[] {
  if (!isRecord(out)) return [];
  const inp = isRecord(input) ? input : {};
  const fp = typeof inp.filePath === "string" ? inp.filePath : undefined;

  if (out.ok === true) {
    return [
      createSpiritToolActivityCard({
        id,
        kind: "workspace_tail",
        label: "Tail log file",
        status: "completed",
        target: typeof out.filePath === "string" ? out.filePath : fp,
        summary: out.truncated === true ? "truncated" : undefined,
      }),
    ];
  }
  return [
    createSpiritToolActivityCard({
      id,
      kind: "tool_blocked",
      label: "Tail log file",
      status: "blocked",
      target: fp,
      safeMessage: typeof out.message === "string" ? out.message : "blocked",
    }),
  ];
}

function cardsFromProposeEdit(out: unknown, id: string): SpiritToolActivityCard[] {
  if (!isRecord(out)) return [];
  if (out.ok === true && typeof out.proposalId === "string") {
    return [
      createSpiritToolActivityCard({
        id,
        kind: "file_edit_proposed",
        label: "Propose file edit",
        status: "confirmation_required",
        target: typeof out.relativeFilePath === "string" ? out.relativeFilePath : undefined,
        summary: `proposal ${out.proposalId}`,
      }),
    ];
  }
  return [
    createSpiritToolActivityCard({
      id,
      kind: "tool_blocked",
      label: "Propose file edit",
      status: "blocked",
      safeMessage: typeof out.message === "string" ? out.message : "failed",
    }),
  ];
}

function cardsFromApplyEdit(out: unknown, id: string): SpiritToolActivityCard[] {
  if (!isRecord(out)) return [];
  if (out.ok === true) {
    return [
      createSpiritToolActivityCard({
        id,
        kind: "file_edit_applied",
        label: "Apply file edit",
        status: "completed",
        target: typeof out.relativeFilePath === "string" ? out.relativeFilePath : undefined,
        summary:
          typeof out.backupRelativePath === "string"
            ? `backup ${out.backupRelativePath}`
            : undefined,
      }),
    ];
  }
  const code = typeof out.code === "string" ? out.code : "";
  const needsConfirm = code === "CONFIRMATION_REQUIRED";
  return [
    createSpiritToolActivityCard({
      id,
      kind: "tool_blocked",
      label: "Apply file edit",
      status: needsConfirm ? "confirmation_required" : "blocked",
      safeMessage: typeof out.message === "string" ? out.message : "failed",
    }),
  ];
}

function cardsFromDevCommand(out: unknown, id: string): SpiritToolActivityCard[] {
  if (!isRecord(out)) return [];
  const cmdId = typeof out.commandId === "string" ? out.commandId : "?";

  if (out.requiresConfirmation === true) {
    return [
      createSpiritToolActivityCard({
        id,
        kind: "dev_command_started",
        label: "Dev command",
        status: "confirmation_required",
        target: cmdId,
        summary: typeof out.label === "string" ? out.label : undefined,
      }),
    ];
  }

  if (out.error && isRecord(out.error)) {
    const code = typeof out.error.code === "string" ? out.error.code : "";
    const unavailable =
      code === "DEV_COMMAND_TOOLS_DISABLED" ||
      code === "SCRIPT_NOT_FOUND" ||
      code === "UNKNOWN_COMMAND";
    return [
      createSpiritToolActivityCard({
        id,
        kind: unavailable ? "tool_unavailable" : "dev_command_failed",
        label: "Dev command",
        status: "failed",
        target: cmdId,
        safeMessage:
          typeof out.error.message === "string" ? out.error.message : "command failed",
      }),
    ];
  }

  if (out.timedOut === true || out.ok === false) {
    return [
      createSpiritToolActivityCard({
        id,
        kind: "dev_command_failed",
        label: "Dev command",
        status: "failed",
        target: cmdId,
        summary: out.timedOut === true ? "Timed out" : `Exit ${out.exitCode ?? "?"}`,
      }),
    ];
  }

  return [
    createSpiritToolActivityCard({
      id,
      kind: "dev_command_completed",
      label: "Dev command",
      status: "completed",
      target: cmdId,
      summary: typeof out.label === "string" ? out.label : undefined,
    }),
  ];
}

/**
 * Derive activity cards from persisted tool UI parts (LLM tool path).
 */
export function toolUIPartsToActivityCards(parts: UIMessage["parts"]): SpiritToolActivityCard[] {
  const cards: SpiritToolActivityCard[] = [];

  for (const part of parts) {
    const name = toolNameFromPart(part);
    if (!name) continue;
    if (!isRecord(part) || !("state" in part)) continue;
    const p = part as {
      state: string;
      toolCallId?: string;
      type?: string;
      input?: unknown;
      output?: unknown;
      errorText?: string;
    };
    const callId = typeof p.toolCallId === "string" ? p.toolCallId : "unknown";
    const baseId = `toolpart_${callId}`;

    if (p.state === "output-error") {
      cards.push(
        createSpiritToolActivityCard({
          id: baseId,
          kind: "tool_blocked",
          label: name.replace(/_/g, " "),
          status: "failed",
          summary: typeof p.errorText === "string" ? p.errorText.slice(0, 200) : undefined,
        }),
      );
      continue;
    }

    if (p.state !== "output-available") continue;
    const input = p.input;

    switch (name) {
      case "list_workspace_files":
        cards.push(...cardsFromListWorkspace(p.output, baseId, input));
        break;
      case "read_workspace_file":
        cards.push(...cardsFromReadFile(p.output, baseId, input));
        break;
      case "read_log_tail":
        cards.push(...cardsFromTail(p.output, baseId, input));
        break;
      case "propose_file_edit":
        cards.push(...cardsFromProposeEdit(p.output, baseId));
        break;
      case "apply_confirmed_file_edit":
        cards.push(...cardsFromApplyEdit(p.output, baseId));
        break;
      case "run_dev_command":
        cards.push(...cardsFromDevCommand(p.output, baseId));
        break;
      default:
        break;
    }
  }

  return cards;
}

/**
 * Metadata from deterministic `/api/spirit` responses plus tool parts from streamed tool calls.
 */
export function mergeSpiritToolActivityCardsForMessage(message: UIMessage): SpiritToolActivityCard[] {
  const meta = readSpiritAssistantMessageMetadata(message)?.spiritToolActivity ?? [];
  const fromParts = toolUIPartsToActivityCards(message.parts);
  const map = new Map<string, SpiritToolActivityCard>();
  for (const c of fromParts) {
    map.set(c.id, c);
  }
  for (const c of meta) {
    map.set(c.id, c);
  }
  return [...map.values()];
}
