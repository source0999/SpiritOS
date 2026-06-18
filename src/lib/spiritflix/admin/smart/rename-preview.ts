// ── SpiritFlix Smart Rename Preview Builder (S6) ────────────────────────
// Builds a rename preview draft without executing anything.
// No filesystem rename, no Level 2 calls, no execute.

import path from "node:path";

// ── Types ──────────────────────────────────────────────────────────────

export interface SpiritFlixSmartRenamePreviewInput {
  sourcePath: string;
  filenameSuggestion: string;
}

export interface SpiritFlixSmartRenamePreviewDraft {
  sourcePath: string;
  suggestedName: string;
  targetPath: string;
  warnings: string[];
  readyForLevel2Preview: boolean;
}

// ── Constants ───────────────────────────────────────────────────────────

const UNSAFE_FILENAME_CHARS = /[\\/:*?"<>|]/g;
const MAX_FILENAME_STEM_LENGTH = 180;
const GENERIC_STEMS = new Set([
  "untitled",
  "video",
  "clip",
  "new",
  "copy",
  "download",
  "screen recording",
]);

function normalizeSanitizedSuggestion(value: string): string {
  return value
    .replace(UNSAFE_FILENAME_CHARS, " ")
    .replace(/\s+\./g, ".")
    .replace(/\s+/g, " ")
    .trim();
}

// ── Pure builder ────────────────────────────────────────────────────────

export function buildSmartRenamePreviewDraft(
  input: SpiritFlixSmartRenamePreviewInput,
): SpiritFlixSmartRenamePreviewDraft {
  const { sourcePath, filenameSuggestion } = input;
  const warnings: string[] = [];

  // Sanitize the suggested name
  const rawName = filenameSuggestion.trim();
  if (!rawName) {
    return {
      sourcePath,
      suggestedName: "",
      targetPath: sourcePath,
      warnings: ["Filename suggestion is empty."],
      readyForLevel2Preview: false,
    };
  }

  // Strip unsafe characters
  const sanitized = normalizeSanitizedSuggestion(rawName);
  if (!sanitized) {
    return {
      sourcePath,
      suggestedName: "",
      targetPath: sourcePath,
      warnings: ["Filename suggestion is empty after sanitization."],
      readyForLevel2Preview: false,
    };
  }

  // Reject slashes in suggested name (directory separator confusion)
  if (/[/\\]/.test(filenameSuggestion)) {
    warnings.push("Filename suggestion contains slashes; only the basename is used.");
  }
  if (/(^|[\\/])\.\.?($|[\\/])|^\.\./.test(filenameSuggestion)) {
    warnings.push("Filename suggestion contains traversal segments.");
  }

  // Preserve original extension
  const originalExtension = path.extname(sourcePath);
  const suggestionAlreadyHasExt = path.extname(sanitized).toLowerCase() === originalExtension.toLowerCase();
  const suggestedStem = suggestionAlreadyHasExt
    ? sanitized.slice(0, -path.extname(sanitized).length)
    : sanitized;
  const suggestedName = originalExtension
    ? `${suggestedStem}${originalExtension}`
    : sanitized;

  // Cap stem length
  const cappedStem = suggestedStem.length > MAX_FILENAME_STEM_LENGTH
    ? suggestedStem.slice(0, MAX_FILENAME_STEM_LENGTH).trim()
    : suggestedStem;
  const finalName = originalExtension
    ? `${cappedStem}${originalExtension}`
    : cappedStem;

  // Target stays in same folder
  const targetPath = path.join(path.dirname(sourcePath), finalName);

  // Validate: no traversal
  if (finalName.split(/[\\/]+/).some((segment) => segment === "..") || finalName.startsWith("..")) {
    warnings.push("Filename suggestion contains traversal segments.");
  }

  // Validate: not empty
  if (!finalName.trim()) {
    warnings.push("Filename suggestion is empty.");
  }

  // Warn: unchanged
  const originalBasename = path.basename(sourcePath);
  if (finalName === originalBasename) {
    warnings.push("Suggested filename is unchanged from current filename.");
  }

  // Warn: too long
  const stemOnly = path.parse(finalName).name;
  if (stemOnly.length > MAX_FILENAME_STEM_LENGTH) {
    warnings.push("Filename stem is very long; may cause filesystem issues.");
  }

  // Warn: generic
  if (GENERIC_STEMS.has(stemOnly.toLowerCase())) {
    warnings.push("Filename stem is generic and may not be useful for organization.");
  }

  const hasBlockingWarning = warnings.some(
    (w) =>
      /empty|traversal|slashes/i.test(w),
  );
  const isUnchanged = finalName === originalBasename;

  return {
    sourcePath,
    suggestedName: finalName,
    targetPath,
    warnings,
    readyForLevel2Preview: !hasBlockingWarning && !isUnchanged,
  };
}
