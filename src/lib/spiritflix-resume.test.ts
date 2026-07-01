import { describe, expect, it } from "vitest";
import type { JellyfinItem } from "./spiritflix-types";
import { getResumeProgressPercent, hasResumeProgress } from "./spiritflix-resume";

const TICKS_PER_SECOND = 10_000_000;

function video(overrides: Partial<JellyfinItem> = {}): JellyfinItem {
  return {
    Id: "video-1",
    Name: "Resume Candidate",
    Type: "Video",
    MediaType: "Video",
    RunTimeTicks: 10 * 60 * TICKS_PER_SECOND,
    UserData: {
      PlaybackPositionTicks: 3 * 60 * TICKS_PER_SECOND,
      Played: false,
      PlayedPercentage: 30,
    },
    ...overrides,
  };
}

describe("SpiritFlix resume rules", () => {
  it("treats a saved midpoint position as resumable even when Jellyfin marks the item played", () => {
    expect(hasResumeProgress(video({
      UserData: {
        PlaybackPositionTicks: 3 * 60 * TICKS_PER_SECOND,
        Played: true,
        PlayedPercentage: 100,
      },
    }))).toBe(true);
  });

  it("does not resume items that are effectively finished", () => {
    expect(hasResumeProgress(video({
      UserData: {
        PlaybackPositionTicks: (10 * 60 - 10) * TICKS_PER_SECOND,
        Played: false,
        PlayedPercentage: 98,
      },
    }))).toBe(false);
  });

  it("uses actual saved position for progress when percentage is stale", () => {
    expect(getResumeProgressPercent(video({
      UserData: {
        PlaybackPositionTicks: 3 * 60 * TICKS_PER_SECOND,
        Played: true,
        PlayedPercentage: 100,
      },
    }))).toBe(30);
  });
});
