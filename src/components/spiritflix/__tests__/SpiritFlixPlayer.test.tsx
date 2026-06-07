import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SpiritFlixPlayer } from "../SpiritFlixPlayer";
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

function createClient(): JellyfinClient {
  return {
    checkPublicInfo: vi.fn().mockResolvedValue({}),
    getHlsUrl: vi.fn(() => "https://media.example/hls.m3u8"),
    getStreamUrl: vi.fn(() => "https://media.example/video.mp4"),
    reportPlayback: vi.fn().mockResolvedValue(undefined),
  } as unknown as JellyfinClient;
}

function renderPlayer() {
  return render(
    <SpiritFlixPlayer
      client={createClient()}
      item={item}
      queue={null}
      onPlaybackProgress={vi.fn()}
      onToggleFavorite={vi.fn()}
      onSelectItem={vi.fn()}
      onClose={vi.fn()}
    />,
  );
}

function touchList(touches: Array<{ clientX: number; clientY: number }>) {
  return Object.assign([...touches], {
    item: (index: number) => touches[index] ?? null,
  });
}

describe("SpiritFlixPlayer mobile controls", () => {
  beforeEach(() => {
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
    global.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
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
});
