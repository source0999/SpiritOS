import type { JellyfinItem, JellyfinLibrary } from "@/lib/spiritflix-types";

export type SpiritFlixAdminItemType = "file" | "folder" | "jellyfin-item";
export type SpiritFlixAdminImageType = "Primary" | "Thumb" | "Backdrop";
export type SpiritFlixAdminImageStatus = "available" | "missing" | "unauthenticated" | "ambiguous";
export type SpiritFlixAdminMatchMethod = "exact-path" | "same-folder-basename" | "filename" | "none" | "ambiguous";

export type SpiritFlixAdminSortBy =
  | "dateAdded"
  | "dateModified"
  | "title"
  | "runtime"
  | "size"
  | "path"
  | "library"
  | "watched"
  | "favorite";

export type SpiritFlixAdminSortOrder = "asc" | "desc";

export interface SpiritFlixAdminItem {
  id: string;
  name: string;
  type: SpiritFlixAdminItemType;
  libraryName?: string;
  jellyfinId?: string;
  jellyfinItemId?: string;
  jellyfinItem?: JellyfinItem;
  imageType?: SpiritFlixAdminImageType;
  imageStatus?: SpiritFlixAdminImageStatus;
  jellyfinMatchedBy?: SpiritFlixAdminMatchMethod;
  jellyfinMatchCandidateCount?: number;
  path?: string;
  parentPath?: string;
  jellyfinPath?: string;
  mediaType?: string;
  itemType?: string;
  extension?: string;
  sizeBytes?: number;
  dateCreated?: string;
  dateModified?: string;
  dateAdded?: string;
  runtimeTicks?: number;
  watched?: boolean;
  favorite?: boolean;
  hasImage?: boolean;
  playable?: boolean;
  resumePositionTicks?: number;
  modelNames?: string[];
}

export interface SpiritFlixAdminLibraryRequest {
  serverUrl?: string;
  accessToken?: string;
  userId?: string;
  searchTerm?: string;
  libraryId?: string;
  parentId?: string;
  recursive?: boolean;
  sortBy?: SpiritFlixAdminSortBy;
  sortOrder?: SpiritFlixAdminSortOrder;
  limit?: number;
  startIndex?: number;
  includeItemTypes?: string;
}

export interface SpiritFlixAdminLibraryResponse {
  schema: "spiritflix-admin-library/v1";
  generatedAt: string;
  libraries: JellyfinLibrary[];
  items: SpiritFlixAdminItem[];
  totalRecordCount: number;
  query: {
    searchTerm: string;
    libraryId: string;
    parentId: string;
    recursive: boolean;
    sortBy: SpiritFlixAdminSortBy;
    sortOrder: SpiritFlixAdminSortOrder;
    limit: number;
    startIndex: number;
    includeItemTypes: string;
  };
}

export interface SpiritFlixAdminFsResponse {
  schema: "spiritflix-admin-fs/v1";
  generatedAt: string;
  root: string;
  currentPath: string;
  parentPath?: string;
  breadcrumbs: Array<{ name: string; path: string }>;
  items: SpiritFlixAdminItem[];
  totalRecordCount: number;
}

export interface JellyfinAdminItemsResponse {
  Items?: JellyfinItem[];
  TotalRecordCount?: number;
}

export type SpiritFlixAdminActionName =
  | "createFolder"
  | "rename"
  | "move"
  | "softDelete"
  | "restore"
  | "writeMetadata"
  | "saveOrder"
  | "requestJellyfinRescan";

export type SpiritFlixAdminReceiptStatus = "planned" | "executed" | "blocked" | "failed" | "rolled_back";

export interface SpiritFlixAdminReceipt {
  id: string;
  timestamp: string;
  actor: "spiritflix-admin";
  action: string;
  status: SpiritFlixAdminReceiptStatus;
  sourcePath?: string;
  targetPath?: string;
  affectedPaths: string[];
  jellyfinItemIds?: string[];
  reason?: string;
  reversible: boolean;
  rollbackHint?: string;
  previewId?: string;
}

export interface SpiritFlixAdminOrderFile {
  version: 1;
  updatedAt: string;
  groups: Array<{
    id: string;
    name: string;
    itemKeys: string[];
  }>;
}

export interface SpiritFlixAdminMetadataSidecar {
  displayTitle?: string;
  customTags?: string[];
  collection?: string;
  notes?: string;
  manualSortGroup?: string;
  manualSortIndex?: number;
  hiddenFromViewer?: boolean;
  favoriteOverride?: boolean;
}

export type SpiritFlixAdminActionRiskLevel = "low" | "medium" | "high";

export interface SpiritFlixAdminActionRequest {
  action: SpiritFlixAdminActionName;
  /** @deprecated prefer `mode` — kept for backward compatibility */
  phase?: "preview" | "execute";
  mode?: "preview" | "execute";
  previewId?: string;
  confirmToken?: string;
  sourcePath?: string;
  targetPath?: string;
  parentPath?: string;
  newName?: string;
  name?: string;
  folderName?: string;
  metadata?: SpiritFlixAdminMetadataSidecar;
  order?: SpiritFlixAdminOrderFile;
  rescanPath?: string;
}

export interface SpiritFlixAdminActionResponse {
  schema: "spiritflix-admin-action/v1";
  action: SpiritFlixAdminActionName;
  phase: "preview" | "execute";
  previewId: string;
  allowed: boolean;
  message: string;
  mutationApplied?: boolean;
  riskLevel?: SpiritFlixAdminActionRiskLevel;
  receipt?: SpiritFlixAdminReceipt;
  preview?: {
    sourcePath?: string;
    targetPath?: string;
    affectedPaths: string[];
    warnings: string[];
    reversible?: boolean;
  };
}
