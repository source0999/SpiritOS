// ── assistant-output-sanitizer — kill leaked CoT / mode contracts in user-visible text ─
// > Models sometimes echo training junk. Strip it before render, copy, TTS, or Dexie.

const TAG_PAIRS: Array<[RegExp, string]> = [
  [/<redacted_thinking[^>]*>[\s\S]*?<\/redacted_thinking>/gi, ""],
  [/<thinking[^>]*>[\s\S]*?<\/thinking>/gi, ""],
  [/<chain_of_thought[^>]*>[\s\S]*?<\/chain_of_thought>/gi, ""],
  [/<system[^>]*>[\s\S]*?<\/system>/gi, ""],
  [/<developer[^>]*>[\s\S]*?<\/developer>/gi, ""],
];

/** Line starts that almost always mean leaked instructions (not user content). */
const LEAK_LINE_STARTS = [
  /^respond in ["']sassy mode["']\s*only\b/i,
  /^respond in ["']sassy mode["']/i,
  /^I'm here to help with coding questions\b/i,
  /^respond in ["']brutal mode["']/i,
  /^keep sentences short\b/i,
  /^no hidden chain[- ]of[- ]thought\b/i,
  /^technical stuff should still be correct\b/i,
  /^answer depth\s*=\s*user'?s message depth\b/i,
  /^mode contract:\s*$/i,
  /^system prompt:\s*$/i,
  /^developer instruction:\s*$/i,
  /^hidden instruction:\s*$/i,
];

function stripTaggedBlocks(text: string): string {
  let t = text;
  for (const [re, rep] of TAG_PAIRS) {
    t = t.replace(re, rep);
  }
  return t;
}

function stripLeakedInstructionLines(text: string): string {
  const lines = text.split("\n");
  const out: string[] = [];
  let skippingLeakRun = false;

  for (const line of lines) {
    const trimmed = line.trim();
    const isLeakStart = LEAK_LINE_STARTS.some((re) => re.test(trimmed));
    if (isLeakStart) {
      skippingLeakRun = true;
      continue;
    }
    if (skippingLeakRun) {
      if (trimmed === "") {
        skippingLeakRun = false;
        continue;
      }
      if (trimmed.startsWith("-") || trimmed.startsWith("•")) {
        continue;
      }
      if (/^respond in\b/i.test(trimmed)) {
        continue;
      }
      skippingLeakRun = false;
    }
    out.push(line);
  }

  return out.join("\n");
}

/**
 * Removes hidden reasoning tags and common leaked mode-contract lines.
 * Conservative: only nukes obvious instruction lines, not every mention of "think".
 */
export function sanitizeAssistantVisibleText(text: string): string {
  if (!text) return "";
  let t = stripTaggedBlocks(text);
  t = stripLeakedInstructionLines(t);
  t = t.replace(/\n{3,}/g, "\n\n").trim();
  return t;
}
