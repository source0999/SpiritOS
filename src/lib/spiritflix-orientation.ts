import type { JellyfinItem } from "./spiritflix-types";

export type SpiritFlixOrientationFilter = "all" | "portrait" | "landscape";
export type SpiritFlixVideoOrientation = Exclude<SpiritFlixOrientationFilter, "all">;

export function getVideoOrientation(item: JellyfinItem): SpiritFlixVideoOrientation | null {
  const videoStream = item.MediaStreams?.find((stream) => stream.Type?.toLowerCase() === "video");
  const width = videoStream?.Width ?? 0;
  const height = videoStream?.Height ?? 0;

  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
    return null;
  }

  return height > width ? "portrait" : "landscape";
}

export function itemMatchesVideoOrientation(item: JellyfinItem, filter: SpiritFlixOrientationFilter): boolean {
  if (filter === "all") return true;
  return getVideoOrientation(item) === filter;
}

export function filterItemsByVideoOrientation<T extends JellyfinItem>(
  items: T[],
  filter: SpiritFlixOrientationFilter,
): T[] {
  return items.filter((item) => itemMatchesVideoOrientation(item, filter));
}

export function countItemsByVideoOrientation(items: JellyfinItem[]): Record<SpiritFlixVideoOrientation, number> {
  return {
    portrait: items.filter((item) => getVideoOrientation(item) === "portrait").length,
    landscape: items.filter((item) => getVideoOrientation(item) === "landscape").length,
  };
}

export function getOrientationFilterLabel(filter: SpiritFlixOrientationFilter): string {
  if (filter === "portrait") return "Portrait";
  if (filter === "landscape") return "Landscape";
  return "All videos";
}
