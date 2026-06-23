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

export function createBenchmarkItem(itemId: string, name = "Benchmark Clip"): JellyfinItem {
  return {
    Id: itemId,
    Name: name,
    Type: "Video",
    MediaType: "Video",
    Path: `/media/yes/benchmark/${name}.mp4`,
    RunTimeTicks: 600_000_000,
    MediaSources: [{ Path: `/media/yes/benchmark/${name}.mp4` }],
    MediaStreams: [
      { Type: "Video", Codec: "h264", Width: 1280, Height: 720 },
      { Type: "Audio", Codec: "aac", Channels: 2 },
    ],
  };
}
