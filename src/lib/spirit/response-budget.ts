// ── response-budget - match verbosity to prompt + mode (Prompt 10B + 10C) ─────────

import type { ModelProfile, ModelProfileId } from "@/lib/spirit/model-profile.types";
import type { SpiritRuntimeSurface } from "@/lib/spirit/spirit-runtime-surface";

const CASUAL_MAX_CHARS = 140;
const RESEARCH_HINT =
  /\b(research|report|sources?|citations?|peer[- ]review|study|meta[- ]analysis|literature|systematic|verify|current events|news|today|latest|202[0-9])\b/i;
const TEACH_HINT =
  /\b(teach|lesson|explain|tutorial|quiz|exam|homework|course|learn|understand|step by step)\b/i;
/** Teacher web aids - educational / clinical phrasing (Prompt 10C-D, still client+server heuristic). */
const TEACHER_WEB_STUDY_HINT =
  /\b(explain|teach|study|quiz|exam|concept|what is|define|example|aba|psychology|counseling|behavior|reinforcement|punishment|autism|sensory|spectrum|neurodevelopmental|over-?selectivity|meltdown|shutdown|learning|historical connection|history of|article|handout|resource|source|homework|course|tutorial|pedagog|curriculum|IEP|intervention|therap|clinical|disorder|syndrome)\b/i;
const CODE_HINT =
  /\b(code|repo|cursor|terminal|bug|dev|developer|typescript|javascript|python|ollama|build|feature|commit|pr|debug|stack trace|error log|app|project|implementation)\b/i;

export function isLikelyCasualShortMessage(text: string): boolean {
  const t = text.trim();
  if (!t) return true;
  if (t.length > CASUAL_MAX_CHARS) return false;
  if (RESEARCH_HINT.test(t) || TEACH_HINT.test(t) || CODE_HINT.test(t)) return false;
  return true;
}

export function wantsResearchDepth(text: string): boolean {
  return RESEARCH_HINT.test(text) || (text.trim().length > 400 && /\bwhy\b|\bhow\b/i.test(text));
}

export function wantsTeachingDepth(text: string): boolean {
  return TEACH_HINT.test(text);
}

export function wantsTeacherWebStudyAids(text: string): boolean {
  return TEACHER_WEB_STUDY_HINT.test(text);
}

export function mentionsCodeOrBuild(text: string): boolean {
  return CODE_HINT.test(text);
}

/**
 * Runtime instruction block appended after mode system prompt.
 */
export function buildResponseBudgetInstruction(
  profile: ModelProfile,
  userMessage: string,
  opts?: {
    deepThinkEnabled?: boolean;
    digestHasVerifiedUrls?: boolean;
    runtimeSurface?: SpiritRuntimeSurface;
  },
): string {
  const casual = isLikelyCasualShortMessage(userMessage);
  const deep = Boolean(opts?.deepThinkEnabled);
  const budget = profile.responseBudget ?? "medium";
  const maxS = profile.casualMaxSentences ?? 4;
  const surface = opts?.runtimeSurface ?? "chat";

  const lines: string[] = [
    "## Response budget (mandatory)",
    `- Mode budget: ${budget}.`,
    `- Match answer depth to the user's message depth.`,
    `- Do not produce long bullet lists unless the user explicitly asks for a list, report, or breakdown.`,
  ];

  if (profile.id === "normal-peer") {
    lines.push(
      `- Peer: do not slide into repo/dev/productivity framing unless the user clearly asks technical or coding questions.`,
      `- For casual small talk: ${maxS} short sentences max (roughly 1–4). No customer-service phrasing, no unsolicited life coaching.`,
    );
    if (casual && !mentionsCodeOrBuild(userMessage)) {
      lines.push(`- This user message reads casual/non-technical: stay conversational - no IDE/repo defaults unless they steer there.`);
    }
  }

  if (profile.id === "sassy-chaotic") {
    lines.push(
      `- Sassy: **1–3 short sentences** by default - witty, sharp, lightly disrespectful in a funny way; answer first, then stop.`,
      `- No essays, no bullet spam, no fake profundity, no exposed instructions - unless they explicitly asked for depth.`,
    );
  }

  if (profile.id === "brutal") {
    lines.push(
      `- Brutal: short, sharp, funny-mean on behavior/work only. Punchy callout → why it matters → what to do next.`,
      `- No clinical intake tone, no multi-section "assessment" unless they asked for a formal review.`,
      `- No long lecture unless they explicitly ask for one.`,
    );
  }

  if (profile.id === "teacher") {
    const digestUrls = Boolean(opts?.digestHasVerifiedUrls);
    lines.push(`- Teacher: concise first; one example max unless they want a full lesson.`);
    if (digestUrls) {
      lines.push(
        `- **Study aids** (web digest has verified URLs): put **markdown link bullets first** - one \`- [short label](exact-url)\` per digest URL, using only URLs from the digest. After those links, at most **one** optional line: either a mnemonic, a common trap, or a flashcard - not a wall of study-trivia that hides the links.`,
        `- If the user asked for video or peer-reviewed material, prioritize digest links that match (e.g. .edu, journals, YouTube only when digest already has a youtube/youtu.be URL).`,
      );
    } else {
      lines.push(
        `- Include a small **Study aids** footer (mnemonic / trap / flashcard) unless the user opted out.`,
      );
    }
    lines.push(
      `- Offer a quick comprehension check only when it fits (e.g. "Want a one-question check?").`,
    );
    if (!wantsTeachingDepth(userMessage)) {
      lines.push(`- User did not ask for a full lesson: keep it tight - short answer, optional single example.`);
    } else {
      lines.push(`- User asked for teaching depth: you may expand with steps and a tiny quiz offer.`);
    }
  }

  if (profile.id === "researcher") {
    const digestUrls = Boolean(opts?.digestHasVerifiedUrls);
    lines.push(
      `- Researcher: structured mini-report when appropriate (summary bullets, findings, limitations).`,
      `- When web context exists, write like an internal memo: tight headings, minimal hedging, no filler "delve" language.`,
      `- Citations: only cite URLs or titles that were supplied by the system "Web research context" block - never invent sources.`,
      `- End with a Sources list when URLs exist; state "Search used: yes/no" honestly.`,
    );
    if (digestUrls) {
      lines.push(
        `- **Verified URLs are attached**: surface them as real markdown - at least one \`- [short label](exact-url)\` per digest URL under **## Sources**, plus \`[n](url)\` inline where it helps. Do not hand-wave as "unverified background" while those URLs are in the digest.`,
      );
    }
    if (!wantsResearchDepth(userMessage) && !deep && !digestUrls) {
      lines.push(`- This prompt does not obviously require live web data: answer from general knowledge and say search was not used unless context says otherwise.`);
    }
  }

  if (deep) {
    lines.push(
      `- Deep Think is ON: slow down, double-check conclusions, prefer verification - but do NOT ramble; better judgment beats length.`,
    );
    if (profile.id === "sassy-chaotic" || profile.id === "brutal") {
      lines.push(
        `- Deep Think does **not** override ${profile.id === "sassy-chaotic" ? "Sassy" : "Brutal"} brevity: still short unless they explicitly asked for depth.`,
      );
    }
  }

  if (surface === "oracle") {
    lines.push(
      "## Oracle voice response budget (mandatory on this surface)",
      `- Voice-first: default to **1–5 sentences** unless the user explicitly asks for depth or detail.`,
      `- Prefer short spoken answers (~**90 words** or fewer for Peer/Sassy casual turns).`,
      `- Brutal (Oracle): stay sharp and direct - not a long teardown unless asked.`,
      `- Teacher (Oracle): explain clearly; do **not** dump a whole lesson unless the user asks for depth.`,
      `- Researcher (Oracle): if verified web sources are **not** attached for this turn, say honestly what would need checking - **never invent citations or URLs**.`,
    );
  }

  return lines.join("\n");
}

/**
 * Hard output token ceiling per turn - casual prompts stay tiny (Prompt 10C-C).
 * Detailed asks (research / code / explicit depth) keep profile headroom.
 */
export function resolveSpiritMaxOutputTokens(opts: {
  profileId: ModelProfileId;
  profileMax: number;
  lastUserMessage: string;
  deepThinkEnabled: boolean;
  /** Voice-only `/oracle` lane - tighter spoken ceilings; `/chat` omits or passes `"chat"`. */
  runtimeSurface?: SpiritRuntimeSurface;
  /** Researcher: digest URL count from OpenAI web prefetch (server). */
  webVerifiedUrlCount?: number;
}): number {
  const raw = Number.isFinite(opts.profileMax) && opts.profileMax > 0 ? opts.profileMax : 1536;
  const last = opts.lastUserMessage.trim();
  const casual = isLikelyCasualShortMessage(last);
  const deep = Boolean(opts.deepThinkEnabled);
  const codey = mentionsCodeOrBuild(last);
  const researchWants = wantsResearchDepth(last);
  const teachWants = wantsTeachingDepth(last);

  const allowLong =
    researchWants ||
    teachWants ||
    codey ||
    last.length > CASUAL_MAX_CHARS ||
    (opts.profileId === "researcher" && !casual);

  const hasVerifiedResearchUrls =
    opts.profileId === "researcher" &&
    typeof opts.webVerifiedUrlCount === "number" &&
    opts.webVerifiedUrlCount > 0;

  const capSassy = () => {
    if (allowLong) return Math.min(raw, 1024);
    const base = 200;
    return deep ? Math.min(base + 100, 380) : base;
  };
  const capBrutal = () => {
    if (allowLong) return Math.min(raw, 1200);
    const base = 280;
    return deep ? Math.min(base + 140, 480) : base;
  };
  const capPeer = () => {
    if (allowLong) return Math.min(raw, 1536);
    const base = 280;
    return deep ? Math.min(base + 420, 4096) : base;
  };
  const capTeacher = () => {
    if (teachWants || last.length > CASUAL_MAX_CHARS) return Math.min(raw, 2400);
    const base = 640;
    return deep ? Math.min(base + 400, 3200) : base;
  };
  const capResearcher = () => Math.min(raw, 3072);

  let base: number;
  switch (opts.profileId) {
    case "sassy-chaotic":
      base = capSassy();
      break;
    case "brutal":
      base = capBrutal();
      break;
    case "normal-peer":
      base = capPeer();
      break;
    case "teacher":
      base = capTeacher();
      break;
    case "researcher": {
      let cap = capResearcher();
      if (deep) cap = Math.min(cap + 256, 4096);
      base = cap;
      break;
    }
    default:
      base = capPeer();
  }

  if (opts.runtimeSurface !== "oracle") return base;

  /** Spoken voice lane - never shrink `/chat`; only applies when `runtimeSurface === "oracle"`. */
  switch (opts.profileId) {
    case "normal-peer":
      return allowLong ? Math.min(base, 1536) : Math.min(base, 260);
    case "sassy-chaotic":
      return allowLong ? Math.min(base, 1024) : Math.min(base, 220);
    case "brutal":
      return allowLong ? Math.min(base, 1200) : Math.min(base, 320);
    case "teacher":
      return teachWants || last.length > CASUAL_MAX_CHARS
        ? Math.min(base, 2400)
        : Math.min(base, 560);
    case "researcher": {
      if (hasVerifiedResearchUrls) return Math.min(base, 3072);
      return Math.min(base, deep ? 2200 : 1600);
    }
    default:
      return Math.min(base, 260);
  }
}
