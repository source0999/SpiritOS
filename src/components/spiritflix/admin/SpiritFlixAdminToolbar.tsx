"use client";

import { ArrowDownAZ, ArrowUpAZ, FileJson, Grid2X2, List, RefreshCw, Search, Sparkles, Upload } from "lucide-react";
import { SPIRITFLIX_ADMIN_LEVEL2_GATE_MESSAGE, SPIRITFLIX_ADMIN_LEVEL2_GATED } from "@/lib/spiritflix/admin/constants";
import type { SpiritFlixAdminSortBy, SpiritFlixAdminSortOrder } from "@/lib/spiritflix/admin/types";

export type SpiritFlixAdminViewMode = "grid" | "list";

interface SpiritFlixAdminToolbarProps {
  includeMetadataFiles: boolean;
  loading: boolean;
  searchTerm: string;
  sortBy: SpiritFlixAdminSortBy;
  sortOrder: SpiritFlixAdminSortOrder;
  viewMode: SpiritFlixAdminViewMode;
  onIncludeMetadataFilesChange: (value: boolean) => void;
  onBatchSmartAnalyze: () => void;
  onManage: () => void;
  onRefresh: () => void;
  onSearchTermChange: (value: string) => void;
  onSortByChange: (value: SpiritFlixAdminSortBy) => void;
  onSortOrderChange: (value: SpiritFlixAdminSortOrder) => void;
  onViewModeChange: (value: SpiritFlixAdminViewMode) => void;
}

const sortOptions: Array<{ label: string; value: SpiritFlixAdminSortBy }> = [
  { label: "Name A-Z", value: "title" },
  { label: "Date added", value: "dateAdded" },
  { label: "Date modified", value: "dateModified" },
  { label: "Size", value: "size" },
  { label: "Runtime", value: "runtime" },
  { label: "Folder/path", value: "path" },
];

export function SpiritFlixAdminToolbar({
  includeMetadataFiles,
  loading,
  searchTerm,
  sortBy,
  sortOrder,
  viewMode,
  onIncludeMetadataFilesChange,
  onBatchSmartAnalyze,
  onManage,
  onRefresh,
  onSearchTermChange,
  onSortByChange,
  onSortOrderChange,
  onViewModeChange,
}: SpiritFlixAdminToolbarProps) {
  return (
    <header className="spiritflix-admin-toolbar">
      <p className="spiritflix-admin-toolbar__title">Files</p>
      <label className="spiritflix-admin-search">
        <Search size={18} aria-hidden="true" />
        <input
          aria-label="Search admin media"
          value={searchTerm}
          onChange={(event) => onSearchTermChange(event.target.value)}
          placeholder="Search filenames, folders, extensions"
        />
      </label>
      <label className="spiritflix-admin-select">
        <span>Sort</span>
        <select aria-label="Sort admin media" value={sortBy} onChange={(event) => onSortByChange(event.target.value as SpiritFlixAdminSortBy)}>
          {sortOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      <button
        className="spiritflix-admin-icon-button"
        type="button"
        aria-label={sortOrder === "asc" ? "Sort descending" : "Sort ascending"}
        onClick={() => onSortOrderChange(sortOrder === "asc" ? "desc" : "asc")}
      >
        {sortOrder === "asc" ? <ArrowDownAZ size={18} aria-hidden="true" /> : <ArrowUpAZ size={18} aria-hidden="true" />}
      </button>
      <div className="spiritflix-admin-view-toggle" role="group" aria-label="Admin view mode">
        <button className={viewMode === "grid" ? "is-active" : ""} type="button" aria-label="Grid view" onClick={() => onViewModeChange("grid")}>
          <Grid2X2 size={18} aria-hidden="true" />
        </button>
        <button className={viewMode === "list" ? "is-active" : ""} type="button" aria-label="List view" onClick={() => onViewModeChange("list")}>
          <List size={18} aria-hidden="true" />
        </button>
      </div>
      <label className="spiritflix-admin-check">
        <input type="checkbox" checked={includeMetadataFiles} onChange={(event) => onIncludeMetadataFilesChange(event.target.checked)} />
        <FileJson size={17} aria-hidden="true" />
        Show metadata
      </label>
      <button
        className="spiritflix-admin-manage-action"
        type="button"
        aria-label="Batch smart analyze"
        onClick={onBatchSmartAnalyze}
      >
        <Sparkles size={17} aria-hidden="true" />
        Batch smart
      </button>
      <button
        className="spiritflix-admin-manage-action"
        type="button"
        disabled={SPIRITFLIX_ADMIN_LEVEL2_GATED}
        title={SPIRITFLIX_ADMIN_LEVEL2_GATED ? SPIRITFLIX_ADMIN_LEVEL2_GATE_MESSAGE : "Preview and confirm guarded file actions"}
        aria-label="Manage"
        onClick={onManage}
      >
        <Upload size={17} aria-hidden="true" />
        Manage
      </button>
      <button className="spiritflix-admin-icon-button" type="button" aria-label="Refresh admin listing" onClick={onRefresh}>
        <RefreshCw className={loading ? "is-spinning" : ""} size={18} aria-hidden="true" />
      </button>
    </header>
  );
}
