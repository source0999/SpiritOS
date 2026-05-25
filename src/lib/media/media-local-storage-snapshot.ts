import type {
  MediaProfileId,
  MediaProfileState,
} from "@/components/media/media-types";
import type { MediaLocalStorageMigrationSnapshot } from "@/lib/media/media-local-storage-migration";

export const MEDIA_SELECTED_PROFILE_STORAGE_KEY =
  "spiritos.media.selectedProfile";
export const MEDIA_PROFILE_STATE_STORAGE_PREFIX = "spiritos.media.profile.";

type ReadableStorage = {
  getItem: (key: string) => string | null;
};

const defaultState = (profileId: MediaProfileId): MediaProfileState => ({
  profileId,
  watchlistIds: [],
  progress: {},
  curationChecks: {},
  playbackAcceptance: {},
});

function readJson<T>(storage: ReadableStorage, key: string, fallback: T): T {
  try {
    const raw = storage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

export function createMediaProfileStorageKey(profileId: MediaProfileId): string {
  return `${MEDIA_PROFILE_STATE_STORAGE_PREFIX}${profileId}`;
}

export function readMediaLocalStorageSnapshot(
  storage: ReadableStorage,
  profileIds: readonly MediaProfileId[],
  fallbackSelectedProfileId: MediaProfileId = "britton",
): MediaLocalStorageMigrationSnapshot {
  const selectedProfileId = readJson<MediaProfileId>(
    storage,
    MEDIA_SELECTED_PROFILE_STORAGE_KEY,
    fallbackSelectedProfileId,
  );
  const profileStates = profileIds.map((profileId) => {
    const savedState = readJson<Partial<MediaProfileState>>(
      storage,
      createMediaProfileStorageKey(profileId),
      defaultState(profileId),
    );

    return {
      ...defaultState(profileId),
      ...savedState,
      profileId,
      watchlistIds: savedState.watchlistIds ?? [],
      progress: savedState.progress ?? {},
      curationChecks: savedState.curationChecks ?? {},
      playbackAcceptance: savedState.playbackAcceptance ?? {},
    };
  });

  return {
    selectedProfileId,
    profileStates,
  };
}
