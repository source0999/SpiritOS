import type {
  CurationCheck,
  MediaProfileId,
  PlaybackAcceptanceEvidence,
  PlaybackProgress,
} from "@/components/media/media-types";
import {
  writeMediaProfileCurationCheckWhenAvailable,
  writeMediaProfilePlaybackAcceptanceWhenAvailable,
  writeMediaProfilePlaybackProgressWhenAvailable,
  writeMediaProfileWatchlistEntryWhenAvailable,
  type MediaProfileStateBrowserWriteResult,
} from "@/lib/media/media-profile-state-browser-write";

export type MediaProfileStateDualWriteResult = {
  localStorage: "written";
  dexie: MediaProfileStateBrowserWriteResult | { status: "skipped" };
};

export async function writeProfileWatchlistEntryBestEffort(
  profileId: MediaProfileId,
  catalogItemId: string,
  inWatchlist: boolean,
  createdAt: string,
): Promise<MediaProfileStateDualWriteResult> {
  return {
    localStorage: "written",
    dexie: await writeMediaProfileWatchlistEntryWhenAvailable(
      profileId,
      catalogItemId,
      inWatchlist,
      createdAt,
    ),
  };
}

export async function writeProfilePlaybackProgressBestEffort(
  profileId: MediaProfileId,
  progress: PlaybackProgress | undefined,
): Promise<MediaProfileStateDualWriteResult> {
  if (!progress) {
    return {
      localStorage: "written",
      dexie: {
        status: "skipped",
      },
    };
  }

  return {
    localStorage: "written",
    dexie: await writeMediaProfilePlaybackProgressWhenAvailable(
      profileId,
      progress,
    ),
  };
}

export async function writeProfileCurationCheckBestEffort(
  profileId: MediaProfileId,
  curationCheck: CurationCheck | undefined,
): Promise<MediaProfileStateDualWriteResult> {
  if (!curationCheck) {
    return {
      localStorage: "written",
      dexie: {
        status: "skipped",
      },
    };
  }

  return {
    localStorage: "written",
    dexie: await writeMediaProfileCurationCheckWhenAvailable(
      profileId,
      curationCheck,
    ),
  };
}

export async function writeProfilePlaybackAcceptanceBestEffort(
  profileId: MediaProfileId,
  playbackAcceptance: PlaybackAcceptanceEvidence | undefined,
): Promise<MediaProfileStateDualWriteResult> {
  if (!playbackAcceptance) {
    return {
      localStorage: "written",
      dexie: {
        status: "skipped",
      },
    };
  }

  return {
    localStorage: "written",
    dexie: await writeMediaProfilePlaybackAcceptanceWhenAvailable(
      profileId,
      playbackAcceptance,
    ),
  };
}
