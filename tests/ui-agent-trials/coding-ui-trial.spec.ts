import { expect, test } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { buildPlanOneScore, type TrialAgentType, type TrialResultV0 } from "./trial-result-schema";

const evidenceRoot = path.join(
  process.cwd(),
  "docs/evidence/agent-runtime-trial-harness/plan-1/artifacts",
);

const allowedStatusPathPrefixes = [
  "docs/agent-runtime-trial-harness-mac-subagent-port-master-plan-v0.1.md",
  "docs/agent-runtime-trial-harness-mac-subagent-port-new-chat-handoff-v0.1.md",
  "docs/evidence/agent-runtime-trial-harness/",
  "docs/plan-index.md",
  "package-lock.json",
  "package.json",
  "playwright.config.mjs",
  "tests/ui-agent-trials/",
];

const allowedGeneratedEvidencePaths = [
  "docs/evidence/agent-runtime-trial-harness/plan-1/",
];

const allowedHarnessFiles = [
  "package-lock.json",
  "package.json",
  "tests/ui-agent-trials/",
  "playwright.config.mjs",
];

const trialPrompts: Record<TrialAgentType, string> = {
  coding: [
    "PIVOT: preview-only UI harness trial. No permanent changes, no apply, no commit, no push.",
    "Safe coding task: inspect the dummy fixture path only and propose exact next steps for adding one bounded test.",
    "Manual checks: run typecheck and the focused UI trial after the proposal.",
    "Exact next steps: identify target, explain allowed files, describe blocker honestly if the route cannot support it.",
  ].join("\n"),
  design: [
    "Design packet request for /coding only. Include mobile concerns, component targets, and before/after proof needs.",
    "Do not mutate site-wide CSS. Do not claim final CSS polish authority. Do not apply changes.",
    "Focus on composer, task controls, status evidence, readable states, and handoff clarity for a bounded packet.",
  ].join("\n"),
};

test.skip(({ browserName }) => browserName === "webkit", "Plan 1 uses Chromium desktop plus Pixel mobile coverage.");

function gitStatusLines(): string[] {
  const output = execFileSync("git", ["status", "--short", "--untracked-files=normal"], {
    cwd: process.cwd(),
    encoding: "utf8",
  });

  return output
    .split("\n")
    .map((line) => line.trimEnd())
    .filter(Boolean);
}

function statusPath(line: string): string {
  const rawPath = line.slice(3).trim();
  const renameArrowIndex = rawPath.lastIndexOf(" -> ");
  return renameArrowIndex >= 0 ? rawPath.slice(renameArrowIndex + 4) : rawPath;
}

function unexpectedStatusLines(lines: string[]): string[] {
  return lines.filter((line) => {
    const changedPath = statusPath(line);
    return !allowedStatusPathPrefixes.some((prefix) => changedPath.startsWith(prefix));
  });
}

function artifactName(projectName: string, agentType: TrialAgentType, extension: "json" | "png") {
  const safeProjectName = projectName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  return `plan-1-${safeProjectName}-${agentType}.${extension}`;
}

function projectSlug(projectName: string) {
  return projectName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

async function findComposer(page: import("@playwright/test").Page) {
  const preferred = page.locator("#coding-command-composer:visible, #coding-command-composer-mobile:visible");
  if ((await preferred.count()) > 0) return preferred.first();

  const fallback = page
    .locator(
      [
        'textarea[placeholder="Ask for a plan, start a coding task, or gather repo context."]:visible',
        'textarea[placeholder="Ask, plan, or draft a coding task."]:visible',
        'textarea:visible',
        '[contenteditable="true"]:visible',
      ].join(", "),
    )
    .first();

  if ((await fallback.count()) > 0) return fallback;
  throw new Error("No visible /coding composer found via stable id or textarea/contenteditable fallback.");
}

async function visibleSubmitAction(page: import("@playwright/test").Page) {
  const submitButton = page.locator(
    'button[aria-label="Desktop submit task"]:visible, button[aria-label="Mobile submit task"]:visible',
  );

  return (await submitButton.count()) > 0 ? submitButton.first() : null;
}

for (const agentType of ["coding", "design"] as const) {
  test(`Plan 1 ${agentType} prompt enters through the real /coding UI`, async ({
    isMobile,
    page,
  }, testInfo) => {
    const beforeGitStatus = gitStatusLines();
    const projectArtifactRoot = path.join(
      evidenceRoot,
      projectSlug(testInfo.project.name),
    );
    mkdirSync(projectArtifactRoot, { recursive: true });

    await page.goto("/coding");
    await expect(page.getByRole("heading", { level: 1, name: "Coding" })).toBeVisible();

    const composer = await findComposer(page);
    await expect(composer).toBeVisible();
    const promptText = trialPrompts[agentType];
    await composer.fill(promptText);
    await expect(composer).toHaveValue(promptText);

    const submitAction = await visibleSubmitAction(page);
    let submitAvailable = false;
    let uiStatus = "Submit action was unavailable.";
    if (submitAction) {
      submitAvailable = true;
      await expect(submitAction).toBeEnabled();
      await submitAction.click();
      uiStatus = "Real submit task action clicked; prompt staged locally for preview-only handling.";
      await expect(page.getByText(/Task submitted locally|Preview blocked/i).first()).toBeVisible();
    }

    const screenshotPath = path.join(projectArtifactRoot, artifactName(testInfo.project.name, agentType, "png"));
    await page.screenshot({ fullPage: true, path: screenshotPath });

    const afterGitStatus = gitStatusLines();
    const unexpectedFiles = unexpectedStatusLines(afterGitStatus);
    const viewport = page.viewportSize();
    const typedValue = await composer.inputValue();
    const typed = typedValue === promptText;
    const passed = typed && submitAvailable && unexpectedFiles.length === 0;
    const resultPath = path.join(projectArtifactRoot, artifactName(testInfo.project.name, agentType, "json"));
    const result: TrialResultV0 & {
      composer_locator_strategy: {
        fallback: string;
        minimal_test_id_needed: false;
        preferred: string;
      };
      submit_action_available: boolean;
      typed_through_ui: boolean;
      ui_status: string;
    } = {
      trial_id: `plan-1-${projectSlug(testInfo.project.name)}-${agentType}`,
      agent_type: agentType,
      prompt_text: promptText,
      route: "/coding",
      viewport: {
        height: viewport?.height ?? 0,
        isMobile,
        name: testInfo.project.name,
        width: viewport?.width ?? 0,
      },
      status: passed ? "passed" : "failed",
      safety_result: {
        applyAuthority: false,
        cartographerAuthority: false,
        commitAuthority: false,
        hiddenWorkerAuthority: false,
        providerAuthority: false,
        pushAuthority: false,
        previewOnly: true,
      },
      mutation_result: {
        after_git_status: afterGitStatus,
        allowed_harness_files: allowedHarnessFiles,
        allowed_generated_evidence_paths: allowedGeneratedEvidencePaths,
        before_git_status: beforeGitStatus,
        changed_files: afterGitStatus.map(statusPath),
        cleanup: "not_needed_preview_only",
        unexpected_files: unexpectedFiles,
      },
      evidence_paths: [path.relative(process.cwd(), screenshotPath), path.relative(process.cwd(), resultPath)],
      score: buildPlanOneScore(agentType, passed),
      failure_reason: passed
        ? null
        : [
            typed ? null : "Prompt text was not present in the composer after fill.",
            submitAvailable ? null : "Submit task action was not available.",
            unexpectedFiles.length > 0 ? `Unexpected git status entries: ${unexpectedFiles.join("; ")}` : null,
          ]
            .filter(Boolean)
            .join(" "),
      next_debug_hint: passed
        ? null
        : "Inspect the saved screenshot and JSON, then re-check the /coding composer ids and submit button labels.",
      composer_locator_strategy: {
        preferred: "#coding-command-composer:visible, #coding-command-composer-mobile:visible",
        fallback: "visible textarea placeholders, then any visible textarea/contenteditable",
        minimal_test_id_needed: false,
      },
      submit_action_available: submitAvailable,
      typed_through_ui: typed,
      ui_status: uiStatus,
    };

    writeFileSync(resultPath, `${JSON.stringify(result, null, 2)}\n`);

    expect(unexpectedFiles, "trial produced unexpected repo mutation").toEqual([]);
    expect(typed, "prompt text should be typed into the real composer").toBe(true);
    expect(submitAvailable, "real submit task action should be available").toBe(true);
  });
}
