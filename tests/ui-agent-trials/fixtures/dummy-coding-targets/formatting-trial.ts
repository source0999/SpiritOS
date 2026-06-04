export function formatEmptyFileList(files: string[]): string {
  return files.length > 0 ? files.join(", ") : "No files changed";
}
