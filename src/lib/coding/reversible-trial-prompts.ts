export type ReversibleTrialCount = 25 | 50 | 100;

export type ReversibleTrialPrompt = {
  auto_revert: true;
  category:
    | "coding UI"
    | "dashboard cards"
    | "scout/agent UI"
    | "oracle UI"
    | "source/sidebar style"
    | "result/diagnostics UX"
    | "status cards"
    | "map/media placeholder UI"
    | "reversible component polish"
    | "small bounded feature additions";
  expected_scope: string[];
  id: string;
  prompt: string;
  protected_paths_blocked: true;
  reversible: true;
  risk: "low" | "medium";
  targetFile: string;
};

export const reversibleTrialCounts = [25, 50, 100] as const;

const basePrompts: ReversibleTrialPrompt[] = [
  {
    id: "scout-soccer-agent-card",
    prompt:
      "Make a new soccer scouting intelligence agent card for SpiritOS that can later connect to scouting data. Keep it simple, visible in the relevant scout/agent area, and make the change reversible.",
    category: "scout/agent UI",
    expected_scope: ["src/components/dashboard/ScoutIntelligenceCenter.tsx"],
    targetFile: "src/components/dashboard/ScoutIntelligenceCenter.tsx",
    reversible: true,
    risk: "low",
    protected_paths_blocked: true,
    auto_revert: true,
  },
  {
    id: "source-voidcore-selected-state",
    prompt:
      "Change the Source sidebar selected state toward a darker voidcore style while keeping the current light layout intact. Make the change reversible.",
    category: "source/sidebar style",
    expected_scope: ["src/components/chat/ChatThreadListItem.tsx"],
    targetFile: "src/components/chat/ChatThreadListItem.tsx",
    reversible: true,
    risk: "low",
    protected_paths_blocked: true,
    auto_revert: true,
  },
  {
    id: "coding-failure-next-step",
    prompt:
      "Make the coding result card easier to understand when a live apply run fails by adding one clear next-step sentence and keeping diagnostics copy available. Make the change reversible.",
    category: "result/diagnostics UX",
    expected_scope: ["src/components/coding/CodingCockpitShell.tsx"],
    targetFile: "src/components/coding/CodingCockpitShell.tsx",
    reversible: true,
    risk: "low",
    protected_paths_blocked: true,
    auto_revert: true,
  },
  {
    id: "oracle-daily-briefing-action",
    prompt:
      "Add a small Oracle quick action for daily briefing preparation, wired as a visible UI option but not connected to external services yet. Make the change reversible.",
    category: "oracle UI",
    expected_scope: ["src/components/dashboard/OracleStagePanel.tsx"],
    targetFile: "src/components/dashboard/OracleStagePanel.tsx",
    reversible: true,
    risk: "low",
    protected_paths_blocked: true,
    auto_revert: true,
  },
];

const promptVariants: Array<Omit<ReversibleTrialPrompt, "id" | "prompt"> & { prompt: (index: number) => string; slug: string }> = [
  {
    slug: "scout-code-intelligence-card",
    prompt: (index) =>
      `Add a useful scout/code intelligence card for SpiritOS run ${index} by shaping it as a soccer scouting intelligence agent card that can later connect to scouting data. Keep it bounded and reversible.`,
    category: "dashboard cards",
    expected_scope: ["src/components/dashboard/ScoutIntelligenceCenter.tsx"],
    targetFile: "src/components/dashboard/ScoutIntelligenceCenter.tsx",
    reversible: true,
    risk: "low",
    protected_paths_blocked: true,
    auto_revert: true,
  },
  {
    slug: "source-sidebar-voidcore-polish",
    prompt: (index) =>
      `Change the Source sidebar selected state toward voidcore style for reversible trial run ${index}, keeping the current layout and interaction model intact.`,
    category: "reversible component polish",
    expected_scope: ["src/components/chat/ChatThreadListItem.tsx"],
    targetFile: "src/components/chat/ChatThreadListItem.tsx",
    reversible: true,
    risk: "low",
    protected_paths_blocked: true,
    auto_revert: true,
  },
  {
    slug: "coding-result-diagnostics-guidance",
    prompt: (index) =>
      `Improve the coding result card after a live apply run fails for reversible trial run ${index}; add one clear next-step sentence while keeping diagnostics copy available.`,
    category: "coding UI",
    expected_scope: ["src/components/coding/CodingCockpitShell.tsx"],
    targetFile: "src/components/coding/CodingCockpitShell.tsx",
    reversible: true,
    risk: "low",
    protected_paths_blocked: true,
    auto_revert: true,
  },
  {
    slug: "oracle-daily-briefing-quick-action",
    prompt: (index) =>
      `Add a small Oracle daily briefing quick action for reversible trial run ${index}, visible as a UI option and not connected to external services.`,
    category: "small bounded feature additions",
    expected_scope: ["src/components/dashboard/OracleStagePanel.tsx"],
    targetFile: "src/components/dashboard/OracleStagePanel.tsx",
    reversible: true,
    risk: "low",
    protected_paths_blocked: true,
    auto_revert: true,
  },
  {
    slug: "scout-source-status-card",
    prompt: (index) =>
      `Add a small reversible source/status card to Scout for trial run ${index} by using the soccer scouting intelligence agent card pattern as the bounded visible affordance.`,
    category: "status cards",
    expected_scope: ["src/components/dashboard/ScoutIntelligenceCenter.tsx"],
    targetFile: "src/components/dashboard/ScoutIntelligenceCenter.tsx",
    reversible: true,
    risk: "medium",
    protected_paths_blocked: true,
    auto_revert: true,
  },
  {
    slug: "coding-session-status-detail",
    prompt: (index) =>
      `Add a small reversible coding session status detail for trial run ${index} by improving the coding result card when a live apply run fails and preserving diagnostics copy.`,
    category: "result/diagnostics UX",
    expected_scope: ["src/components/coding/CodingCockpitShell.tsx"],
    targetFile: "src/components/coding/CodingCockpitShell.tsx",
    reversible: true,
    risk: "low",
    protected_paths_blocked: true,
    auto_revert: true,
  },
  {
    slug: "map-media-placeholder-scout-affordance",
    prompt: (index) =>
      `Add a small reversible map/media placeholder UI affordance to Scout for trial run ${index}, represented as a soccer scouting intelligence agent card for later data wiring.`,
    category: "map/media placeholder UI",
    expected_scope: ["src/components/dashboard/ScoutIntelligenceCenter.tsx"],
    targetFile: "src/components/dashboard/ScoutIntelligenceCenter.tsx",
    reversible: true,
    risk: "medium",
    protected_paths_blocked: true,
    auto_revert: true,
  },
  {
    slug: "oracle-briefing-prep-affordance",
    prompt: (index) =>
      `Add a small reversible Oracle UI affordance for daily briefing preparation in trial run ${index}; keep it visible and disconnected from external services.`,
    category: "oracle UI",
    expected_scope: ["src/components/dashboard/OracleStagePanel.tsx"],
    targetFile: "src/components/dashboard/OracleStagePanel.tsx",
    reversible: true,
    risk: "low",
    protected_paths_blocked: true,
    auto_revert: true,
  },
];

function buildCatalog(): ReversibleTrialPrompt[] {
  const prompts = [...basePrompts];
  let index = prompts.length + 1;
  while (prompts.length < 100) {
    for (const variant of promptVariants) {
      if (prompts.length >= 100) break;
      prompts.push({
        ...variant,
        id: `${variant.slug}-${String(index).padStart(3, "0")}`,
        prompt: variant.prompt(index),
      });
      index += 1;
    }
  }
  return prompts;
}

export const reversibleTrialPromptCatalog = buildCatalog();

export function selectReversibleTrialPrompts(count: ReversibleTrialCount): ReversibleTrialPrompt[] {
  return reversibleTrialPromptCatalog.slice(0, count);
}
