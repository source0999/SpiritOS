"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import type { JellyfinClient } from "@/lib/spiritflix/jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix/types";

interface SpiritFlixImageProps {
  client: JellyfinClient;
  item: JellyfinItem;
  type?: "Primary" | "Backdrop" | "Thumb";
  width?: number;
  alt?: string;
  className?: string;
}

export function SpiritFlixImage({
  client,
  item,
  type = "Primary",
  width = 500,
  alt = "",
  className,
}: SpiritFlixImageProps) {
  const [src, setSrc] = useState("");
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let alive = true;
    let objectUrl = "";

    client
      .getImageObjectUrl(item, type, width)
      .then((nextSrc) => {
        objectUrl = nextSrc;
        if (alive) {
          setFailed(false);
          setSrc(nextSrc);
        }
      })
      .catch(() => {
        if (alive) setFailed(true);
      });

    return () => {
      alive = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [client, item, type, width]);

  if (failed || !src) {
    return (
      <span className={`spiritflix-image-fallback ${className ?? ""}`} aria-label={alt || item.Name}>
        <span>{item.Name.slice(0, 1).toUpperCase()}</span>
      </span>
    );
  }

  return (
    <Image
      src={src}
      alt={alt}
      className={className}
      loading="lazy"
      width={width}
      height={Math.round(width * 1.5)}
      unoptimized
    />
  );
}
