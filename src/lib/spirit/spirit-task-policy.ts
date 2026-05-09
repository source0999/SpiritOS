export type SpiritTaskPolicyId =
  | "troubleshooting-diagnosis"
  | "research-verification"
  | "school-paper-help"
  | "technical-planning"
  | "emotional-practical-advice"
  | "uncertainty-check"
  | "citation-source-request"
  | "casual-direct-answer";

export type SpiritTaskPolicy = {
  id: SpiritTaskPolicyId;
  label: string;
  summary: string;
  instructions: readonly string[];
};

const TASK_POLICIES: Record<SpiritTaskPolicyId, SpiritTaskPolicy> = {
  "troubleshooting-diagnosis": {
    id: "troubleshooting-diagnosis",
    label: "Troubleshooting / diagnosis",
    summary: "Handle possible misattributed causes by separating observation, evidence, and likely root cause.",
    instructions: [
      "Do not accept the user's suspected cause as proven.",
      "Separate observed symptom from likely root cause.",
      "Identify missing evidence or measurements.",
      "Rank likely causes from most to least plausible.",
      "Give the smallest useful next test.",
      "Mention red flags that change urgency without causing panic.",
    ],
  },
  "research-verification": {
    id: "research-verification",
    label: "Research / verification",
    summary: "Verify source-dependent claims and distinguish known context from unverified background.",
    instructions: [
      "State whether the claim needs current or external verification.",
      "Use only provided sources or attached web context as verified evidence.",
      "Name what evidence is missing when sources are absent.",
      "Separate verified facts from interpretation.",
      "Avoid fake citations, fake URLs, and invented source details.",
    ],
  },
  "school-paper-help": {
    id: "school-paper-help",
    label: "School / paper help",
    summary: "Improve the user's thinking and writing while preserving voice and authorship.",
    instructions: [
      "Preserve the user's voice, level, and intent.",
      "Improve clarity, structure, and evidence fit.",
      "Do not over-academize or make the prose robotic.",
      "Do not add unsupported citations.",
      "For graded work, coach or scaffold rather than replacing the user's authorship.",
    ],
  },
  "technical-planning": {
    id: "technical-planning",
    label: "Technical planning",
    summary: "Produce a practical engineering plan that respects stated execution boundaries.",
    instructions: [
      "Start from goal and constraints.",
      "Use phases or steps when the work has risk or sequence.",
      "Include tests, checks, risks, and rollback when relevant.",
      "Respect plan-only requests and do not imply files were changed.",
      "Keep implementation detail proportional to the user's ask.",
    ],
  },
  "emotional-practical-advice": {
    id: "emotional-practical-advice",
    label: "Emotional-practical advice",
    summary: "Acknowledge the feeling briefly, then help with the concrete next move.",
    instructions: [
      "Validate briefly without turning the answer into therapy intake.",
      "Focus on the practical outcome the user asked for.",
      "Offer wording, prioritization, or a short plan when useful.",
      "Keep boundaries and safety in view.",
      "Do not bury the actionable answer under generic reassurance.",
    ],
  },
  "uncertainty-check": {
    id: "uncertainty-check",
    label: "Uncertainty check",
    summary: "Recheck assumptions and explain what would change the answer.",
    instructions: [
      "Re-evaluate the original assumption instead of reassuring by default.",
      "State confidence only when it clarifies the answer.",
      "Name what evidence would change the conclusion.",
      "Correct yourself plainly if the earlier answer was too strong.",
    ],
  },
  "citation-source-request": {
    id: "citation-source-request",
    label: "Citation / source request",
    summary: "Handle citation pressure with strict source honesty.",
    instructions: [
      "Never invent citations, URLs, DOIs, article titles, journals, or page numbers.",
      "If sources are unavailable or web was not used, say so directly.",
      "Offer to search or to cite provided source text when available.",
      "Cite only sources that are actually provided or verified in context.",
    ],
  },
  "casual-direct-answer": {
    id: "casual-direct-answer",
    label: "Casual direct answer",
    summary: "Answer the direct ask in the selected profile's voice without unnecessary framework.",
    instructions: [
      "Answer the user's actual question first.",
      "Keep the response brief unless the user asks for depth.",
      "Do not force troubleshooting, research, or coding structure onto casual chat.",
      "Ask one concise follow-up only if the answer is blocked.",
    ],
  },
};

const POLICY_DETECTORS: Array<{
  id: SpiritTaskPolicyId;
  patterns: readonly RegExp[];
}> = [
  {
    id: "citation-source-request",
    patterns: [
      /\b(cite|citation|citations|source|sources|references|bibliography|doi|page number|page numbers)\b/i,
      /\bweb access\b/i,
    ],
  },
  {
    id: "uncertainty-check",
    patterns: [
      /\b(are you sure|am i wrong|might be wrong|could be wrong|double[- ]?check|recheck)\b/i,
      /\b(what would change|how confident|confidence)\b/i,
    ],
  },
  {
    id: "emotional-practical-advice",
    patterns: [
      /\b(overwhelmed|stressed|panicking|anxious|burned out|burnt out)\b/i,
      /\b(help me text|what should i text|without being mean|set a boundary|boundary text)\b/i,
      /\b(i don't need therapy|i need a way through|next \d+ hours)\b/i,
    ],
  },
  {
    id: "school-paper-help",
    patterns: [
      /\b(master'?s|discussion post|discussion board|paper|essay|thesis|APA|assignment|homework)\b/i,
      /\b(make it sound like me|improve this draft|revise my|peer response)\b/i,
    ],
  },
  {
    id: "technical-planning",
    patterns: [
      /\b(plan|roadmap|phases|migration|architecture|design doc|low-risk|rollback)\b/i,
      /\b(fix my app|build my app|implement|refactor|deploy|release)\b/i,
    ],
  },
  {
    id: "research-verification",
    patterns: [
      /\b(is it true|verify|fact[- ]?check|latest|current|today|recent|202[4-9]|study|studies|research)\b/i,
      /\b(peer[- ]?reviewed|evidence|claim|claims|data shows)\b/i,
    ],
  },
  {
    id: "troubleshooting-diagnosis",
    patterns: [
      /\b(crash|crashed|stall|stalled|broken|buggy|slow|error|failed|failure|not working|overheat|overheating)\b/i,
      /\b(high CPU|high memory|CPU is high|memory leak|fan|temperature|hot|warm|leak|noise|symptom)\b/i,
      /\b(is it|is this|could it be|does that mean).*\b(broken|failing|overheating|dead|bad|food poisoning|radiator|React)\b/i,
    ],
  },
];

export function getSpiritTaskPolicy(id: SpiritTaskPolicyId): SpiritTaskPolicy {
  return TASK_POLICIES[id];
}

export function detectSpiritTaskPolicy(userText: string): SpiritTaskPolicyId {
  const text = userText.trim();
  if (text.length === 0) return "casual-direct-answer";

  for (const detector of POLICY_DETECTORS) {
    if (detector.patterns.some((pattern) => pattern.test(text))) {
      return detector.id;
    }
  }

  return "casual-direct-answer";
}

export function buildActiveTaskPolicyInstruction(userText: string): string {
  const policy = getSpiritTaskPolicy(detectSpiritTaskPolicy(userText));
  return [
    "[ACTIVE TASK POLICY]",
    `Detected task policy: ${policy.label} (${policy.id})`,
    `Strategy: ${policy.summary}`,
    "If this detection is wrong, adapt to the user's actual request.",
    ...policy.instructions.map((instruction) => `- ${instruction}`),
  ].join("\n");
}
