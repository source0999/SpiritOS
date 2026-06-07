export type ChangedFilesDiagnostics = {
  appliedChangedFiles: string[];
  changedFiles: string[];
  diskChangedFiles: string[];
  previewChangedFiles: string[];
};

function normalizeRepoPath(path: string): string {
  const trimmed = path.trim().replace(/\\/g, "/");
  if (trimmed.endsWith("/") && /\.[A-Za-z0-9]+$/.test(trimmed.slice(0, -1))) {
    return trimmed.slice(0, -1);
  }
  return trimmed;
}

export function changedFilesFromDiffPreview(diff: string): string[] {
  const files = new Set<string>();
  for (const line of diff.split("\n")) {
    const match = line.match(/^diff --git a\/(.+?) b\/(.+)$/);
    if (match?.[2]) {
      files.add(normalizeRepoPath(match[2]));
      continue;
    }
    const plusMatch = line.match(/^\+\+\+ [ab]\/(.+)$/);
    if (plusMatch?.[1] && plusMatch[1] !== "/dev/null") {
      files.add(normalizeRepoPath(plusMatch[1]));
    }
  }
  return Array.from(files).filter(Boolean);
}

export function buildChangedFilesDiagnostics(input: {
  appliedAt?: string | null;
  diff?: string;
  status?: string | null;
  verificationChangedFiles?: string[];
}): ChangedFilesDiagnostics {
  const previewChangedFiles =
    input.diff && input.diff.trim()
      ? changedFilesFromDiffPreview(input.diff)
      : input.verificationChangedFiles && input.status !== "idle"
        ? [...input.verificationChangedFiles]
        : [];
  const appliedChangedFiles =
    input.appliedAt && previewChangedFiles.length > 0 ? [...previewChangedFiles] : [];
  const diskChangedFiles = appliedChangedFiles.length > 0 ? [...appliedChangedFiles] : [];
  const changedFiles = previewChangedFiles.length > 0 ? previewChangedFiles : [];

  return {
    appliedChangedFiles,
    changedFiles,
    diskChangedFiles,
    previewChangedFiles,
  };
}

export function formatChangedFilesDiagnosticsLines(diagnostics: ChangedFilesDiagnostics): string[] {
  return [
    `preview_changed_files: ${diagnostics.previewChangedFiles.join(", ") || "none"}`,
    `disk_changed_files: ${diagnostics.diskChangedFiles.join(", ") || "none"}`,
    `applied_changed_files: ${diagnostics.appliedChangedFiles.join(", ") || "none"}`,
    `changed_files: ${diagnostics.changedFiles.join(", ") || "none"}`,
  ];
}
