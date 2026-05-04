// ── buildModelRuntime — profile → prompt + sampling (client + server safe) ─────
import { getModelProfile } from "@/lib/spirit/model-profiles";
import type { ModelProfile } from "@/lib/spirit/model-profile.types";
import {
  buildResponseBudgetInstruction,
  resolveSpiritMaxOutputTokens,
} from "@/lib/spirit/response-budget";
import { buildFinalAnswerContract } from "@/lib/spirit/spirit-answer-contract";

export type ModelRuntime = {
  profile: ModelProfile;
  systemPrompt: string;
  temperature: number;
  maxOutputTokens?: number;
  numCtx?: number;
};

export type BuildModelRuntimeOptions = {
  /** Trimmed, server-validated slice appended after mode system prompt */
  personalizationSummary?: string | null;
  /** Last user text (server) — drives response budget helper */
  lastUserMessage?: string | null;
  deepThinkEnabled?: boolean;
  /** OpenAI web digest or failure banner */
  researchWebContext?: string | null;
  /** Optional user-approved research plan (Stage 5 stub) */
  researchPlanSummary?: string | null;
  /** OpenAI web prefetch: verified http(s) URL count (Researcher + Teacher — aligns digest + link-first budget). */
  webVerifiedUrlCount?: number;
};

export function buildModelRuntime(
  profileId?: string | null,
  opts?: BuildModelRuntimeOptions,
): ModelRuntime {
  const profile = getModelProfile(profileId);
  const extra = opts?.personalizationSummary?.trim();
  const lastUser = opts?.lastUserMessage?.trim() ?? "";
  const deep = Boolean(opts?.deepThinkEnabled);
  const research = opts?.researchWebContext?.trim();
  const plan = opts?.researchPlanSummary?.trim();
  const digestHasVerifiedUrls =
    typeof opts?.webVerifiedUrlCount === "number"
      ? opts.webVerifiedUrlCount > 0
      : Boolean(research && /Verified URL sources \(\d+\):/m.test(research));

  const budget = buildResponseBudgetInstruction(profile, lastUser || " ", {
    deepThinkEnabled: deep,
    digestHasVerifiedUrls,
  });

  const contract = buildFinalAnswerContract(profile.id, deep);

  const deepBlock = deep
    ? `

## Deep Think Lite (user enabled)
- Take a breath: check assumptions, edge cases, and whether you are answering what was actually asked.
- Prefer correctness and judgment over length — especially in Peer/Sassy/Brutal modes (no essay mode).
- Researcher: verify claims against provided web context when present; Teacher: optional one-line comprehension check.
`
    : "";

  const researchBlock =
    research && research.length > 0
      ? `

${research}
`
      : "";

  const planBlock =
    plan && plan.length > 0
      ? `

${plan}
`
      : "";

  const prefsBlock =
    extra && extra.length > 0
      ? `

---
User style preferences (local, editable by the user; respect when safe, do not overfit or leak as facts about third parties):
${extra}`
    : "";

  const systemPrompt = `${profile.systemPrompt}

${budget}${deepBlock}${researchBlock}${planBlock}${prefsBlock}

${contract}`.trim();

  const profileMax =
    typeof profile.maxOutputTokens === "number" && Number.isFinite(profile.maxOutputTokens)
      ? profile.maxOutputTokens
      : 1536;
  const maxOut = resolveSpiritMaxOutputTokens({
    profileId: profile.id,
    profileMax,
    lastUserMessage: lastUser || " ",
    deepThinkEnabled: deep,
  });

  return {
    profile,
    systemPrompt,
    temperature: profile.temperature,
    maxOutputTokens: maxOut,
    numCtx: profile.numCtx,
  };
}
