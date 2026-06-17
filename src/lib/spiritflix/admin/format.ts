import type { SpiritFlixAdminItem } from "./types";

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export function formatItemDateLabel(item: SpiritFlixAdminItem): { label: string; text: string } {
  if (item.dateAdded && (item.jellyfinId || item.jellyfinItemId)) {
    return { label: "Added", text: formatDate(item.dateAdded) };
  }

  if (item.dateCreated && item.dateModified && item.dateCreated !== item.dateModified) {
    return { label: "Created", text: formatDate(item.dateCreated) };
  }

  if (item.dateModified) {
    return { label: "Modified", text: formatDate(item.dateModified) };
  }

  if (item.dateAdded) {
    return { label: "Added", text: formatDate(item.dateAdded) };
  }

  if (item.dateCreated) {
    return { label: "Created", text: formatDate(item.dateCreated) };
  }

  return { label: "", text: "" };
}

export function formatBytes(value?: number): string {
  if (!value) return "";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = value;
  let unit = 0;
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024;
    unit += 1;
  }
  return `${size.toFixed(size >= 10 || unit === 0 ? 0 : 1)} ${units[unit]}`;
}

export function isMetadataSidecar(name: string): boolean {
  if (name.startsWith(".")) return true;
  const lower = name.toLowerCase();
  return lower.endsWith(".media-ingest.json") || lower.endsWith(".face-meta.json") || lower.endsWith(".json");
}
