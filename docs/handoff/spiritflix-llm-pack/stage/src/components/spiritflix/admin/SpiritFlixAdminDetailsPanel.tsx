"use client";

import { useState } from "react";
import { Copy, ExternalLink, FolderOpen, RefreshCw, X } from "lucide-react";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import { formatItemDateLabel } from "@/lib/spiritflix/admin/format";
import type { SpiritFlixAdminItem } from "@/lib/spiritflix/admin/types";
import { SpiritFlixAdminThumbnail, type SpiritFlixAdminThumbnailSource } from "./SpiritFlixAdminThumbnail";

interface SpiritFlixAdminDetailsPanelProps {
  item: SpiritFlixAdminItem | null;
  jellyfinClient?: JellyfinClient;
  serverImageProxy?: boolean;
  onClose: () => void;
  onBrowsePath: (path: string) => void;
}

function copyText(value?: string) {
  if (!value || typeof navigator === "undefined") return;
  void navigator.clipboard?.writeText(value);
}

function thumbnailStatusLabel(source: SpiritFlixAdminThumbnailSource, item: SpiritFlixAdminItem): string {
  if (source === "jellyfin") return "Jellyfin";
  if (source === "local") return "Local cache";
  if (item.playable) return "Fallback icon";
  if (item.type === "folder") return "Folder icon";
  return "Fallback icon";
}

function jellyfinMatchLabel(item: SpiritFlixAdminItem): string | undefined {
  if (!item.jellyfinMatchedBy || item.jellyfinMatchedBy === "none") return "No Jellyfin match";
  return item.jellyfinMatchedBy;
}

function detailRows(item: SpiritFlixAdminItem, thumbnailSource: SpiritFlixAdminThumbnailSource): Array<[string, string | undefined]> {
  const date = formatItemDateLabel(item);
  return [
    ["Type", item.itemType ?? item.type],
    ["Extension", item.extension],
    ["File size", item.sizeBytes ? `${item.sizeBytes.toLocaleString()} bytes` : undefined],
    [date.label || "Date", date.text || item.dateAdded || item.dateCreated || item.dateModified],
    ["Date created", item.dateCreated],
    ["Date modified", item.dateModified],
    ["Path", item.path],
    ["Parent folder", item.parentPath],
    ["Thumbnail", thumbnailStatusLabel(thumbnailSource, item)],
    ["Jellyfin match", jellyfinMatchLabel(item)],
    ["Jellyfin item ID", item.jellyfinItemId ?? item.jellyfinId],
    ["Duration", item.runtimeTicks ? `${Math.round(item.runtimeTicks / 600000000)} min` : undefined],
    ["Models", item.modelNames?.join(", ")],
  ];
}

export function SpiritFlixAdminDetailsPanel({ item, jellyfinClient, serverImageProxy, onClose, onBrowsePath }: SpiritFlixAdminDetailsPanelProps) {
  const [thumbnailSource, setThumbnailSource] = useState<SpiritFlixAdminThumbnailSource>("fallback");

  if (!item) {
    return null;
  }

  return (
    <div className="spiritflix-admin-details-overlay" role="presentation" onClick={onClose}>
      <aside
        className="spiritflix-admin-details is-open is-overlay"
        aria-label="Admin details"
        role="dialog"
        aria-modal="true"
        onClick={(event) => event.stopPropagation()}
      >
      <div className="spiritflix-admin-details__header">
        <SpiritFlixAdminThumbnail
          client={jellyfinClient}
          item={item}
          serverImageProxy={serverImageProxy}
          onSourceChange={setThumbnailSource}
        />
        <div>
          <p>{item.type}</p>
          <h2>{item.name}</h2>
        </div>
        <button type="button" aria-label="Close details" onClick={onClose}>
          <X size={18} aria-hidden="true" />
        </button>
      </div>
      <div className="spiritflix-admin-detail-actions">
        <button type="button" onClick={() => copyText(item.path)}>
          <Copy size={16} aria-hidden="true" />
          Copy path
        </button>
        <button type="button" onClick={() => copyText(item.name)}>
          <Copy size={16} aria-hidden="true" />
          Copy filename
        </button>
        {item.parentPath ? (
          <button type="button" onClick={() => onBrowsePath(item.parentPath as string)}>
            <FolderOpen size={16} aria-hidden="true" />
            Open folder
          </button>
        ) : null}
        {item.jellyfinItemId || item.jellyfinId ? (
          <a href={`/spiritflix?item=${encodeURIComponent(item.jellyfinItemId ?? item.jellyfinId ?? "")}`}>
            <ExternalLink size={16} aria-hidden="true" />
            Open viewer
          </a>
        ) : null}
        <button type="button" onClick={() => item.parentPath && onBrowsePath(item.parentPath)}>
          <RefreshCw size={16} aria-hidden="true" />
          Refresh listing
        </button>
      </div>
      <dl className="spiritflix-admin-detail-list">
        {detailRows(item, thumbnailSource).map(([label, value]) =>
          value ? (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ) : null,
        )}
      </dl>
      </aside>
    </div>
  );
}
