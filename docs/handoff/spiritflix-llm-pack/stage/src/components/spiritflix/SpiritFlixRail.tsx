"use client";

import { useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix-types";
import { SpiritFlixCard } from "./SpiritFlixCard";

interface SpiritFlixRailProps {
  title: string;
  variant?: "poster" | "landscape";
  client: JellyfinClient;
  items: JellyfinItem[];
  emptyText: string;
  playOnPrimaryTap?: boolean;
  onOpenDetails: (item: JellyfinItem) => void;
  onPlay: (item: JellyfinItem, queueItems?: JellyfinItem[], sourceTitle?: string, startPositionTicks?: number) => void;
}

export function SpiritFlixRail({
  title,
  variant = "poster",
  client,
  items,
  emptyText,
  playOnPrimaryTap = false,
  onOpenDetails,
  onPlay,
}: SpiritFlixRailProps) {
  const trackRef = useRef<HTMLDivElement | null>(null);

  const scroll = (direction: "left" | "right") => {
    const track = trackRef.current;
    if (!track) return;
    track.scrollBy({ left: direction === "left" ? -520 : 520, behavior: "smooth" });
  };

  return (
    <section className={`spiritflix-rail spiritflix-rail--${variant}`}>
      <div className="spiritflix-rail__header">
        <h2>{title}</h2>
        {items.length ? (
          <div className="spiritflix-rail__controls" aria-hidden="true">
            <button type="button" onClick={() => scroll("left")} tabIndex={-1}>
              <ChevronLeft size={17} />
            </button>
            <button type="button" onClick={() => scroll("right")} tabIndex={-1}>
              <ChevronRight size={17} />
            </button>
          </div>
        ) : null}
      </div>
      {items.length ? (
        <div className="spiritflix-rail__track" ref={trackRef}>
          {items.map((item) => (
            <SpiritFlixCard
              key={item.Id}
              variant={variant}
              client={client}
              item={item}
              playOnPrimaryTap={playOnPrimaryTap}
              onOpenDetails={onOpenDetails}
              onPlay={(selectedItem, startPositionTicks) => onPlay(selectedItem, items, title, startPositionTicks)}
            />
          ))}
        </div>
      ) : (
        <p className="spiritflix-empty">{emptyText}</p>
      )}
    </section>
  );
}
