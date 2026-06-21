import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getSmartFillScale, SpiritFlixPlayer } from "../SpiritFlixPlayer";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix-types";

const item: JellyfinItem = {
  Id: "video-1",
  Name: "Fold Tap Test",
  Type: "Video",
  RunTimeTicks: 1200000000,
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
    getStreamUrl: vi.fn(() => "https://media.example/video.mp4"),
    reportPlayback: vi.fn().mockResolvedValue(undefined),
  } as unknown as JellyfinClient;
}

function renderPlayer(options: {
  onSelectItem?: (item: JellyfinItem) => void;
  onShuffleQueue?: (currentItemId: string) => void;
  queueItems?: JellyfinItem[];
  isShuffled?: boolean;
} = {}) {
  const queueItems = options.queueItems;
  return render(
    <SpiritFlixPlayer
      client={createClient()}
      item={item}
      queue={
        queueItems
          ? {
              items: queueItems,
              originalItems: queueItems,
              currentIndex: Math.max(0, queueItems.findIndex((queueItem) => queueItem.Id === item.Id)),
              sourceTitle: "Test Queue",
              isShuffled: options.isShuffled,
            }
          : null
      }
      onPlaybackProgress={vi.fn()}
      onToggleFavorite={vi.fn()}
      onSelectItem={options.onSelectItem ?? vi.fn()}
      onShuffleQueue={options.onShuffleQueue ?? vi.fn()}
      onClose={vi.fn()}
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
    global.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  });

  afterEach(() => {
    vi.restoreAllMocks();
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

    fireEvent.click(screen.getByRole("button", { name: "Unmute" }));

    const video = document.querySelector("video");
    expect(video?.muted).toBe(false);
    expect(video?.volume).toBe(0.8);
    expect(screen.getByLabelText("Volume")).toHaveValue("0.8");
    expect(screen.getByRole("button", { name: "Mute" })).toHaveAttribute("aria-expanded", "true");
  });

  it("keeps diagnostics out of the visible player controls", async () => {
    renderPlayer();

    await waitFor(() => expect(screen.getByLabelText("Fold Tap Test player")).toHaveClass("is-awake"));

    expect(screen.queryByRole("button", { name: "Playback diagnostics" })).not.toBeInTheDocument();
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
    expect(screen.getByRole("button", { name: /Fold Tap Test/i })).toHaveAttribute("aria-current", "true");

    fireEvent.click(screen.getByRole("button", { name: /Queue Next Test/i }));

    expect(onSelectItem).toHaveBeenCalledWith(nextItem);
    expect(screen.queryByLabelText("Playback queue")).not.toBeInTheDocument();
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
