import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getSmartFillScale, getTitleMatchedModelItems, SpiritFlixPlayer } from "../SpiritFlixPlayer";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix-types";

const item: JellyfinItem = {
  Id: "video-1",
  Name: "Fold Tap Test",
  Type: "Video",
  SeriesName: "Sava Schultz",
  Path: "/mnt/spirit-8tb/media/yes/Sava Schultz/Fold Tap Test.mp4",
  RunTimeTicks: 1200000000,
  MediaStreams: [{ Type: "Video", Width: 1080, Height: 1920 }],
  UserData: {
    IsFavorite: false,
    PlaybackPositionTicks: 0,
    PlayCount: 0,
  },
};

const nextItem: JellyfinItem = {
  Id: "video-2",
  Name: "Queue Next Test",
  Type: "Video",
  RunTimeTicks: 900000000,
  MediaStreams: [{ Type: "Video", Width: 1920, Height: 1080 }],
  UserData: {
    IsFavorite: false,
    PlaybackPositionTicks: 0,
    PlayCount: 0,
  },
};

function createClient(): JellyfinClient {
  return {
    checkPublicInfo: vi.fn().mockResolvedValue({}),
    getHlsUrl: vi.fn(() => "https://media.example/hls.m3u8"),
    getMobileOptimizedSource: vi.fn().mockResolvedValue({ available: false }),
    getCachedMobileOptimizedSource: vi.fn(() => null),
    getSystemDiagnostics: vi.fn().mockResolvedValue({ dellFfmpegActive: false, dellFfmpegProcesses: [], checkedAt: "2026-06-20T00:00:00.000Z" }),
    getStreamUrl: vi.fn(() => "https://media.example/video.mp4"),
    getImageProxyUrl: vi.fn(() => "/api/spiritflix/jellyfin-image?test=1"),
    getFaceOrganizerMetadata: vi.fn().mockResolvedValue({
      knownPerformers: [],
      videos: {},
      scannedCount: 0,
      generatedAt: "2026-06-21T00:00:00.000Z",
    }),
    reportPlayback: vi.fn().mockResolvedValue(undefined),
  } as unknown as JellyfinClient;
}

function renderPlayer(options: {
  client?: JellyfinClient;
  onSelectItem?: (item: JellyfinItem) => void;
  onReorderQueue?: (activeItemId: string, overItemId: string) => void;
  onShuffleQueue?: (currentItemId: string, orientation?: "portrait" | "landscape") => void;
  onPlayModelShuffle?: (currentItem: JellyfinItem, modelName: string, modelItems: JellyfinItem[]) => void;
  onDeleteItem?: (deletedItem: JellyfinItem, nextItem: JellyfinItem | null) => void;
  onClose?: () => void;
  itemOverride?: JellyfinItem;
  queueItems?: JellyfinItem[];
  libraryItems?: JellyfinItem[];
  isShuffled?: boolean;
} = {}) {
  const queueItems = options.queueItems;
  const playingItem = options.itemOverride ?? item;
  return render(
    <SpiritFlixPlayer
      client={options.client ?? createClient()}
      item={playingItem}
      queue={
        queueItems
          ? {
              items: queueItems,
              originalItems: queueItems,
              currentIndex: Math.max(0, queueItems.findIndex((queueItem) => queueItem.Id === playingItem.Id)),
              sourceTitle: "Test Queue",
              isShuffled: options.isShuffled,
            }
          : null
      }
      libraryItems={options.libraryItems}
      onPlaybackProgress={vi.fn()}
      onToggleFavorite={vi.fn()}
      onSelectItem={options.onSelectItem ?? vi.fn()}
      onShuffleQueue={options.onShuffleQueue ?? vi.fn()}
      onPlayModelShuffle={options.onPlayModelShuffle ?? vi.fn()}
      onReorderQueue={options.onReorderQueue ?? vi.fn()}
      onDeleteItem={options.onDeleteItem ?? vi.fn()}
      onClose={options.onClose ?? vi.fn()}
    />,
  );
}

function touchList(touches: Array<{ clientX: number; clientY: number }>) {
  return Object.assign([...touches], {
    item: (index: number) => touches[index] ?? null,
  });
}

describe("getSmartFillScale", () => {
  it("caps fill zoom for portrait videos on Fold-like screens", () => {
    expect(getSmartFillScale(0.86, 0.5625)).toBeCloseTo(1.12, 2);
  });

  it("caps fill zoom for wide and multi-panel videos", () => {
    expect(getSmartFillScale(0.76, 1.78)).toBeCloseTo(1.24, 2);
  });

  it("does not zoom when the screen and video already nearly match", () => {
    expect(getSmartFillScale(1.02, 1)).toBe(1);
  });
});

describe("getTitleMatchedModelItems", () => {
  it("matches trusted title aliases without pulling unrelated source folders", () => {
    const current = {
      ...item,
      Id: "luna-current",
      Name: "luna🌸 - volume up",
      ManualModelName: "Luna x pearl",
    };
    const titleMatch = {
      ...nextItem,
      Id: "luna-title",
      Name: "luna☁️ - i hate getting interrupted",
      Path: "/media/yes/videos from x/luna cloud.mp4",
    };
    const compactMatch = {
      ...nextItem,
      Id: "luna-compact",
      Name: "lunaxpearl clip",
    };
    const unrelated = {
      ...nextItem,
      Id: "unrelated",
      Name: "videos from x random clip",
    };
    const assignedElsewhere = {
      ...nextItem,
      Id: "other-model",
      Name: "luna title but already assigned",
      ManualModelName: "Other Model",
    };

    expect(getTitleMatchedModelItems("Luna x pearl", [current, titleMatch, compactMatch, unrelated, assignedElsewhere], current)).toEqual([
      titleMatch,
      compactMatch,
    ]);
  });
});

describe("SpiritFlixPlayer mobile controls", () => {
  beforeEach(() => {
    window.localStorage.clear();
    Object.defineProperty(HTMLMediaElement.prototype, "load", {
      configurable: true,
      value: vi.fn(),
    });
    Object.defineProperty(HTMLMediaElement.prototype, "pause", {
      configurable: true,
      value: vi.fn(),
    });
    Object.defineProperty(HTMLMediaElement.prototype, "play", {
      configurable: true,
      value: vi.fn().mockResolvedValue(undefined),
    });
    Object.defineProperty(HTMLVideoElement.prototype, "requestPictureInPicture", {
      configurable: true,
      value: undefined,
    });
    Object.defineProperty(document, "pictureInPictureEnabled", {
      configurable: true,
      value: false,
    });
    Object.defineProperty(document, "pictureInPictureElement", {
      configurable: true,
      value: null,
    });
    Object.defineProperty(document, "exitPictureInPicture", {
      configurable: true,
      value: undefined,
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string | URL | Request) => {
        const href = String(url);
        if (href.includes("/model-index")) {
          return Response.json({ schema: "spiritflix-manual-model-index/v1", updatedAt: "2026-06-20T00:00:00.000Z", models: [] });
        }
        if (href.includes("/model")) {
          return Response.json({
            schema: "spiritflix-manual-model/v1",
            itemId: "video-1",
            modelName: "",
            updatedAt: "2026-06-20T00:00:00.000Z",
            source: "manual",
          });
        }
        if (href.includes("/tags") && !href.endsWith("/tags")) {
          return Response.json({
            schema: "spiritflix-manual-tags/v1",
            itemId: "video-1",
            manualTags: [],
            updatedAt: "2026-06-20T00:00:00.000Z",
            source: "manual",
          });
        }
        if (href.includes("/captions/manifest")) {
          return Response.json({ mediaPath: item.Path, mediaKey: "caption-test", generatedAt: "2026-06-27T00:00:00.000Z", tracks: [] });
        }
        return Response.json({ schema: "spiritflix-manual-tag-index/v1", updatedAt: "2026-06-20T00:00:00.000Z", tags: [] });
      }),
    );
    global.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("uses the MP4 stream proxy before HLS on HTTPS pages", async () => {
    vi.spyOn(window, "location", "get").mockReturnValue({
      ...window.location,
      protocol: "https:",
      hostname: "10.0.0.186",
      href: "https://10.0.0.186:3000/spiritflix",
    } as Location);
    const client = {
      ...createClient(),
      getStreamUrl: vi.fn(() => "/api/spiritflix/stream?itemId=video-1"),
      getHlsUrl: vi.fn(() => "/api/spiritflix/hls?itemId=video-1"),
      getMobileOptimizedSource: vi.fn().mockResolvedValue({ available: false }),
    } as unknown as JellyfinClient;

    renderPlayer({ client });

    const video = document.querySelector("video");
    await waitFor(() => expect(video?.getAttribute("src")).toBe("/api/spiritflix/stream?itemId=video-1"));
    expect(screen.getByLabelText("Playback diagnostics")).toHaveTextContent("proxied stream");
    fireEvent.click(screen.getByRole("button", { name: "Details" }));
    expect(screen.getByText("Selected source")).toBeInTheDocument();
    expect(screen.getByText("canonical_mp4")).toBeInTheDocument();
  });

  it("renders native WebVTT tracks from the caption manifest", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string | URL | Request) => {
        const href = String(url);
        if (href.includes("/captions/manifest")) {
          return Response.json({
            mediaPath: item.Path,
            mediaKey: "caption-test",
            generatedAt: "2026-06-27T00:00:00.000Z",
            tracks: [
              {
                id: "caption-default",
                sourceType: "embedded",
                sourceFormat: "mov_text",
                outputFormat: "vtt",
                language: "eng",
                label: "English",
                kind: "subtitles",
                default: true,
                publicUrl: "/api/spiritflix/captions/file?key=caption-test&track=caption-default",
                reviewStatus: "source",
              },
              {
                id: "caption-forced",
                sourceType: "embedded",
                sourceFormat: "mov_text",
                outputFormat: "vtt",
                language: "eng",
                label: "SubtitleHandler",
                kind: "subtitles",
                forced: true,
                publicUrl: "/api/spiritflix/captions/file?key=caption-test&track=caption-forced",
                reviewStatus: "source",
              },
            ],
          });
        }
        return Response.json({ schema: "spiritflix-manual-tag-index/v1", updatedAt: "2026-06-20T00:00:00.000Z", tags: [] });
      }),
    );

    renderPlayer();

    await waitFor(() => expect(document.querySelectorAll("video track")).toHaveLength(2));
    const tracks = Array.from(document.querySelectorAll("video track"));
    expect(tracks[0]).toHaveAttribute("src", "/api/spiritflix/captions/file?key=caption-test&track=caption-default");
    expect(tracks[0]).toHaveAttribute("srclang", "eng");
    expect(tracks[0]).toHaveAttribute("label", "English");
    expect(tracks[0]).toHaveAttribute("default");
    expect(tracks[1]).toHaveAttribute("label", "English Forced");
  });

  it("lets the user turn subtitles off and remembers the choice", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string | URL | Request) => {
        const href = String(url);
        if (href.includes("/captions/manifest")) {
          return Response.json({
            mediaPath: item.Path,
            mediaKey: "caption-test",
            generatedAt: "2026-06-27T00:00:00.000Z",
            tracks: [
              {
                id: "caption-default",
                sourceType: "embedded",
                sourceFormat: "mov_text",
                outputFormat: "vtt",
                language: "eng",
                label: "English",
                kind: "subtitles",
                default: true,
                publicUrl: "/api/spiritflix/captions/file?key=caption-test&track=caption-default",
                reviewStatus: "source",
              },
            ],
          });
        }
        return Response.json({ schema: "spiritflix-manual-tag-index/v1", updatedAt: "2026-06-20T00:00:00.000Z", tags: [] });
      }),
    );

    renderPlayer();

    const button = await screen.findByRole("button", { name: "Turn subtitles off" });
    expect(button).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(button);

    expect(screen.getByRole("button", { name: "Turn subtitles on" })).toHaveAttribute("aria-pressed", "false");
    expect(window.localStorage.getItem("spiritflix_player_caption_mode")).toBe("off");
  });

  it("keeps generated AI captions actually showing through repeated subtitle toggles", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string | URL | Request) => {
        const href = String(url);
        if (href.includes("/captions/manifest")) {
          return Response.json({
            mediaPath: item.Path,
            mediaKey: "caption-test",
            generatedAt: "2026-06-27T00:00:00.000Z",
            tracks: [
              {
                id: "caption-source",
                sourceType: "embedded",
                sourceFormat: "mov_text",
                outputFormat: "vtt",
                language: "eng",
                label: "English Source",
                kind: "subtitles",
                default: true,
                publicUrl: "/api/spiritflix/captions/file?key=caption-test&track=caption-source",
                reviewStatus: "source",
              },
              {
                id: "ai-en",
                sourceType: "generated",
                sourceFormat: "ai",
                outputFormat: "vtt",
                language: "en",
                label: "English AI Captions",
                kind: "captions",
                publicUrl: "/api/spiritflix/captions/file?key=caption-test&track=ai-en",
                reviewStatus: "draft",
              },
            ],
          });
        }
        return Response.json({ schema: "spiritflix-manual-tag-index/v1", updatedAt: "2026-06-20T00:00:00.000Z", tags: [] });
      }),
    );

    renderPlayer();
    const video = document.querySelector("video") as HTMLVideoElement;
    await waitFor(() => expect(document.querySelectorAll("video track")).toHaveLength(2));
    const trackElements = Array.from(document.querySelectorAll("video track"));
    const sourceTrack = { label: "English Source", language: "eng", kind: "subtitles", mode: "disabled" };
    const aiTrack = { label: "English AI Captions", language: "en", kind: "captions", mode: "disabled" };
    Object.defineProperty(video, "textTracks", {
      configurable: true,
      value: { length: 2, 0: sourceTrack, 1: aiTrack },
    });
    Object.defineProperty(trackElements[0], "track", { configurable: true, value: sourceTrack });
    Object.defineProperty(trackElements[1], "track", { configurable: true, value: aiTrack });

    fireEvent.load(trackElements[1]);
    await waitFor(() => expect(aiTrack.mode).toBe("showing"));
    expect(sourceTrack.mode).toBe("disabled");
    expect(trackElements[1]).toHaveAttribute("default");

    fireEvent.click(screen.getByRole("button", { name: "Turn subtitles off" }));
    expect(sourceTrack.mode).toBe("disabled");
    expect(aiTrack.mode).toBe("disabled");

    fireEvent.click(screen.getByRole("button", { name: "Turn subtitles on" }));
    await waitFor(() => expect(aiTrack.mode).toBe("showing"));
    expect(sourceTrack.mode).toBe("disabled");
    expect(screen.getByRole("button", { name: "Turn subtitles off" })).toHaveAttribute("aria-pressed", "true");
  });

  it("keeps playback alive when the caption manifest fetch fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string | URL | Request) => {
        const href = String(url);
        if (href.includes("/captions/manifest")) {
          return new Response("caption route unavailable", { status: 500 });
        }
        return Response.json({ schema: "spiritflix-manual-tag-index/v1", updatedAt: "2026-06-20T00:00:00.000Z", tags: [] });
      }),
    );

    renderPlayer();

    const video = document.querySelector("video");
    await waitFor(() => expect(video?.getAttribute("src")).toBe("https://media.example/video.mp4"));
    expect(document.querySelectorAll("video track")).toHaveLength(0);
  });

  it("uses cached mobile optimized source immediately without waiting on network", async () => {
    const client = {
      ...createClient(),
      getStreamUrl: vi.fn(() => "/api/spiritflix/stream?itemId=video-1"),
      getCachedMobileOptimizedSource: vi.fn(() => ({
        available: true,
        mode: "mobile optimized",
        url: "/api/spiritflix/mobile-optimized?stream=1&key=video-1",
      })),
      getMobileOptimizedSource: vi.fn(),
    } as unknown as JellyfinClient;

    renderPlayer({ client });

    const video = document.querySelector("video");
    await waitFor(() => expect(video?.getAttribute("src")).toBe("/api/spiritflix/mobile-optimized?stream=1&key=video-1"));
    expect(client.getMobileOptimizedSource).not.toHaveBeenCalled();
  });

  it("assigns direct MP4 immediately and upgrades to mobile optimized when receipt resolves on desktop", async () => {
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
    let resolveMobile: (value: { available: boolean; url?: string; mode?: string }) => void = () => undefined;
    const mobilePromise = new Promise<{ available: boolean; url?: string; mode?: string }>((resolve) => {
      resolveMobile = resolve;
    });
    const client = {
      ...createClient(),
      getStreamUrl: vi.fn(() => "/api/spiritflix/stream?itemId=video-1"),
      getCachedMobileOptimizedSource: vi.fn(() => null),
      getMobileOptimizedSource: vi.fn(() => mobilePromise),
    } as unknown as JellyfinClient;

    renderPlayer({ client });

    const video = document.querySelector("video");
    await waitFor(() => expect(video?.getAttribute("src")).toBe("/api/spiritflix/stream?itemId=video-1"));
    resolveMobile({
      available: true,
      mode: "mobile optimized",
      url: "/api/spiritflix/mobile-optimized?stream=1&key=video-1",
    });
    await waitFor(() => expect(video?.getAttribute("src")).toBe("/api/spiritflix/mobile-optimized?stream=1&key=video-1"));
  });

  it("does not swap sources when direct MP4 is already playing as the optimized receipt arrives", async () => {
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
    let resolveMobile: (value: { available: boolean; url?: string; mode?: string }) => void = () => undefined;
    const mobileResolved = vi.fn();
    const mobilePromise = new Promise<{ available: boolean; url?: string; mode?: string }>((resolve) => {
      resolveMobile = (value) => {
        mobileResolved();
        resolve(value);
      };
    });
    const client = {
      ...createClient(),
      getStreamUrl: vi.fn(() => "/api/spiritflix/stream?itemId=video-1"),
      getCachedMobileOptimizedSource: vi.fn(() => null),
      getMobileOptimizedSource: vi.fn(() => mobilePromise),
    } as unknown as JellyfinClient;

    renderPlayer({ client });

    const video = document.querySelector("video") as HTMLVideoElement | null;
    await waitFor(() => expect(video?.getAttribute("src")).toBe("/api/spiritflix/stream?itemId=video-1"));
    if (!video) throw new Error("Expected player video element");
    Object.defineProperty(video, "paused", { configurable: true, value: false });
    video.currentTime = 0.5;

    resolveMobile({
      available: true,
      mode: "mobile optimized",
      url: "/api/spiritflix/mobile-optimized?stream=1&key=video-1",
    });

    await waitFor(() => expect(mobileResolved).toHaveBeenCalledTimes(1));
    await Promise.resolve();
    expect(video.getAttribute("src")).toBe("/api/spiritflix/stream?itemId=video-1");
  });

  it("prefers a Mac-created mobile optimized MP4 receipt when available", async () => {
    const client = {
      ...createClient(),
      getStreamUrl: vi.fn(() => "/api/spiritflix/stream?itemId=video-1"),
      getMobileOptimizedSource: vi.fn().mockResolvedValue({
        available: true,
        mode: "mobile optimized",
        url: "/api/spiritflix/mobile-optimized?stream=1&key=video-1",
        receipt: {
          encoder: "mac-videotoolbox-h264-mobile",
          ffprobe: { container: "mov,mp4,m4a,3gp,3g2,mj2", videoCodec: "h264", audioCodec: "aac" },
        },
      }),
    } as unknown as JellyfinClient;

    renderPlayer({ client });

    const video = document.querySelector("video");
    await waitFor(() => expect(video?.getAttribute("src")).toBe("/api/spiritflix/mobile-optimized?stream=1&key=video-1"));
    await waitFor(() => expect(screen.getByLabelText("Playback diagnostics")).toHaveTextContent("mobile optimized"));
    fireEvent.click(screen.getByRole("button", { name: "Details" }));
    expect(screen.getByText("mac_optimized_mp4")).toBeInTheDocument();
    expect(screen.getByText("valid Mac optimized MP4 receipt and output found")).toBeInTheDocument();
  });

  it("lets a side tap hide controls even while paused and lets a center tap wake them", async () => {
    renderPlayer();

    const player = screen.getByLabelText("Fold Tap Test player");
    Object.defineProperty(player, "clientWidth", { configurable: true, value: 900 });

    await waitFor(() => expect(player).toHaveClass("is-awake"));

    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 90, clientY: 320 }]),
    });
    fireEvent.touchEnd(player, {
      changedTouches: touchList([{ clientX: 90, clientY: 320 }]),
      touches: touchList([]),
    });

    await waitFor(() => {
      expect(player).toHaveClass("is-controls-hidden");
      expect(player).not.toHaveClass("is-awake");
    });

    fireEvent.mouseMove(player, { clientX: 92, clientY: 321 });
    fireEvent.pointerMove(player, { clientX: 92, clientY: 321, pointerType: "mouse" });

    await waitFor(() => {
      expect(player).toHaveClass("is-controls-hidden");
      expect(player).not.toHaveClass("is-awake");
    });

    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 450, clientY: 320 }]),
    });
    fireEvent.touchEnd(player, {
      changedTouches: touchList([{ clientX: 450, clientY: 320 }]),
      touches: touchList([]),
    });

    await waitFor(() => {
      expect(player).toHaveClass("is-awake");
      expect(player).not.toHaveClass("is-controls-hidden");
    });
  });

  it("unmutes mobile playback to an audible volume and opens the volume slider", async () => {
    window.localStorage.setItem("spiritflix_player_muted", "true");
    window.localStorage.setItem("spiritflix_player_volume", "0");
    renderPlayer();

    const player = screen.getByLabelText("Fold Tap Test player");
    await waitFor(() => expect(player).toHaveClass("is-awake"));

    fireEvent.click(screen.getByRole("button", { name: "Open volume" }));

    const video = document.querySelector("video");
    expect(video?.muted).toBe(false);
    expect(video?.volume).toBe(0.8);
    expect(screen.getByLabelText("Volume")).toHaveValue("0.8");
    expect(screen.getByRole("button", { name: "Close volume" })).toHaveAttribute("aria-expanded", "true");
  });

  it("uses episode controls and hides library tools for anime series playback", async () => {
    const episodeOne: JellyfinItem = {
      ...item,
      Id: "kenshin-1",
      Name: "The Handsome Swordsman of Legend",
      Type: "Video",
      SeriesName: "Rurouni Kenshin (1996)",
      Path: "/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 01/Rurouni Kenshin (1996) - S01E01.mp4",
      ParentIndexNumber: 1,
      IndexNumber: 1,
      MediaStreams: [
        { Type: "Video", Width: 720, Height: 540 },
        { Type: "Audio", Language: "jpn", DisplayTitle: "Japanese AAC" },
        { Type: "Audio", Language: "eng", DisplayTitle: "English AAC" },
      ],
    };
    const episodeTwo: JellyfinItem = {
      ...episodeOne,
      Id: "kenshin-2",
      Name: "Kid Samurai",
      Path: "/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 01/Rurouni Kenshin (1996) - S01E02.mp4",
      IndexNumber: 2,
    };

    renderPlayer({ itemOverride: episodeOne, queueItems: [episodeOne], libraryItems: [episodeTwo] });

    expect(screen.getByRole("button", { name: "Previous episode" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Next episode" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Switch audio to English dub" })).toBeInTheDocument();
    expect(screen.getByText("Kid Samurai")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /favorite/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /shuffle/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /repeat/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Edit model name" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Edit manual tags" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Delete video" })).not.toBeInTheDocument();
  });

  it("keeps anime episode controls scoped to the source folder when SeriesName is stale", async () => {
    const gurrenEpisode: JellyfinItem = {
      ...item,
      Id: "gurren-1",
      Name: "Bust Through the Heavens with Your Drill!",
      Type: "Video",
      SeriesName: "Rurouni Kenshin (1996)",
      Path: "/mnt/spirit-8tb/media/anime/Gurren Lagann (2007)/Season 01/Gurren Lagann (2007) - S01E01.mp4",
      ParentIndexNumber: 1,
      IndexNumber: 1,
      MediaStreams: [{ Type: "Video", Width: 1280, Height: 720 }],
    };
    const kenshinEpisode: JellyfinItem = {
      ...gurrenEpisode,
      Id: "kenshin-1",
      Name: "The Handsome Swordsman of Legend",
      Path: "/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 01/Rurouni Kenshin (1996) - S01E01.mp4",
    };

    renderPlayer({ itemOverride: gurrenEpisode, queueItems: [gurrenEpisode, kenshinEpisode], libraryItems: [kenshinEpisode] });

    expect(screen.getByRole("button", { name: "Previous episode" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Next episode" })).toBeDisabled();
    expect(screen.queryByText("The Handsome Swordsman of Legend")).not.toBeInTheDocument();
  });

  it("persists and applies the selected series audio preference", async () => {
    const client = {
      ...createClient(),
      getStreamUrl: vi.fn((_itemId: string, options?: { audioStreamIndex?: number }) =>
        `/api/spiritflix/stream?itemId=kenshin-1${options?.audioStreamIndex !== undefined ? `&audioStreamIndex=${options.audioStreamIndex}` : ""}`,
      ),
      getHlsUrl: vi.fn((_itemId: string, options?: { audioStreamIndex?: number }) =>
        `/api/spiritflix/hls?itemId=kenshin-1${options?.audioStreamIndex !== undefined ? `&audioStreamIndex=${options.audioStreamIndex}` : ""}`,
      ),
    } as unknown as JellyfinClient;
    const animeItem: JellyfinItem = {
      ...item,
      Id: "kenshin-1",
      Name: "The Handsome Swordsman of Legend",
      Type: "Video",
      SeriesName: "Rurouni Kenshin (1996)",
      Path: "/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 01/Rurouni Kenshin (1996) - S01E01.mp4",
      MediaStreams: [
        { Type: "Video", Width: 720, Height: 540 },
        { Index: 1, Type: "Audio", Language: "jpn", DisplayTitle: "Japanese AAC" },
        { Index: 2, Type: "Audio", Language: "eng", DisplayTitle: "English AAC" },
      ],
    };
    const tracks = [
      { language: "jpn", label: "Japanese", enabled: true },
      { language: "eng", label: "English", enabled: false },
    ];

    renderPlayer({ client, itemOverride: animeItem });
    const video = document.querySelector("video");
    Object.defineProperty(video as HTMLVideoElement, "audioTracks", {
      configurable: true,
      value: tracks,
    });
    fireEvent.loadedMetadata(video as HTMLVideoElement);
    fireEvent.canPlay(video as HTMLVideoElement);

    fireEvent.click(screen.getByRole("button", { name: "Switch audio to English dub" }));

    expect(tracks[0].enabled).toBe(false);
    expect(tracks[1].enabled).toBe(true);
    await waitFor(() => expect(client.getHlsUrl).toHaveBeenCalledWith("kenshin-1", { audioStreamIndex: 2 }));
    expect(screen.getByRole("button", { name: "Switch audio to Japanese sub" })).toHaveAttribute("aria-pressed", "true");
    expect(JSON.parse(window.localStorage.getItem("spiritflix_series_audio_preferences") ?? "{}")).toEqual({
      "rurouni kenshin (1996)": "dub",
    });
  });

  it("keeps generated captions showing while switching anime audio streams", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string | URL | Request) => {
        const href = String(url);
        if (href.includes("/captions/manifest")) {
          return Response.json({
            mediaPath: item.Path,
            mediaKey: "caption-test",
            generatedAt: "2026-06-27T00:00:00.000Z",
            tracks: [
              {
                id: "caption-source",
                sourceType: "embedded",
                sourceFormat: "mov_text",
                outputFormat: "vtt",
                language: "eng",
                label: "English Source",
                kind: "subtitles",
                default: true,
                publicUrl: "/api/spiritflix/captions/file?key=caption-test&track=caption-source",
                reviewStatus: "source",
              },
              {
                id: "ai-en",
                sourceType: "generated",
                sourceFormat: "ai",
                outputFormat: "vtt",
                language: "en",
                label: "English AI Captions",
                kind: "captions",
                publicUrl: "/api/spiritflix/captions/file?key=caption-test&track=ai-en",
                reviewStatus: "draft",
              },
            ],
          });
        }
        return Response.json({ schema: "spiritflix-manual-tag-index/v1", updatedAt: "2026-06-20T00:00:00.000Z", tags: [] });
      }),
    );
    const client = {
      ...createClient(),
      getStreamUrl: vi.fn((_itemId: string, options?: { audioStreamIndex?: number }) =>
        `/api/spiritflix/stream?itemId=kenshin-1${options?.audioStreamIndex !== undefined ? `&audioStreamIndex=${options.audioStreamIndex}` : ""}`,
      ),
      getHlsUrl: vi.fn((_itemId: string, options?: { audioStreamIndex?: number }) =>
        `/api/spiritflix/hls?itemId=kenshin-1${options?.audioStreamIndex !== undefined ? `&audioStreamIndex=${options.audioStreamIndex}` : ""}`,
      ),
    } as unknown as JellyfinClient;
    const animeItem: JellyfinItem = {
      ...item,
      Id: "kenshin-1",
      Name: "The Handsome Swordsman of Legend",
      Type: "Video",
      SeriesName: "Rurouni Kenshin (1996)",
      Path: "/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 01/Rurouni Kenshin (1996) - S01E01.mp4",
      MediaStreams: [
        { Type: "Video", Width: 720, Height: 540 },
        { Index: 1, Type: "Audio", Language: "jpn", DisplayTitle: "Japanese AAC" },
        { Index: 2, Type: "Audio", Language: "eng", DisplayTitle: "English AAC" },
      ],
    };
    const audioTracks = [
      { language: "jpn", label: "Japanese", enabled: true },
      { language: "eng", label: "English", enabled: false },
    ];

    renderPlayer({ client, itemOverride: animeItem });
    const video = document.querySelector("video") as HTMLVideoElement;
    await waitFor(() => expect(document.querySelectorAll("video track")).toHaveLength(2));
    const trackElements = Array.from(document.querySelectorAll("video track"));
    const sourceTrack = { label: "English Source", language: "eng", kind: "subtitles", mode: "disabled" };
    const aiTrack = { label: "English AI Captions", language: "en", kind: "captions", mode: "disabled" };
    Object.defineProperty(video, "audioTracks", { configurable: true, value: audioTracks });
    Object.defineProperty(video, "textTracks", {
      configurable: true,
      value: { length: 2, 0: sourceTrack, 1: aiTrack },
    });
    Object.defineProperty(trackElements[0], "track", { configurable: true, value: sourceTrack });
    Object.defineProperty(trackElements[1], "track", { configurable: true, value: aiTrack });
    fireEvent.loadedMetadata(video);
    fireEvent.canPlay(video);
    fireEvent.load(trackElements[1]);

    await waitFor(() => expect(aiTrack.mode).toBe("showing"));
    fireEvent.click(screen.getByRole("button", { name: "Switch audio to English dub" }));
    await waitFor(() => expect(client.getHlsUrl).toHaveBeenCalledWith("kenshin-1", { audioStreamIndex: 2 }));
    fireEvent.loadedMetadata(video);
    fireEvent.canPlay(video);

    await waitFor(() => expect(aiTrack.mode).toBe("showing"));
    expect(sourceTrack.mode).toBe("disabled");
    expect(audioTracks[0].enabled).toBe(false);
    expect(audioTracks[1].enabled).toBe(true);
    expect(screen.getByRole("button", { name: "Turn subtitles off" })).toHaveAttribute("aria-pressed", "true");
  });

  it("renders selected manual tags highlighted and auto-saves a toggled tag", async () => {
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (init?.method === "PUT") {
        expect(JSON.parse(String(init.body))).toEqual(expect.objectContaining({
          manualTags: ["asmr", "blowjob"],
        }));
        return Response.json({
          record: {
            schema: "spiritflix-manual-tags/v1",
            itemId: "video-1",
            manualTags: ["asmr", "blowjob"],
            updatedAt: "2026-06-20T00:00:01.000Z",
            source: "manual",
          },
          index: {
            schema: "spiritflix-manual-tag-index/v1",
            updatedAt: "2026-06-20T00:00:01.000Z",
            tags: [
              { tag: "asmr", label: "asmr", count: 1 },
              { tag: "blowjob", label: "blowjob", count: 1 },
            ],
          },
          propagated: { tags: [], itemIds: [] },
        });
      }
      if (url.includes("/videos/video-1/tags")) {
        return Response.json({
          schema: "spiritflix-manual-tags/v1",
          itemId: "video-1",
          manualTags: ["blowjob"],
          updatedAt: "2026-06-20T00:00:00.000Z",
          source: "manual",
        });
      }
      return Response.json({
        schema: "spiritflix-manual-tag-index/v1",
        updatedAt: "2026-06-20T00:00:00.000Z",
        tags: [
          { tag: "asmr", label: "asmr", count: 0 },
          { tag: "blowjob", label: "blowjob", count: 1 },
        ],
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    const changedListener = vi.fn();
    window.addEventListener("spiritflix:manual-tags-changed", changedListener);

    renderPlayer({
      libraryItems: [
        item,
        { ...nextItem, Id: "video-2", SeriesName: "Sava Schultz", Path: "/media/sava/two.mp4" },
        { ...nextItem, Id: "video-3", SeriesName: "Other Model", Path: "/media/other/three.mp4" },
      ],
    });
    fireEvent.click(screen.getByRole("button", { name: "Edit manual tags" }));

    const asmr = await screen.findByRole("button", { name: "asmr" });
    const blowjob = await screen.findByRole("button", { name: "blowjob" });
    expect(blowjob).toHaveAttribute("aria-pressed", "true");
    expect(asmr).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(asmr);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/videos/video-1/tags"), expect.objectContaining({ method: "PUT" })));
    expect(await screen.findByText("Saved")).toBeInTheDocument();
    expect(changedListener).toHaveBeenCalled();
    window.removeEventListener("spiritflix:manual-tags-changed", changedListener);
  });

  it("adopts known model attributes into the model attribute section for an assigned model", async () => {
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.includes("/tags?modelName=")) {
        return Response.json({
          schema: "spiritflix-model-manual-tags/v1",
          modelName: "Luna x pearl",
          modelTags: ["bbw", "curvy", "handjob"],
          itemIds: ["video-2"],
        });
      }
      if (url.includes("/videos/video-1/tags") && init?.method === "PUT") {
        expect(JSON.parse(String(init.body))).toEqual(expect.objectContaining({
          manualTags: ["bbw", "curvy"],
        }));
        return Response.json({
          record: {
            schema: "spiritflix-manual-tags/v1",
            itemId: "video-1",
            manualTags: ["bbw", "curvy"],
            updatedAt: "2026-06-21T00:00:01.000Z",
            source: "manual",
          },
          index: {
            schema: "spiritflix-manual-tag-index/v1",
            updatedAt: "2026-06-21T00:00:01.000Z",
            tags: [
              { tag: "handjob", label: "handjob", count: 1 },
            ],
            modelAttributes: [
              { tag: "bbw", label: "bbw", count: 2 },
              { tag: "curvy", label: "curvy", count: 2 },
            ],
          },
          propagated: { tags: [], itemIds: [] },
        });
      }
      if (url.includes("/videos/video-1/tags")) {
        return Response.json({
          schema: "spiritflix-manual-tags/v1",
          itemId: "video-1",
          manualTags: [],
          updatedAt: "1970-01-01T00:00:00.000Z",
          source: "manual",
        });
      }
      return Response.json({
        schema: "spiritflix-manual-tag-index/v1",
        updatedAt: "2026-06-21T00:00:00.000Z",
        tags: [
          { tag: "handjob", label: "handjob", count: 1 },
          { tag: "asmr", label: "asmr", count: 1 },
        ],
        modelAttributes: [
          { tag: "bbw", label: "bbw", count: 1 },
          { tag: "curvy", label: "curvy", count: 1 },
        ],
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    renderPlayer({
      itemOverride: { ...item, ManualModelName: "Luna x pearl" },
      libraryItems: [
        { ...item, ManualModelName: "Luna x pearl" },
        { ...nextItem, Id: "video-2", ManualModelName: "Luna x pearl", Path: "/media/luna/two.mp4" },
      ],
    });
    fireEvent.click(screen.getByRole("button", { name: "Edit manual tags" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/tags?modelName=Luna%20x%20pearl"), expect.objectContaining({ cache: "no-store" })));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/videos/video-1/tags"), expect.objectContaining({ method: "PUT" })));
    expect(await screen.findByLabelText("Action tags")).toBeInTheDocument();
    expect(screen.getByLabelText("Model attributes")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "bbw" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "curvy" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "handjob" })).toHaveAttribute("aria-pressed", "false");
  });

  it("does not let a late tag load erase a newly added draft tag", async () => {
    let resolveIndex!: (response: Response) => void;
    let resolveItem!: (response: Response) => void;
    const indexPromise = new Promise<Response>((resolve) => {
      resolveIndex = resolve;
    });
    const itemPromise = new Promise<Response>((resolve) => {
      resolveItem = resolve;
    });
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (init?.method === "PUT") {
        expect(JSON.parse(String(init.body))).toEqual(expect.objectContaining({ manualTags: ["cumshot"] }));
        return Response.json({
          record: {
            schema: "spiritflix-manual-tags/v1",
            itemId: "video-1",
            manualTags: ["cumshot"],
            updatedAt: "2026-06-20T00:00:01.000Z",
            source: "manual",
          },
          index: {
            schema: "spiritflix-manual-tag-index/v1",
            updatedAt: "2026-06-20T00:00:01.000Z",
            tags: [{ tag: "cumshot", label: "cumshot", count: 1 }],
          },
        });
      }
      if (url.includes("/videos/video-1/tags")) return itemPromise;
      return indexPromise;
    });
    vi.stubGlobal("fetch", fetchMock);

    renderPlayer();
    fireEvent.click(screen.getByRole("button", { name: "Edit manual tags" }));
    fireEvent.change(screen.getByLabelText("Add manual tag"), { target: { value: "cumshot" } });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));

    expect(screen.getByRole("button", { name: "cumshot" })).toHaveAttribute("aria-pressed", "true");

    resolveIndex(Response.json({
      schema: "spiritflix-manual-tag-index/v1",
      updatedAt: "2026-06-20T00:00:00.000Z",
      tags: [{ tag: "busty", label: "busty", count: 1 }],
    }));
    resolveItem(Response.json({
      schema: "spiritflix-manual-tags/v1",
      itemId: "video-1",
      manualTags: [],
      updatedAt: "2026-06-20T00:00:00.000Z",
      source: "manual",
    }));

    await waitFor(() => expect(screen.getByRole("button", { name: "cumshot" })).toHaveAttribute("aria-pressed", "true"));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/videos/video-1/tags"), expect.objectContaining({ method: "PUT" })));
  });

  it("saves a manual model name using an existing model option", async () => {
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (init?.method === "PUT") {
        expect(JSON.parse(String(init.body))).toEqual(expect.objectContaining({ modelName: "Sava Schultz" }));
        return Response.json({
          record: {
            schema: "spiritflix-manual-model/v1",
            itemId: "video-1",
            modelName: "Sava Schultz",
            updatedAt: "2026-06-21T00:00:01.000Z",
            source: "manual",
          },
          index: {
            schema: "spiritflix-manual-model-index/v1",
            updatedAt: "2026-06-21T00:00:01.000Z",
            models: [{ modelName: "Sava Schultz", count: 2 }],
          },
        });
      }
      if (url.includes("/videos/video-1/model")) {
        return Response.json({
          schema: "spiritflix-manual-model/v1",
          itemId: "video-1",
          modelName: "",
          updatedAt: "1970-01-01T00:00:00.000Z",
          source: "manual",
        });
      }
      if (url.includes("/model-index")) {
        return Response.json({
          schema: "spiritflix-manual-model-index/v1",
          updatedAt: "2026-06-21T00:00:00.000Z",
          models: [{ modelName: "Sava Schultz", count: 1 }],
        });
      }
      return Response.json({ schema: "spiritflix-manual-tag-index/v1", updatedAt: "2026-06-20T00:00:00.000Z", tags: [] });
    });
    vi.stubGlobal("fetch", fetchMock);
    const changedListener = vi.fn();
    window.addEventListener("spiritflix:manual-models-changed", changedListener);

    renderPlayer({ queueItems: [item, { ...nextItem, SeriesName: "Sava Schultz" }] });
    fireEvent.click(screen.getByRole("button", { name: "Edit model name" }));

    const existingModel = await screen.findByRole("button", { name: "Sava Schultz" });
    fireEvent.click(existingModel);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/videos/video-1/model"), expect.objectContaining({ method: "PUT" })));
    expect(await screen.findByText("Saved as Sava Schultz")).toBeInTheDocument();
    expect(screen.getByText("Saved in system")).toBeInTheDocument();
    expect(changedListener).toHaveBeenCalledWith(expect.objectContaining({ detail: expect.objectContaining({ modelName: "Sava Schultz" }) }));
    window.removeEventListener("spiritflix:manual-models-changed", changedListener);
  });

  it("auto-saves unassigned title-matched library videos when a model is saved", async () => {
    const titleMatched = {
      ...nextItem,
      Id: "video-2",
      Name: "luna☁️ - i hate getting interrupted",
      Path: "/media/yes/videos from x/luna clip.mp4",
    };
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (init?.method === "PUT") {
        const itemId = url.includes("/videos/video-2/model") ? "video-2" : "video-1";
        return Response.json({
          record: {
            schema: "spiritflix-manual-model/v1",
            itemId,
            modelName: "Luna x pearl",
            updatedAt: "2026-06-21T00:00:01.000Z",
            source: "manual",
          },
          index: {
            schema: "spiritflix-manual-model-index/v1",
            updatedAt: "2026-06-21T00:00:01.000Z",
            models: [{ modelName: "Luna x pearl", count: 2 }],
          },
        });
      }
      if (url.includes("/videos/video-1/model")) {
        return Response.json({
          schema: "spiritflix-manual-model/v1",
          itemId: "video-1",
          modelName: "",
          updatedAt: "1970-01-01T00:00:00.000Z",
          source: "manual",
        });
      }
      if (url.includes("/model-index")) {
        return Response.json({
          schema: "spiritflix-manual-model-index/v1",
          updatedAt: "2026-06-21T00:00:00.000Z",
          models: [{ modelName: "Luna x pearl", count: 1 }],
        });
      }
      if (url.includes("/face-learning")) {
        return Response.json({
          record: {
            schema: "spiritflix-face-learning-request/v1",
            itemId: "video-1",
            modelName: "Luna x pearl",
            relatedItems: [{ itemId: "video-2", filePath: titleMatched.Path }],
            requestedAt: "2026-06-21T00:00:01.000Z",
            status: "queued",
            actions: { pendingCorrectionWritten: false, scanCurrentVideoRequested: true, scanLibraryMatchesRequested: true },
            source: "player-model-widget",
          },
        });
      }
      return Response.json({ schema: "spiritflix-manual-tag-index/v1", updatedAt: "2026-06-20T00:00:00.000Z", tags: [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    const currentLuna = { ...item, Name: "luna🌸 - current" };
    renderPlayer({
      itemOverride: currentLuna,
      queueItems: [currentLuna, titleMatched],
      libraryItems: [currentLuna, titleMatched],
    });
    fireEvent.click(screen.getByRole("button", { name: "Edit model name" }));
    fireEvent.click(await screen.findByRole("button", { name: "Luna x pearl" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/videos/video-2/model"), expect.objectContaining({ method: "PUT" })),
    );
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/videos/video-1/face-learning"),
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining("video-2"),
        }),
      ),
    );
  });

  it("loads the current manual model even when the known model index is unavailable", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (url.includes("/videos/video-1/model")) {
        return Response.json({
          schema: "spiritflix-manual-model/v1",
          itemId: "video-1",
          modelName: "Luna x pearl",
          updatedAt: "2026-06-21T00:00:00.000Z",
          source: "manual",
        });
      }
      if (url.includes("/model-index")) {
        return Response.json({ error: "model index unavailable" }, { status: 500 });
      }
      return Response.json({ schema: "spiritflix-manual-tag-index/v1", updatedAt: "2026-06-20T00:00:00.000Z", tags: [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    renderPlayer();
    fireEvent.click(screen.getByRole("button", { name: "Edit model name" }));

    expect(await screen.findAllByText("Luna x pearl")).toHaveLength(2);
    expect(screen.getAllByText("Saved in system")).toHaveLength(2);
    expect(screen.queryByText("Manual model could not be loaded.")).not.toBeInTheDocument();
  });

  it("loads a manual model through the source path fallback when the player item id changed", async () => {
    const shuffledItem = {
      ...item,
      Id: "shuffle-video-id",
      Path: "/mnt/spirit-8tb/media/yes/Aaliyah Yasin/source clip.mp4",
      ManualModelName: undefined,
    };
    const fetchMock = vi.fn(async (url: string) => {
      const href = String(url);
      if (href.includes("/videos/shuffle-video-id/model")) {
        const requestUrl = new URL(href, "http://localhost");
        if (requestUrl.searchParams.get("filePath") === shuffledItem.Path) {
          return Response.json({
            schema: "spiritflix-manual-model/v1",
            itemId: "old-video-id",
            filePath: shuffledItem.Path,
            modelName: "Aaliyah Yasin",
            updatedAt: "2026-06-21T00:00:00.000Z",
            source: "manual",
          });
        }
        return Response.json({ error: "missing fallback path" }, { status: 404 });
      }
      if (href.includes("/model-index")) {
        return Response.json({
          schema: "spiritflix-manual-model-index/v1",
          updatedAt: "2026-06-21T00:00:00.000Z",
          models: [{ modelName: "Aaliyah Yasin", count: 1 }],
        });
      }
      if (href.includes("/videos/shuffle-video-id/tags")) {
        return Response.json({
          schema: "spiritflix-manual-tags/v1",
          itemId: "old-video-id",
          filePath: shuffledItem.Path,
          manualTags: [],
          updatedAt: "2026-06-21T00:00:00.000Z",
          source: "manual",
        });
      }
      if (href.includes("/captions/manifest")) {
        return Response.json({ mediaPath: shuffledItem.Path, mediaKey: "caption-test", generatedAt: "2026-06-27T00:00:00.000Z", tracks: [] });
      }
      return Response.json({ schema: "spiritflix-manual-tag-index/v1", updatedAt: "2026-06-20T00:00:00.000Z", tags: [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    renderPlayer({ itemOverride: shuffledItem, queueItems: [shuffledItem], isShuffled: true });
    fireEvent.click(screen.getByRole("button", { name: "Edit model name" }));

    expect(await screen.findAllByText("Aaliyah Yasin")).toHaveLength(2);
    const itemModelCalls = fetchMock.mock.calls
      .map(([url]) => String(url))
      .filter((url) => url.includes("/videos/shuffle-video-id/model"));
    expect(itemModelCalls.some((url) => new URL(url, "http://localhost").searchParams.get("filePath") === shuffledItem.Path)).toBe(true);
    expect(screen.queryByText("Manual model could not be loaded.")).not.toBeInTheDocument();
  });

  it("retries a transient manual model network error before showing the editor error state", async () => {
    let itemModelCalls = 0;
    const fetchMock = vi.fn(async (url: string) => {
      const href = String(url);
      if (href.includes("/videos/video-1/model")) {
        itemModelCalls += 1;
        if (itemModelCalls === 1) {
          throw new TypeError("NetworkError when attempting to fetch resource.");
        }
        return Response.json({
          schema: "spiritflix-manual-model/v1",
          itemId: "video-1",
          modelName: "Sava Schultz",
          updatedAt: "2026-06-21T00:00:00.000Z",
          source: "manual",
        });
      }
      if (href.includes("/model-index")) {
        return Response.json({
          schema: "spiritflix-manual-model-index/v1",
          updatedAt: "2026-06-21T00:00:00.000Z",
          models: [{ modelName: "Sava Schultz", count: 1 }],
        });
      }
      if (href.includes("/videos/video-1/tags")) {
        return Response.json({
          schema: "spiritflix-manual-tags/v1",
          itemId: "video-1",
          manualTags: [],
          updatedAt: "2026-06-21T00:00:00.000Z",
          source: "manual",
        });
      }
      if (href.includes("/captions/manifest")) {
        return Response.json({ mediaPath: item.Path, mediaKey: "caption-test", generatedAt: "2026-06-27T00:00:00.000Z", tracks: [] });
      }
      return Response.json({ schema: "spiritflix-manual-tag-index/v1", updatedAt: "2026-06-20T00:00:00.000Z", tags: [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    renderPlayer();
    fireEvent.click(screen.getByRole("button", { name: "Edit model name" }));

    expect(await screen.findAllByText("Sava Schultz")).toHaveLength(2);
    expect(itemModelCalls).toBeGreaterThanOrEqual(2);
    expect(screen.queryByText("Manual model could not be loaded.")).not.toBeInTheDocument();
    expect(screen.queryByText("NetworkError when attempting to fetch resource.")).not.toBeInTheDocument();
  });

  it("starts a shuffled queue for the current known model from the tools drawer", async () => {
    const onPlayModelShuffle = vi.fn();
    const current = { ...item, ManualModelName: "Luna Pearl" };
    const second = { ...nextItem, Id: "video-2", ManualModelName: "Luna Pearl", Path: "/media/luna/two.mp4" };
    const other = { ...nextItem, Id: "video-3", ManualModelName: "Other Model", Path: "/media/other/three.mp4" };
    const fetchMock = vi.fn(async (url: string) => {
      if (url.includes("/videos/video-1/model")) {
        return Response.json({
          schema: "spiritflix-manual-model/v1",
          itemId: "video-1",
          modelName: "Luna Pearl",
          updatedAt: "2026-06-21T00:00:00.000Z",
          source: "manual",
        });
      }
      return Response.json({
        schema: "spiritflix-manual-model-index/v1",
        updatedAt: "2026-06-21T00:00:00.000Z",
        models: [{ modelName: "Luna Pearl", count: 2 }],
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    renderPlayer({
      itemOverride: current,
      libraryItems: [current, second, other],
      onPlayModelShuffle,
    });
    fireEvent.click(screen.getByRole("button", { name: "More player controls" }));
    fireEvent.click(await screen.findByRole("button", { name: /shuffle luna pearl model mix/i }));

    expect(onPlayModelShuffle).toHaveBeenCalledWith(
      expect.objectContaining({ Id: "video-1" }),
      "Luna Pearl",
      [expect.objectContaining({ Id: "video-1" }), expect.objectContaining({ Id: "video-2" })],
    );

    fireEvent.click(screen.getByRole("button", { name: "Edit model name" }));
    expect(await screen.findByText("Known models")).toBeInTheDocument();
    expect(screen.queryByText("Model mix")).not.toBeInTheDocument();
  });

  it("adopts known model-scoped tags when a model is assigned", async () => {
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.includes("/face-learning")) {
        return Response.json({
          record: {
            schema: "spiritflix-face-learning-request/v1",
            itemId: "video-1",
            modelName: "Luna Pearl",
            relatedItems: [{ itemId: "video-2", filePath: "/media/luna/two.mp4" }],
            requestedAt: "2026-06-21T00:00:01.000Z",
            status: "queued",
            actions: {
              pendingCorrectionWritten: false,
              scanCurrentVideoRequested: false,
              scanLibraryMatchesRequested: true,
            },
            source: "player-model-widget",
          },
        });
      }
      if (url.includes("/videos/video-1/tags") && init?.method === "PUT") {
        expect(JSON.parse(String(init.body))).toEqual(expect.objectContaining({
          manualTags: ["bbw", "big tits", "curvy", "handjob"],
        }));
        return Response.json({
          record: {
            schema: "spiritflix-manual-tags/v1",
            itemId: "video-1",
            manualTags: ["bbw", "big tits", "curvy", "handjob"],
            updatedAt: "2026-06-21T00:00:02.000Z",
            source: "manual",
          },
          index: {
            schema: "spiritflix-manual-tag-index/v1",
            updatedAt: "2026-06-21T00:00:02.000Z",
            tags: [
              { tag: "bbw", label: "bbw", count: 2 },
              { tag: "big tits", label: "big tits", count: 1 },
              { tag: "curvy", label: "curvy", count: 2 },
              { tag: "handjob", label: "handjob", count: 1 },
            ],
          },
          propagated: { tags: [], itemIds: [] },
        });
      }
      if (url.includes("/tags?modelName=")) {
        return Response.json({
          schema: "spiritflix-model-manual-tags/v1",
          modelName: "Luna Pearl",
          modelTags: ["bbw", "curvy", "handjob"],
          itemIds: ["video-2"],
        });
      }
      if (url.includes("/videos/video-1/tags")) {
        return Response.json({
          schema: "spiritflix-manual-tags/v1",
          itemId: "video-1",
          manualTags: ["big tits", "handjob"],
          updatedAt: "2026-06-21T00:00:00.000Z",
          source: "manual",
        });
      }
      if (url.includes("/videos/video-1/model") && init?.method === "PUT") {
        return Response.json({
          record: {
            schema: "spiritflix-manual-model/v1",
            itemId: "video-1",
            modelName: "Luna Pearl",
            updatedAt: "2026-06-21T00:00:01.000Z",
            source: "manual",
          },
          index: {
            schema: "spiritflix-manual-model-index/v1",
            updatedAt: "2026-06-21T00:00:01.000Z",
            models: [{ modelName: "Luna Pearl", count: 2 }],
          },
        });
      }
      if (url.includes("/videos/video-1/model")) {
        return Response.json({
          schema: "spiritflix-manual-model/v1",
          itemId: "video-1",
          modelName: "",
          updatedAt: "1970-01-01T00:00:00.000Z",
          source: "manual",
        });
      }
      return Response.json({
        schema: "spiritflix-manual-model-index/v1",
        updatedAt: "2026-06-21T00:00:00.000Z",
        models: [{ modelName: "Luna Pearl", count: 1 }],
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    renderPlayer({
      libraryItems: [
        item,
        { ...nextItem, Id: "video-2", ManualModelName: "Luna Pearl", Path: "/media/luna/two.mp4" },
      ],
    });
    fireEvent.click(screen.getByRole("button", { name: "Edit model name" }));
    fireEvent.click(await screen.findByRole("button", { name: "Luna Pearl" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/videos/video-1/model"), expect.objectContaining({ method: "PUT" })));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/tags?modelName=Luna%20Pearl"), expect.objectContaining({ cache: "no-store" })));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/videos/video-1/tags"), expect.objectContaining({ method: "PUT" })));
  });

  it("shows a face guess and queues face learning after saving a model", async () => {
    const client = createClient();
    vi.mocked(client.getFaceOrganizerMetadata).mockResolvedValue({
      knownPerformers: [],
      videos: {
        "video-1": {
          itemId: "video-1",
          itemPath: item.Path,
          sidecarPath: "/mnt/spirit-8tb/media/yes/Sava Schultz/Fold Tap Test.mp4.face-meta.json",
          primaryPerformer: { name: "Luna Pearl", confidence: 0.62, source: "sidecar" },
          performers: [{ name: "Luna Pearl", confidence: 0.62, source: "sidecar" }],
          status: "needs_review",
          label: "Needs review: Luna Pearl (62%)",
          confidence: 0.62,
          verificationNeeded: true,
        },
      },
      scannedCount: 1,
      generatedAt: "2026-06-21T00:00:00.000Z",
    });
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.includes("/face-learning")) {
        expect(init?.method).toBe("POST");
        expect(JSON.parse(String(init?.body))).toEqual(expect.objectContaining({
          modelName: "Luna Pearl",
          sidecarPath: "/mnt/spirit-8tb/media/yes/Sava Schultz/Fold Tap Test.mp4.face-meta.json",
          faceGuess: expect.objectContaining({ name: "Luna Pearl" }),
        }));
        return Response.json({
          record: {
            schema: "spiritflix-face-learning-request/v1",
            itemId: "video-1",
            filePath: item.Path,
            modelName: "Luna Pearl",
            sidecarPath: "/mnt/spirit-8tb/media/yes/Sava Schultz/Fold Tap Test.mp4.face-meta.json",
            relatedItems: [],
            requestedAt: "2026-06-21T00:00:01.000Z",
            status: "queued",
            actions: {
              pendingCorrectionWritten: true,
              scanCurrentVideoRequested: false,
              scanLibraryMatchesRequested: false,
            },
            source: "player-model-widget",
          },
        });
      }
      if (init?.method === "PUT") {
        return Response.json({
          record: {
            schema: "spiritflix-manual-model/v1",
            itemId: "video-1",
            modelName: "Luna Pearl",
            updatedAt: "2026-06-21T00:00:01.000Z",
            source: "manual",
          },
          index: {
            schema: "spiritflix-manual-model-index/v1",
            updatedAt: "2026-06-21T00:00:01.000Z",
            models: [{ modelName: "Luna Pearl", count: 1 }],
          },
        });
      }
      if (url.includes("/videos/video-1/model")) {
        return Response.json({
          schema: "spiritflix-manual-model/v1",
          itemId: "video-1",
          modelName: "",
          updatedAt: "1970-01-01T00:00:00.000Z",
          source: "manual",
        });
      }
      return Response.json({
        schema: "spiritflix-manual-model-index/v1",
        updatedAt: "2026-06-21T00:00:00.000Z",
        models: [],
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    renderPlayer({ client });
    fireEvent.click(screen.getByRole("button", { name: "Edit model name" }));

    expect(await screen.findByText("Face suggestion")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Use" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/face-learning"), expect.objectContaining({ method: "POST" })));
    expect(await screen.findByText("Face learning queued with sidecar correction.")).toBeInTheDocument();
  });

  it("auto-saves a face match above 80 percent into the model widget", async () => {
    const client = createClient();
    vi.mocked(client.getFaceOrganizerMetadata).mockResolvedValue({
      knownPerformers: [],
      videos: {
        "video-1": {
          itemId: "video-1",
          itemPath: item.Path,
          sidecarPath: "/mnt/spirit-8tb/media/yes/Ruth Lee/Fold Tap Test.mp4.face-meta.json",
          primaryPerformer: { name: "Ruth Lee", confidence: 0.87, source: "sidecar" },
          performers: [{ name: "Ruth Lee", confidence: 0.87, source: "sidecar" }],
          status: "needs_review",
          label: "Needs review: Ruth Lee (87%)",
          confidence: 0.87,
          verificationNeeded: true,
        },
      },
      scannedCount: 1,
      generatedAt: "2026-06-21T00:00:00.000Z",
    });
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.includes("/face-learning")) {
        return Response.json({
          record: {
            schema: "spiritflix-face-learning-request/v1",
            itemId: "video-1",
            filePath: item.Path,
            modelName: "Ruth Lee",
            sidecarPath: "/mnt/spirit-8tb/media/yes/Ruth Lee/Fold Tap Test.mp4.face-meta.json",
            relatedItems: [],
            requestedAt: "2026-06-21T00:00:01.000Z",
            status: "queued",
            actions: {
              pendingCorrectionWritten: true,
              scanCurrentVideoRequested: false,
              scanLibraryMatchesRequested: false,
            },
            source: "player-model-widget",
          },
        });
      }
      if (url.includes("/videos/video-1/model") && init?.method === "PUT") {
        expect(JSON.parse(String(init.body))).toEqual(expect.objectContaining({ modelName: "Ruth Lee" }));
        return Response.json({
          record: {
            schema: "spiritflix-manual-model/v1",
            itemId: "video-1",
            modelName: "Ruth Lee",
            updatedAt: "2026-06-21T00:00:01.000Z",
            source: "manual",
          },
          index: {
            schema: "spiritflix-manual-model-index/v1",
            updatedAt: "2026-06-21T00:00:01.000Z",
            models: [{ modelName: "Ruth Lee", count: 1 }],
          },
        });
      }
      if (url.includes("/videos/video-1/model")) {
        return Response.json({
          schema: "spiritflix-manual-model/v1",
          itemId: "video-1",
          modelName: "",
          updatedAt: "1970-01-01T00:00:00.000Z",
          source: "manual",
        });
      }
      return Response.json({
        schema: "spiritflix-manual-model-index/v1",
        updatedAt: "2026-06-21T00:00:00.000Z",
        models: [],
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    renderPlayer({ client });
    fireEvent.click(screen.getByRole("button", { name: "Edit model name" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/videos/video-1/model"), expect.objectContaining({ method: "PUT" })));
    expect(await screen.findByText("Auto-used face match")).toBeInTheDocument();
    expect(screen.getByText("Auto-saved face match")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Ruth Lee")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Use" })).not.toBeInTheDocument();
  });

  it("shows an applied confirmed face match as confirmed without a use action", async () => {
    const client = createClient();
    vi.mocked(client.getFaceOrganizerMetadata).mockResolvedValue({
      knownPerformers: [],
      videos: {
        "video-1": {
          itemId: "video-1",
          itemPath: item.Path,
          sidecarPath: "/mnt/spirit-8tb/media/yes/Lily Phillips/Fold Tap Test.mp4.face-meta.json",
          primaryPerformer: { name: "Lily Phillips", confidence: 1, source: "sidecar" },
          performers: [{ name: "Lily Phillips", confidence: 1, source: "sidecar" }],
          status: "confirmed",
          label: "Identified: Lily Phillips (100%)",
          confidence: 1,
          verificationNeeded: false,
        },
      },
      scannedCount: 1,
      generatedAt: "2026-06-21T00:00:00.000Z",
    });
    const fetchMock = vi.fn(async (url: string) => {
      if (url.includes("/videos/video-1/model")) {
        return Response.json({
          schema: "spiritflix-manual-model/v1",
          itemId: "video-1",
          modelName: "Lily Phillips",
          updatedAt: "2026-06-21T00:00:00.000Z",
          source: "manual",
        });
      }
      return Response.json({
        schema: "spiritflix-manual-model-index/v1",
        updatedAt: "2026-06-21T00:00:00.000Z",
        models: [{ modelName: "Lily Phillips", count: 1 }],
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    renderPlayer({ client, queueItems: [{ ...item, ManualModelName: "Lily Phillips" }] });
    fireEvent.click(screen.getByRole("button", { name: "Edit model name" }));

    expect(await screen.findByText("Face confirmed saved model")).toBeInTheDocument();
    expect(screen.getByText("Saved + face confirmed")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Use" })).not.toBeInTheDocument();
  });

  it("closes app widgets when player controls are hidden", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (url.includes("/videos/video-1/tags")) {
        return Response.json({
          schema: "spiritflix-manual-tags/v1",
          itemId: "video-1",
          manualTags: ["busty"],
          updatedAt: "2026-06-20T00:00:00.000Z",
          source: "manual",
        });
      }
      return Response.json({
        schema: "spiritflix-manual-tag-index/v1",
        updatedAt: "2026-06-20T00:00:00.000Z",
        tags: [{ tag: "busty", label: "busty", count: 1 }],
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    renderPlayer();
    fireEvent.click(screen.getByRole("button", { name: "Edit manual tags" }));
    expect(await screen.findByLabelText("Action tags")).toBeInTheDocument();

    const player = screen.getByLabelText("Fold Tap Test player");
    Object.defineProperty(player, "clientWidth", { configurable: true, value: 900 });
    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 90, clientY: 320 }]),
    });
    fireEvent.touchEnd(player, {
      changedTouches: touchList([{ clientX: 90, clientY: 320 }]),
      touches: touchList([]),
    });

    await waitFor(() => expect(screen.queryByLabelText("Action tags")).not.toBeInTheDocument());
  });

  it("keeps app widgets open while editing instead of closing on the short controls timeout", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (url.includes("/videos/video-1/tags")) {
        return Response.json({
          schema: "spiritflix-manual-tags/v1",
          itemId: "video-1",
          manualTags: ["busty"],
          updatedAt: "2026-06-20T00:00:00.000Z",
          source: "manual",
        });
      }
      return Response.json({
        schema: "spiritflix-manual-tag-index/v1",
        updatedAt: "2026-06-20T00:00:00.000Z",
        tags: [{ tag: "busty", label: "busty", count: 1 }],
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    renderPlayer();
    fireEvent.click(screen.getByRole("button", { name: "Edit manual tags" }));
    expect(await screen.findByLabelText("Action tags")).toBeInTheDocument();

    vi.useFakeTimers();
    act(() => {
      vi.advanceTimersByTime(3000);
    });
    expect(screen.getByLabelText("Action tags")).toBeInTheDocument();

    const input = screen.getByLabelText("Add manual tag");
    input.focus();
    act(() => {
      vi.advanceTimersByTime(60000);
    });

    expect(screen.getByLabelText("Action tags")).toBeInTheDocument();
    vi.useRealTimers();
  });

  it("previews and confirms a yes-folder video soft delete from the player tools", async () => {
    const onClose = vi.fn();
    const onDeleteItem = vi.fn();
    const fetchMock = vi.fn(async (_url: string, init?: RequestInit) => {
      if (init?.method === "POST") {
        const payload = JSON.parse(String(init.body));
        if (payload.mode === "preview") {
          expect(payload).toEqual(expect.objectContaining({
            action: "softDelete",
            sourcePath: "/mnt/spirit-8tb/media/yes/Sava Schultz/Fold Tap Test.mp4",
          }));
          return Response.json({
            schema: "spiritflix-admin-action/v1",
            action: "softDelete",
            phase: "preview",
            previewId: "preview-delete-1",
            allowed: true,
            message: "Move item to soft trash",
            preview: {
              sourcePath: payload.sourcePath,
              targetPath: "/mnt/spirit-8tb/media/.trash/20260621/yes/Sava Schultz/Fold Tap Test.mp4",
              affectedPaths: [payload.sourcePath],
              warnings: [],
              reversible: true,
            },
          });
        }
        expect(payload).toEqual(expect.objectContaining({
          action: "softDelete",
          mode: "execute",
          confirmToken: "preview-delete-1",
        }));
        return Response.json({
          schema: "spiritflix-admin-action/v1",
          action: "softDelete",
          phase: "execute",
          previewId: "preview-delete-1",
          allowed: true,
          message: "Moved to trash.",
        });
      }
      return Response.json({ schema: "spiritflix-manual-tag-index/v1", updatedAt: "2026-06-20T00:00:00.000Z", tags: [] });
    });
    vi.stubGlobal("fetch", fetchMock);

    renderPlayer({ onClose, onDeleteItem, queueItems: [item, nextItem] });
    fireEvent.click(screen.getByRole("button", { name: "Delete video" }));

    expect(await screen.findByText("Move this video to trash?")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("button", { name: "Delete" })).not.toBeDisabled());

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => expect(onDeleteItem).toHaveBeenCalledWith(item, nextItem));
    expect(onClose).not.toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledWith("/api/spiritflix/admin/actions", expect.objectContaining({ method: "POST" }));
  });

  it("normalizes container media paths before soft delete preview", async () => {
    const containerPathItem = { ...item, Path: "/media/yes/Sava Schultz/Fold Tap Test.mp4" };
    const fetchMock = vi.fn(async (_url: string, init?: RequestInit) => {
      const payload = JSON.parse(String(init?.body));
      expect(payload.sourcePath).toBe("/mnt/spirit-8tb/media/yes/Sava Schultz/Fold Tap Test.mp4");
      return Response.json({
        schema: "spiritflix-admin-action/v1",
        action: "softDelete",
        phase: "preview",
        previewId: "preview-delete-1",
        allowed: true,
        message: "Move item to soft trash",
        preview: {
          sourcePath: payload.sourcePath,
          targetPath: "/mnt/spirit-8tb/media/.trash/20260621/yes/Sava Schultz/Fold Tap Test.mp4",
          affectedPaths: [payload.sourcePath],
          warnings: [],
          reversible: true,
        },
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    renderPlayer({ itemOverride: containerPathItem });
    fireEvent.click(screen.getByRole("button", { name: "Delete video" }));

    expect(await screen.findByText("Move this video to trash?")).toBeInTheDocument();
  });

  it("shows private playback diagnostics with the selected mode", async () => {
    renderPlayer();

    await waitFor(() => expect(screen.getByLabelText("Fold Tap Test player")).toHaveClass("is-awake"));

    expect(screen.getByLabelText("Playback diagnostics")).toHaveTextContent("direct stream");
    fireEvent.click(screen.getByRole("button", { name: "Details" }));
    expect(screen.getByText("Live transcode")).toBeInTheDocument();
    expect(screen.getByText("Dell ffmpeg active")).toBeInTheDocument();
  });

  it("does not show a fatal stream error for browser-aborted playback transitions", async () => {
    Object.defineProperty(HTMLMediaElement.prototype, "play", {
      configurable: true,
      value: vi.fn().mockRejectedValue(new DOMException("The fetching process for the media resource was aborted by the user agent at the user's request.", "AbortError")),
    });

    renderPlayer();

    await waitFor(() => expect(screen.getByLabelText("Fold Tap Test player")).toHaveClass("is-awake"));

    await waitFor(() => {
      expect(screen.queryByText("Stream unavailable")).not.toBeInTheDocument();
    });
  });

  it("keeps repeat and shuffle as separate controls", async () => {
    const onShuffleQueue = vi.fn();
    renderPlayer({ onShuffleQueue, queueItems: [item, nextItem] });

    await waitFor(() => expect(screen.getByLabelText("Fold Tap Test player")).toHaveClass("is-awake"));

    expect(screen.getByRole("button", { name: "Repeat off" })).toBeInTheDocument();
    const shuffleButton = screen.getByRole("button", { name: "Shuffle off for Test Queue" });
    expect(shuffleButton).not.toBeDisabled();
    expect(shuffleButton).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(screen.getByRole("button", { name: "Repeat off" }));

    expect(onShuffleQueue).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Repeat queue" })).toBeInTheDocument();

    fireEvent.click(shuffleButton);
    expect(onShuffleQueue).toHaveBeenCalledWith("video-1");
  });

  it("opens orientation shuffle choices from the shuffle button hold menu", async () => {
    const onShuffleQueue = vi.fn();
    renderPlayer({ onShuffleQueue, queueItems: [item, nextItem, { ...item, Id: "video-3", Name: "Portrait Two" }] });

    await waitFor(() => expect(screen.getByLabelText("Fold Tap Test player")).toHaveClass("is-awake"));

    fireEvent.contextMenu(screen.getByRole("button", { name: "Shuffle off for Test Queue" }));
    expect(screen.getByRole("menu", { name: "Shuffle by video orientation" })).toBeInTheDocument();
    const portraitShuffle = screen.getByRole("menuitem", { name: /^portrait\s+2$/i });
    expect(screen.getByRole("menuitem", { name: /^landscape\s+1$/i })).toBeDisabled();
    expect(portraitShuffle.querySelector(".spiritflix-player__shuffle-picker-label")).toHaveTextContent("Portrait");
    expect(portraitShuffle.querySelector(".spiritflix-player__shuffle-picker-count")).toHaveTextContent("2");

    fireEvent.click(portraitShuffle);

    expect(onShuffleQueue).toHaveBeenCalledWith("video-1", "portrait");
  });

  it("shows shuffle as active when the queue is shuffled", async () => {
    renderPlayer({ queueItems: [item, nextItem], isShuffled: true });

    await waitFor(() => expect(screen.getByLabelText("Fold Tap Test player")).toHaveClass("is-awake"));

    const shuffleButton = screen.getByRole("button", { name: "Shuffle on for Test Queue" });
    expect(shuffleButton).toHaveClass("is-active");
    expect(shuffleButton).toHaveAttribute("aria-pressed", "true");
  });

  it("opens the playback queue drawer and selects a queued item", async () => {
    const onSelectItem = vi.fn();
    renderPlayer({ onSelectItem, queueItems: [item, nextItem] });

    await waitFor(() => expect(screen.getByLabelText("Fold Tap Test player")).toHaveClass("is-awake"));

    fireEvent.click(screen.getByRole("button", { name: "Open queue" }));

    expect(screen.getByLabelText("Playback queue")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Drag Fold Tap Test to reorder queue" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "01 Fold Tap Test" })).toHaveAttribute("aria-current", "true");

    fireEvent.click(screen.getByRole("button", { name: "02 Queue Next Test" }));

    expect(onSelectItem).toHaveBeenCalledWith(nextItem);
    expect(screen.queryByLabelText("Playback queue")).not.toBeInTheDocument();
  });

  it("loads queue drawer thumbnails eagerly from Jellyfin Thumb image tags", async () => {
    const client = createClient();
    const currentWithThumb = {
      ...item,
      ImageTags: {
        Primary: "primary-current",
        Thumb: "thumb-current",
      },
    };
    const nextWithThumb = {
      ...nextItem,
      ImageTags: {
        Thumb: "thumb-next",
      },
    };

    renderPlayer({
      client,
      itemOverride: currentWithThumb,
      queueItems: [currentWithThumb, nextWithThumb],
    });

    await waitFor(() => expect(screen.getByLabelText("Fold Tap Test player")).toHaveClass("is-awake"));
    fireEvent.click(screen.getByRole("button", { name: "Open queue" }));

    await waitFor(() => {
      expect(client.getImageProxyUrl).toHaveBeenCalledWith(expect.objectContaining({ Id: "video-1" }), "Thumb", 160);
      expect(client.getImageProxyUrl).toHaveBeenCalledWith(expect.objectContaining({ Id: "video-2" }), "Thumb", 160);
    });
  });

  it("enables the mini player button when Picture-in-Picture is supported", async () => {
    const requestPictureInPicture = vi.fn().mockResolvedValue({});
    Object.defineProperty(document, "pictureInPictureEnabled", {
      configurable: true,
      value: true,
    });
    Object.defineProperty(HTMLVideoElement.prototype, "requestPictureInPicture", {
      configurable: true,
      value: requestPictureInPicture,
    });

    renderPlayer();

    await waitFor(() => expect(screen.getByRole("button", { name: "Mini player" })).not.toBeDisabled());
    const video = document.querySelector("video");
    expect(video).not.toHaveAttribute("disablePictureInPicture");

    fireEvent.click(screen.getByRole("button", { name: "Mini player" }));

    await waitFor(() => expect(requestPictureInPicture).toHaveBeenCalledTimes(1));
  });

  it("falls back to an in-app mini player when native Picture-in-Picture is unavailable", async () => {
    Object.defineProperty(document, "pictureInPictureEnabled", {
      configurable: true,
      value: false,
    });
    Object.defineProperty(HTMLVideoElement.prototype, "requestPictureInPicture", {
      configurable: true,
      value: undefined,
    });

    renderPlayer();

    const player = screen.getByLabelText("Fold Tap Test player");
    const miniButton = await screen.findByRole("button", { name: "Mini player" });
    expect(miniButton).not.toBeDisabled();

    fireEvent.click(miniButton);

    await waitFor(() => expect(player).toHaveClass("is-app-mini"));
    fireEvent.click(screen.getByRole("button", { name: "Back to tab" }));
    await waitFor(() => expect(player).not.toHaveClass("is-app-mini"));
  });

  it("prefers the in-app mini player on mobile even when native Picture-in-Picture exists", async () => {
    const requestPictureInPicture = vi.fn().mockResolvedValue({});
    Object.defineProperty(document, "pictureInPictureEnabled", {
      configurable: true,
      value: true,
    });
    Object.defineProperty(HTMLVideoElement.prototype, "requestPictureInPicture", {
      configurable: true,
      value: requestPictureInPicture,
    });
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: vi.fn().mockReturnValue({ matches: true }),
    });

    renderPlayer();

    const player = screen.getByLabelText("Fold Tap Test player");
    fireEvent.click(await screen.findByRole("button", { name: "Mini player" }));

    await waitFor(() => expect(player).toHaveClass("is-app-mini"));
    expect(requestPictureInPicture).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Back to tab" })).toBeInTheDocument();
  });

  it("seeks backward and forward by 10 seconds on side double taps", async () => {
    renderPlayer();

    const player = screen.getByLabelText("Fold Tap Test player");
    Object.defineProperty(player, "clientWidth", { configurable: true, value: 900 });
    const video = document.querySelector("video");
    expect(video).not.toBeNull();
    if (!video) return;
    video.currentTime = 50;

    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 300, clientY: 320 }]),
    });
    fireEvent.touchEnd(player, {
      changedTouches: touchList([{ clientX: 300, clientY: 320 }]),
      touches: touchList([]),
    });

    await waitFor(() => expect(player).toHaveClass("is-controls-hidden"));

    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 90, clientY: 320 }]),
    });
    fireEvent.touchEnd(player, {
      changedTouches: touchList([{ clientX: 90, clientY: 320 }]),
      touches: touchList([]),
    });
    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 90, clientY: 320 }]),
    });
    fireEvent.touchEnd(player, {
      changedTouches: touchList([{ clientX: 90, clientY: 320 }]),
      touches: touchList([]),
    });

    expect(video.currentTime).toBe(40);
    expect(screen.getByText("10s")).toBeInTheDocument();

    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 300, clientY: 320 }]),
    });
    fireEvent.touchEnd(player, {
      changedTouches: touchList([{ clientX: 300, clientY: 320 }]),
      touches: touchList([]),
    });

    await waitFor(() => expect(player).toHaveClass("is-controls-hidden"));

    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 810, clientY: 320 }]),
    });
    fireEvent.touchEnd(player, {
      changedTouches: touchList([{ clientX: 810, clientY: 320 }]),
      touches: touchList([]),
    });
    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 810, clientY: 320 }]),
    });
    fireEvent.touchEnd(player, {
      changedTouches: touchList([{ clientX: 810, clientY: 320 }]),
      touches: touchList([]),
    });

    expect(video.currentTime).toBe(50);
  });

  it("seeks by 10 seconds on side double taps even when controls start visible", async () => {
    renderPlayer();

    const player = screen.getByLabelText("Fold Tap Test player");
    Object.defineProperty(player, "clientWidth", { configurable: true, value: 900 });
    const video = document.querySelector("video");
    expect(video).not.toBeNull();
    if (!video) return;
    video.currentTime = 50;

    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 90, clientY: 320 }]),
    });
    fireEvent.touchEnd(player, {
      changedTouches: touchList([{ clientX: 90, clientY: 320 }]),
      touches: touchList([]),
    });
    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 90, clientY: 320 }]),
    });
    fireEvent.touchEnd(player, {
      changedTouches: touchList([{ clientX: 90, clientY: 320 }]),
      touches: touchList([]),
    });

    expect(video.currentTime).toBe(40);
    expect(screen.getByText("10s")).toBeInTheDocument();
  });

  it("does not turn a surface hide tap into an accidental seek", async () => {
    renderPlayer();

    const player = screen.getByLabelText("Fold Tap Test player");
    Object.defineProperty(player, "clientWidth", { configurable: true, value: 900 });
    const video = document.querySelector("video");
    expect(video).not.toBeNull();
    if (!video) return;
    video.currentTime = 50;

    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 315, clientY: 320 }]),
    });
    fireEvent.touchEnd(player, {
      changedTouches: touchList([{ clientX: 315, clientY: 320 }]),
      touches: touchList([]),
    });
    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 315, clientY: 320 }]),
    });
    fireEvent.touchEnd(player, {
      changedTouches: touchList([{ clientX: 315, clientY: 320 }]),
      touches: touchList([]),
    });

    expect(video.currentTime).toBe(50);
    expect(screen.queryByText("10s")).not.toBeInTheDocument();
  });

  it("selects the next queued video on swipe up when TikTok mode is enabled", async () => {
    const onSelectItem = vi.fn();
    renderPlayer({ onSelectItem, queueItems: [item, nextItem] });

    const player = screen.getByLabelText("Fold Tap Test player");
    fireEvent.click(screen.getByRole("button", { name: "More player controls" }));
    fireEvent.click(screen.getByRole("button", { name: "TikTok swipe mode off" }));

    expect(window.localStorage.getItem("spiritflix_player_tiktok_mode")).toBe("true");

    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 420, clientY: 700 }]),
    });
    fireEvent.touchEnd(player, {
      changedTouches: touchList([{ clientX: 418, clientY: 520 }]),
      touches: touchList([]),
    });

    expect(onSelectItem).toHaveBeenCalledWith(nextItem);
  });

  it("selects the previous queued video on swipe down when TikTok mode is enabled", async () => {
    const onSelectItem = vi.fn();
    const previousItem = { ...item, Id: "video-0", Name: "Queue Previous Test" };
    renderPlayer({ itemOverride: nextItem, onSelectItem, queueItems: [previousItem, nextItem] });

    const player = screen.getByLabelText("Queue Next Test player");
    fireEvent.click(screen.getByRole("button", { name: "More player controls" }));
    fireEvent.click(screen.getByRole("button", { name: "TikTok swipe mode off" }));

    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 420, clientY: 460 }]),
    });
    fireEvent.touchEnd(player, {
      changedTouches: touchList([{ clientX: 422, clientY: 640 }]),
      touches: touchList([]),
    });

    expect(onSelectItem).toHaveBeenCalledWith(previousItem);
  });

  it("does not seek on a quick horizontal slip", async () => {
    renderPlayer();

    const player = screen.getByLabelText("Fold Tap Test player");
    Object.defineProperty(player, "clientWidth", { configurable: true, value: 900 });
    const video = document.querySelector("video");
    expect(video).not.toBeNull();
    if (!video) return;
    video.currentTime = 30;

    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 100, clientY: 320 }]),
    });
    fireEvent.touchMove(player, {
      touches: touchList([{ clientX: 175, clientY: 322 }]),
    });

    expect(video.currentTime).toBe(30);
    expect(screen.queryByText("10s")).not.toBeInTheDocument();
  });

  it("uses a fixed-rate hold-and-drag seek on touch move", async () => {
    renderPlayer();

    const player = screen.getByLabelText("Fold Tap Test player");
    Object.defineProperty(player, "clientWidth", { configurable: true, value: 900 });
    const video = document.querySelector("video");
    expect(video).not.toBeNull();
    if (!video) return;
    video.currentTime = 30;
    let now = 1000;
    vi.spyOn(Date, "now").mockImplementation(() => now);

    fireEvent.touchStart(player, {
      touches: touchList([{ clientX: 100, clientY: 320 }]),
    });
    now += 220;
    fireEvent.touchMove(player, {
      touches: touchList([{ clientX: 175, clientY: 322 }]),
    });

    expect(video.currentTime).toBe(40);
    expect(screen.getByText("10s")).toBeInTheDocument();
  });
});
