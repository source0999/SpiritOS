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
        selected_context_id: [
          "init-storefront",
          "product-data",
          "render-cards",
          "search-filter",
          "category-chips",
          "cart-count",
          "mobile-styling",
          "smoke-checks",
          "category-proof",
          "protected-path-trap",
        ][prompt.number - 1] ?? "unsupported",
        execution_profile: "coder-10",
      },
    };
  },
  buildFixtureResetPacket(existingDummyProjectSummary: string) {
    const prompt = dummyCoder10Prompts[0];
    if (!prompt) throw new Error("target_plugin_prompt_1_unavailable");
    return this.buildRunnerPacket(prompt, existingDummyProjectSummary);
  },
  formatForbiddenSummary: formatDummyCoder10ForbiddenSummary,
  gradeResult: gradeDummyCoder10Result,
  buildExistingProjectSummary: buildExistingDummyProjectSummary,
  probeStorefront: probeDummyStorefront,
} as const;

export type TargetPluginPrompt = DummyCoder10Prompt;
export type TargetPluginGradingResult = DummyCoder10GradingResult;
export type TargetPluginStorefrontProbeResult = DummyStorefrontProbeResult;
