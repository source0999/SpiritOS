import type { JellyfinItem } from "@/lib/spiritflix-types";
import type { SpiritFlixAdminImageStatus, SpiritFlixAdminImageType, SpiritFlixAdminMatchMethod } from "./types";
import { adminPathsEquivalent, expandSpiritFlixPathAliases, normalizeAdminPath } from "./path-aliases";

export interface SpiritFlixAdminJellyfinMatch {
  item?: JellyfinItem;
  itemId?: string;
  imageType?: SpiritFlixAdminImageType;
  imageStatus: SpiritFlixAdminImageStatus;
  matchedBy: SpiritFlixAdminMatchMethod;
  candidateCount: number;
}

function basename(value?: string): string {
  const normalized = normalizeAdminPath(value);
  return normalized ? (normalized.split("/").filter(Boolean).at(-1) ?? "") : "";
}

function dirname(value?: string): string {
  const normalized = normalizeAdminPath(value);
  const parts = normalized.split("/").filter(Boolean);
  if (parts.length <= 1) return "";
  return `${normalized.startsWith("/") ? "/" : ""}${parts.slice(0, -1).join("/")}`;
}

function itemPaths(item: JellyfinItem): string[] {
  const paths = [item.Path, ...(item.MediaSources ?? []).map((source) => source.Path)].filter(Boolean) as string[];
  return [...new Set(paths.map(normalizeAdminPath).filter(Boolean))];
}

function itemNames(item: JellyfinItem): string[] {
  return [...new Set([item.Name, ...itemPaths(item).map((itemPath) => basename(itemPath))].map((name) => name?.toLowerCase()).filter(Boolean) as string[])];
}

function foldersEquivalent(left?: string, right?: string): boolean {
  const leftAliases = expandSpiritFlixPathAliases(left);
  const rightAliases = expandSpiritFlixPathAliases(right);
  return leftAliases.some((alias) => rightAliases.includes(alias));
}

export function preferredAdminImageType(item?: JellyfinItem): SpiritFlixAdminImageType | undefined {
  if (!item) return undefined;
  if (item.ImageTags?.Primary) return "Primary";
  if (item.ImageTags?.Thumb) return "Thumb";
  if (item.BackdropImageTags?.length) return "Backdrop";
  return undefined;
}

function matchResult(item: JellyfinItem, matchedBy: SpiritFlixAdminMatchMethod, candidateCount: number): SpiritFlixAdminJellyfinMatch {
  const imageType = preferredAdminImageType(item);
  return {
    item,
    itemId: item.Id,
    imageType,
    imageStatus: imageType ? "available" : "missing",
    matchedBy,
    candidateCount,
  };
}

function uniqueById(items: JellyfinItem[]): JellyfinItem[] {
  const byId = new Map<string, JellyfinItem>();
  for (const item of items) {
    byId.set(item.Id, item);
  }
  return [...byId.values()];
}

export function matchJellyfinItemForAdminFile(filePath: string | undefined, jellyfinItems: JellyfinItem[]): SpiritFlixAdminJellyfinMatch {
  const normalizedFilePath = normalizeAdminPath(filePath);
  if (!normalizedFilePath) {
    return { imageStatus: "missing", matchedBy: "none", candidateCount: 0 };
  }

  const fileName = basename(normalizedFilePath);
  const fileFolder = dirname(normalizedFilePath);

  const exactMatches = uniqueById(
    jellyfinItems.filter((item) => itemPaths(item).some((itemPath) => adminPathsEquivalent(itemPath, normalizedFilePath))),
  );
  if (exactMatches.length === 1) return matchResult(exactMatches[0], "exact-path", exactMatches.length);
  if (exactMatches.length > 1) return { imageStatus: "ambiguous", matchedBy: "ambiguous", candidateCount: exactMatches.length };

  const sameFolderMatches = uniqueById(
    jellyfinItems.filter((item) =>
      itemPaths(item).some((itemPath) => basename(itemPath) === fileName && foldersEquivalent(dirname(itemPath), fileFolder)),
    ),
  );
  if (sameFolderMatches.length === 1) return matchResult(sameFolderMatches[0], "same-folder-basename", sameFolderMatches.length);
  if (sameFolderMatches.length > 1) return { imageStatus: "ambiguous", matchedBy: "ambiguous", candidateCount: sameFolderMatches.length };

  const filenameMatches = uniqueById(
    jellyfinItems.filter((item) => {
      const paths = itemPaths(item);
      const hasPathInCurrentFolder = paths.some(
        (itemPath) => foldersEquivalent(dirname(itemPath), fileFolder) && basename(itemPath) === fileName,
      );
      if (hasPathInCurrentFolder) return true;
      if (paths.length > 0) return false;
      return itemNames(item).includes(fileName);
    }),
  );
  if (filenameMatches.length === 1) return matchResult(filenameMatches[0], "filename", filenameMatches.length);
  if (filenameMatches.length > 1) return { imageStatus: "ambiguous", matchedBy: "ambiguous", candidateCount: filenameMatches.length };

  return { imageStatus: "missing", matchedBy: "none", candidateCount: 0 };
}
