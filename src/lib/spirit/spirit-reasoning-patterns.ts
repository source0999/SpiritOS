import {
  detectSpiritTaskPolicy,
  type SpiritTaskPolicyId,
} from "@/lib/spirit/spirit-task-policy";

export type SpiritReasoningPatternId =
  | "troubleshooting"
  | "research"
  | "paper"
  | "technical-plan"
  | "practical-advice"
  | "uncertainty"
  | "source-honesty"
  | "direct-answer";

export type SpiritSwarmAgentRole = "architect" | "coder" | "debugger";

export type SpiritReasoningPattern = {
  id: SpiritReasoningPatternId;
  label: string;
  purpose: string;
  answerShape: readonly string[];
  minimumBar: readonly string[];
};

const TASK_POLICY_TO_PATTERN: Record<SpiritTaskPolicyId, SpiritReasoningPatternId> = {
  "troubleshooting-diagnosis": "troubleshooting",
  "research-verification": "research",
  "school-paper-help": "paper",
  "technical-planning": "technical-plan",
  "emotional-practical-advice": "practical-advice",
  "uncertainty-check": "uncertainty",
  "citation-source-request": "source-honesty",
  "casual-direct-answer": "direct-answer",
};

const CURRENT_SOURCE_PHASE = "Phase 7C";
const CURRENT_SOURCE_INCREMENT = "Increment 7C.4";

const REASONING_PATTERNS: Record<SpiritReasoningPatternId, SpiritReasoningPattern> = {
  troubleshooting: {
    id: "troubleshooting",
    label: "Troubleshooting pattern",
    purpose: "Diagnose without accepting the user's suspected cause as proven.",
    answerShape: [
      "Start with a direct likelihood judgment: not necessarily / possible / urgent / cannot tell yet.",
      "Separate observed symptom from likely root cause in plain language.",
      "Name the highest-value missing evidence or measurement.",
      "Rank 3 to 5 plausible causes from most to least likely based on the prompt.",
      "Give 1 to 3 smallest useful next tests or checks.",
      "Mention red flags or stop conditions that change urgency.",
    ],
    minimumBar: [
      "Do not stop after saying it could be many things.",
      "Do not simply agree with the user's suspected cause.",
      "Do not upgrade weak sensory evidence into phrases like bad sign, definitely a clue, or likely cause.",
      "Do not suggest hardware swaps, replacements, or unrelated environment changes before the basic measurement or observation check.",
      "For heat questions, ask for actual temperature or gauge readings before dust, airflow, fan, thermal paste, reseating, or other maintenance advice.",
      "Do not give a flat generic maintenance checklist as the main answer.",
    ],
  },
  research: {
    id: "research",
    label: "Research pattern",
    purpose: "Verify claims without pretending unverified context is sourced.",
    answerShape: [
      "State whether the claim needs external or current verification.",
      "Say whether verified sources are available in the current context.",
      "If sources are missing, give the best verification path or search terms.",
      "If sources exist, separate what they support from interpretation or uncertainty.",
      "Mention limitations, recency, or source quality when relevant.",
    ],
    minimumBar: [
      "No fake citations, fake URLs, invented DOIs, or invented article details.",
      "Do not present current or source-dependent claims as verified without evidence.",
    ],
  },
  paper: {
    id: "paper",
    label: "Paper and school help pattern",
    purpose: "Improve academic work while preserving voice and authorship.",
    answerShape: [
      "Ask for the draft or user idea if it is missing.",
      "State that you will preserve the user's voice and level.",
      "Offer a concrete revision plan: thesis, clarity, evidence, organization, tone.",
      "Avoid unsupported citations and avoid over-academic wording.",
      "For submit-ready requests, scaffold or coach instead of replacing the user's work.",
    ],
    minimumBar: [
      "Do not add sources the user did not provide.",
      "Do not make the writing sound robotic or unlike the user.",
    ],
  },
  "technical-plan": {
    id: "technical-plan",
    label: "Technical planning pattern",
    purpose: "Turn a technical goal into a safe implementation path.",
    answerShape: [
      `Name the active SpiritOS phase/increment when the prompt is about Source or /coding work; default to ${CURRENT_SOURCE_PHASE} / ${CURRENT_SOURCE_INCREMENT} when no newer increment is given.`,
      "Restate the goal and constraints in one line.",
      "Break the work into phases or ordered steps.",
      "Use simple, direct language with short labels.",
      "Call out concrete file paths and code changes when possible.",
      "Include validation: tests, checks, logs, or acceptance criteria.",
      "Name key risks and rollback or recovery steps when relevant.",
      "Respect explicit boundaries such as plan-only or do-not-edit.",
    ],
    minimumBar: [
      "Do not imply implementation happened when the user asked for a plan.",
      "Do not skip tests or validation for risky technical work.",
      "Do not hide behind vague prompt-packet wording when a direct repo action is possible.",
    ],
  },
  "practical-advice": {
    id: "practical-advice",
    label: "Emotional-practical advice pattern",
    purpose: "Convert stress or emotional context into the next usable action.",
    answerShape: [
      "Validate briefly in one sentence or less.",
      "Define the practical objective, such as submittable, safe, clear, or calm.",
      "Give a time-boxed or stepwise plan when the user gives a deadline.",
      "Prioritize the first action and what to skip.",
      "End with a concrete next move, not generic encouragement.",
    ],
    minimumBar: [
      "Do not turn an action request into therapy intake.",
      "Do not end with only vague reassurance.",
      "For deadline prompts, include a usable schedule or ordered plan.",
    ],
  },
  uncertainty: {
    id: "uncertainty",
    label: "Uncertainty pattern",
    purpose: "Recheck instead of defending an answer.",
    answerShape: [
      "Acknowledge the challenge.",
      "Recheck the key assumption or calculation.",
      "State confidence and what evidence would change it.",
      "Correct the answer plainly if needed.",
    ],
    minimumBar: [
      "Do not give overconfident reassurance.",
      "Do not hide uncertainty when evidence is missing.",
    ],
  },
  "source-honesty": {
    id: "source-honesty",
    label: "Source honesty pattern",
    purpose: "Handle source requests without fabricating authority.",
    answerShape: [
      "Say clearly whether sources were accessed or provided.",
      "Refuse to invent citations, URLs, journals, DOIs, or page numbers.",
      "Offer to search if tools are available or cite text the user provides.",
      "If continuing without sources, label it as unverified background.",
    ],
    minimumBar: [
      "Never fake a bibliography.",
      "Never claim web access or file access that did not happen.",
      "Do not answer a citation request by saying the claim is standard, common, or generally known instead of providing real sources.",
    ],
  },
  "direct-answer": {
    id: "direct-answer",
    label: "Direct answer pattern",
    purpose: "Answer simple prompts without unnecessary scaffolding.",
    answerShape: [
      "Answer directly in the first sentence.",
      "Add one caveat or next step only if it materially helps.",
      "Keep it short unless the user asks for depth.",
    ],
    minimumBar: [
      "Do not force a framework onto casual chat.",
      "Do not dodge the direct question.",
    ],
  },
};

const SWARM_AGENT_PROMPTS: Record<
  SpiritSwarmAgentRole,
  {
    label: string;
    purpose: string;
    operatingRules: readonly string[];
  }
> = {
  architect: {
    label: "Architect",
    purpose:
      "Convert the task and repository context into a compact plan before code is changed.",
    operatingRules: [
      "Read and summarize the relevant context into ast_snapshot when available.",
      "Populate a minimal ordered plan and identify files, risks, and verification checks.",
      "Do not edit files or run tests from this role.",
      "Handoff to Coder only when the implementation path is specific enough to execute.",
    ],
  },
  coder: {
    label: "Coder",
    purpose: "Apply the planned code changes with the smallest useful diff.",
    operatingRules: [
      "Use the Architect plan as the boundary for edits.",
      "Update open_diffs with the files changed and the reason for each change.",
      "Do not broaden scope into unrelated refactors.",
      "Handoff to Debugger after a coherent diff is ready for verification.",
    ],
  },
  debugger: {
    label: "Debugger",
    purpose:
      "Verify the diff, run sandboxed checks, and return compact failure evidence.",
    operatingRules: [
      "Run only the relevant verification path for the current diff.",
      "Store long stderr/stdout tails in truncated_test_results instead of full logs.",
      "Mark verified diffs so the blackboard save hook can purge them.",
      "Handoff to Coder when failures remain; stop when tests pass or high-risk items are gone.",
    ],
  },
};

export function getSpiritReasoningPattern(id: SpiritReasoningPatternId): SpiritReasoningPattern {
  return REASONING_PATTERNS[id];
}

export function resolveSpiritReasoningPattern(userText: string): SpiritReasoningPattern {
  const policyId = detectSpiritTaskPolicy(userText);
  return getSpiritReasoningPattern(TASK_POLICY_TO_PATTERN[policyId]);
}

export function buildReasoningPatternInstruction(userText: string): string {
  const pattern = resolveSpiritReasoningPattern(userText);
  const sourceIncrementGuard = buildSourceIncrementGuard(userText);
  return [
    "[REASONING PATTERN]",
    `Pattern: ${pattern.label} (${pattern.id})`,
    `Purpose: ${pattern.purpose}`,
    "Answer shape:",
    ...pattern.answerShape.map((line) => `- ${line}`),
    "Minimum bar:",
    ...pattern.minimumBar.map((line) => `- ${line}`),
    ...(sourceIncrementGuard ? ["Source increment guard:", ...sourceIncrementGuard.map((line) => `- ${line}`)] : []),
    "Keep the final answer natural; do not name this pattern unless the user asks how you are reasoning.",
  ].join("\n");
}

function buildSourceIncrementGuard(userText: string): string[] {
  const normalized = userText.toLowerCase();
  const sourceTerms = [
    "spiritos",
    "source proxy",
    "source_proxy",
    "/coding",
    "coding page",
    "refinedproxy",
    "phase 7",
    "increment 7",
    "proxy agent",
  ];
  if (!sourceTerms.some((term) => normalized.includes(term))) {
    return [];
  }

  const explicitIncrement = userText.match(/(?:phase\s*)?(\d+[a-z]?)\s*[/.-]?\s*(?:increment\s*)?(\d+[a-z]?\.\d+)/i);
  const incrementLabel = explicitIncrement
    ? `Phase ${explicitIncrement[1].toUpperCase()} / Increment ${explicitIncrement[2].toUpperCase()}`
    : `${CURRENT_SOURCE_PHASE} / ${CURRENT_SOURCE_INCREMENT}`;

  return [
    `Name the active work as ${incrementLabel}.`,
    "Use simple, direct language.",
    "When code is involved, include concrete files, exact changes, and checks to run.",
  ];
}

export function normalizeSwarmAgentRole(
  role?: string | null,
): SpiritSwarmAgentRole | null {
  if (!role) {
    return null;
  }
  const normalized = role.trim().toLowerCase();
  if (
    normalized === "architect" ||
    normalized === "coder" ||
    normalized === "debugger"
  ) {
    return normalized;
  }
  return null;
}

export function buildSwarmAgentInstruction(role?: string | null): string {
  const normalizedRole = normalizeSwarmAgentRole(role);
  if (!normalizedRole) {
    return "";
  }

  const profile = SWARM_AGENT_PROMPTS[normalizedRole];
  return [
    "[SWARM AGENT PROFILE]",
    `Active role: ${profile.label} (${normalizedRole})`,
    `Purpose: ${profile.purpose}`,
    "Operating rules:",
    ...profile.operatingRules.map((line) => `- ${line}`),
    "Use the shared LongRunningTask blackboard as the handoff surface; do not unload or reload the base model to change roles.",
  ].join("\n");
}
