"use client";

import { useCallback, useState } from "react";
import { Heart, Star } from "lucide-react";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import { formatBytes, formatItemDateLabel } from "@/lib/spiritflix/admin/format";
import type { SpiritFlixAdminItem } from "@/lib/spiritflix/admin/types";
import { SpiritFlixAdminContextMenu } from "./SpiritFlixAdminContextMenu";
import { SpiritFlixAdminItemMenuButton } from "./SpiritFlixAdminItemMenuButton";
import { buildItemMenuItems, type SpiritFlixAdminMenuActionId } from "./item-menu";
import type { SpiritFlixAdminViewMode } from "./SpiritFlixAdminToolbar";
import { SpiritFlixAdminThumbnail } from "./SpiritFlixAdminThumbnail";

interface SpiritFlixAdminTableProps {
  items: SpiritFlixAdminItem[];
  jellyfinClient?: JellyfinClient;
  loading: boolean;
  selectedItem: SpiritFlixAdminItem | null;
  serverImageProxy?: boolean;
  viewMode: SpiritFlixAdminViewMode;
  onBrowsePath: (path: string) => void;
  onSelectItem: (item: SpiritFlixAdminItem | null) => void;
  onMenuAction: (actionId: SpiritFlixAdminMenuActionId, item: SpiritFlixAdminItem | null) => void;
}

function cardMeta(item: SpiritFlixAdminItem): string {
  const date = formatItemDateLabel(item);
  const parts: string[] = [];

  if (item.type === "folder") {
    if (date.text) parts.push(`${date.label} ${date.text}`.trim());
    return parts.join(" · ");
  }

  if (date.text) parts.push(`${date.label} ${date.text}`.trim());
  const size = formatBytes(item.sizeBytes);
  if (size) parts.push(size);

  return parts.join(" · ");
}

export function SpiritFlixAdminTable({
  items,
  jellyfinClient,
  loading,
  selectedItem,
  serverImageProxy,
  viewMode,
  onBrowsePath,
  onSelectItem,
  onMenuAction,
}: SpiritFlixAdminTableProps) {
  const [openMenuItemId, setOpenMenuItemId] = useState<string | null>(null);
  const [menuPosition, setMenuPosition] = useState<{ x: number; y: number } | null>(null);
  const [contextItem, setContextItem] = useState<SpiritFlixAdminItem | null>(null);

  const closeMenu = useCallback(() => {
    setOpenMenuItemId(null);
    setMenuPosition(null);
    setContextItem(null);
  }, []);

  const openContextMenu = useCallback((event: React.MouseEvent, item: SpiritFlixAdminItem) => {
    event.preventDefault();
    event.stopPropagation();
    onSelectItem(item);
    setContextItem(item);
    setOpenMenuItemId(null);
    setMenuPosition({ x: event.clientX, y: event.clientY });
  }, [onSelectItem]);

  const handleCardClick = useCallback(
    (item: SpiritFlixAdminItem) => {
      onSelectItem(item);
    },
    [onSelectItem],
  );

  const handleCardDoubleClick = useCallback(
    (item: SpiritFlixAdminItem) => {
      if (item.type === "folder" && item.path) {
        onBrowsePath(item.path);
        return;
      }
      if (item.jellyfinItemId || item.jellyfinId) {
        window.location.assign(`/spiritflix?item=${encodeURIComponent(item.jellyfinItemId ?? item.jellyfinId ?? "")}`);
      }
    },
    [onBrowsePath],
  );

  if (loading) {
    return <div className="spiritflix-admin-empty">Loading files...</div>;
  }

  if (!items.length) {
    return <div className="spiritflix-admin-empty">No files or folders here.</div>;
  }

  const contextMenuItems = contextItem ? buildItemMenuItems(contextItem, "") : [];

  return (
    <div className={`spiritflix-admin-items is-${viewMode}`}>
      <table className="spiritflix-admin-table" aria-hidden={viewMode === "grid"}>
        <thead>
          <tr>
            <th>Name</th>
            <th>Library</th>
            <th>Type</th>
            <th>Size</th>
            <th>Date</th>
            <th>State</th>
            <th aria-label="Actions" />
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const date = formatItemDateLabel(item);
            const menuItems = buildItemMenuItems(item, "");
            const menuOpen = openMenuItemId === item.id && viewMode === "list";
            return (
              <tr
                className={selectedItem?.id === item.id ? "is-selected" : ""}
                data-testid="admin-item-row"
                key={item.id}
                onClick={() => handleCardClick(item)}
                onContextMenu={(event) => openContextMenu(event, item)}
                onDoubleClick={() => handleCardDoubleClick(item)}
              >
                <td>
                  <div className="spiritflix-admin-name-button">
                    <SpiritFlixAdminThumbnail compact client={jellyfinClient} item={item} serverImageProxy={serverImageProxy} />
                    <span>{item.name}</span>
                  </div>
                </td>
                <td>{item.libraryName ?? ""}</td>
                <td>{item.itemType ?? item.type}</td>
                <td>{formatBytes(item.sizeBytes)}</td>
                <td>{date.text ? `${date.label} ${date.text}`.trim() : ""}</td>
                <td>
                  <span className="spiritflix-admin-state-icons">
                    {item.watched ? <Star size={15} aria-label="Watched" /> : null}
                    {item.favorite ? <Heart size={15} aria-label="Favorite" /> : null}
                  </span>
                </td>
                <td>
                  <SpiritFlixAdminItemMenuButton
                    itemLabel={item.name}
                    items={menuItems}
                    open={menuOpen}
                    position={menuOpen ? menuPosition : null}
                    onClose={closeMenu}
                    onOpen={(position) => {
                      onSelectItem(item);
                      setContextItem(null);
                      setOpenMenuItemId(item.id);
                      setMenuPosition(position);
                    }}
                    onSelect={(actionId) => onMenuAction(actionId, item)}
                  />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <div
        className="spiritflix-admin-card-list"
        aria-hidden={viewMode === "list"}
        onContextMenu={(event) => {
          if ((event.target as HTMLElement).closest("[data-testid='admin-item-card']")) return;
          event.preventDefault();
        }}
      >
        {items.map((item) => {
          const menuItems = buildItemMenuItems(item, "");
          const menuOpen = openMenuItemId === item.id && viewMode === "grid";
          return (
            <div
              className={`spiritflix-admin-card${selectedItem?.id === item.id ? " is-selected" : ""}`}
              data-testid="admin-item-card"
              data-image-status={item.imageStatus ?? "missing"}
              data-jellyfin-match={item.jellyfinMatchedBy ?? "none"}
              key={item.id}
              role="button"
              tabIndex={0}
              title={item.path}
              onClick={() => handleCardClick(item)}
              onContextMenu={(event) => openContextMenu(event, item)}
              onDoubleClick={() => handleCardDoubleClick(item)}
              onKeyDown={(event) => {
                if (event.key === "Enter") handleCardDoubleClick(item);
                if (event.key === " ") {
                  event.preventDefault();
                  handleCardClick(item);
                }
              }}
            >
              <SpiritFlixAdminThumbnail client={jellyfinClient} item={item} serverImageProxy={serverImageProxy} />
              <span className="spiritflix-admin-card-title">{item.name}</span>
              <span className="spiritflix-admin-card-meta">{cardMeta(item)}</span>
              <SpiritFlixAdminItemMenuButton
                itemLabel={item.name}
                items={menuItems}
                open={menuOpen}
                position={menuOpen ? menuPosition : null}
                onClose={closeMenu}
                onOpen={(position) => {
                  onSelectItem(item);
                  setContextItem(null);
                  setOpenMenuItemId(item.id);
                  setMenuPosition(position);
                }}
                onSelect={(actionId) => onMenuAction(actionId, item)}
              />
            </div>
          );
        })}
      </div>

      {contextItem && menuPosition && !openMenuItemId ? (
        <SpiritFlixAdminContextMenu
          items={contextMenuItems}
          position={menuPosition}
          onClose={closeMenu}
          onSelect={(actionId) => onMenuAction(actionId, contextItem)}
        />
      ) : null}
    </div>
  );
}
