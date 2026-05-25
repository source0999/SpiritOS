import type {
  CurationCheck,
  MediaProfileId,
  MediaProfileState,
  PlaybackAcceptanceEvidence,
  PlaybackProgress,
} from "@/components/media/media-types";

const SELECTED_PROFILE_KEY = "spiritos.media.selectedProfile";
const PROFILE_STATE_PREFIX = "spiritos.media.profile.";

const defaultState = (profileId: MediaProfileId): MediaProfileState => ({
  profileId,
  watchlistIds: [],
  progress: {},
  curationChecks: {},
  playbackAcceptance: {},
});

function canUseStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function readJson<T>(key: string, fallback: T): T {
  if (!canUseStorage()) {
    return fallback;
  }

  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function writeJson<T>(key: string, value: T): void {
  if (!canUseStorage()) {
    return;
  }

  window.localStorage.setItem(key, JSON.stringify(value));
}

export function loadSelectedProfile(
  fallback: MediaProfileId = "britton",
): MediaProfileId {
  return readJson<MediaProfileId>(SELECTED_PROFILE_KEY, fallback);
}

export function saveSelectedProfile(profileId: MediaProfileId): void {
  writeJson(SELECTED_PROFILE_KEY, profileId);
}

export function loadProfileState(profileId: MediaProfileId): MediaProfileState {
  const savedState = readJson<Partial<MediaProfileState>>(
    `${PROFILE_STATE_PREFIX}${profileId}`,
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
}

export function saveProfileState(state: MediaProfileState): void {
  writeJson(`${PROFILE_STATE_PREFIX}${state.profileId}`, state);
}

export function resetProfileState(profileId: MediaProfileId): MediaProfileState {
  const nextState = defaultState(profileId);
  saveProfileState(nextState);
  return nextState;
}

export function toggleWatchlistItem(
  state: MediaProfileState,
  itemId: string,
): MediaProfileState {
  const exists = state.watchlistIds.includes(itemId);
  return {
    ...state,
    watchlistIds: exists
      ? state.watchlistIds.filter((id) => id !== itemId)
      : [...state.watchlistIds, itemId],
  };
}

export function savePlaybackProgress(
  state: MediaProfileState,
  itemId: string,
  seconds: number,
): MediaProfileState {
  const roundedSeconds = Math.max(0, Math.floor(seconds));
  const progress: PlaybackProgress = {
    itemId,
    seconds: roundedSeconds,
    updatedAt: new Date().toISOString(),
  };

  return {
    ...state,
    progress: {
      ...state.progress,
      [itemId]: progress,
    },
  };
}

export function setCurationCheck(
  state: MediaProfileState,
  itemId: string,
  authorizedFileConfirmed: boolean,
): MediaProfileState {
  const curationCheck: CurationCheck = {
    itemId,
    authorizedFileConfirmed,
    updatedAt: new Date().toISOString(),
  };

  return {
    ...state,
    curationChecks: {
      ...state.curationChecks,
      [itemId]: curationCheck,
    },
  };
}

export function setPlaybackAcceptanceEvidence(
  state: MediaProfileState,
  itemId: string,
  field: keyof Omit<PlaybackAcceptanceEvidence, "itemId" | "updatedAt">,
  confirmed: boolean,
): MediaProfileState {
  const currentEvidence = state.playbackAcceptance[itemId];
  const playbackAcceptance: PlaybackAcceptanceEvidence = {
    itemId,
    sourceReadyConfirmed: currentEvidence?.sourceReadyConfirmed ?? false,
    refreshProgressConfirmed: currentEvidence?.refreshProgressConfirmed ?? false,
    profileIsolationConfirmed: currentEvidence?.profileIsolationConfirmed ?? false,
    [field]: confirmed,
    updatedAt: new Date().toISOString(),
  };

  return {
    ...state,
    playbackAcceptance: {
      ...state.playbackAcceptance,
      [itemId]: playbackAcceptance,
    },
  };
}
