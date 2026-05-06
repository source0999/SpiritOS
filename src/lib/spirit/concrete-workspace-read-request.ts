// ── concrete-workspace-read-request - gate LLM path vs capability shortcut ──
// > True only for path-specific read/list/tail asks, not vague permission questions.

/** Strip trailing punctuation / quotes from a captured path fragment. */
function trimPathFragment(fragment: string): string {
  return fragment.replace(/^[`"'“”]+/, "").replace(/[`"'“”.,;:!?]+$/, "").trim();
}

/**
 * True when the fragment looks like a workspace-relative path or filename,
 * not a vague noun phrase ("my files", "folders").
 */
export function pathFragmentLooksConcrete(fragment: string): boolean {
  const s = trimPathFragment(fragment);
  if (s.length < 1) return false;
  if (/^(files?|folders?|directories?)$/i.test(s)) return false;
  if (/^(my|your|the|a|an|any|all|arbitrary|some)\s+files?$/i.test(s)) return false;
  if (/^my\s+/i.test(s) && !s.includes("/")) return false;

  if (s.includes("/")) return true;
  if (/^\.env/i.test(s)) return true;
  if (/\.(?:ts|tsx|js|jsx|json|md|mjs|cjs|css|html|txt|log|yaml|yml|toml|xml|svg|pem|key)(?:\.\w+)?$/i.test(s))
    return true;
  if (s === "package.json" || s === "nohup.out" || /^[\w.-]+\.json$/i.test(s)) return true;
  if (/^(src|lib|app|test|tests|public|docs|packages|components|scripts|config)(\/[\w.-]+)*$/i.test(s))
    return true;
  return false;
}

/**
 * True when the user is asking for a concrete workspace read/list/tail operation
 * (so Hermes can use read-only tools), not a capability meta-question.
 */
export function isConcreteWorkspaceReadRequest(text: string): boolean {
  const raw = text.trim();
  if (raw.length < 6) return false;
  const lower = raw.toLowerCase();

  if (
    /\b(run|execute|exec|bash|shell|terminal|sudo|npm\s+(test|run|install|ci|start|dev|exec)|pnpm\s|yarn\s+(test|install|add))\b/i.test(
      lower,
    )
  ) {
    return false;
  }

  if (/\b(edit|delete|write|create|mkdir|rm\s|mv\s|cp\s)\s+/i.test(lower)) return false;

  if (/\bshow\s+(the\s+)?(last|past)\s+\d+\s+lines\s+of\s+([^\s?!,]+)/i.test(raw)) {
    const m = raw.match(/\bshow\s+(the\s+)?(last|past)\s+\d+\s+lines\s+of\s+([^\s?!,]+)/i);
    if (m?.[3] && pathFragmentLooksConcrete(m[3])) return true;
  }

  if (/\btail\s+([^\s?!,]+)/i.test(raw)) {
    const m = raw.match(/\btail\s+([^\s?!,]+)/i);
    if (m?.[1] && pathFragmentLooksConcrete(m[1])) return true;
  }

  const listFilesIn = raw.match(/\blist\s+(the\s+)?files?\s+in\s+([^\s?!,]+)/i);
  if (listFilesIn?.[2] && pathFragmentLooksConcrete(listFilesIn[2])) return true;

  const listDir = raw.match(/\blist\s+(the\s+)?(directory|dir)\s+([^\s?!,]+)/i);
  if (listDir?.[3] && pathFragmentLooksConcrete(listDir[3])) return true;

  const showFilesIn = raw.match(/\bshow\s+(the\s+)?files?\s+in\s+([^\s?!,]+)/i);
  if (showFilesIn?.[2] && pathFragmentLooksConcrete(showFilesIn[2])) return true;

  const showContents = raw.match(/\bshow\s+(the\s+)?contents\s+of\s+([^\s?!,]+)/i);
  if (showContents?.[2] && pathFragmentLooksConcrete(showContents[2])) return true;

  const readFile = raw.match(/\bread\s+([^\s?!,]+)/i);
  if (readFile?.[1] && !/^(files?|folders?|directories?)$/i.test(readFile[1])) {
    if (pathFragmentLooksConcrete(readFile[1])) return true;
  }

  const openFile = raw.match(/\bopen\s+([^\s?!,]+)/i);
  if (openFile?.[1] && pathFragmentLooksConcrete(openFile[1])) return true;

  return false;
}
