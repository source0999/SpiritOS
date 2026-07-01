"use client";

import { useEffect, useMemo, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { SpiritFlixPlayer } from "@/components/spiritflix/SpiritFlixPlayer";
import {
  createBenchmarkItem,
  createSpiritFlixBenchmarkClient,
  SPIRITFLIX_BENCHMARK_DEFAULT_ITEM_ID,
} from "@/lib/spiritflix/benchmark-client";
import { SPIRITFLIX_DEFAULT_SERVER } from "@/lib/spiritflix-jellyfin-client";

export default function SpiritFlixBenchmarkPlayerPage() {
  const searchParams = useSearchParams();
  const itemId = searchParams.get("itemId") ?? SPIRITFLIX_BENCHMARK_DEFAULT_ITEM_ID;
  const sourcePath = searchParams.get("sourcePath") ?? undefined;
  const autoPlay = searchParams.get("autoplay") !== "0";
  const markedRef = useRef(false);
  const item = useMemo(() => createBenchmarkItem(itemId, undefined, sourcePath), [itemId, sourcePath]);
  const client = useMemo(() => createSpiritFlixBenchmarkClient(item, SPIRITFLIX_DEFAULT_SERVER), [item]);

  useEffect(() => {
    void client.getMobileOptimizedSource(item).catch(() => undefined);
  }, [client, item]);

  useEffect(() => {
    if (markedRef.current || typeof performance === "undefined") return;
    markedRef.current = true;
    performance.mark("spiritflix:benchmark-page-start");
  }, []);

  useEffect(() => {
    if (!autoPlay) return;
    const timer = window.setTimeout(() => {
      const playButton = document.querySelector<HTMLButtonElement>(".spiritflix-player button[aria-label='Play']");
      playButton?.click();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [autoPlay, itemId]);

  return (
    <main data-spiritflix-benchmark="player" data-spiritflix-item-id={itemId}>
      <SpiritFlixPlayer
        client={client}
        item={item}
        queue={null}
        onPlaybackProgress={() => undefined}
        onToggleFavorite={() => undefined}
        onSelectItem={() => undefined}
        onShuffleQueue={() => undefined}
        onPlayModelShuffle={() => undefined}
        onReorderQueue={() => undefined}
        onDeleteItem={() => undefined}
        onClose={() => undefined}
      />
    </main>
  );
}
