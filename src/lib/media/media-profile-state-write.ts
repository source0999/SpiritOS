import type {
  CurationCheck,
  MediaProfileId,
  PlaybackAcceptanceEvidence,
  PlaybackProgress,
} from "@/components/media/media-types";
import type {
  DurableMediaCurationCheckRecord,
  DurableMediaPlaybackAcceptanceEvidenceRecord,
  DurableMediaPlaybackProgressRecord,
  DurableMediaWatchlistEntryRecord,
} from "@/lib/media/media-durable-types";

type PutWritableTable<TRecord> = {
  put: (record: TRecord) => Promise<unknown>;
};

type DeleteWritableTable<TKey> = {
  delete: (key: TKey) => Promise<unknown>;
};

export type MediaProfileStateWritableTables = {
  watchlistEntries: PutWritableTable<DurableMediaWatchlistEntryRecord> &
    DeleteWritableTable<[MediaProfileId, string]>;
  playbackProgress: PutWritableTable<DurableMediaPlaybackProgressRecord>;
  curationChecks: PutWritableTable<DurableMediaCurationCheckRecord>;
  playbackAcceptance: PutWritableTable<DurableMediaPlaybackAcceptanceEvidenceRecord>;
};

export type MediaProfileStateWriteSummary =
  | {
      tableName: "watchlistEntries";
      action: "put" | "delete";
      profileId: MediaProfileId;
      catalogItemId: string;
    }
  | {
      tableName: "playbackProgress";
      action: "put";
      profileId: MediaProfileId;
      catalogItemId: string;
      seconds: number;
    }
  | {
      tableName: "curationChecks";
      action: "put";
      profileId: MediaProfileId;
      catalogItemId: string;
      authorizedFileConfirmed: boolean;
    }
  | {
      tableName: "playbackAcceptance";
      action: "put";
      profileId: MediaProfileId;
      catalogItemId: string;
      complete: boolean;
    };

export async function writeMediaProfileWatchlistEntry(
  tables: MediaProfileStateWritableTables,
  profileId: MediaProfileId,
  catalogItemId: string,
  inWatchlist: boolean,
  createdAt: string,
): Promise<MediaProfileStateWriteSummary> {
  if (!inWatchlist) {
    await tables.watchlistEntries.delete([profileId, catalogItemId]);
    return {
      tableName: "watchlistEntries",
      action: "delete",
      profileId,
      catalogItemId,
    };
  }

  await tables.watchlistEntries.put({
    profileId,
    catalogItemId,
    createdAt,
  });

  return {
    tableName: "watchlistEntries",
    action: "put",
    profileId,
    catalogItemId,
  };
}

export async function writeMediaProfilePlaybackProgress(
  tables: MediaProfileStateWritableTables,
  profileId: MediaProfileId,
  progress: PlaybackProgress,
): Promise<MediaProfileStateWriteSummary> {
  const seconds = Math.max(0, Math.floor(progress.seconds));

  await tables.playbackProgress.put({
    profileId,
    catalogItemId: progress.itemId,
    seconds,
    updatedAt: progress.updatedAt,
  });

  return {
    tableName: "playbackProgress",
    action: "put",
    profileId,
    catalogItemId: progress.itemId,
    seconds,
  };
}

export async function writeMediaProfileCurationCheck(
  tables: MediaProfileStateWritableTables,
  profileId: MediaProfileId,
  curationCheck: CurationCheck,
): Promise<MediaProfileStateWriteSummary> {
  await tables.curationChecks.put({
    profileId,
    catalogItemId: curationCheck.itemId,
    authorizedFileConfirmed: curationCheck.authorizedFileConfirmed,
    updatedAt: curationCheck.updatedAt,
  });

  return {
    tableName: "curationChecks",
    action: "put",
    profileId,
    catalogItemId: curationCheck.itemId,
    authorizedFileConfirmed: curationCheck.authorizedFileConfirmed,
  };
}

export async function writeMediaProfilePlaybackAcceptance(
  tables: MediaProfileStateWritableTables,
  profileId: MediaProfileId,
  playbackAcceptance: PlaybackAcceptanceEvidence,
): Promise<MediaProfileStateWriteSummary> {
  const complete =
    playbackAcceptance.sourceReadyConfirmed &&
    playbackAcceptance.refreshProgressConfirmed &&
    playbackAcceptance.profileIsolationConfirmed;

  await tables.playbackAcceptance.put({
    profileId,
    catalogItemId: playbackAcceptance.itemId,
    sourceReadyConfirmed: playbackAcceptance.sourceReadyConfirmed,
    refreshProgressConfirmed: playbackAcceptance.refreshProgressConfirmed,
    profileIsolationConfirmed: playbackAcceptance.profileIsolationConfirmed,
    updatedAt: playbackAcceptance.updatedAt,
  });

  return {
    tableName: "playbackAcceptance",
    action: "put",
    profileId,
    catalogItemId: playbackAcceptance.itemId,
    complete,
  };
}
