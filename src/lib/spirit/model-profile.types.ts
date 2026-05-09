// ── Model profile ids - Prompt 7 runtime layer (no model id hardcoding) ─────────

export type ModelProfileId =
  | "normal-peer"
  | "researcher"
  | "teacher"
  | "brutal"
  | "sassy-chaotic";

export type ModelProfileBadgeTone = "neutral" | "cyan" | "amber" | "rose" | "violet";

export type ResponseBudget = "short" | "medium" | "report";

export type ModelProfile = {
  id: ModelProfileId;
  /** Longer chrome / docs label */
  label: string;
  /** Dropdown + compact UI */
  shortLabel: string;
  /** Badge line: Mode: X - one-liner hint */
  responseStyleSummary: string;
  description: string;
  systemPrompt: string;
  temperature: number;
  maxOutputTokens?: number;
  /** Prompt 10B - guides Hermes verbosity + budget helper */
  responseBudget?: ResponseBudget;
  casualMaxSentences?: number;
  ttsDefaultStrategy?: "summary" | "full-chunks";
  thinkingDefault?: boolean;
  /** Hint for Ollama / local providers - wire in Prompt 8+ when options API is stable. */
  numCtx?: number;
  searchEnabled?: boolean;
  /** Prompt 10B - Researcher wants search when it lands */
  searchPreferred?: boolean;
  requiresCitationStyle?: boolean;
  reportStyle?: boolean;
  learningMode?: boolean;
  directnessLevel?: 1 | 2 | 3 | 4 | 5;
  sassLevel?: 0 | 1 | 2 | 3 | 4 | 5;
  deepThinkDefault?: boolean;
  slowGenerationDefault?: boolean;
  badgeTone?: ModelProfileBadgeTone;
};

export const DEFAULT_MODEL_PROFILE_ID: ModelProfileId = "normal-peer";
