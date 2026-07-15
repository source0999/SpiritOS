import {
  buildDummyCoder10RunnerPacket,
  dummyCoder10Prompts,
  formatDummyCoder10ForbiddenSummary,
  type DummyCoder10Prompt,
} from "./lumacart/prompts";
import {
  gradeDummyCoder10Result,
  type DummyCoder10GradingResult,
} from "./lumacart/grader";
import {
  buildExistingDummyProjectSummary,
  probeDummyStorefront,
  type DummyStorefrontProbeResult,
} from "./lumacart/project-summary";

/**
 * The only browser-facing gateway to a target-specific coding exercise.
 * The cockpit consumes this generic surface; names, DOM expectations, graders,
 * and fixture paths remain inside the selected target-plugin module.
 */
export const codingTargetPlugin = {
  id: "lumacart",
  prompts: dummyCoder10Prompts,
  buildRunnerPacket(prompt: DummyCoder10Prompt, existingDummyProjectSummary: string) {
    return {
      ...buildDummyCoder10RunnerPacket(prompt, existingDummyProjectSummary),
      target_plugin: {
        schema_version: "spiritos-target-plugin/v1",
        id: "lumacart",
        repository_id: "spiritos-campaign-1",
        worktree_id: "spiritos-campaign-1-20260712",
        fixture_root: prompt.fixtureRoot,
        selected_prompt_id: prompt.id,
        selected_context_id: prompt.number === 1 ? "init-storefront" : prompt.number === 2 ? "product-data" : prompt.number === 3 ? "render-cards" : "unsupported",
        execution_profile: "coder-10",
      },
    };
  },
  formatForbiddenSummary: formatDummyCoder10ForbiddenSummary,
  gradeResult: gradeDummyCoder10Result,
  buildExistingProjectSummary: buildExistingDummyProjectSummary,
  probeStorefront: probeDummyStorefront,
} as const;

export type TargetPluginPrompt = DummyCoder10Prompt;
export type TargetPluginGradingResult = DummyCoder10GradingResult;
export type TargetPluginStorefrontProbeResult = DummyStorefrontProbeResult;
