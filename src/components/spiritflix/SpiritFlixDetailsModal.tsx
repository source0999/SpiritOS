"use client";

import { Heart, Play, Shuffle, X } from "lucide-react";
import { formatRuntime, isPlaylistItem, type JellyfinClient } from "@/lib/spiritflix/jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix/types";
import { SpiritFlixImage } from "./SpiritFlixImage";

interface SpiritFlixDetailsModalProps {
  client: JellyfinClient;
  item: JellyfinItem;
  onClose: () => void;
  onPlay: (item: JellyfinItem) => void;
}

export function SpiritFlixDetailsModal({ client, item, onClose, onPlay }: SpiritFlixDetailsModalProps) {
  const isPlaylist = isPlaylistItem(item);

  return (
    <div className="spiritflix-modal" role="dialog" aria-modal="true" aria-label={`${item.Name} details`}>
      <div className="spiritflix-modal__scrim" onClick={onClose} />
      <section className="spiritflix-modal__panel">
        <button className="spiritflix-modal__close" type="button" onClick={onClose} aria-label="Close details">
          <X size={20} aria-hidden="true" />
        </button>
        <SpiritFlixImage client={client} item={item} type="Backdrop" width={1200} className="spiritflix-modal__backdrop" />
        <div className="spiritflix-modal__content">
          <h2>{item.Name}</h2>
          <div className="spiritflix-modal__facts">
            <span>{item.ProductionYear ?? "Unknown year"}</span>
            <span>{formatRuntime(item.RunTimeTicks)}</span>
            <span>{item.UserData?.Played ? "Played" : "Unplayed"}</span>
            {item.UserData?.IsFavorite ? (
              <span className="spiritflix-favorite">
                <Heart size={14} fill="currentColor" aria-hidden="true" />
                Favorite
              </span>
            ) : null}
          </div>
          <p>{item.Overview || "No overview is available from Jellyfin for this item."}</p>
          {item.Genres?.length ? (
            <div className="spiritflix-genres">
              {item.Genres.map((genre) => (
                <span key={genre}>{genre}</span>
              ))}
            </div>
          ) : null}
          <button className="spiritflix-primary-button" type="button" onClick={() => onPlay(item)}>
            {isPlaylist ? <Shuffle size={18} aria-hidden="true" /> : <Play size={18} aria-hidden="true" />}
            {isPlaylist ? "Shuffle Playlist" : "Play"}
          </button>
        </div>
      </section>
    </div>
  );
}
