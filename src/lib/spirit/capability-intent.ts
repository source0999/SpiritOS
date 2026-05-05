// ── capability-intent — categorized detector for deterministic /api/spirit replies ─
// > Order matters: narrow intents before broad; false negatives beat hijacking normal chat.

export type CapabilityIntentKind =
  | "hardware_summary"
  | "node_status"
  | "storage_status"
  | "file_access"
  | "desktop_control"
  | "ai_runtime"
  | "tool_inventory"
  | "general_capabilities";

/** Exported for tests — normalizes typos like "capabilites" before pattern matching */
export function normalizeForCapabilityIntent(raw: string): string {
  let s = raw.trim().toLowerCase();
  s = s.replace(/\s+/g, " ");
  // strip decorative wrapping punctuation (keep ? ! . inside phrase)
  s = s.replace(/^[^a-z0-9]+/i, "");
  s = s.replace(/[^a-z0-9?.!]+$/i, "");

  s = s.replace(/\bcapabilites\b/g, "capabilities");
  s = s.replace(/\bcapabilties\b/g, "capabilities");
  s = s.replace(/\bcapibility\b/g, "capabilities");
  s = s.replace(/\bcapabilty\b/g, "capabilities");
  s = s.replace(/\bcapabilitiy\b/g, "capabilities");
  s = s.replace(/\babilites\b/g, "abilities");

  return s.trim();
}

/** Avoid matching “what can you see wrong with this” — only pure capability asks */
function isStandaloneWhatCanYouSeeOrControl(t: string): boolean {
  return (
    /^(what\s+can\s+you\s+see)(\s*[?.!])*$/i.test(t) ||
    /^(what\s+can\s+you\s+control)(\s*[?.!])*$/i.test(t)
  );
}

/** Need pairing with telemetry/host context to avoid “best CPU for gaming” false positives */
const HARDWARE_TERMS = /\b(cpu|processor|ram|memory|gpu)\b/i;
const TELEMETRY_CONTEXT =
  /\b(telemetry|nodes?|hardware|homelab|spirit|machine|host|online|offline|uptime|disk|drive|storage)\b/i;

const MODEL_RUNTIME =
  /\b(hermes|ollama|oracle\s+model|which\s+model|what\s+model|what\s+ai\b|backend\s+model)\b/i;

const INFRA_STATUS =
  /\b(web\s+search|tts|stt|whisper|piper|elevenlabs|voice)\b/i;

/** Legacy catch-all patterns → general_capabilities */
const GENERAL_STRONG: RegExp[] = [
  /\bcluster\s+telemetry\b/i,
  /\bstorage\s+telemetry\b/i,
  /can\s+you\s+see.*\b(nodes?|machines?)\b/i,
  /\bspirit(os)?\s+capabilities\b/i,
];

/** Filesystem / path ops — not drive-level “see” visibility */
function matchesFileAccessIntent(t: string): boolean {
  if (
    /\b(can\s+you\s+)?(browse|list|open)\b.*\b(files?|folders?|directories?)\b/i.test(t)
  ) {
    return true;
  }
  if (/\b(list|browse)\b.*\b(my\s+)?files?\b/i.test(t)) return true;
  if (/\b(show\s+folders|list\s+files)\b/i.test(t)) return true;
  if (/\b(can\s+you\s+)?(read|write|edit|delete|move)\b.*\bfiles?\b/i.test(t)) return true;
  // Path + browse/list/open (no “see” — that’s storage visibility)
  if (
    (/\bc:[\\\/]/i.test(t) || /\bc\s*drive\b/i.test(t) || /\bd\s*drive\b/i.test(t)) &&
    /\b(browse|list|open)\b/i.test(t)
  ) {
    return true;
  }
  // files/folders on a drive letter
  if (/\b(files?|folders?)\b/i.test(t) && /\b(c:|c\s*drive|d\s*drive|e\s*drive)\b/i.test(t)) {
    return true;
  }
  return false;
}

/** See drives / storage volumes — not browse/list files (exported for storage formatter) */
export function matchesStorageVisibilityIntent(t: string): boolean {
  if (matchesFileAccessIntent(t)) return false;

  return (
    /\b(can\s+you\s+|do\s+you\s+)?see\b.*\b(c:|c\s*drive|d\s*drive|e\s*drive|my\s+drives?|my\s+storage)\b/i.test(
      t,
    ) ||
    /\b(can\s+you\s+|do\s+you\s+)?see\b.*\b(my\s+)?drives?\b/i.test(t) ||
    /\bwhat\s+drives\b/i.test(t) ||
    /\bwhat\s+storage\b.*\b(see|show|have)\b/i.test(t) ||
    /\bdo\s+you\s+see\b.*\bc:/i.test(t) ||
    /\bhow\s+much\s+(disk|storage)\b/i.test(t) ||
    (/\bstorage\b/i.test(t) && /\b(see|show|have|telemetry|drives?)\b/i.test(t))
  );
}

export function detectCapabilityIntent(raw: string): CapabilityIntentKind | null {
  const t = normalizeForCapabilityIntent(raw);
  if (t.length < 6) return null;

  // ── 1. File / folder / explicit path file ops (before “see my C:” storage) ─
  if (matchesFileAccessIntent(t)) {
    return "file_access";
  }

  // ── 2. Drive & storage visibility (see C:, what drives, what storage can you see) ─
  if (matchesStorageVisibilityIntent(t)) {
    return "storage_status";
  }

  // ── 3. Desktop / remote control / SSH (app-level) ─
  if (
    /\b(can\s+you\s+)?control\b.*\b(desktop|my\s+pc|this\s+machine|computer)\b/i.test(t) ||
    /\bssh\b/i.test(t) ||
    /\bremote\s+(desktop|control)\b/i.test(t)
  ) {
    return "desktop_control";
  }

  // ── 4. Models / runtime ─
  if (
    /\b(hermes|ollama)\b/i.test(t) ||
    /\b(what|which)\s+(model|ai|backend)\b/i.test(t) ||
    /\b(running|using)\s+(on\s+)?(hermes|ollama)\b/i.test(t) ||
    /\bare\s+you\s+running\b/i.test(t)
  ) {
    return "ai_runtime";
  }

  // ── 5. Tools vs broad capability / “what can you do” ─
  const toolsExplicit =
    /\bwhat\s+tools\b/i.test(t) ||
    /\btools\b.*\b(have|got|available)\b/i.test(t) ||
    /\bspirit\s*os\s+tools\b/i.test(t) ||
    /\bspiritos\s+tools\b/i.test(t);

  const capabilityOverview =
    /\bwhat\s+are\s+your\s+capabilities\b/i.test(t) ||
    /\bwhat\s+can\s+you\s+do\b/i.test(t) ||
    /\bwhat\s+abilities\b/i.test(t) ||
    /\bwhat\s+powers\b/i.test(t) ||
    /\bwhat\s+access\b/i.test(t) ||
    /\bwhat\s+can\s+spirit\s*os\b/i.test(t) ||
    /\bwhat\s+can\s+spiritos\b/i.test(t) ||
    /\bwhat\s+do\s+you\s+know\s+about\s+your\s+system\b/i.test(t) ||
    isStandaloneWhatCanYouSeeOrControl(t);

  if (toolsExplicit) return "tool_inventory";
  if (capabilityOverview) return "general_capabilities";

  // ── 6. Nodes (online/offline) ─
  if (
    /\bwhat\s+nodes\b/i.test(t) ||
    /\bwhich\s+nodes\b/i.test(t) ||
    /\bnodes\s+are\s+online\b/i.test(t) ||
    (/\bwhat\s+machines\b/i.test(t) && /\bonline|offline\b/i.test(t))
  ) {
    return "node_status";
  }

  // ── 7. Storage quantity (without “see” already handled) ─
  if (/\bwhat\s+storage\b/i.test(t)) {
    return "storage_status";
  }

  // ── 8. Hardware overview ─
  if (
    /\bwhat\s+hardware\b/i.test(t) ||
    /\bhardware\b.*\b(see|have|show)\b/i.test(t) ||
    /\bcan\s+you\s+see.*\b(hardware|machines)\b/i.test(t)
  ) {
    return "hardware_summary";
  }

  // ── 9. General capability / infra questions ─
  if (GENERAL_STRONG.some((re) => re.test(t))) return "general_capabilities";
  if (MODEL_RUNTIME.test(t) || INFRA_STATUS.test(t)) return "general_capabilities";
  if (HARDWARE_TERMS.test(t) && TELEMETRY_CONTEXT.test(t)) return "general_capabilities";

  return null;
}

export function isCapabilityIntent(raw: string): boolean {
  return detectCapabilityIntent(raw) !== null;
}
