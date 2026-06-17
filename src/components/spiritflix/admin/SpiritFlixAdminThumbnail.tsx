"use client";

import Image from "next/image";
import { useEffect, useMemo, useState } from "react";
import { FileJson, FileVideo, Folder, Play } from "lucide-react";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { SpiritFlixAdminItem } from "@/lib/spiritflix/admin/types";
import { SpiritFlixImage } from "../SpiritFlixImage";

export type SpiritFlixAdminThumbnailSource = "jellyfin" | "local" | "fallback";

interface SpiritFlixAdminThumbnailProps {
  client?: JellyfinClient;
  item: SpiritFlixAdminItem;
  compact?: boolean;
  serverImageProxy?: boolean;
  onSourceChange?: (source: SpiritFlixAdminThumbnailSource) => void;
}

type ThumbnailStage = "jellyfin-client" | "jellyfin-server" | "local" | "fallback";

function fallbackIcon(item: SpiritFlixAdminItem) {
  if (item.type === "folder") return <Folder size={28} aria-hidden="true" />;
  if (item.extension?.includes("json")) return <FileJson size={24} aria-hidden="true" />;
  if (item.playable) return <Play size={26} aria-hidden="true" />;
  return <FileVideo size={24} aria-hidden="true" />;
}

function imageTagForItem(item: SpiritFlixAdminItem): string | undefined {
  if (!item.jellyfinItem || !item.imageType) return undefined;
  if (item.imageType === "Backdrop") return item.jellyfinItem.BackdropImageTags?.[0];
  return item.jellyfinItem.ImageTags?.[item.imageType];
}

function stageToSource(stage: ThumbnailStage): SpiritFlixAdminThumbnailSource {
  if (stage === "jellyfin-client" || stage === "jellyfin-server") return "jellyfin";
  if (stage === "local") return "local";
  return "fallback";
}

function AdminServerImage({
  alt,
  compact,
  item,
  onFailed,
}: {
  alt: string;
  compact: boolean;
  item: SpiritFlixAdminItem;
  onFailed: () => void;
}) {
  const [failed, setFailed] = useState(false);
  const width = compact ? 96 : 360;
  const itemId = item.jellyfinItemId ?? item.jellyfinId;
  const tag = imageTagForItem(item);

  useEffect(() => {
    if (failed) onFailed();
  }, [failed, onFailed]);

  if (!itemId || !item.imageType || failed) {
    return <span className="spiritflix-admin-thumbnail__fallback">{fallbackIcon(item)}</span>;
  }

  const query = new URLSearchParams({
    itemId,
    type: item.imageType,
    width: String(width),
    ...(tag ? { tag } : {}),
  });

  return (
    <Image
      src={`/api/spiritflix/admin/image?${query.toString()}`}
      alt={alt}
      loading="lazy"
      width={width}
      height={Math.round(width * 1.5)}
      unoptimized
      onError={() => setFailed(true)}
    />
  );
}

function LocalVideoThumbnail({
  alt,
  compact,
  item,
  onFailed,
}: {
  alt: string;
  compact: boolean;
  item: SpiritFlixAdminItem;
  onFailed: () => void;
}) {
  const [failed, setFailed] = useState(false);
  const width = compact ? 96 : 360;

  useEffect(() => {
    if (failed) onFailed();
  }, [failed, onFailed]);

  if (!item.path || failed) {
    return <span className="spiritflix-admin-thumbnail__fallback">{fallbackIcon(item)}</span>;
  }

  const query = new URLSearchParams({ path: item.path });

  return (
    <Image
      src={`/api/spiritflix/admin/thumbnail?${query.toString()}`}
      alt={alt}
      loading="lazy"
      width={width}
      height={Math.round(width * 0.56)}
      unoptimized
      data-thumbnail-source="local"
      onError={() => setFailed(true)}
    />
  );
}

export function SpiritFlixAdminThumbnail({ client, item, compact = false, serverImageProxy = false, onSourceChange }: SpiritFlixAdminThumbnailProps) {
  const canShowJellyfinImage =
    Boolean(item.jellyfinItem) &&
    Boolean(item.imageType) &&
    item.imageStatus === "available" &&
    item.type !== "folder";

  const canUseClientImage = canShowJellyfinImage && Boolean(client);
  const canUseServerImage = canShowJellyfinImage && serverImageProxy && Boolean(item.jellyfinItemId ?? item.jellyfinId);
  const canUseLocalThumbnail = item.playable && Boolean(item.path) && item.type !== "folder";

  const initialStage = useMemo<ThumbnailStage>(() => {
    if (canUseClientImage) return "jellyfin-client";
    if (canUseServerImage) return "jellyfin-server";
    if (canUseLocalThumbnail) return "local";
    return "fallback";
  }, [canUseClientImage, canUseLocalThumbnail, canUseServerImage, item.id]);

  const [stage, setStage] = useState<ThumbnailStage>(initialStage);

  useEffect(() => {
    setStage(initialStage);
  }, [initialStage]);

  const source = stageToSource(stage);

  useEffect(() => {
    onSourceChange?.(source);
  }, [onSourceChange, source]);

  const advanceFromJellyfin = () => {
    setStage(canUseLocalThumbnail ? "local" : "fallback");
  };

  const showPlayBadge = item.playable && source !== "fallback";

  let body: React.ReactNode;
  if (stage === "jellyfin-client" && client && item.jellyfinItem && item.imageType) {
    body = (
      <SpiritFlixImage
        client={client}
        item={item.jellyfinItem}
        type={item.imageType}
        width={compact ? 96 : 360}
        alt={item.name}
        fallback={
          canUseLocalThumbnail ? (
            <LocalVideoThumbnail alt={item.name} compact={compact} item={item} onFailed={() => setStage("fallback")} />
          ) : (
            <span className="spiritflix-admin-thumbnail__fallback">{fallbackIcon(item)}</span>
          )
        }
      />
    );
  } else if (stage === "jellyfin-server") {
    body = <AdminServerImage alt={item.name} compact={compact} item={item} onFailed={advanceFromJellyfin} />;
  } else if (stage === "local") {
    body = <LocalVideoThumbnail alt={item.name} compact={compact} item={item} onFailed={() => setStage("fallback")} />;
  } else {
    body = <span className="spiritflix-admin-thumbnail__fallback">{fallbackIcon(item)}</span>;
  }

  return (
    <span
      className={`spiritflix-admin-thumbnail${compact ? " is-compact" : ""}${source !== "fallback" ? " has-image" : ""}`}
      data-image-status={item.imageStatus ?? "missing"}
      data-match={item.jellyfinMatchedBy ?? "none"}
      data-thumbnail-source={source}
    >
      {body}
      {showPlayBadge ? (
        <span className="spiritflix-admin-thumbnail__play" aria-hidden="true">
          <Play size={compact ? 13 : 17} />
        </span>
      ) : null}
    </span>
  );
}
