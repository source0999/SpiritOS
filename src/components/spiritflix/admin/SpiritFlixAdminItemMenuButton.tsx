"use client";

import { MoreVertical } from "lucide-react";
import type { SpiritFlixAdminMenuItemDef } from "./item-menu";
import { SpiritFlixAdminContextMenu, type SpiritFlixAdminContextMenuPosition } from "./SpiritFlixAdminContextMenu";

interface SpiritFlixAdminItemMenuButtonProps {
  itemLabel: string;
  items: SpiritFlixAdminMenuItemDef[];
  open: boolean;
  position: SpiritFlixAdminContextMenuPosition | null;
  onOpen: (position: SpiritFlixAdminContextMenuPosition) => void;
  onClose: () => void;
  onSelect: (id: SpiritFlixAdminMenuItemDef["id"]) => void;
}

export function SpiritFlixAdminItemMenuButton({
  itemLabel,
  items,
  open,
  position,
  onOpen,
  onClose,
  onSelect,
}: SpiritFlixAdminItemMenuButtonProps) {
  return (
    <>
      <button
        className="spiritflix-admin-card-menu"
        type="button"
        aria-label={`Actions for ${itemLabel}`}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={(event) => {
          event.stopPropagation();
          const rect = (event.currentTarget as HTMLButtonElement).getBoundingClientRect();
          onOpen({ x: rect.right - 4, y: rect.bottom + 4 });
        }}
        onContextMenu={(event) => {
          event.preventDefault();
          event.stopPropagation();
        }}
      >
        <MoreVertical size={16} aria-hidden="true" />
      </button>
      {open && position ? (
        <SpiritFlixAdminContextMenu items={items} position={position} onSelect={onSelect} onClose={onClose} />
      ) : null}
    </>
  );
}
