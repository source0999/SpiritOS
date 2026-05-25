import type {
  CurationCheck,
  MediaProfileId,
  PlaybackAcceptanceEvidence,
  PlaybackProgress,
} from "@/components/media/media-types";
import { mediaDb, type SpiritMediaDB } from "@/lib/media/media-db";
import {
  writeMediaProfileCurationCheck,
  writeMediaProfilePlaybackAcceptance,
  writeMediaProfilePlaybackProgress,
  writeMediaProfileWatchlistEntry,
  type MediaProfileStateWritableTables,
  type MediaProfileStateWriteSummary,
} from "@/lib/media/media-profile-state-write";

export type MediaProfileStateBrowserWriteResult =
  | {
      status: "unavailable";
      reason: "indexeddb-unavailable";
    }
  | {
      status: "written";
      summary: MediaProfileStateWriteSummary;
    };

function toProfileStateWritableTables(
  db: SpiritMediaDB,
): MediaProfileStateWritableTables {
  return {
    watchlistEntries: db.watchlistEntries,
    playbackProgress: db.playbackProgress,
    curationChecks: db.curationChecks,
    playbackAcceptance: db.playbackAcceptance,
  };
}

function unavailable(): MediaProfileStateBrowserWriteResult {
  return {
    status: "unavailable",
    reason: "indexeddb-unavailable",
  };
}

export async function writeMediaProfileWatchlistEntryWhenAvailable(
  profileId: MediaProfileId,
  catalogItemId: string,
  inWatchlist: boolean,
  createdAt: string,
  db: SpiritMediaDB | null | undefined = mediaDb,
): Promise<MediaProfileStateBrowserWriteResult> {
  if (!db) {
    return unavailable();
  }

  return {
    status: "written",
    summary: await writeMediaProfileWatchlistEntry(
      toProfileStateWritableTables(db),
      profileId,
      catalogItemId,
      inWatchlist,
      createdAt,
    ),
  };
}

export async function writeMediaProfilePlaybackProgressWhenAvailable(
  profileId: MediaProfileId,
  progress: PlaybackProgress,
  db: SpiritMediaDB | null | undefined = mediaDb,
): Promise<MediaProfileStateBrowserWriteResult> {
  if (!db) {
    return unavailable();
  }

  return {
    status: "written",
    summary: await writeMediaProfilePlaybackProgress(
      toProfileStateWritableTables(db),
      profileId,
      progress,
    ),
  };
}

export async function writeMediaProfileCurationCheckWhenAvailable(
  profileId: MediaProfileId,
  curationCheck: CurationCheck,
  db: SpiritMediaDB | null | undefined = mediaDb,
): Promise<MediaProfileStateBrowserWriteResult> {
  if (!db) {
    return unavailable();
  }

  return {
    status: "written",
    summary: await writeMediaProfileCurationCheck(
      toProfileStateWritableTables(db),
      profileId,
      curationCheck,
    ),
  };
}

export async function writeMediaProfilePlaybackAcceptanceWhenAvailable(
  profileId: MediaProfileId,
  playbackAcceptance: PlaybackAcceptanceEvidence,
  db: SpiritMediaDB | null | undefined = mediaDb,
): Promise<MediaProfileStateBrowserWriteResult> {
  if (!db) {
    return unavailable();
  }

  return {
    status: "written",
    summary: await writeMediaProfilePlaybackAcceptance(
      toProfileStateWritableTables(db),
      profileId,
      playbackAcceptance,
    ),
  };
}
