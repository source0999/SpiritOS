"use client";

import { Info, ListVideo, Play, Shuffle } from "lucide-react";
import { isPlayableItem, isPlaylistItem, type JellyfinClient } from "@/lib/spiritflix/jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix/types";
import { SpiritFlixImage } from "./SpiritFlixImage";

interface SpiritFlixCardProps {
  client: JellyfinClient;
  item: JellyfinItem;
  onOpenDetails: (item: JellyfinItem) => void;
  onPlay: (item: JellyfinItem) => void;
}

export function SpiritFlixCard({ client, item, onOpenDetails, onPlay }: SpiritFlixCardProps) {
  const progress = item.UserData?.PlayedPercentage ?? 0;
  const isPlaylist = isPlaylistItem(item);
  if (isPlaylist) return null;

  const canPlay = isPlayableItem(item) || isPlaylist;

  return (
    <article className="spiritflix-card">
      <button className="spiritflix-card__poster" type="button" onClick={() => onOpenDetails(item)}>
        <SpiritFlixImage client={client} item={item} width={420} alt={item.Name} />
        {progress > 0 ? (
          <span className="spiritflix-card__progress">
            <span style={{ width: `${Math.min(100, progress)}%` }} />
          </span>
        ) : null}
      </button>
      <div className="spiritflix-card__meta">
        <h3>{item.Name}</h3>
        <p>{[item.ProductionYear, item.Type].filter(Boolean).join(" • ")}</p>
      </div>
      <div className="spiritflix-card__actions">
        {canPlay ? (
          <button type="button" onClick={() => onPlay(item)} aria-label={`${isPlaylist ? "Shuffle" : "Play"} ${item.Name}`}>
            {isPlaylist ? <Shuffle size={17} aria-hidden="true" /> : <Play size={17} aria-hidden="true" />}
          </button>
        ) : null}
        <button type="button" onClick={() => onOpenDetails(item)} aria-label={`Open details for ${item.Name}`}>
          {isPlaylist ? <ListVideo size={17} aria-hidden="true" /> : <Info size={17} aria-hidden="true" />}
        </button>
      </div>
    </article>
  );
}
