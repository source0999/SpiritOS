import { isSpiritFlixAdminTrashPath } from "@/lib/spiritflix/admin/path-rules";
import type { SpiritFlixAdminActionName, SpiritFlixAdminItem } from "@/lib/spiritflix/admin/types";

export type SpiritFlixAdminMenuActionId =
  | "openViewer"
  | "openFolder"
  | "info"
  | "smartTags"
  | "rename"
  | "move"
  | "softDelete"
  | "editMetadata"
  | "copyPath"
  | "copyFilename"
  | "copyFolderName"
  | "refresh"
  | "newFolder"
  | "restore";

export interface SpiritFlixAdminMenuItemDef {
  id: SpiritFlixAdminMenuActionId;
  label: string;
  destructive?: boolean;
  disabled?: boolean;
}

const VIDEO_EXTENSIONS = new Set([".avi", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".webm", ".wmv"]);

export function isSpiritFlixAdminVideoItem(item: SpiritFlixAdminItem): boolean {
  if (item.type !== "file") return false;
  const extension = item.extension?.toLowerCase() ?? "";
  return Boolean(item.playable || VIDEO_EXTENSIONS.has(extension));
}

export function menuActionToDialogAction(id: SpiritFlixAdminMenuActionId): SpiritFlixAdminActionName | null {
  switch (id) {
    case "rename":
      return "rename";
    case "move":
      return "move";
    case "softDelete":
      return "softDelete";
    case "editMetadata":
      return "writeMetadata";
    case "newFolder":
      return "createFolder";
    case "restore":
      return "restore";
    default:
      return null;
  }
}

export function buildItemMenuItems(
  item: SpiritFlixAdminItem | null,
  currentPath: string,
): SpiritFlixAdminMenuItemDef[] {
  if (!item) {
    return [
      { id: "newFolder", label: "New folder" },
      { id: "refresh", label: "Refresh listing" },
    ];
  }

  const isTrash = Boolean(item.path && isSpiritFlixAdminTrashPath(item.path));
  const isFolder = item.type === "folder";
  const hasViewer = Boolean(item.jellyfinItemId || item.jellyfinId);

  if (isTrash) {
    return [
      { id: "restore", label: "Restore" },
      { id: "info", label: "Info" },
      { id: "copyPath", label: "Copy path" },
      { id: "refresh", label: "Refresh listing" },
    ];
  }

  if (isFolder) {
    return [
      { id: "openFolder", label: "Open folder" },
      { id: "info", label: "Info" },
      { id: "smartTags", label: "Smart tags are available for videos only.", disabled: true },
      { id: "rename", label: "Rename" },
      { id: "move", label: "Move" },
      { id: "softDelete", label: "Soft delete", destructive: true },
      { id: "copyPath", label: "Copy path" },
      { id: "copyFolderName", label: "Copy folder name" },
      { id: "refresh", label: "Refresh listing" },
    ];
  }

  const fileItems: SpiritFlixAdminMenuItemDef[] = [];
  if (hasViewer) fileItems.push({ id: "openViewer", label: "Open viewer" });
  fileItems.push(
    { id: "info", label: "Info" },
  );
  if (isSpiritFlixAdminVideoItem(item)) {
    fileItems.push({ id: "smartTags", label: "Smart tags" });
  }
  fileItems.push(
    { id: "rename", label: "Rename" },
    { id: "move", label: "Move" },
    { id: "softDelete", label: "Soft delete", destructive: true },
    { id: "editMetadata", label: "Edit metadata" },
    { id: "copyPath", label: "Copy path" },
    { id: "copyFilename", label: "Copy filename" },
    { id: "refresh", label: "Refresh listing" },
  );
  return fileItems;
}

export function buildBackgroundMenuItems(): SpiritFlixAdminMenuItemDef[] {
  return [
    { id: "newFolder", label: "New folder" },
    { id: "refresh", label: "Refresh listing" },
  ];
}
