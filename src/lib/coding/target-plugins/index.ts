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
  buildRunnerPacket: buildDummyCoder10RunnerPacket,
  formatForbiddenSummary: formatDummyCoder10ForbiddenSummary,
  gradeResult: gradeDummyCoder10Result,
  buildExistingProjectSummary: buildExistingDummyProjectSummary,
  probeStorefront: probeDummyStorefront,
} as const;

export type TargetPluginPrompt = DummyCoder10Prompt;
export type TargetPluginGradingResult = DummyCoder10GradingResult;
export type TargetPluginStorefrontProbeResult = DummyStorefrontProbeResult;
