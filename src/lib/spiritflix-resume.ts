import type { JellyfinItem } from "./spiritflix-types";
import { ticksToSeconds } from "./spiritflix-jellyfin-client";

export function formatResumeTime(seconds: number): string {
  if (!Number.isFinite(seconds)) return "0:00";
  const whole = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(whole / 3600);
  const minutes = Math.floor((whole % 3600) / 60);
  const rest = whole % 60;
  return hours
    ? `${hours}:${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`
    : `${minutes}:${String(rest).padStart(2, "0")}`;
}

export function getResumePositionTicks(item: JellyfinItem): number {
  return Math.max(0, item.UserData?.PlaybackPositionTicks ?? 0);
}

export function getResumeProgressPercent(item: JellyfinItem): number {
  const positionTicks = getResumePositionTicks(item);
  const runtimeTicks = item.RunTimeTicks ?? 0;
  if (positionTicks && runtimeTicks) {
    return Math.max(0, Math.min(100, (positionTicks / runtimeTicks) * 100));
  }
  if (item.UserData?.PlayedPercentage && item.UserData.PlayedPercentage > 0) {
    return Math.max(0, Math.min(100, item.UserData.PlayedPercentage));
  }
  return 0;
}

export function hasResumeProgress(item: JellyfinItem): boolean {
  const positionSeconds = ticksToSeconds(getResumePositionTicks(item));
  const durationSeconds = ticksToSeconds(item.RunTimeTicks);
  if (positionSeconds <= 0) return false;
  if (durationSeconds > 0 && positionSeconds >= durationSeconds - 20) return false;
  if (item.UserData?.Played && durationSeconds <= 0) return false;
  return true;
}

/** True once this user has started or completed the item in Jellyfin. */
export function hasWatchActivity(item: JellyfinItem): boolean {
  return Boolean(
    item.UserData?.LastPlayedDate ||
      item.UserData?.Played ||
      (item.UserData?.PlaybackPositionTicks && item.UserData.PlaybackPositionTicks > 0) ||
      (item.UserData?.PlayCount && item.UserData.PlayCount > 0),
  );
}

export function getResumeSlotLabel(item: JellyfinItem): string {
  const positionSeconds = ticksToSeconds(getResumePositionTicks(item));
  const durationSeconds = ticksToSeconds(item.RunTimeTicks);
  if (durationSeconds > 0) {
    return `${formatResumeTime(positionSeconds)} / ${formatResumeTime(durationSeconds)}`;
  }
  return `Resume from ${formatResumeTime(positionSeconds)}`;
}

export function getTimeLeftLabel(item: JellyfinItem): string {
  const positionSeconds = ticksToSeconds(getResumePositionTicks(item));
  const durationSeconds = ticksToSeconds(item.RunTimeTicks);
  if (!durationSeconds || durationSeconds <= positionSeconds) return "";
  const minutesLeft = Math.max(1, Math.ceil((durationSeconds - positionSeconds) / 60));
  return `${minutesLeft}m left`;
}
