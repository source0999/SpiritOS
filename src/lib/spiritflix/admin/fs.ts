import fs from "node:fs/promises";
import path from "node:path";
import type { SpiritFlixAdminFsResponse, SpiritFlixAdminItem, SpiritFlixAdminSortBy, SpiritFlixAdminSortOrder } from "./types";
import { resolveSpiritFlixAdminPath } from "./paths";

const MEDIA_EXTENSIONS = new Set([".avi", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".webm", ".wmv"]);

function compareValue(left: string | number | boolean | undefined, right: string | number | boolean | undefined): number {
  if (typeof left === "number" || typeof right === "number") return (left ?? 0) < (right ?? 0) ? -1 : (left ?? 0) > (right ?? 0) ? 1 : 0;
  if (typeof left === "boolean" || typeof right === "boolean") return Number(left ?? false) - Number(right ?? false);
  return String(left ?? "").localeCompare(String(right ?? ""), undefined, { numeric: true, sensitivity: "base" });
}

function itemSortValue(item: SpiritFlixAdminItem, sortBy: SpiritFlixAdminSortBy): string | number | boolean | undefined {
  if (sortBy === "dateModified") return item.dateModified;
  if (sortBy === "dateAdded") return item.dateAdded ?? item.dateCreated;
  if (sortBy === "runtime") return item.runtimeTicks;
  if (sortBy === "size") return item.sizeBytes;
  if (sortBy === "path") return item.path;
  if (sortBy === "library") return item.libraryName;
  if (sortBy === "watched") return item.watched;
  if (sortBy === "favorite") return item.favorite;
  return item.name;
}

function sortItems(items: SpiritFlixAdminItem[], sortBy: SpiritFlixAdminSortBy, sortOrder: SpiritFlixAdminSortOrder): SpiritFlixAdminItem[] {
  const direction = sortOrder === "desc" ? -1 : 1;
  return [...items].sort((left, right) => {
    if (left.type !== right.type) return left.type === "folder" ? -1 : 1;
    return compareValue(itemSortValue(left, sortBy), itemSortValue(right, sortBy)) * direction || left.name.localeCompare(right.name);
  });
}

function breadcrumbs(root: string, currentPath: string): Array<{ name: string; path: string }> {
  const parts = path.relative(root, currentPath).split(path.sep).filter(Boolean);
  const rootName = path.basename(root) || root;
  return [
    { name: rootName, path: root },
    ...parts.map((name, index) => ({
      name,
      path: path.join(root, ...parts.slice(0, index + 1)),
    })),
  ];
}

export async function listSpiritFlixAdminDirectory(options: {
  path?: string;
  searchTerm?: string;
  sortBy?: SpiritFlixAdminSortBy;
  sortOrder?: SpiritFlixAdminSortOrder;
  limit?: number;
  startIndex?: number;
}): Promise<SpiritFlixAdminFsResponse> {
  const resolved = await resolveSpiritFlixAdminPath(options.path);
  const stats = await fs.stat(resolved.realPath);

  if (!stats.isDirectory()) {
    throw new Error("SpiritFlix admin filesystem listing requires a folder path.");
  }

  const entries = await fs.readdir(resolved.realPath, { withFileTypes: true });
  const search = options.searchTerm?.trim().toLowerCase() ?? "";
  const items: SpiritFlixAdminItem[] = [];

  for (const entry of entries) {
    if (!entry.isDirectory() && !entry.isFile()) continue;
    if (entry.name.startsWith(".")) continue;
    if (search && !entry.name.toLowerCase().includes(search)) continue;

    const itemPath = path.join(resolved.realPath, entry.name);
    const itemStat = await fs.stat(itemPath);
    const extension = entry.isFile() ? path.extname(entry.name).toLowerCase() : undefined;

    items.push({
      id: `${entry.isDirectory() ? "folder" : "file"}:${itemPath}`,
      name: entry.name,
      type: entry.isDirectory() ? "folder" : "file",
      path: itemPath,
      parentPath: resolved.realPath,
      extension,
      sizeBytes: entry.isFile() ? itemStat.size : undefined,
      dateCreated: itemStat.birthtime.toISOString(),
      dateModified: itemStat.mtime.toISOString(),
      playable: Boolean(extension && MEDIA_EXTENSIONS.has(extension)),
    });
  }

  const sorted = sortItems(items, options.sortBy ?? "title", options.sortOrder ?? "asc");
  const startIndex = Math.max(0, options.startIndex ?? 0);
  const limit = Math.max(1, Math.min(500, options.limit ?? 200));
  const page = sorted.slice(startIndex, startIndex + limit);
  const parentPath = resolved.realPath === resolved.allowedRoot ? undefined : path.dirname(resolved.realPath);

  return {
    schema: "spiritflix-admin-fs/v1",
    generatedAt: new Date().toISOString(),
    root: resolved.allowedRoot,
    currentPath: resolved.realPath,
    parentPath,
    breadcrumbs: breadcrumbs(resolved.allowedRoot, resolved.realPath),
    items: page,
    totalRecordCount: sorted.length,
  };
}
