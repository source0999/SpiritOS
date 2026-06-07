export type TrialChangedFiles = {
  applied: string[];
  preview: string[];
};

export function formatTrialChangedFiles(files: TrialChangedFiles): string {
  const combined = [...files.preview, ...files.applied];
  return combined.length > 0 ? combined.join(", ") : "No files changed";
}
