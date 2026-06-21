"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix-types";

interface SpiritFlixImageProps {
  client: JellyfinClient;
  item: JellyfinItem;
  type?: "Primary" | "Backdrop" | "Thumb";
  width?: number;
  alt?: string;
  className?: string;
  fallback?: ReactNode;
  onLoad?: () => void;
}

const MAX_IMAGE_REQUESTS = 6;
let activeImageRequests = 0;
const imageQueue: Array<() => void> = [];

async function withImageRequestLimit<T>(task: () => Promise<T>): Promise<T> {
  if (activeImageRequests >= MAX_IMAGE_REQUESTS) {
    await new Promise<void>((resolve) => imageQueue.push(resolve));
  }
  activeImageRequests += 1;
  try {
    return await task();
  } finally {
    activeImageRequests = Math.max(0, activeImageRequests - 1);
    imageQueue.shift()?.();
  }
}

function imageFallbackOrder(type: "Primary" | "Backdrop" | "Thumb"): Array<"Primary" | "Backdrop" | "Thumb"> {
  if (type === "Thumb") return ["Thumb", "Primary", "Backdrop"];
  if (type === "Backdrop") return ["Backdrop", "Thumb", "Primary"];
  return ["Primary", "Thumb", "Backdrop"];
}

export function SpiritFlixImage({
  client,
  item,
  type = "Primary",
  width = 500,
  alt = "",
  className,
  fallback,
  onLoad,
}: SpiritFlixImageProps) {
  const [src, setSrc] = useState("");
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let alive = true;
    let objectUrl = "";

    async function loadImage() {
      setFailed(false);
      setSrc("");

      for (const imageType of imageFallbackOrder(type)) {
        try {
          const nextSrc = await withImageRequestLimit(() => client.getImageObjectUrl(item, imageType, width));
          if (alive) {
            objectUrl = nextSrc;
            setSrc(nextSrc);
            return;
          }
          URL.revokeObjectURL(nextSrc);
          return;
        } catch {
          // Try the next Jellyfin image type before falling back to the letter tile.
        }
      }

      if (alive) setFailed(true);
    }

    void loadImage();

    return () => {
      alive = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [client, item, type, width]);

  if (failed || !src) {
    if (fallback) return fallback;
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
      onLoad={onLoad}
    />
  );
}
