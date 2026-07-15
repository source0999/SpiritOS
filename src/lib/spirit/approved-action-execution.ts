import "server-only";

import { promises as fs } from "fs";

import { applyUnifiedDiffToText } from "@/lib/spirit/apply-unified-diff";
import {
  applyConfirmedFileEdit,
  proposeFileEdit,
} from "@/lib/spirit/tools/file-edit-tools";
import { resolveSafeWorkspacePath } from "@/lib/spirit/tools/tool-safety";

export type ApprovedActionExecutionInput = {
  action: string;
  content?: string;
  /** Unified diff from the Coder Agent / approval gate when `content` is empty. */
  approvedDiff?: string;
  target: string;
};

export type ApprovedActionExecutionResult =
  | {
      ok: true;
      action: string;
      appliedAt: string;
      backupRelativePath: string;
      diff: string;
      message: string;
      proposalId: string;
      relativeFilePath: string;
      target: string;
    }
  | {
      ok: false;
      code: string;
      message: string;
    };

async function nextContentFromApprovedUnifiedDiff(
  target: string,
  approvedDiff: string,
): Promise<string | null> {
  const patch = approvedDiff.trim();
  if (!patch) {
    return null;
  }
  let abs: string;
  try {
    abs = resolveSafeWorkspacePath(target);
  } catch {
    return null;
  }
  let original = "";
  try {
    original = await fs.readFile(abs, "utf8");
  } catch (e) {
    const err = e as NodeJS.ErrnoException;
    if (err?.code === "ENOENT") {
      original = "";
    } else {
      return null;
    }
  }
  return applyUnifiedDiffToText(original, patch);
}

export async function executeApprovedAction(
  input: ApprovedActionExecutionInput,
): Promise<ApprovedActionExecutionResult> {
  const action = input.action.trim();
  const target = input.target.trim();
  const nextContent =
    approvedFileContentFor(action, target, input.content) ||
    (await nextContentFromApprovedUnifiedDiff(target, input.approvedDiff ?? ""));
  if (!nextContent) {
    return {
      ok: false,
      code: "NO_APPROVED_EXECUTION_TEMPLATE",
      message:
        "This approved action does not include executable file content yet. Paste a unified diff in the proposal, run the Coder Agent path so proposed_diff is populated, or supply full file content.",
    };
  }

  const proposal = await proposeFileEdit({
    filePath: target,
    nextContent,
    reason: action,
  });
  if (!proposal.ok) {
    return proposal;
  }

  const applied = await applyConfirmedFileEdit({
    proposalId: proposal.proposalId,
    confirm: true,
  });
  if (!applied.ok) {
    return applied;
  }

  return {
    ok: true,
    action,
    appliedAt: applied.appliedAt,
    backupRelativePath: applied.backupRelativePath,
    diff: proposal.diff,
    message: applied.message,
    proposalId: proposal.proposalId,
    relativeFilePath: applied.relativeFilePath,
    target,
  };
}

export function approvedFileContentFor(
  action: string,
  target: string,
  approvedContent = "",
) {
  if (approvedContent.trim()) {
    return approvedContent.endsWith("\n") ? approvedContent : `${approvedContent}\n`;
  }

  const normalizedAction = action.toLowerCase();
  const normalizedTarget = target.replace(/\\/g, "/");
  if (
    normalizedTarget === "src/app/design-demo/coding/page.tsx" &&
    (normalizedAction.includes("create") ||
      normalizedAction.includes("implement") ||
      normalizedAction.includes("file"))
  ) {
    return [
      'import { redirect } from "next/navigation";',
      "",
      "export default function DesignDemoCodingPage() {",
      '  redirect("/coding");',
      "}",
      "",
    ].join("\n");
  }

  return "";
}
