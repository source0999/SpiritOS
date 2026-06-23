"use client";

import { useEffect, useMemo, useRef } from "react";
import { SpiritFlixHome } from "@/components/spiritflix/SpiritFlixHome";
import { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem, SpiritFlixHomeData, SpiritFlixSession } from "@/lib/spiritflix-types";
import { createBenchmarkItem, SPIRITFLIX_BENCHMARK_DEFAULT_ITEM_ID } from "@/lib/spiritflix/benchmark-client";

function buildWarmShellData(itemId: string): SpiritFlixHomeData {
  const libraryId = "benchmark-library";
  const items: JellyfinItem[] = Array.from({ length: 12 }, (_, index) =>
    createBenchmarkItem(`${itemId}-${index}`, `Benchmark Clip ${index + 1}`),
  );
  return {
    libraries: [{ Id: libraryId, Name: "Other", CollectionType: "homevideos" }],
    playlists: [],
    selectedLibraryId: libraryId,
    featuredItems: [],
    libraryItems: items,
    continueWatching: items.slice(0, 2),
    watchHistory: [],
    latestAdded: items.slice(2, 5),
    favorites: items.slice(5, 7),
  };
}

const noop = () => undefined;
const noopAsync = async () => undefined;

export default function SpiritFlixBenchmarkShellPage() {
  const markedRef = useRef(false);
  const data = useMemo(() => buildWarmShellData(SPIRITFLIX_BENCHMARK_DEFAULT_ITEM_ID), []);
  const client = useMemo(() => new JellyfinClient("http://127.0.0.1:8096"), []);
  const session = useMemo<SpiritFlixSession>(
    () => ({
      serverUrl: "http://127.0.0.1:8096",
      accessToken: "benchmark-token",
      userId: "benchmark-user",
      username: "benchmark",
    }),
    [],
  );

  useEffect(() => {
    if (markedRef.current || typeof performance === "undefined") return;
    markedRef.current = true;
    performance.mark("spiritflix:benchmark-shell-start");
  }, []);

  return (
    <main data-spiritflix-benchmark="shell">
      <SpiritFlixHome
        client={client}
        data={data}
        loading={false}
        error=""
        session={session}
        searchTerm=""
        serverInfo={{ ServerName: "Benchmark", Version: "bench" }}
        onLogout={noop}
        onRefresh={noop}
        onSearch={noop}
        onSelectHome={noop}
        onSelectLibrary={noop}
        onSelectModel={noop}
        onOpenDetails={noop}
        onPlay={noopAsync}
      />
    </main>
  );
}
