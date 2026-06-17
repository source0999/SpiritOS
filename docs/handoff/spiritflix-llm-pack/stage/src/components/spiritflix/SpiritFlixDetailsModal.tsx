"use client";

import { Calendar, Clock, Heart, Play, RotateCcw, X } from "lucide-react";
import { formatRuntime, isPlayableItem, type JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import { getResumeSlotLabel, hasResumeProgress } from "@/lib/spiritflix-resume";
import type { JellyfinItem } from "@/lib/spiritflix-types";
import { SpiritFlixImage } from "./SpiritFlixImage";

interface SpiritFlixDetailsModalProps {
  client: JellyfinClient;
  item: JellyfinItem;
  onClose: () => void;
  onPlay: (item: JellyfinItem) => void;
}

export function SpiritFlixDetailsModal({ client, item, onClose, onPlay }: SpiritFlixDetailsModalProps) {
  const progress = item.UserData?.PlayedPercentage ?? 0;
  const hasProgress = hasResumeProgress(item);
  const canPlay = isPlayableItem(item);

  return (
    <div className="spiritflix-modal" role="dialog" aria-modal="true" aria-label={`${item.Name} details`}>
      <div className="spiritflix-modal__scrim" onClick={onClose} />
      <section className="spiritflix-modal__panel">
        <div className="spiritflix-modal__glow" />
        <button className="spiritflix-modal__close" type="button" onClick={onClose} aria-label="Close details">
          <X size={20} aria-hidden="true" />
        </button>
        <div className="spiritflix-modal__media">
          <SpiritFlixImage client={client} item={item} type="Backdrop" width={1200} className="spiritflix-modal__backdrop" />
          <div className="spiritflix-modal__fade" />
        </div>
        <div className="spiritflix-modal__content">
          <div className="spiritflix-modal__layout">
            <div className="spiritflix-modal__poster">
              <SpiritFlixImage client={client} item={item} type="Primary" width={340} alt={item.Name} />
            </div>
            <div className="spiritflix-modal__copy">
              <span className="spiritflix-modal__type">{item.Type}</span>
              <h2>{item.Name}</h2>
              <div className="spiritflix-modal__facts">
                <span>
                  <Calendar size={14} aria-hidden="true" />
                  {item.ProductionYear ?? "Unknown year"}
                </span>
                <span>
                  <Clock size={14} aria-hidden="true" />
                  {formatRuntime(item.RunTimeTicks)}
                </span>
                <span>{item.UserData?.Played ? "Played" : "Unplayed"}</span>
                {item.UserData?.IsFavorite ? (
                  <span className="spiritflix-favorite">
                    <Heart size={14} fill="currentColor" aria-hidden="true" />
                    Favorite
                  </span>
                ) : null}
              </div>
              {progress > 0 ? (
                <div className="spiritflix-modal__progress">
                  <div>
                    <span>{Math.round(progress)}% watched</span>
                    {hasProgress ? <span>{getResumeSlotLabel(item)}</span> : null}
                  </div>
                  <span>
                    <span style={{ width: `${Math.min(100, progress)}%` }} />
                  </span>
                </div>
              ) : null}
              <p>{item.Overview || "No overview is available from Jellyfin for this item."}</p>
              {item.Genres?.length ? (
                <div className="spiritflix-genres">
                  {item.Genres.map((genre) => (
                    <span key={genre}>{genre}</span>
                  ))}
                </div>
              ) : null}
              {canPlay ? (
                <div className="spiritflix-modal__actions">
                  <button className="spiritflix-primary-button" type="button" onClick={() => onPlay(item)}>
                    {hasProgress ? (
                      <RotateCcw size={18} aria-hidden="true" />
                    ) : (
                      <Play size={18} fill="currentColor" aria-hidden="true" />
                    )}
                    {hasProgress ? `Resume from ${getResumeSlotLabel(item).split(" / ")[0]}` : "Play"}
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
