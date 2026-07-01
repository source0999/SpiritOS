"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix-types";
import { SpiritFlixCard } from "./SpiritFlixCard";

interface SpiritFlixRailProps {
  title: string;
  titleMeta?: string;
  variant?: "poster" | "landscape";
  client: JellyfinClient;
  items: JellyfinItem[];
  emptyText: string;
  playOnPrimaryTap?: boolean;
  hasMore?: boolean;
  loadingMore?: boolean;
  onLoadMore?: () => void;
  onTitleClick?: () => void;
  titleActionLabel?: string;
  onOpenDetails: (item: JellyfinItem) => void;
  onPlay: (item: JellyfinItem, queueItems?: JellyfinItem[], sourceTitle?: string, startPositionTicks?: number) => void;
}

export function SpiritFlixRail({
  title,
  titleMeta,
  variant = "poster",
  client,
  items,
  emptyText,
  playOnPrimaryTap = false,
  hasMore = false,
  loadingMore = false,
  onLoadMore,
  onTitleClick,
  titleActionLabel,
  onOpenDetails,
  onPlay,
}: SpiritFlixRailProps) {
  const trackRef = useRef<HTMLDivElement | null>(null);
  const initialWindow = variant === "landscape" ? 6 : 8;
  const windowStep = variant === "landscape" ? 4 : 6;
  const [renderCount, setRenderCount] = useState(initialWindow);
  const visibleItems = useMemo(() => items.slice(0, renderCount), [items, renderCount]);

  useEffect(() => {
    setRenderCount(initialWindow);
  }, [initialWindow, items.length, title]);

  const requestMore = () => {
    setRenderCount((current) => Math.min(items.length, current + windowStep));
    if (hasMore && !loadingMore && renderCount >= items.length - windowStep) {
      onLoadMore?.();
    }
  };

  const handleScroll = () => {
    const track = trackRef.current;
    if (!track) return;
    const remaining = track.scrollWidth - track.scrollLeft - track.clientWidth;
    if (remaining < Math.max(320, track.clientWidth * 0.6)) {
      requestMore();
    }
  };

  const scroll = (direction: "left" | "right") => {
    const track = trackRef.current;
    if (!track) return;
    track.scrollBy({ left: direction === "left" ? -520 : 520, behavior: "smooth" });
    window.setTimeout(requestMore, 120);
  };

  return (
    <section className={`spiritflix-rail spiritflix-rail--${variant}`}>
      <div className="spiritflix-rail__header">
        {onTitleClick ? (
          <button
            type="button"
            className="spiritflix-rail__title-button"
            onClick={onTitleClick}
            aria-label={titleActionLabel ?? `Open ${title}`}
          >
            <span className="spiritflix-rail__title-copy">
              <h2>{title}</h2>
              {titleMeta ? <span className="spiritflix-rail__title-meta">{titleMeta}</span> : null}
            </span>
            <ChevronRight size={18} aria-hidden="true" />
          </button>
        ) : (
          <span className="spiritflix-rail__title-copy">
            <h2>{title}</h2>
            {titleMeta ? <span className="spiritflix-rail__title-meta">{titleMeta}</span> : null}
          </span>
        )}
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
        <div className="spiritflix-rail__track" ref={trackRef} onScroll={handleScroll}>
          {visibleItems.map((item, index) => (
            <SpiritFlixCard
              key={item.Id}
              variant={variant}
              client={client}
              item={item}
              playOnPrimaryTap={playOnPrimaryTap}
              imagePriority={index < (variant === "landscape" ? 2 : 4)}
              onOpenDetails={onOpenDetails}
              onPlay={(selectedItem, startPositionTicks) => onPlay(selectedItem, items, title, startPositionTicks)}
            />
          ))}
          {renderCount < items.length || hasMore ? (
            <button
              type="button"
              className="spiritflix-rail__load-more"
              onClick={requestMore}
              disabled={loadingMore}
            >
              {loadingMore ? "Loading..." : "Load more"}
            </button>
          ) : null}
        </div>
      ) : (
        <p className="spiritflix-empty">{emptyText}</p>
      )}
    </section>
  );
}
