import { isSpiritFlixAdminTrashPath } from "@/lib/spiritflix/admin/path-rules";
import type { SpiritFlixAdminActionName, SpiritFlixAdminItem } from "@/lib/spiritflix/admin/types";

export type SpiritFlixAdminMenuActionId =
  | "openViewer"
  | "openFolder"
  | "info"
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
