// ── system-state - dynamic [SYSTEM STATE] block for the SpiritOS system prompt ─
// > resolveSpiritSystemState reads process.env and is server-only in practice.
// > buildSystemStateBlock is a pure string builder - client + server safe.

import type { SpiritRuntimeSurface } from "@/lib/spirit/spirit-runtime-surface";

export type SpiritSystemCapability =
  | "chat"
  | "tts"
  | "stt"
  | "web_search_when_enabled"
  | "workspace_file_read"
  | "workspace_file_list"
  | "log_tail_read"
  | "system_status"
  | "file_editing"
  | "terminal_execution"
  | "email_access"
  | "calendar_access";

export type SpiritSystemStateInput = {
  currentTimeIso: string;
  runtimeSurface: SpiritRuntimeSurface;
  modelHint: string | null;
  modelProfileId: string | null;
  modelProfileLabel: string | null;
  hardwareProfile: string;
  projectPathConfigured: boolean;
  availableCapabilities: SpiritSystemCapability[];
  unavailableCapabilities: SpiritSystemCapability[];
  /** When env enables read-only tools but they are not on the wire for this model */
  localToolsAttachmentNote?: string | null;
  /** When env enables file edit but tools are not attached */
  fileEditingAttachmentNote?: string | null;
  /** When env enables dev commands but run_dev_command is not on the wire for this model */
  devCommandAttachmentNote?: string | null;
};

export type SpiritSystemStateResolveInput = {
  currentTimeIso?: string;
  runtimeSurface: SpiritRuntimeSurface;
  modelHint?: string | null;
  modelProfileId?: string | null;
  modelProfileLabel?: string | null;
  /** Reflects whether read-only tools were actually passed to streamText for this request */
  localToolsAttached?: boolean;
  /** True only when propose_file_edit / apply_confirmed_file_edit are on the wire */
  fileEditToolsAttached?: boolean;
  /** True only when run_dev_command was passed to streamText for this request */
  devCommandToolsAttached?: boolean;
};

const BASELINE_AVAILABLE: SpiritSystemCapability[] = [
  "chat",
  "tts",
  "stt",
  "web_search_when_enabled",
];

const LOCAL_TOOL_CAPS: SpiritSystemCapability[] = [
  "workspace_file_read",
  "workspace_file_list",
  "log_tail_read",
  "system_status",
];

export function resolveSpiritSystemState(
  input: SpiritSystemStateResolveInput,
): SpiritSystemStateInput {
  const available: SpiritSystemCapability[] = [...BASELINE_AVAILABLE];
  const unavailable: SpiritSystemCapability[] = [];

  const localToolsCfg = process.env.SPIRIT_ENABLE_LOCAL_TOOLS === "true";
  const ollamaToolsTransport = process.env.SPIRIT_OLLAMA_SUPPORTS_TOOLS === "true";
  const envSaysReadOnlyTools = localToolsCfg && ollamaToolsTransport;

  let localToolsEffective = envSaysReadOnlyTools;
  if (input.localToolsAttached === false) {
    localToolsEffective = false;
  } else if (input.localToolsAttached === true) {
    localToolsEffective = true;
  }

  const localToolsAttachmentNote =
    localToolsCfg &&
    ollamaToolsTransport &&
    !localToolsEffective
      ? "Read-only tools are configured in the environment but are not attached for this model (tool-call probe failed or transport rejected)."
      : null;
  const fileEditEnv = process.env.SPIRIT_ENABLE_FILE_EDIT_TOOLS === "true";
  const devCommandEnv = process.env.SPIRIT_ENABLE_DEV_COMMAND_TOOLS === "true";
  const emailTools = process.env.SPIRIT_ENABLE_EMAIL_TOOLS === "true";
  const calendarTools = process.env.SPIRIT_ENABLE_CALENDAR_TOOLS === "true";

  let fileEditingEffective = false;
  if (fileEditEnv) {
    if (input.fileEditToolsAttached === true) {
      fileEditingEffective = true;
    } else if (input.fileEditToolsAttached === false) {
      fileEditingEffective = false;
    } else {
      fileEditingEffective = false;
    }
  }

  const fileEditingAttachmentNote =
    fileEditEnv && !fileEditingEffective
      ? "File editing is configured in the environment but edit tools are not attached for this model. Guarded edits require propose_file_edit then apply_confirmed_file_edit after explicit user confirmation."
      : null;

  let terminalExecutionEffective = false;
  if (devCommandEnv) {
    terminalExecutionEffective = input.devCommandToolsAttached === true;
  }

  const devCommandAttachmentNote =
    devCommandEnv && !terminalExecutionEffective
      ? "Dev command tools are configured but not attached for this model/session."
      : null;

  if (localToolsEffective) {
    available.push(...LOCAL_TOOL_CAPS);
  } else {
    unavailable.push(...LOCAL_TOOL_CAPS);
  }

  if (fileEditingEffective) {
    available.push("file_editing");
  } else {
    unavailable.push("file_editing");
  }

  if (terminalExecutionEffective) {
    available.push("terminal_execution");
  } else {
    unavailable.push("terminal_execution");
  }

  if (emailTools) {
    available.push("email_access");
  } else {
    unavailable.push("email_access");
  }

  if (calendarTools) {
    available.push("calendar_access");
  } else {
    unavailable.push("calendar_access");
  }

  return {
    currentTimeIso: input.currentTimeIso ?? new Date().toISOString(),
    runtimeSurface: input.runtimeSurface,
    modelHint: input.modelHint ?? null,
    modelProfileId: input.modelProfileId ?? null,
    modelProfileLabel: input.modelProfileLabel ?? null,
    hardwareProfile: process.env.SPIRIT_HARDWARE_PROFILE || "unknown",
    projectPathConfigured: Boolean(process.env.SPIRIT_PROJECT_PATH),
    availableCapabilities: available,
    unavailableCapabilities: unavailable,
    localToolsAttachmentNote,
    fileEditingAttachmentNote,
    devCommandAttachmentNote,
  };
}

export function buildSystemStateBlock(input: SpiritSystemStateInput): string {
  const lines: string[] = ["[SYSTEM STATE]"];

  lines.push(`Time: ${input.currentTimeIso}`);
  lines.push(`Surface: ${input.runtimeSurface}`);

  if (input.modelProfileId) {
    const profilePart = input.modelProfileLabel
      ? `${input.modelProfileId} (${input.modelProfileLabel})`
      : input.modelProfileId;
    lines.push(`Active profile: ${profilePart}`);
  }

  if (input.modelHint) {
    lines.push(`Model: ${input.modelHint}`);
  }

  lines.push(`Hardware profile: ${input.hardwareProfile}`);
  lines.push(`Project path configured: ${input.projectPathConfigured ? "yes" : "no"}`);
  lines.push(`Available capabilities: ${input.availableCapabilities.join(", ")}`);
  lines.push(`Unavailable capabilities: ${input.unavailableCapabilities.join(", ")}`);
  if (input.localToolsAttachmentNote) {
    lines.push(input.localToolsAttachmentNote);
  }
  if (input.fileEditingAttachmentNote) {
    lines.push(input.fileEditingAttachmentNote);
  }
  if (input.devCommandAttachmentNote) {
    lines.push(input.devCommandAttachmentNote);
  }
  lines.push("");
  lines.push(
    "Do not claim you used a tool, read a file, edited a file, ran a command, checked email, or accessed calendar unless that capability is listed as available and an actual tool result was returned in this conversation.",
  );
  lines.push(
    "If a capability is unavailable, say so clearly instead of pretending it happened.",
  );
  lines.push(
    "If the user asks you to use an unavailable capability, explain what is unavailable and offer a manual alternative or explain what would be needed to enable it.",
  );

  return lines.join("\n");
}
