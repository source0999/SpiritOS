"use client";

import { Info, Play } from "lucide-react";
import { isPlayableItem, type JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import { getResumeProgressPercent, getResumeSlotLabel, hasResumeProgress } from "@/lib/spiritflix-resume";
import type { FaceOrganizerVideoMatch, JellyfinItem } from "@/lib/spiritflix-types";
import { SpiritFlixImage } from "./SpiritFlixImage";

export interface SpiritFlixReadinessState {
  state: "queued" | "scanning" | "matching" | "converting" | "moving" | "ready" | "needs_review" | "failed";
  jobId: string;
  playable: boolean;
}

interface SpiritFlixCardProps {
  client: JellyfinClient;
  item: JellyfinItem;
  variant?: "poster" | "landscape";
  showResume?: boolean;
  faceMatch?: FaceOrganizerVideoMatch;
  modelName?: string;
  playOnPrimaryTap?: boolean;
  imagePriority?: boolean;
  readiness?: SpiritFlixReadinessState;
  onOpenDetails: (item: JellyfinItem) => void;
  onPlay: (item: JellyfinItem, startPositionTicks?: number) => void;
}

export function SpiritFlixCard({
  client,
  item,
  variant = "poster",
  showResume = true,
  faceMatch,
  modelName,
  playOnPrimaryTap = false,
  imagePriority = false,
  readiness,
  onOpenDetails,
  onPlay,
}: SpiritFlixCardProps) {
  const progress = getResumeProgressPercent(item);
  const hasProgress = showResume && hasResumeProgress(item);
  const canPlay = isPlayableItem(item) && (!readiness || readiness.playable);
  const readinessLabel = readiness?.state.replace("_", " ");
  const blocksPlayback = Boolean(readiness && !readiness.playable);
  const imageType = variant === "landscape" ? "Thumb" : "Primary";
  const resumeTicks = item.UserData?.PlaybackPositionTicks;

  return (
    <article className={`spiritflix-card spiritflix-card--${variant}`}>
      <button
        className="spiritflix-card__poster"
        type="button"
        onClick={() => {
          if (playOnPrimaryTap && canPlay) {
            onPlay(item, hasProgress ? resumeTicks : undefined);
          } else {
            onOpenDetails(item);
          }
        }}
      >
        <SpiritFlixImage
          client={client}
          item={item}
          type={imageType}
          width={variant === "landscape" ? 520 : 420}
          alt={item.Name}
          priority={imagePriority}
        />
        <span className="spiritflix-card__veil" />
        {progress > 0 ? (
          <span className="spiritflix-card__progress">
            <span style={{ width: `${Math.min(100, progress)}%` }} />
          </span>
        ) : null}
        {faceMatch ? (
          <span className={`spiritflix-face-badge spiritflix-card__face-badge is-${faceMatch.status}`}>
            {faceMatch.status === "confirmed"
              ? `Identified: ${faceMatch.primaryPerformer?.name ?? modelName ?? "Performer"} (${Math.round((faceMatch.confidence ?? 0) * 100)}%)`
              : faceMatch.label}
          </span>
        ) : null}
        {readiness ? (
          <span className={`spiritflix-card__readiness-badge is-${readiness.state}`}>{readinessLabel}</span>
        ) : null}
        {blocksPlayback ? <span className="spiritflix-card__processing-overlay">Still processing</span> : null}
        {hasProgress ? <span className="spiritflix-card__resume-badge">Resume</span> : null}
      </button>
      <div className="spiritflix-card__meta">
        <h3>{item.Name}</h3>
        <p>{modelName ?? (hasProgress ? getResumeSlotLabel(item) : [item.ProductionYear, item.Type].filter(Boolean).join(" / "))}</p>
      </div>
      <div className="spiritflix-card__actions">
        {canPlay ? (
          <button
            type="button"
            onClick={() => onPlay(item, hasProgress ? resumeTicks : undefined)}
            aria-label={`${hasProgress ? "Resume" : "Play"} ${item.Name}`}
          >
            <Play size={17} aria-hidden="true" />
          </button>
        ) : null}
        <button type="button" onClick={() => onOpenDetails(item)} aria-label={`Open details for ${item.Name}`}>
          <Info size={17} aria-hidden="true" />
        </button>
      </div>
    </article>
  );
}
