"use client";

import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";
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
  priority?: boolean;
  rootMargin?: string;
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
  priority = false,
  rootMargin = "640px 320px",
}: SpiritFlixImageProps) {
  const frameRef = useRef<HTMLSpanElement | null>(null);
  const [shouldLoad, setShouldLoad] = useState(priority);
  const [src, setSrc] = useState("");
  const [failed, setFailed] = useState(false);
  const [imageTypeIndex, setImageTypeIndex] = useState(0);
  const availableTypes = useMemo(
    () =>
      imageFallbackOrder(type).filter((imageType) => {
        if (imageType === "Backdrop") return Boolean(item.BackdropImageTags?.length);
        return Boolean(item.ImageTags?.[imageType]);
      }),
    [item.BackdropImageTags, item.ImageTags, type],
  );

  useEffect(() => {
    if (priority || shouldLoad || typeof IntersectionObserver === "undefined") {
      setShouldLoad(true);
      return undefined;
    }

    const node = frameRef.current;
    if (!node) return undefined;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setShouldLoad(true);
          observer.disconnect();
        }
      },
      { rootMargin },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [priority, rootMargin, shouldLoad]);

  useEffect(() => {
    setSrc("");
    setFailed(false);
    setImageTypeIndex(0);
  }, [item.Id, type, width]);

  useEffect(() => {
    if (imageTypeIndex < availableTypes.length) return;
    setImageTypeIndex(0);
  }, [availableTypes.length, imageTypeIndex]);

  useEffect(() => {
    if (!shouldLoad) return;

    const imageType = availableTypes[imageTypeIndex];
    if (!imageType) {
      setSrc("");
      setFailed(true);
      return;
    }

    setFailed(false);
    setSrc(client.getImageProxyUrl(item, imageType, width));
  }, [availableTypes, client, imageTypeIndex, item, shouldLoad, width]);

  const fallbackNode = fallback ?? (
    <span className="spiritflix-image-fallback" aria-label={alt || item.Name}>
      <span>{item.Name.slice(0, 1).toUpperCase()}</span>
    </span>
  );

  return (
    <span
      ref={frameRef}
      className={`spiritflix-image-frame ${className ?? ""}`.trim()}
      data-spiritflix-image-state={failed ? "fallback" : src ? "loaded" : "pending"}
    >
      {src && !failed ? (
        <Image
          src={src}
          alt={alt}
          className="spiritflix-image-frame__image"
          loading={priority ? "eager" : "lazy"}
          fetchPriority={priority ? "high" : "auto"}
          width={width}
          height={Math.round(width * 1.5)}
          unoptimized
          onError={() => {
            if (imageTypeIndex < availableTypes.length - 1) {
              setImageTypeIndex((current) => Math.min(current + 1, availableTypes.length - 1));
            } else {
              setFailed(true);
            }
          }}
          onLoad={onLoad}
        />
      ) : (
        fallbackNode
      )}
    </span>
  );
}
