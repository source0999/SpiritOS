import { describe, expect, it } from "vitest";

import { deriveProposalDraft } from "@/components/coding/CodingAgentInterface";
import {
  buildWorkflowTaskFromProposal,
  effectivePlanningTaskText,
  parseBoundedProposalTask,
  proposalDraftResultToBounded,
} from "@/lib/coding/proposal-task-handoff";

describe("proposal-task-handoff", () => {
  it("parses bounded proposal JSON and preserves target_file over forbidden_files", () => {
    const draft = deriveProposalDraft({
      allowedFilesText: "src/app/proxy-backend/page.tsx",
      expectedChecksText: "git diff --check\ntarget-only",
      forbiddenFilesText: ".env\n.env.local\n.env.*\npackage.json",
      mode: "proposal",
      rollbackHint: "git restore <target_file>",
      targetFile: "src/app/proxy-backend/page.tsx",
      task: "Create the proxy backend page.",
    });
    const parsed = parseBoundedProposalTask(draft.text);
    expect(parsed).not.toBeNull();
    expect(parsed?.target_file).toBe("src/app/proxy-backend/page.tsx");
    expect(parsed?.forbidden_files).toContain(".env");
    expect(parsed?.allowed_files).toEqual(["src/app/proxy-backend/page.tsx"]);
  });

  it("buildWorkflowTaskFromProposal prepends Target file line before JSON", () => {
    const proposal = proposalDraftResultToBounded(
      deriveProposalDraft({
        allowedFilesText: "src/app/proxy-backend/page.tsx",
        expectedChecksText: "target-only",
        forbiddenFilesText: ".env",
        mode: "proposal",
        rollbackHint: "git restore <target_file>",
        targetFile: "src/app/proxy-backend/page.tsx",
        task: "Create the proxy backend page.",
      }),
    );
    const workflowTask = buildWorkflowTaskFromProposal(proposal);
    expect(workflowTask.indexOf("Target file: src/app/proxy-backend/page.tsx")).toBe(0);
    expect(workflowTask).toContain('"forbidden_files"');
    expect(workflowTask).toContain(".env");
    expect(workflowTask).not.toMatch(/apply now|commit now|push now/i);
  });

  it("returns null for plain text without proposal envelope", () => {
    expect(parseBoundedProposalTask("Fix the dashboard footer.")).toBeNull();
  });

  it("effectivePlanningTaskText ignores JSON envelope when proposal task is empty", () => {
    const proposal = proposalDraftResultToBounded(
      deriveProposalDraft({
        allowedFilesText: "docs/phase-8-manual-check.md",
        expectedChecksText: "target-only",
        forbiddenFilesText: ".env",
        mode: "proposal",
        rollbackHint: "git restore <target_file>",
        targetFile: "docs/phase-8-manual-check.md",
        task: "",
      }),
    );
    const workflowTask = buildWorkflowTaskFromProposal(proposal);
    const effective = effectivePlanningTaskText(workflowTask);
    expect(effective).toBe("Target file: docs/phase-8-manual-check.md");
    expect(effective).not.toContain("allowed_files");
    expect(effective).not.toContain(".env");
  });
});
