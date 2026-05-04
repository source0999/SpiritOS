// ── research-plan — plan-first stub (Prompt 10C Stage 5) ─────────────────────────
// > Editable steps only — no background job queue until a later prompt eats PM2 alive.

export type ResearchPlanStepStatus = "pending" | "active" | "done" | "error";

export type ResearchPlanStep = {
  id: string;
  label: string;
  detail?: string;
  searchQuery?: string;
  status: ResearchPlanStepStatus;
};

export type ResearchPlan = {
  id: string;
  title: string;
  originalQuestion: string;
  createdAt: number;
  freshnessTarget?: string;
  sourcePreferences: string[];
  steps: ResearchPlanStep[];
};

function uid(): string {
  try {
    if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  } catch {
    /* ignore */
  }
  return `rp_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

const DEFAULT_STEP_LABELS = [
  "Clarify the research question.",
  "Search recent professional or academic sources.",
  "Review source quality.",
  "Compare findings and limitations.",
  "Draft answer.",
  "Provide citations and source list.",
] as const;

export function draftResearchPlanFromPrompt(question: string): ResearchPlan {
  const q = question.trim() || "Untitled research";
  const steps: ResearchPlanStep[] = DEFAULT_STEP_LABELS.map((label, i) => ({
    id: `step_${i + 1}`,
    label,
    status: "pending" as const,
  }));
  return {
    id: uid(),
    title: q.length > 72 ? `${q.slice(0, 69)}…` : q,
    originalQuestion: q,
    createdAt: Date.now(),
    freshnessTarget: "Prefer sources from the last ~5 years when relevant.",
    sourcePreferences: ["academic", "professional", "government", "primary sources", "credible news"],
    steps,
  };
}

export function editResearchPlanStep(
  plan: ResearchPlan,
  stepId: string,
  patch: Partial<Pick<ResearchPlanStep, "label" | "detail" | "searchQuery" | "status">>,
): ResearchPlan {
  return {
    ...plan,
    steps: plan.steps.map((s) => (s.id === stepId ? { ...s, ...patch } : s)),
  };
}

export function addResearchPlanStep(plan: ResearchPlan, label: string): ResearchPlan {
  const id = `step_${uid()}`;
  return {
    ...plan,
    steps: [...plan.steps, { id, label, status: "pending" }],
  };
}

export function removeResearchPlanStep(plan: ResearchPlan, stepId: string): ResearchPlan {
  return {
    ...plan,
    steps: plan.steps.filter((s) => s.id !== stepId),
  };
}

export function researchPlanToSummary(plan: ResearchPlan): string {
  const lines = plan.steps.map((s, i) => `${i + 1}. ${s.label}${s.detail ? ` — ${s.detail}` : ""}`);
  return `## User-approved research plan\nTitle: ${plan.title}\nQuestion: ${plan.originalQuestion}\nSteps:\n${lines.join("\n")}`;
}
