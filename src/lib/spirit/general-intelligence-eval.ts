export type GeneralIntelligenceEvalCategory =
  | "troubleshooting-diagnosis"
  | "research-verification"
  | "school-paper-help"
  | "technical-planning"
  | "emotional-practical-advice"
  | "uncertainty-honesty"
  | "source-citation-honesty"
  | "direct-answer-vs-generic-checklist";

export type GeneralIntelligenceTrait = {
  id: string;
  label: string;
  patterns: readonly RegExp[];
  matchMode?: "any" | "all";
};

export type GeneralIntelligenceMinimumPassingCriteria = {
  minExpectedTraits: number;
  maxForbiddenTraits: number;
  requiredExpectedTraitIds?: readonly string[];
  notes: string;
};

export type GeneralIntelligenceEvalCase = {
  id: string;
  category: GeneralIntelligenceEvalCategory;
  userPrompt: string;
  weakAnswerPattern?: readonly RegExp[];
  weakFailureMode?: string;
  expectedTraits: readonly GeneralIntelligenceTrait[];
  forbiddenTraits: readonly GeneralIntelligenceTrait[];
  needsWeb: boolean;
  needsFiles: boolean;
  idealFirstMove: string;
  minimumPassingCriteria: GeneralIntelligenceMinimumPassingCriteria;
};

export type GeneralIntelligenceEvalScore = {
  pass: boolean;
  expectedTraitCount: number;
  forbiddenTraitCount: number;
  missingTraitCount: number;
  score: number;
};

export type GeneralIntelligenceEvalReport = GeneralIntelligenceEvalScore & {
  evalCaseId: string;
  category: GeneralIntelligenceEvalCategory;
  matchedExpectedTraits: GeneralIntelligenceTrait[];
  matchedForbiddenTraits: GeneralIntelligenceTrait[];
  missingTraits: GeneralIntelligenceTrait[];
  criteria: GeneralIntelligenceMinimumPassingCriteria;
};

function traitMatches(answer: string, trait: GeneralIntelligenceTrait): boolean {
  const matches = trait.patterns.map((pattern) => pattern.test(answer));
  if (trait.matchMode === "all") return matches.every(Boolean);
  return matches.some(Boolean);
}

export function detectExpectedTraits(
  answer: string,
  evalCase: GeneralIntelligenceEvalCase,
): GeneralIntelligenceTrait[] {
  return evalCase.expectedTraits.filter((trait) => traitMatches(answer, trait));
}

export function detectForbiddenTraits(
  answer: string,
  evalCase: GeneralIntelligenceEvalCase,
): GeneralIntelligenceTrait[] {
  return evalCase.forbiddenTraits.filter((trait) => traitMatches(answer, trait));
}

function requiredTraitsMet(
  matchedExpectedTraits: readonly GeneralIntelligenceTrait[],
  requiredExpectedTraitIds: readonly string[] | undefined,
): boolean {
  if (!requiredExpectedTraitIds || requiredExpectedTraitIds.length === 0) return true;
  const matchedIds = new Set(matchedExpectedTraits.map((trait) => trait.id));
  return requiredExpectedTraitIds.every((id) => matchedIds.has(id));
}

export function scoreAnswerAgainstTraits(
  answer: string,
  evalCase: GeneralIntelligenceEvalCase,
): GeneralIntelligenceEvalScore {
  const matchedExpectedTraits = detectExpectedTraits(answer, evalCase);
  const matchedForbiddenTraits = detectForbiddenTraits(answer, evalCase);
  const missingTraitCount = evalCase.expectedTraits.length - matchedExpectedTraits.length;
  const criteria = evalCase.minimumPassingCriteria;
  const pass =
    matchedExpectedTraits.length >= criteria.minExpectedTraits &&
    matchedForbiddenTraits.length <= criteria.maxForbiddenTraits &&
    requiredTraitsMet(matchedExpectedTraits, criteria.requiredExpectedTraitIds);

  return {
    pass,
    expectedTraitCount: matchedExpectedTraits.length,
    forbiddenTraitCount: matchedForbiddenTraits.length,
    missingTraitCount,
    score: matchedExpectedTraits.length - matchedForbiddenTraits.length,
  };
}

export function createEvalReport(
  answer: string,
  evalCase: GeneralIntelligenceEvalCase,
): GeneralIntelligenceEvalReport {
  const matchedExpectedTraits = detectExpectedTraits(answer, evalCase);
  const matchedForbiddenTraits = detectForbiddenTraits(answer, evalCase);
  const matchedIds = new Set(matchedExpectedTraits.map((trait) => trait.id));
  const missingTraits = evalCase.expectedTraits.filter((trait) => !matchedIds.has(trait.id));
  const score = scoreAnswerAgainstTraits(answer, evalCase);

  return {
    ...score,
    evalCaseId: evalCase.id,
    category: evalCase.category,
    matchedExpectedTraits,
    matchedForbiddenTraits,
    missingTraits,
    criteria: evalCase.minimumPassingCriteria,
  };
}
