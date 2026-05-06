// ── file-edit-tools - guarded propose / confirmed apply, no silent writes ─
// > Phase 5: fs/promises only. Paths via tool-safety. Backups live under .spirit-backups/.

import "server-only";

import { randomUUID } from "crypto";
import { promises as fs } from "fs";
import path from "path";

import {
  TOOL_MAX_FILE_BYTES,
  TOOL_MAX_OUTPUT_CHARS,
  SpiritToolPathError,
  normalizeWorkspaceRelativePath,
  resolveSafeWorkspacePath,
  truncateToolOutput,
  toolErrorFromUnknown,
  type ToolSafeError,
} from "@/lib/spirit/tools/tool-safety";

export const FILE_EDIT_MAX_NEXT_BYTES = 200 * 1024;
export const FILE_EDIT_PROPOSAL_TTL_MS = 10 * 60 * 1000;

export type FileEditProposal = {
  id: string;
  createdAt: number;
  expiresAt: number;
  relativeFilePath: string;
  previousContent: string;
  nextContent: string;
  diff: string;
  reason?: string;
};

const fileEditProposalStore = new Map<string, FileEditProposal>();

export function isFileEditToolsEnvEnabled(): boolean {
  return process.env.SPIRIT_ENABLE_FILE_EDIT_TOOLS === "true";
}

export function clearExpiredFileEditProposals(): void {
  const now = Date.now();
  for (const [id, p] of fileEditProposalStore) {
    if (p.expiresAt <= now) fileEditProposalStore.delete(id);
  }
}

/** Vitest only */
export function clearAllFileEditProposalsForTests(): void {
  fileEditProposalStore.clear();
}

/** Vitest only */
export function setFileEditProposalExpiryForTest(id: string, expiresAt: number): void {
  const p = fileEditProposalStore.get(id);
  if (p) {
    p.expiresAt = expiresAt;
  }
}

/** Vitest only: inspect stored proposal */
export function getFileEditProposalForTest(id: string): FileEditProposal | undefined {
  return fileEditProposalStore.get(id);
}

function assertUtf8NoNul(buf: Buffer): void {
  if (buf.includes(0)) {
    throw new SpiritToolPathError("NOT_TEXT_FILE", "Only UTF-8 text files are allowed.");
  }
}

/** Simple line-aligned unified-ish diff (no external deps); capped for tool output */
export function buildSimpleUnifiedDiff(
  relativeDisplayPath: string,
  previousContent: string,
  nextContent: string,
): string {
  const a = previousContent.split(/\r?\n/);
  const b = nextContent.split(/\r?\n/);
  const lines: string[] = [`--- ${relativeDisplayPath}`, `+++ ${relativeDisplayPath}`, "@@"];
  const maxLines = 800;
  const maxRows = Math.max(a.length, b.length);
  for (let i = 0; i < maxRows; i++) {
    if (lines.length > maxLines) {
      lines.push("... [diff truncated]");
      break;
    }
    const la = i < a.length ? a[i] : undefined;
    const lb = i < b.length ? b[i] : undefined;
    if (la === lb && la !== undefined) {
      lines.push(` ${la}`);
    } else {
      if (la !== undefined) lines.push(`-${la}`);
      if (lb !== undefined) lines.push(`+${lb}`);
    }
  }
  const raw = lines.join("\n");
  const capped = truncateToolOutput(raw, TOOL_MAX_OUTPUT_CHARS);
  return capped.text + (capped.truncated ? "\n... [diff output truncated]" : "");
}

export type ProposeFileEditInput = {
  filePath: string;
  nextContent: string;
  reason?: string;
};

export type ProposeFileEditOk = {
  ok: true;
  proposalId: string;
  relativeFilePath: string;
  diff: string;
  confirmationRequired: true;
  expiresAt: number;
  message: string;
};

export async function proposeFileEdit(
  input: ProposeFileEditInput,
): Promise<ProposeFileEditOk | ToolSafeError> {
  clearExpiredFileEditProposals();

  if (!isFileEditToolsEnvEnabled()) {
    return {
      ok: false,
      code: "FILE_EDIT_DISABLED",
      message: "SPIRIT_ENABLE_FILE_EDIT_TOOLS is not enabled.",
    };
  }

  if (typeof input.nextContent !== "string") {
    return { ok: false, code: "INVALID_INPUT", message: "nextContent must be a string." };
  }

  const nextBuf = Buffer.from(input.nextContent, "utf8");
  if (nextBuf.length > FILE_EDIT_MAX_NEXT_BYTES) {
    return {
      ok: false,
      code: "NEXT_TOO_LARGE",
      message: `nextContent exceeds maximum of ${FILE_EDIT_MAX_NEXT_BYTES} bytes.`,
    };
  }

  let rel: string;
  try {
    rel = normalizeWorkspaceRelativePath(input.filePath);
    resolveSafeWorkspacePath(input.filePath);
  } catch (e) {
    return toolErrorFromUnknown(e);
  }

  const abs = resolveSafeWorkspacePath(input.filePath);

  let previousContent = "";
  try {
    const st = await fs.stat(abs);
    if (!st.isFile()) {
      return { ok: false, code: "NOT_A_FILE", message: "Path is not a file." };
    }
    if (st.size > TOOL_MAX_FILE_BYTES) {
      return {
        ok: false,
        code: "FILE_TOO_LARGE",
        message: `Existing file exceeds maximum size of ${TOOL_MAX_FILE_BYTES} bytes.`,
      };
    }
    const buf = await fs.readFile(abs);
    assertUtf8NoNul(buf);
    previousContent = buf.toString("utf8");
  } catch (e) {
    const err = e as NodeJS.ErrnoException;
    if (err?.code === "ENOENT") {
      previousContent = "";
    } else {
      return toolErrorFromUnknown(e);
    }
  }

  const relDisplay = rel.split(path.sep).join("/");
  const diff = buildSimpleUnifiedDiff(relDisplay, previousContent, input.nextContent);

  const id = randomUUID();
  const createdAt = Date.now();
  const expiresAt = createdAt + FILE_EDIT_PROPOSAL_TTL_MS;

  const proposal: FileEditProposal = {
    id,
    createdAt,
    expiresAt,
    relativeFilePath: relDisplay,
    previousContent,
    nextContent: input.nextContent,
    diff,
    reason: input.reason,
  };
  fileEditProposalStore.set(id, proposal);

  return {
    ok: true,
    proposalId: id,
    relativeFilePath: relDisplay,
    diff,
    confirmationRequired: true,
    expiresAt,
    message:
      "Review this diff. To apply it, call apply_confirmed_file_edit with this proposalId and confirm: true after the user approves.",
  };
}

export type ApplyConfirmedFileEditInput = {
  proposalId: string;
  confirm: boolean;
};

export type ApplyConfirmedFileEditOk = {
  ok: true;
  relativeFilePath: string;
  backupRelativePath: string;
  appliedAt: string;
  message: string;
};

export async function applyConfirmedFileEdit(
  input: ApplyConfirmedFileEditInput,
): Promise<ApplyConfirmedFileEditOk | ToolSafeError> {
  if (!isFileEditToolsEnvEnabled()) {
    return {
      ok: false,
      code: "FILE_EDIT_DISABLED",
      message: "SPIRIT_ENABLE_FILE_EDIT_TOOLS is not enabled.",
    };
  }

  if (!input.confirm) {
    return {
      ok: false,
      code: "CONFIRMATION_REQUIRED",
      message: "confirm must be true to apply a stored proposal.",
    };
  }

  const proposal = fileEditProposalStore.get(input.proposalId);
  if (!proposal) {
    return { ok: false, code: "PROPOSAL_NOT_FOUND", message: "Unknown or expired proposal id." };
  }

  if (proposal.expiresAt <= Date.now()) {
    fileEditProposalStore.delete(input.proposalId);
    return { ok: false, code: "PROPOSAL_EXPIRED", message: "This proposal has expired." };
  }

  let rel: string;
  try {
    rel = normalizeWorkspaceRelativePath(proposal.relativeFilePath);
    resolveSafeWorkspacePath(proposal.relativeFilePath);
  } catch (e) {
    return toolErrorFromUnknown(e);
  }

  const abs = resolveSafeWorkspacePath(proposal.relativeFilePath);

  let currentContent = "";
  try {
    const st = await fs.stat(abs);
    if (!st.isFile()) {
      return { ok: false, code: "NOT_A_FILE", message: "Path is not a file." };
    }
    if (st.size > TOOL_MAX_FILE_BYTES) {
      return {
        ok: false,
        code: "FILE_TOO_LARGE",
        message: "File grew beyond the maximum allowed size since the proposal.",
      };
    }
    const buf = await fs.readFile(abs);
    assertUtf8NoNul(buf);
    currentContent = buf.toString("utf8");
  } catch (e) {
    const err = e as NodeJS.ErrnoException;
    if (err?.code === "ENOENT") {
      currentContent = "";
    } else {
      return toolErrorFromUnknown(e);
    }
  }

  if (currentContent !== proposal.previousContent) {
    return {
      ok: false,
      code: "CONFLICT",
      message:
        "File content changed since the proposal was created. Re-run propose_file_edit with a fresh diff.",
    };
  }

  clearExpiredFileEditProposals();

  const appliedAt = new Date().toISOString();
  const day = appliedAt.slice(0, 10);
  const ts = Date.now();
  const safeBase = path.basename(rel).replace(/[^\w.-]+/g, "_") || "file";
  const backupRelPath = path.join(".spirit-backups", day, `${safeBase}.${ts}.bak`).split(path.sep).join("/");

  let backupAbs: string;
  try {
    backupAbs = resolveSafeWorkspacePath(backupRelPath);
  } catch (e) {
    return toolErrorFromUnknown(e);
  }

  await fs.mkdir(path.dirname(backupAbs), { recursive: true });

  if (currentContent.length > 0) {
    await fs.writeFile(backupAbs, currentContent, "utf8");
  }

  await fs.mkdir(path.dirname(abs), { recursive: true });

  await fs.writeFile(abs, proposal.nextContent, "utf8");
  fileEditProposalStore.delete(input.proposalId);

  return {
    ok: true,
    relativeFilePath: rel.split(path.sep).join("/"),
    backupRelativePath: backupRelPath,
    appliedAt,
    message: "Applied confirmed edit and created a backup.",
  };
}
