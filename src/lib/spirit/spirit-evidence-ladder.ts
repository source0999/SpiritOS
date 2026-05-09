import {
  detectSpiritTaskPolicy,
  type SpiritTaskPolicyId,
} from "@/lib/spirit/spirit-task-policy";

export type SpiritEvidenceStrength = "direct" | "strong" | "medium" | "weak" | "missing";

export type SpiritEvidenceSignal = {
  id: string;
  strength: SpiritEvidenceStrength;
  label: string;
  instruction: string;
};

export type SpiritEvidenceAssessment = {
  taskPolicyId: SpiritTaskPolicyId;
  signals: readonly SpiritEvidenceSignal[];
  leadGuards: readonly string[];
  confidenceGuidance: readonly string[];
};

const DEFAULT_SIGNALS: readonly SpiritEvidenceSignal[] = [
  {
    id: "user-observation",
    strength: "medium",
    label: "User observation",
    instruction: "Treat the user's report as important evidence, but separate what they observed from what they concluded.",
  },
  {
    id: "missing-measurement",
    strength: "missing",
    label: "Missing measurement",
    instruction: "If a measurement, log, source, timestamp, screenshot, error text, or direct artifact would decide the issue, say so.",
  },
];

const TROUBLESHOOTING_SIGNALS: readonly SpiritEvidenceSignal[] = [
  {
    id: "subjective-symptom",
    strength: "weak",
    label: "Subjective symptom or sensory clue",
    instruction:
      "Treat touch, feels hot, seems slow, sounds weird, or similar sensory impressions as weak clues until backed by measurements, logs, gauges, or repeatable behavior. Do not call a weak clue a bad sign, a definite clue, or strong evidence by itself.",
  },
  {
    id: "instrumented-measurement",
    strength: "direct",
    label: "Instrumented measurement",
    instruction:
      "Prefer actual temperatures, gauges, error codes, logs, profiler output, warning lights, repro steps, or direct measurements over guesses.",
  },
  {
    id: "competing-causes",
    strength: "medium",
    label: "Competing causes",
    instruction:
      "Rank competing explanations before treating the user's suspected cause as likely. Avoid phrasing like 'that's a common cause' when the prompt only supports 'possible, but not proven.'",
  },
];

const SOURCE_SIGNALS: readonly SpiritEvidenceSignal[] = [
  {
    id: "verified-source-context",
    strength: "direct",
    label: "Verified source context",
    instruction:
      "Only citations, URLs, files, or web results actually provided in context count as verified source evidence.",
  },
  {
    id: "model-memory",
    strength: "weak",
    label: "Model memory",
    instruction:
      "Treat memory-only facts as unverified background when the user asks for citations, current facts, or source-dependent claims. Do not substitute 'this is standard/common knowledge' for a citation.",
  },
];

const HIGH_STAKES_SIGNALS: readonly SpiritEvidenceSignal[] = [
  {
    id: "safety-sensitive",
    strength: "weak",
    label: "Safety-sensitive inference",
    instruction:
      "For medical, legal, financial, medication, vehicle safety, electrical, smoke/fire, or self-harm-adjacent topics, avoid false certainty and route toward qualified help or safety-first checks when risk is plausible.",
  },
];

const TASK_EXTRA_SIGNALS: Partial<Record<SpiritTaskPolicyId, readonly SpiritEvidenceSignal[]>> = {
  "troubleshooting-diagnosis": TROUBLESHOOTING_SIGNALS,
  "research-verification": SOURCE_SIGNALS,
  "citation-source-request": SOURCE_SIGNALS,
  "uncertainty-check": SOURCE_SIGNALS,
};

function hasHighStakesLanguage(userText: string): boolean {
  return /\b(insulin|medication|medicine|dose|doctor|ER|emergency|chest pain|smoke|burning smell|fire|sparking|brakes|stalled|highway|legal|lawsuit|tax|invest|self[- ]?harm|suicide)\b/i.test(
    userText,
  );
}

function hasWeakSensoryTroubleshootingClue(userText: string): boolean {
  return /\b(warm|hot|feels hot|touch|slow|buggy|sounds weird|noise|stalled|crashed|high CPU|CPU is high)\b/i.test(
    userText,
  );
}

function hasSuspectedCauseQuestion(userText: string): boolean {
  return /\b(is it|is this|could it be|does that mean|is .* broken|is .* bad|is .* overheating|is .* the)\b/i.test(
    userText,
  );
}

function hasHeatOrTemperatureClue(userText: string): boolean {
  return /\b(warm|hot|heat|overheat|overheating|temperature|temp|thermal|cooling)\b/i.test(
    userText,
  );
}

function buildLeadGuards(userText: string, taskPolicyId: SpiritTaskPolicyId): string[] {
  const guards: string[] = [];
  if (
    taskPolicyId === "troubleshooting-diagnosis" &&
    hasWeakSensoryTroubleshootingClue(userText) &&
    hasSuspectedCauseQuestion(userText)
  ) {
    guards.push(
      "Weak-clue troubleshooting guard: open by downgrading the suspected cause, e.g. 'possible, but not proven from that alone' or 'not enough evidence to conclude that yet.'",
      "Do not open with 'that sounds like a bad sign,' 'definitely a clue,' or a similar alarm phrase unless the prompt includes direct danger evidence such as smoke, fire, repeated shutdowns, severe warning lights, or visible damage.",
      "Before suggesting swaps, replacements, outlets, or maintenance, ask for or recommend the decisive measurement/log/gauge/profiler check.",
    );
    if (hasHeatOrTemperatureClue(userText)) {
      guards.push(
        "Heat-specific guard: if the only heat evidence is touch, prioritize actual sensor temperature or gauge readings before dust, airflow, fan, thermal paste, reseating, or other maintenance advice. Maintenance belongs after measured high temps, failed fans, artifacts, repeated thermal shutdowns, smoke, burning smell, or visible damage.",
      );
    }
  }
  if (taskPolicyId === "citation-source-request" || taskPolicyId === "research-verification") {
    guards.push(
      "Source guard: if no verified source context is attached, do not reassure with 'standard,' 'common,' or 'generally known'; say sources are missing and offer a verification path.",
    );
  }
  return guards;
}

export function assessSpiritEvidence(userText: string): SpiritEvidenceAssessment {
  const taskPolicyId = detectSpiritTaskPolicy(userText);
  const signals = [
    ...DEFAULT_SIGNALS,
    ...(TASK_EXTRA_SIGNALS[taskPolicyId] ?? []),
    ...(hasHighStakesLanguage(userText) ? HIGH_STAKES_SIGNALS : []),
  ];

  return {
    taskPolicyId,
    signals,
    leadGuards: buildLeadGuards(userText, taskPolicyId),
    confidenceGuidance: [
      "High confidence requires direct evidence such as source text, logs, measurements, files, or verified tool/web results.",
      "Medium confidence is appropriate for strong reasoning with one important missing measurement or artifact.",
      "Low confidence is appropriate when the answer depends on a hunch, sensory impression, memory-only fact, or missing source.",
      "If evidence is weak but the stakes are high, lead with caution and the safest next verification step.",
    ],
  };
}

export function buildEvidenceLadderInstruction(userText: string): string {
  const assessment = assessSpiritEvidence(userText);
  return [
    "[EVIDENCE LADDER]",
    `Task policy: ${assessment.taskPolicyId}`,
    ...(assessment.leadGuards.length > 0
      ? ["Highest-priority calibration:", ...assessment.leadGuards.map((line) => `- ${line}`)]
      : []),
    "Evidence weighting:",
    ...assessment.signals.map(
      (signal) => `- ${signal.label} (${signal.strength}): ${signal.instruction}`,
    ),
    "Confidence calibration:",
    ...assessment.confidenceGuidance.map((line) => `- ${line}`),
    "Use the ladder to decide how strongly to state conclusions. Do not label every answer with confidence unless it materially helps.",
  ].join("\n");
}
