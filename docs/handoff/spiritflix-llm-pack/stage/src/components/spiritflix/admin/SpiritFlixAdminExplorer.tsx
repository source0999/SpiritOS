"use client";

import type { SpiritFlixAdminItem } from "@/lib/spiritflix/admin/types";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import { SpiritFlixAdminBreadcrumbs } from "./SpiritFlixAdminBreadcrumbs";
import { SpiritFlixAdminTable } from "./SpiritFlixAdminTable";
import type { SpiritFlixAdminMenuActionId } from "./item-menu";
import type { SpiritFlixAdminViewMode } from "./SpiritFlixAdminToolbar";

interface SpiritFlixAdminExplorerProps {
  currentPath: string;
  items: SpiritFlixAdminItem[];
  jellyfinClient?: JellyfinClient;
  loading: boolean;
  selectedItem: SpiritFlixAdminItem | null;
  serverImageProxy?: boolean;
  viewMode: SpiritFlixAdminViewMode;
  scrollRef?: React.RefObject<HTMLElement | null>;
  onBrowsePath: (path: string) => void;
  onSelectItem: (item: SpiritFlixAdminItem | null) => void;
  onMenuAction: (actionId: SpiritFlixAdminMenuActionId, item: SpiritFlixAdminItem | null) => void;
}

export function SpiritFlixAdminExplorer({
  currentPath,
  items,
  jellyfinClient,
  loading,
  selectedItem,
  serverImageProxy,
  viewMode,
  scrollRef,
  onBrowsePath,
  onSelectItem,
  onMenuAction,
}: SpiritFlixAdminExplorerProps) {
  return (
    <section ref={scrollRef} className={`spiritflix-admin-explorer is-${viewMode}`} aria-label="SpiritFlix files">
      <SpiritFlixAdminBreadcrumbs path={currentPath} onBrowsePath={onBrowsePath} />
      <SpiritFlixAdminTable
        items={items}
        jellyfinClient={jellyfinClient}
        loading={loading}
        selectedItem={selectedItem}
        serverImageProxy={serverImageProxy}
        viewMode={viewMode}
        onBrowsePath={onBrowsePath}
        onSelectItem={onSelectItem}
        onMenuAction={onMenuAction}
      />
    </section>
  );
}
