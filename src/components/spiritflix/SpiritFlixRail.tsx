"use client";

import type { JellyfinClient } from "@/lib/spiritflix/jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix/types";
import { SpiritFlixCard } from "./SpiritFlixCard";

interface SpiritFlixRailProps {
  title: string;
  client: JellyfinClient;
  items: JellyfinItem[];
  emptyText: string;
  onOpenDetails: (item: JellyfinItem) => void;
  onPlay: (item: JellyfinItem) => void;
}

export function SpiritFlixRail({
  title,
  client,
  items,
  emptyText,
  onOpenDetails,
  onPlay,
}: SpiritFlixRailProps) {
  return (
    <section className="spiritflix-rail">
      <h2>{title}</h2>
      {items.length ? (
        <div className="spiritflix-rail__track">
          {items.map((item) => (
            <SpiritFlixCard
              key={item.Id}
              client={client}
              item={item}
              onOpenDetails={onOpenDetails}
              onPlay={onPlay}
            />
          ))}
        </div>
      ) : (
        <p className="spiritflix-empty">{emptyText}</p>
      )}
    </section>
  );
}
