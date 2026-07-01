import { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix-types";

/** Minimal Jellyfin client for /spiritflix/benchmark player timing — real playback APIs only. */
export function createSpiritFlixBenchmarkClient(item: JellyfinItem, serverUrl: string): JellyfinClient {
  const client = new JellyfinClient(serverUrl);
  client.reportPlayback = async () => undefined;
  client.getSystemDiagnostics = async () => ({
    dellFfmpegActive: false,
    dellFfmpegProcesses: [],
    checkedAt: new Date().toISOString(),
  });
  void item;
  return client;
}

export const SPIRITFLIX_BENCHMARK_DEFAULT_ITEM_ID = "phase7-candidate-02";

export function createBenchmarkItem(itemId: string, name = "Benchmark Clip", sourcePath?: string): JellyfinItem {
  const mediaPath = sourcePath || `/media/yes/benchmark/${name}.mp4`;
  const isAnimeBenchmark = mediaPath.toLowerCase().includes("/anime/");
  return {
    Id: itemId,
    Name: name,
    Type: isAnimeBenchmark ? "Episode" : "Video",
    MediaType: "Video",
    Path: mediaPath,
    SeriesName: isAnimeBenchmark ? "Rurouni Kenshin (1996)" : undefined,
    RunTimeTicks: 600_000_000,
    MediaSources: [{ Path: mediaPath }],
    MediaStreams: isAnimeBenchmark
      ? [
          { Type: "Video", Codec: "h264", Width: 720, Height: 540 },
          { Index: 1, Type: "Audio", Codec: "aac", Language: "jpn", DisplayTitle: "Japanese AAC", Channels: 2 },
          { Index: 2, Type: "Audio", Codec: "aac", Language: "eng", DisplayTitle: "English AAC", Channels: 2 },
        ]
      : [
          { Type: "Video", Codec: "h264", Width: 1280, Height: 720 },
          { Type: "Audio", Codec: "aac", Channels: 2 },
        ],
  };
}
