"use client";

import { useEffect, useLayoutEffect, useRef } from "react";
import type { SpiritFlixAdminMenuItemDef } from "./item-menu";

export interface SpiritFlixAdminContextMenuPosition {
  x: number;
  y: number;
}

interface SpiritFlixAdminContextMenuProps {
  items: SpiritFlixAdminMenuItemDef[];
  position: SpiritFlixAdminContextMenuPosition;
  onSelect: (id: SpiritFlixAdminMenuItemDef["id"]) => void;
  onClose: () => void;
}

export function SpiritFlixAdminContextMenu({ items, position, onSelect, onClose }: SpiritFlixAdminContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const activatedRef = useRef(false);

  useLayoutEffect(() => {
    const node = menuRef.current;
    if (!node) return;
    const rect = node.getBoundingClientRect();
    const padding = 8;
    let left = position.x;
    let top = position.y;
    if (left + rect.width > window.innerWidth - padding) {
      left = Math.max(padding, window.innerWidth - rect.width - padding);
    }
    if (top + rect.height > window.innerHeight - padding) {
      top = Math.max(padding, window.innerHeight - rect.height - padding);
    }
    node.style.left = `${left}px`;
    node.style.top = `${top}px`;
  }, [position.x, position.y, items]);

  useEffect(() => {
    activatedRef.current = false;

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    function onPointerDown(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        onClose();
      }
    }

    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("mousedown", onPointerDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("mousedown", onPointerDown);
    };
  }, [onClose]);

  function activateItem(menuItemId: SpiritFlixAdminMenuItemDef["id"]) {
    if (activatedRef.current) return;
    activatedRef.current = true;
    onSelect(menuItemId);
    onClose();
  }

  return (
    <div
      ref={menuRef}
      className="spiritflix-admin-context-menu"
      role="menu"
      aria-label="File actions"
      style={{ left: position.x, top: position.y }}
      onMouseDown={(event) => event.stopPropagation()}
    >
      {items.map((item) => (
        <button
          key={item.id}
          className={item.destructive ? "is-destructive" : ""}
          role="menuitem"
          type="button"
          onMouseDown={(event) => {
            event.preventDefault();
            event.stopPropagation();
            if (event.button !== 0) return;
            activateItem(item.id);
          }}
          onClick={(event) => {
            event.preventDefault();
            event.stopPropagation();
            activateItem(item.id);
          }}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
