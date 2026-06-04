"use client";

import { useEffect, useMemo, useRef, useState, type SyntheticEvent } from "react";

import type {
  CatalogItem,
  MediaProfileId,
  MediaProfileState,
} from "@/components/media/media-types";
import { mediaCatalogSource } from "@/lib/media/media-catalog-source";
import {
  installMediaManualBrowserHarness,
  type MediaManualBrowserHarness,
} from "@/lib/media/media-manual-browser-harness";
import type { MediaIndexedDbManualAcceptanceReport } from "@/lib/media/media-indexeddb-manual-acceptance";
import {
  evaluateMediaIndexedDbManualEvidence,
  type MediaIndexedDbManualEvidenceStatus,
} from "@/lib/media/media-indexeddb-manual-evidence";
import { mediaIndexedDbBrowserRunNotesTemplate } from "@/lib/media/media-indexeddb-browser-run-notes";
import {
  evaluateMediaDexiePrimaryPromotionDecision,
  formatMediaDexiePrimaryPromotionDecision,
} from "@/lib/media/media-dexie-primary-promotion-decision";
import {
  evaluateMediaBrowserEvidenceArchivePacket,
  formatMediaBrowserEvidenceArchivePacketStatus,
} from "@/lib/media/media-browser-evidence-archive-packet";
import {
  evaluateMediaBrowserEvidenceExportDecision,
  formatMediaBrowserEvidenceExportDecision,
} from "@/lib/media/media-browser-evidence-export-decision";
import { createMediaEvidenceManualCopyTemplate } from "@/lib/media/media-evidence-manual-copy-template";
import { mediaEvidenceManualFillInProcedure } from "@/lib/media/media-evidence-manual-fill-in-procedure";
import { mediaEvidenceBrowserRunChecklist } from "@/lib/media/media-evidence-browser-run-checklist";
import { isBrowserMediaDbAvailable } from "@/lib/media/media-db";
import {
  evaluateMediaProfileStatePrimaryReadiness,
  formatMediaProfileStatePrimaryReadiness,
} from "@/lib/media/media-profile-state-primary-readiness";
import {
  resolveMediaRuntimeReadSource,
  type MediaRuntimeReadSource,
} from "@/lib/media/media-runtime-read-source";
import {
  writeProfileCurationCheckBestEffort,
  writeProfilePlaybackAcceptanceBestEffort,
  writeProfilePlaybackProgressBestEffort,
  writeProfileWatchlistEntryBestEffort,
  type MediaProfileStateDualWriteResult,
} from "@/lib/media/media-profile-state-dual-write";
import {
  loadProfileState,
  loadSelectedProfile,
  resetProfileState,
  savePlaybackProgress,
  saveProfileState,
  saveSelectedProfile,
  setCurationCheck,
  setPlaybackAcceptanceEvidence,
  toggleWatchlistItem,
} from "@/lib/media/media-storage";

function formatRuntime(minutes: number): string {
  if (minutes < 60) {
    return `${minutes} min`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return remainingMinutes ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
}

function formatTimestamp(seconds: number): string {
  const totalSeconds = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(totalSeconds / 60);
  const remainingSeconds = totalSeconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
}

function getProgressLabel(itemId: string, state: MediaProfileState): string {
  const progress = state.progress[itemId];
  return progress?.seconds ? `Resume at ${formatTimestamp(progress.seconds)}` : "";
}

function getPublicMediaPath(mediaSource: string): string {
  return `public${mediaSource}`;
}

function formatLibraryStatus(status: CatalogItem["metadata"]["libraryStatus"]): string {
  return status === "ready-for-owned-file"
    ? "Ready for owned file"
    : "Demo placeholder";
}

const browserAcceptanceChecks = [
  "Confirm the four manual public/media MP4 entries play directly from /media/*.mp4.",
  "Open /media from the main workspace navigation and confirm only one nav is visible.",
  "Select They Were Right and confirm the source status becomes Ready after the browser can load it.",
  "Select Kabbalah Intro and confirm the player source is /media/kabbalah-intro.mp4.",
  "Seek or pause playback, refresh, and confirm Continue Watching keeps the saved timestamp.",
  "Resize to phone width and confirm cards, paths, controls, and video stay inside the page.",
  "Switch profiles and confirm watchlist, progress, and curation checks stay separate.",
];

const persistenceDecisionRows = [
  {
    label: "Profile state",
    value: "Keep localStorage for the next loop",
  },
  {
    label: "Catalog source",
    value: "Keep the manual local catalog entries in code",
  },
  {
    label: "Deferred",
    value: "Database, API routes, filesystem scanning, and manifest import",
  },
  {
    label: "Revisit when",
    value: "Browser acceptance proves one authorized local sample works end to end",
  },
];

const playbackAcceptanceSteps = [
  {
    field: "sourceReadyConfirmed",
    label: "Source reached Ready for this authorized local sample.",
  },
  {
    field: "refreshProgressConfirmed",
    label: "Pause or seek progress survived a browser refresh.",
  },
  {
    field: "profileIsolationConfirmed",
    label: "Another profile did not inherit this playback progress.",
  },
] as const;

const acceptanceFreezeItems = [
  "Profiles remain local mock profiles.",
  "Catalog remains manual source-code entries for public/media files.",
  "Playback uses browser-native video controls with manually added authorized samples.",
  "Progress, Watchlist, curation, and acceptance evidence remain browser-local.",
  "No database, API route, scanner, PWA, transcoder, or committed media binary is part of Plan 1.",
];

function formatHarnessStatus(
  report: MediaIndexedDbManualAcceptanceReport | null,
): string {
  if (!report) {
    return "Not run";
  }

  return report.status === "passed"
    ? "Passed"
    : report.status === "blocked"
      ? "Blocked"
      : "Needs browser run";
}

function formatRuntimeReadSourceStatus(
  status: MediaRuntimeReadSource["status"],
): string {
  return status === "dexie" ? "Dexie" : "Local fallback";
}

function formatDualWriteStatus(
  result: MediaProfileStateDualWriteResult | null,
): string {
  if (!result) {
    return "Not attempted";
  }

  return result.dexie.status === "written"
    ? "Dexie written"
    : result.dexie.status === "skipped"
      ? "Dexie skipped"
      : "Dexie unavailable";
}

function formatManualEvidenceStatus(
  status: MediaIndexedDbManualEvidenceStatus,
): string {
  return status === "accepted"
    ? "Accepted"
    : status === "incomplete"
      ? "Incomplete"
      : "Blocked";
}

function unavailableProfileWriteResult(): MediaProfileStateDualWriteResult {
  return {
    localStorage: "written",
    dexie: {
      status: "unavailable",
      reason: "indexeddb-unavailable",
    },
  };
}

type MediaCardProps = {
  item: CatalogItem;
  profileState: MediaProfileState;
  isInWatchlist: boolean;
  onOpen: (item: CatalogItem) => void;
  onToggleWatchlist: (itemId: string) => void;
};

function MediaCard({
  item,
  profileState,
  isInWatchlist,
  onOpen,
  onToggleWatchlist,
}: MediaCardProps) {
  const [posterMissing, setPosterMissing] = useState(false);
  const progressLabel = getProgressLabel(item.id, profileState);

  return (
    <article className="media-card">
      <button
        className="poster-button"
        type="button"
        onClick={() => onOpen(item)}
        aria-label={`Open ${item.title}`}
      >
        {!posterMissing ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            alt=""
            src={item.posterPath}
            onError={() => setPosterMissing(true)}
          />
        ) : (
          <span className="poster-fallback">Poster placeholder</span>
        )}
      </button>
      <div className="card-copy">
        <div>
          <p className="eyebrow">{item.type === "movie" ? "Movie" : "Episode"}</p>
          <h3>{item.title}</h3>
          <p className="meta">
            {item.metadata.releaseYear} · {item.metadata.rating} ·{" "}
            {formatRuntime(item.runtimeMinutes)}
            {progressLabel ? ` · ${progressLabel}` : ""}
          </p>
          <p className="metadata-line">{item.metadata.genres.join(" / ")}</p>
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => onToggleWatchlist(item.id)}
        >
          {isInWatchlist ? "Remove from Watchlist" : "Add to Watchlist"}
        </button>
      </div>
    </article>
  );
}

export function MediaExperience() {
  const [catalogSource, setCatalogSource] = useState(mediaCatalogSource);
  const [runtimeReadSourceStatus, setRuntimeReadSourceStatus] =
    useState<MediaRuntimeReadSource["status"]>("local-fallback");
  const [selectedProfileId, setSelectedProfileId] = useState<MediaProfileId>(() =>
    loadSelectedProfile("britton"),
  );
  const [profileState, setProfileState] = useState<MediaProfileState>(() => {
    return loadProfileState(loadSelectedProfile("britton"));
  });
  const [activeItem, setActiveItem] = useState<CatalogItem>(
    mediaCatalogSource.flattenedCatalogItems[0],
  );
  const [sourceStatus, setSourceStatus] = useState<
    "idle" | "checking" | "ready" | "missing"
  >("idle");
  const [harnessStatus, setHarnessStatus] = useState<
    "idle" | "running" | "complete" | "unavailable"
  >("idle");
  const [harnessReport, setHarnessReport] =
    useState<MediaIndexedDbManualAcceptanceReport | null>(null);
  const [lastProfileWriteResult, setLastProfileWriteResult] =
    useState<MediaProfileStateDualWriteResult | null>(null);
  const [showDevEvidence, setShowDevEvidence] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const lastSavedSecondRef = useRef(0);
  const manualHarnessRef = useRef<MediaManualBrowserHarness | null>(null);

  const mediaProfiles = catalogSource.mediaProfiles;
  const demoCatalog = catalogSource.demoCatalog;
  const flattenedCatalogItems = catalogSource.flattenedCatalogItems;
  const getCatalogItemById = catalogSource.getCatalogItemById;

  useEffect(() => {
    let isMounted = true;

    void resolveMediaRuntimeReadSource().then((runtimeSource) => {
      if (!isMounted) {
        return;
      }

      if (
        runtimeSource.status === "local-fallback" &&
        runtimeSource.adapterResult === mediaCatalogSource
      ) {
        return;
      }

      setCatalogSource(runtimeSource.adapterResult);
      setRuntimeReadSourceStatus(runtimeSource.status);
      setActiveItem((currentItem) => {
        return (
          runtimeSource.adapterResult.getCatalogItemById(currentItem.id) ??
          runtimeSource.adapterResult.flattenedCatalogItems[0] ??
          currentItem
        );
      });
    });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    saveSelectedProfile(selectedProfileId);
    saveProfileState(profileState);
  }, [profileState, selectedProfileId]);

  const continueWatching = useMemo(() => {
    return Object.values(profileState.progress)
      .filter((entry) => entry.seconds > 0)
      .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
      .map((entry) => getCatalogItemById(entry.itemId))
      .filter((item): item is CatalogItem => Boolean(item));
  }, [getCatalogItemById, profileState.progress]);

  const watchlistItems = useMemo(() => {
    return profileState.watchlistIds
      .map((itemId) => getCatalogItemById(itemId))
      .filter((item): item is CatalogItem => Boolean(item));
  }, [getCatalogItemById, profileState.watchlistIds]);
  const primaryProfileStateReadiness = useMemo(() => {
    return evaluateMediaProfileStatePrimaryReadiness({
      runtimeReadSourceStatus,
      latestProfileWriteResult: lastProfileWriteResult,
      manualAcceptanceReport: harnessReport,
    });
  }, [harnessReport, lastProfileWriteResult, runtimeReadSourceStatus]);
  const indexedDbManualEvidence = useMemo(() => {
    return evaluateMediaIndexedDbManualEvidence({
      manualAcceptanceReport: harnessReport,
      runtimeReadSourceStatus,
      latestProfileWriteResult: lastProfileWriteResult,
      indexedDbTablesInspected: false,
      localStorageFallbackPreserved:
        harnessReport?.checklist.localStoragePreserved ?? true,
      skippedEntriesReviewed:
        harnessReport?.checklist.skippedEntriesReviewed ?? false,
      requiresAutomationOrServerWork: false,
    });
  }, [harnessReport, lastProfileWriteResult, runtimeReadSourceStatus]);
  const dexiePrimaryPromotionDecision = useMemo(() => {
    return evaluateMediaDexiePrimaryPromotionDecision({
      manualEvidence: indexedDbManualEvidence,
      explicitPromotionApproval: false,
      rollbackPlanConfirmed: false,
      localStorageFallbackPreserved:
        indexedDbManualEvidence.captured.localStorageFallbackPreserved,
      scopeExpandedBeyondProfileState: false,
    });
  }, [indexedDbManualEvidence]);
  const browserEvidenceArchivePacket = useMemo(() => {
    return evaluateMediaBrowserEvidenceArchivePacket({
      manualEvidence: indexedDbManualEvidence,
      promotionDecision: dexiePrimaryPromotionDecision,
      browserRunNotesCaptured: false,
      archiveLocationRecorded: false,
      localOnlyScopeDeclared: true,
      mediaBinariesAttached: false,
      requiresServerOrAutomationEvidence: false,
    });
  }, [dexiePrimaryPromotionDecision, indexedDbManualEvidence]);
  const browserEvidenceExportDecision = useMemo(() => {
    return evaluateMediaBrowserEvidenceExportDecision({
      archivePacket: browserEvidenceArchivePacket,
      manualExportApproval: false,
      exportLocationSelected: false,
      mediaBinariesExcluded:
        browserEvidenceArchivePacket.includes.mediaBinaries === "excluded",
      appFileWriteRequested: false,
      serverExportRequested: false,
    });
  }, [browserEvidenceArchivePacket]);
  const evidenceManualCopyTemplate = useMemo(() => {
    return createMediaEvidenceManualCopyTemplate({
      manualEvidence: indexedDbManualEvidence,
      promotionDecision: dexiePrimaryPromotionDecision,
      archivePacket: browserEvidenceArchivePacket,
      exportDecision: browserEvidenceExportDecision,
    });
  }, [
    browserEvidenceArchivePacket,
    browserEvidenceExportDecision,
    dexiePrimaryPromotionDecision,
    indexedDbManualEvidence,
  ]);

  function selectProfile(profileId: MediaProfileId) {
    setSelectedProfileId(profileId);
    const nextState = loadProfileState(profileId);
    setProfileState(nextState);
  }

  function openItem(item: CatalogItem) {
    setActiveItem(item);
    setSourceStatus("idle");
    lastSavedSecondRef.current = 0;
  }

  function updateProfileState(nextState: MediaProfileState) {
    setProfileState(nextState);
    saveProfileState(nextState);
  }

  function handleResetCurrentProfile() {
    setProfileState(resetProfileState(selectedProfileId));
    setSourceStatus("idle");
    lastSavedSecondRef.current = 0;
  }

  function handleToggleWatchlist(itemId: string) {
    const nextState = toggleWatchlistItem(profileState, itemId);
    updateProfileState(nextState);
    if (!isBrowserMediaDbAvailable()) {
      setLastProfileWriteResult(unavailableProfileWriteResult());
      return;
    }

    void writeProfileWatchlistEntryBestEffort(
      nextState.profileId,
      itemId,
      nextState.watchlistIds.includes(itemId),
      new Date().toISOString(),
    ).then(setLastProfileWriteResult);
  }

  function handleCurationCheck(itemId: string, authorizedFileConfirmed: boolean) {
    const nextState = setCurationCheck(
      profileState,
      itemId,
      authorizedFileConfirmed,
    );
    updateProfileState(nextState);
    if (!isBrowserMediaDbAvailable()) {
      setLastProfileWriteResult(unavailableProfileWriteResult());
      return;
    }

    void writeProfileCurationCheckBestEffort(
      nextState.profileId,
      nextState.curationChecks[itemId],
    ).then(setLastProfileWriteResult);
  }

  function handlePlaybackAcceptanceCheck(
    itemId: string,
    field: (typeof playbackAcceptanceSteps)[number]["field"],
    confirmed: boolean,
  ) {
    const nextState = setPlaybackAcceptanceEvidence(
      profileState,
      itemId,
      field,
      confirmed,
    );
    updateProfileState(nextState);
    if (!isBrowserMediaDbAvailable()) {
      setLastProfileWriteResult(unavailableProfileWriteResult());
      return;
    }

    void writeProfilePlaybackAcceptanceBestEffort(
      nextState.profileId,
      nextState.playbackAcceptance[itemId],
    ).then(setLastProfileWriteResult);
  }

  async function handleManualIndexedDbAcceptanceRun() {
    setHarnessStatus("running");
    const harness =
      manualHarnessRef.current ?? installMediaManualBrowserHarness();

    if (!harness) {
      setHarnessReport(null);
      setHarnessStatus("unavailable");
      return;
    }

    manualHarnessRef.current = harness;
    const report = await harness.runIndexedDbAcceptance();
    setHarnessReport(report);
    setHarnessStatus("complete");
  }

  function persistProgress(seconds: number) {
    if (!activeItem || !Number.isFinite(seconds)) {
      return;
    }

    if (seconds < 1) {
      return;
    }

    const nextState = savePlaybackProgress(profileState, activeItem.id, seconds);
    updateProfileState(nextState);
    if (!isBrowserMediaDbAvailable()) {
      setLastProfileWriteResult(unavailableProfileWriteResult());
      lastSavedSecondRef.current = Math.floor(seconds);
      return;
    }

    void writeProfilePlaybackProgressBestEffort(
      nextState.profileId,
      nextState.progress[activeItem.id],
    ).then(setLastProfileWriteResult);
    lastSavedSecondRef.current = Math.floor(seconds);
  }

  function handleLoadedMetadata() {
    const video = videoRef.current;
    const savedSeconds = profileState.progress[activeItem.id]?.seconds;
    if (!video || !savedSeconds || savedSeconds < 3) {
      return;
    }

    const safeResumePoint = Math.max(0, savedSeconds - 2);
    if (Number.isFinite(video.duration)) {
      video.currentTime = Math.min(safeResumePoint, Math.max(0, video.duration - 2));
      return;
    }

    video.currentTime = safeResumePoint;
  }

  function handleTimeUpdate(event: SyntheticEvent<HTMLVideoElement>) {
    const seconds = Math.floor(event.currentTarget.currentTime);
    if (seconds > 0 && Math.abs(seconds - lastSavedSecondRef.current) >= 5) {
      persistProgress(seconds);
    }
  }

  function renderRow(title: string, items: CatalogItem[], emptyCopy: string) {
    return (
      <section className="media-section" aria-labelledby={`${title}-heading`}>
        <div className="section-heading">
          <h2 id={`${title}-heading`}>{title}</h2>
          <span>{items.length ? `${items.length} item${items.length === 1 ? "" : "s"}` : "Empty"}</span>
        </div>
        {items.length ? (
          <div className="card-row">
            {items.map((item) => (
              <MediaCard
                key={item.id}
                item={item}
                profileState={profileState}
                isInWatchlist={profileState.watchlistIds.includes(item.id)}
                onOpen={openItem}
                onToggleWatchlist={handleToggleWatchlist}
              />
            ))}
          </div>
        ) : (
          <p className="empty-state">{emptyCopy}</p>
        )}
      </section>
    );
  }

  const activeProfile = mediaProfiles.find(
    (profile) => profile.id === selectedProfileId,
  );
  const activeProgressLabel = getProgressLabel(activeItem.id, profileState);
  const activeCurationCheck = profileState.curationChecks[activeItem.id];
  const activePlaybackAcceptance =
    profileState.playbackAcceptance[activeItem.id];
  const activePlaybackAcceptanceComplete = Boolean(
    activePlaybackAcceptance?.sourceReadyConfirmed &&
      activePlaybackAcceptance.refreshProgressConfirmed &&
      activePlaybackAcceptance.profileIsolationConfirmed,
  );
  const readinessRows = [
    {
      label: "Source path",
      state: getPublicMediaPath(activeItem.mediaSource),
      tone: "good",
    },
    {
      label: "Curation",
      state: activeCurationCheck?.authorizedFileConfirmed
        ? "Confirmed for this profile"
        : "Waiting on manual confirmation",
      tone: activeCurationCheck?.authorizedFileConfirmed ? "good" : "warn",
    },
    {
      label: "Playback evidence",
      state: activePlaybackAcceptanceComplete
        ? "Complete for this profile"
        : "Waiting on browser playback",
      tone: activePlaybackAcceptanceComplete ? "good" : "warn",
    },
    {
      label: "Continue Watching",
      state: activeProgressLabel || "No saved timestamp",
      tone: activeProgressLabel ? "good" : "quiet",
    },
    {
      label: "Current source status",
      state:
        sourceStatus === "ready"
          ? "Ready"
          : sourceStatus === "checking"
            ? "Checking local file"
            : sourceStatus === "missing"
              ? "Missing local file"
              : "Waiting to load",
      tone:
        sourceStatus === "ready"
          ? "good"
          : sourceStatus === "missing"
            ? "warn"
            : "quiet",
    },
  ] as const;

  return (
      <main className="media-page">
        <section className="hero-band">
        <div>
          <p className="eyebrow">SpiritOS local proof of concept</p>
          <h1>Media</h1>
          <p>
            A local media library for manually cataloged public/media MP4 files,
            native browser playback, Continue Watching, and Watchlist state. This is
            mock local auth only, not real security.
          </p>
        </div>
        </section>

        <section className="media-section profile-gate" aria-labelledby="profiles-heading">
        <div>
          <p className="eyebrow">Profiles</p>
          <h2 id="profiles-heading">Local mock profile gate</h2>
          <p>
            Selected profile: <strong>{activeProfile?.name ?? "Britton"}</strong>.
            State is stored in this browser only.
          </p>
        </div>
        <div className="profile-buttons" role="list" aria-label="Local mock profiles">
          {mediaProfiles.map((profile) => (
            <button
              key={profile.id}
              className={
                profile.id === selectedProfileId
                  ? "primary-button"
                  : "secondary-button"
              }
              type="button"
              onClick={() => selectProfile(profile.id)}
            >
              {profile.name}
            </button>
          ))}
        </div>
        <div className="reset-panel" aria-label="Current profile reset control">
          <h3>Reset current profile</h3>
          <p>
            Clear Watchlist, Continue Watching, curation checks, and playback
            acceptance evidence for {activeProfile?.name ?? "this profile"} only.
            Catalog items and other profiles stay untouched.
          </p>
          <button
            className="danger-button"
            type="button"
            onClick={handleResetCurrentProfile}
          >
            Reset Current Profile State
          </button>
        </div>
        </section>

        <section className="media-section dev-toggle-section" aria-labelledby="dev-evidence-toggle-heading">
        <div>
          <p className="eyebrow">Developer</p>
          <h2 id="dev-evidence-toggle-heading">Dev / Evidence</h2>
          <p>
            Evidence, checklists, and storage decision panels are collapsed so
            the normal page opens as a media library first.
          </p>
        </div>
        <button
          className="secondary-button"
          type="button"
          aria-expanded={showDevEvidence}
          onClick={() => setShowDevEvidence((current) => !current)}
        >
          {showDevEvidence ? "Hide Dev / Evidence" : "Show Dev / Evidence"}
        </button>
        </section>

        {showDevEvidence ? (
        <>
        <section className="media-section acceptance-freeze" aria-labelledby="acceptance-freeze-heading">
        <div>
          <p className="eyebrow">Phase 11 freeze</p>
          <h2 id="acceptance-freeze-heading">Local media acceptance freeze</h2>
          <p>
            Plan 1 freezes here as a browser-local proof. Any real storage,
            real auth, friend-facing access, media serving, scanner, or manifest
            work should open as a new explicitly approved plan.
          </p>
        </div>
        <ul>
          {acceptanceFreezeItems.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        </section>

        <section className="media-section readiness-summary" aria-labelledby="readiness-summary-heading">
        <div>
          <p className="eyebrow">Phase 9 readiness</p>
          <h2 id="readiness-summary-heading">Local media readiness summary</h2>
          <p>
            Read-only summary for {activeProfile?.name ?? "this profile"} and{" "}
            {activeItem.title}. It reflects local browser state only and does not
            scan files, validate rights, or change storage.
          </p>
        </div>
        <div className="readiness-grid">
          {readinessRows.map((row) => (
            <div className={`readiness-row readiness-row-${row.tone}`} key={row.label}>
              <span>{row.label}</span>
              <strong>{row.state}</strong>
            </div>
          ))}
          <div className="readiness-row readiness-row-quiet">
            <span>Runtime read source</span>
            <strong>{formatRuntimeReadSourceStatus(runtimeReadSourceStatus)}</strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Profile write path</span>
            <strong>{formatDualWriteStatus(lastProfileWriteResult)}</strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Primary profile state</span>
            <strong>
              {formatMediaProfileStatePrimaryReadiness(
                primaryProfileStateReadiness,
              )}
            </strong>
          </div>
        </div>
        </section>

        <section className="media-section manual-harness-panel" aria-labelledby="manual-harness-heading">
        <div>
          <p className="eyebrow">Plan 9 manual check</p>
          <h2 id="manual-harness-heading">Manual IndexedDB acceptance harness</h2>
          <p>
            Run the explicit harness only when checking browser IndexedDB seed
            and migration readiness. The media page still reads this proof from
            the local demo catalog and localStorage state.
          </p>
        </div>
        <div className="readiness-grid">
          <div className="readiness-row readiness-row-quiet">
            <span>Report</span>
            <strong>{formatHarnessStatus(harnessReport)}</strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Metadata seed</span>
            <strong>
              {harnessReport?.checklist.metadataSeeded ? "Confirmed" : "Not confirmed"}
            </strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Profile state</span>
            <strong>
              {harnessReport?.checklist.profileStateMigrated
                ? "Migration report created"
                : "Not migrated"}
            </strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>localStorage</span>
            <strong>
              {harnessReport?.checklist.localStoragePreserved
                ? "Preserved"
                : "Untouched until run"}
            </strong>
          </div>
        </div>
        <div className="manual-harness-actions">
          <button
            className="secondary-button"
            type="button"
            onClick={() => {
              void handleManualIndexedDbAcceptanceRun();
            }}
            disabled={harnessStatus === "running"}
          >
            {harnessStatus === "running"
              ? "Running IndexedDB Check"
              : "Run Manual IndexedDB Check"}
          </button>
          {harnessStatus === "unavailable" ? (
            <p className="missing-media">Manual harness unavailable outside a browser window.</p>
          ) : null}
          {harnessReport ? (
            <p className="media-note">
              Latest manual report: {formatHarnessStatus(harnessReport)}.
              Skipped entries must be reviewed before route wiring.
            </p>
          ) : (
            <p className="media-note">
              No automatic migration runs from this panel.
            </p>
          )}
        </div>
        </section>

        <section className="media-section manual-evidence-summary" aria-labelledby="manual-evidence-heading">
        <div>
          <p className="eyebrow">Plan 17 evidence</p>
          <h2 id="manual-evidence-heading">Manual IndexedDB evidence summary</h2>
          <p>
            Read-only summary of the manual browser evidence needed before any
            future Dexie primary-state decision. DevTools table inspection stays
            manual and this panel does not promote storage.
          </p>
        </div>
        <div className="readiness-grid">
          <div className="readiness-row readiness-row-quiet">
            <span>Evidence decision</span>
            <strong>
              {formatManualEvidenceStatus(indexedDbManualEvidence.status)}
            </strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Manual report</span>
            <strong>{formatHarnessStatus(harnessReport)}</strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Runtime source</span>
            <strong>{formatRuntimeReadSourceStatus(runtimeReadSourceStatus)}</strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Profile write</span>
            <strong>{formatDualWriteStatus(lastProfileWriteResult)}</strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Table inspection</span>
            <strong>
              {indexedDbManualEvidence.captured.indexedDbTablesInspected
                ? "Captured"
                : "Manual DevTools check required"}
            </strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Fallback</span>
            <strong>
              {indexedDbManualEvidence.captured.localStorageFallbackPreserved
                ? "Preserved"
                : "Not preserved"}
            </strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Skipped entries</span>
            <strong>
              {indexedDbManualEvidence.captured.skippedEntriesReviewed
                ? "Reviewed"
                : "Not reviewed"}
            </strong>
          </div>
        </div>
        </section>

        <section className="media-section dexie-promotion-decision" aria-labelledby="dexie-promotion-heading">
        <div>
          <p className="eyebrow">Plan 19 decision</p>
          <h2 id="dexie-promotion-heading">Dexie primary profile-state decision</h2>
          <p>
            Read-only promotion gate. localStorage remains the primary profile
            state source until accepted evidence, explicit approval, and a
            rollback path are all present.
          </p>
        </div>
        <div className="readiness-grid">
          <div className="readiness-row readiness-row-quiet">
            <span>Decision</span>
            <strong>
              {formatMediaDexiePrimaryPromotionDecision(
                dexiePrimaryPromotionDecision,
              )}
            </strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Manual evidence</span>
            <strong>{formatManualEvidenceStatus(indexedDbManualEvidence.status)}</strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Approval</span>
            <strong>Missing</strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Rollback</span>
            <strong>Not confirmed</strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Primary source</span>
            <strong>localStorage</strong>
          </div>
        </div>
        </section>

        <section className="media-section browser-evidence-archive" aria-labelledby="browser-evidence-archive-heading">
        <div>
          <p className="eyebrow">Plan 20 archive</p>
          <h2 id="browser-evidence-archive-heading">Browser evidence archive packet</h2>
          <p>
            Read-only archive checklist for the browser evidence packet. It
            excludes media binaries and does not upload, persist, or serve media.
          </p>
        </div>
        <div className="readiness-grid">
          <div className="readiness-row readiness-row-quiet">
            <span>Packet status</span>
            <strong>
              {formatMediaBrowserEvidenceArchivePacketStatus(
                browserEvidenceArchivePacket.status,
              )}
            </strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Manual evidence</span>
            <strong>{formatManualEvidenceStatus(indexedDbManualEvidence.status)}</strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Promotion decision</span>
            <strong>
              {formatMediaDexiePrimaryPromotionDecision(
                dexiePrimaryPromotionDecision,
              )}
            </strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Run notes</span>
            <strong>
              {browserEvidenceArchivePacket.includes.browserRunNotes
                ? "Captured"
                : "Not captured"}
            </strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Archive location</span>
            <strong>
              {browserEvidenceArchivePacket.includes.archiveLocation
                ? "Recorded"
                : "Not recorded"}
            </strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Media binaries</span>
            <strong>{browserEvidenceArchivePacket.includes.mediaBinaries}</strong>
          </div>
        </div>
        </section>

        <section className="media-section browser-evidence-export" aria-labelledby="browser-evidence-export-heading">
        <div>
          <p className="eyebrow">Plan 21 export</p>
          <h2 id="browser-evidence-export-heading">Browser evidence export decision</h2>
          <p>
            Read-only export gate. The app does not write files, create
            downloads, or send evidence to a server.
          </p>
        </div>
        <div className="readiness-grid">
          <div className="readiness-row readiness-row-quiet">
            <span>Export decision</span>
            <strong>
              {formatMediaBrowserEvidenceExportDecision(
                browserEvidenceExportDecision,
              )}
            </strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Archive packet</span>
            <strong>
              {formatMediaBrowserEvidenceArchivePacketStatus(
                browserEvidenceArchivePacket.status,
              )}
            </strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Approval</span>
            <strong>Missing</strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Export location</span>
            <strong>Not selected</strong>
          </div>
          <div className="readiness-row readiness-row-quiet">
            <span>Export method</span>
            <strong>Manual only</strong>
          </div>
        </div>
        </section>

        <section className="media-section evidence-copy-template" aria-labelledby="evidence-copy-heading">
        <div>
          <p className="eyebrow">Plan 22 copy</p>
          <h2 id="evidence-copy-heading">Evidence packet manual copy template</h2>
          <p>
            Human-readable copy template for the browser evidence packet. It is
            not saved, downloaded, copied to the clipboard, or sent anywhere by
            the app.
          </p>
        </div>
        <div className="note-capture-list" role="list">
          {evidenceManualCopyTemplate.sections.map((section) => (
            <article className="note-capture-item" key={section.id} role="listitem">
              <div>
                <span>manual-copy</span>
                <h3>{section.heading}</h3>
              </div>
              {section.lines.map((line) => (
                <p key={line}>{line}</p>
              ))}
            </article>
          ))}
        </div>
        </section>

        <section className="media-section evidence-fill-procedure" aria-labelledby="evidence-fill-heading">
        <div>
          <p className="eyebrow">Plan 23 procedure</p>
          <h2 id="evidence-fill-heading">Evidence packet manual fill-in procedure</h2>
          <p>
            Manual browser procedure for filling the evidence packet outside the
            app. Nothing here is saved, downloaded, copied, uploaded, or
            automated.
          </p>
        </div>
        <div className="note-capture-list" role="list">
          {mediaEvidenceManualFillInProcedure.steps.map((step) => (
            <article className="note-capture-item" key={step.id} role="listitem">
              <div>
                <span>manual-step</span>
                <h3>{step.title}</h3>
              </div>
              <p>{step.action}</p>
              <strong>{step.expectedResult}</strong>
            </article>
          ))}
        </div>
        </section>

        <section className="media-section evidence-browser-checklist" aria-labelledby="evidence-browser-checklist-heading">
        <div>
          <p className="eyebrow">Plan 24 checklist</p>
          <h2 id="evidence-browser-checklist-heading">Evidence packet browser manual run checklist</h2>
          <p>
            Manual checklist for running the evidence packet workflow in a real
            browser. The app does not store checklist results or turn them into
            export, automation, or primary-state changes.
          </p>
        </div>
        <div className="note-capture-list" role="list">
          {mediaEvidenceBrowserRunChecklist.items.map((item) => (
            <article className="note-capture-item" key={item.id} role="listitem">
              <div>
                <span>manual-check</span>
                <h3>{item.label}</h3>
              </div>
              <p>{item.detail}</p>
              <strong>Required</strong>
            </article>
          ))}
        </div>
        </section>

        <section className="media-section browser-run-notes" aria-labelledby="browser-run-notes-heading">
        <div>
          <p className="eyebrow">Plan 18 notes</p>
          <h2 id="browser-run-notes-heading">Browser run capture notes</h2>
          <p>
            Manual note template for a real browser run. These notes are not
            saved by the app and do not replace DevTools inspection.
          </p>
        </div>
        <div className="note-capture-list" role="list">
          {mediaIndexedDbBrowserRunNotesTemplate.fields.map((field) => (
            <article className="note-capture-item" key={field.id} role="listitem">
              <div>
                <span>{field.source}</span>
                <h3>{field.label}</h3>
              </div>
              <p>{field.prompt}</p>
              <strong>{field.required ? "Required" : "Optional"}</strong>
            </article>
          ))}
        </div>
        </section>

        <section className="media-section persistence-gate" aria-labelledby="persistence-heading">
        <div>
          <p className="eyebrow">Phase 6 decision gate</p>
          <h2 id="persistence-heading">Local media persistence decision</h2>
          <p>
            Decision: keep this POC browser-local and code-cataloged until the
            first authorized sample passes browser acceptance. This preserves the
            smallest useful surface before any database, API, scanner, or manifest
            step is approved.
          </p>
        </div>
        <dl>
          {persistenceDecisionRows.map((row) => (
            <div key={row.label}>
              <dt>{row.label}</dt>
              <dd>{row.value}</dd>
            </div>
          ))}
        </dl>
        </section>
        </>
        ) : null}

        {renderRow(
          "Continue Watching",
          continueWatching,
          "Play or seek in an authorized local sample video to populate Continue Watching.",
        )}

        {renderRow(
          "Watchlist",
          watchlistItems,
          "Add movies or episodes to keep a local Watchlist for this profile.",
        )}

        <section className="media-section" aria-labelledby="library-heading">
        <div className="section-heading">
          <h2 id="library-heading">Library</h2>
          <span>{flattenedCatalogItems.length} playable items</span>
        </div>
        <div className="card-row">
          {flattenedCatalogItems.map((item) => (
            <MediaCard
              key={item.id}
              item={item}
              profileState={profileState}
              isInWatchlist={profileState.watchlistIds.includes(item.id)}
              onOpen={openItem}
              onToggleWatchlist={handleToggleWatchlist}
            />
          ))}
        </div>
        <div className="show-list">
          {demoCatalog.shows.map((show) => (
            <article key={show.id}>
              <h3>{show.title}</h3>
              <p>{show.description}</p>
              <p className="meta">
                {show.seasons.length} season ·{" "}
                {show.seasons.reduce(
                  (total, season) => total + season.episodes.length,
                  0,
                )}{" "}
                episodes
              </p>
            </article>
          ))}
        </div>
        {showDevEvidence ? (
        <>
        <div className="acceptance-panel" aria-label="Local library acceptance plan">
          <h3>Local library acceptance plan</h3>
          <p>
            Metadata is manually curated and maps local files by exact
            `public/media` path. Direct public/media serving works for the listed
            MP4s; a future scanner or database should only be added after this
            manual catalog shape feels right.
          </p>
          <ul>
            <li>Each playable item has year, rating, genres, runtime, and source path.</li>
            <li>Each playable item declares whether it is ready for an owned file.</li>
            <li>Each playable item keeps the manual public media match strategy.</li>
          </ul>
        </div>
        <div className="browser-acceptance-panel" aria-label="Local media browser acceptance checklist">
          <h3>Browser acceptance checklist</h3>
          <ol>
            {browserAcceptanceChecks.map((check) => (
              <li key={check}>{check}</li>
            ))}
          </ol>
        </div>
        </>
        ) : null}
        </section>

        <section className="media-section player-section" aria-labelledby="player-heading">
        <div className="player-copy">
          <p className="eyebrow">Player</p>
          <h2 id="player-heading">{activeItem.title}</h2>
          <p>{activeItem.description}</p>
          <div className="curation-panel" aria-label="Manual local library curation">
            <h3>Manual curation workflow</h3>
            <p>{activeItem.metadata.curation.rightsReminder}</p>
            <p>
              Expected file: <code>{activeItem.metadata.curation.expectedFileName}</code>
            </p>
            <ol>
              {activeItem.metadata.curation.checklist.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
            <label className="curation-confirm">
              <input
                type="checkbox"
                checked={activeCurationCheck?.authorizedFileConfirmed ?? false}
                onChange={(event) =>
                  handleCurationCheck(activeItem.id, event.currentTarget.checked)
                }
              />
              <span>
                I confirmed this authorized local file path for{" "}
                {activeProfile?.name ?? "this profile"}.
              </span>
            </label>
            {activeCurationCheck?.authorizedFileConfirmed ? (
              <p className="curation-saved">
                Curation check saved locally for this profile.
              </p>
            ) : (
              <p className="empty-state">
                This is a local checklist only. It does not scan the filesystem.
              </p>
            )}
          </div>
          <div className="source-contract" aria-label="Local media source contract">
            <p>
              Source contract: manually add an authorized sample file at{" "}
              <code>{getPublicMediaPath(activeItem.mediaSource)}</code>.
            </p>
            <p>
              {activeItem.sourceLabel}. No copyrighted, downloaded, pirated, or
              binary media files are committed by this POC.
            </p>
          </div>
          <div className="playback-acceptance-panel" aria-label="Local sample playback acceptance">
            <h3>Local sample playback acceptance</h3>
            <p>
              Record browser evidence only after adding an authorized local sample
              and manually testing this item. These checks are profile-local notes.
            </p>
            {playbackAcceptanceSteps.map((step) => (
              <label className="curation-confirm" key={step.field}>
                <input
                  type="checkbox"
                  checked={activePlaybackAcceptance?.[step.field] ?? false}
                  onChange={(event) =>
                    handlePlaybackAcceptanceCheck(
                      activeItem.id,
                      step.field,
                      event.currentTarget.checked,
                    )
                  }
                />
                <span>{step.label}</span>
              </label>
            ))}
            {activePlaybackAcceptance?.sourceReadyConfirmed &&
            activePlaybackAcceptance.refreshProgressConfirmed &&
            activePlaybackAcceptance.profileIsolationConfirmed ? (
              <p className="curation-saved">
                Playback acceptance evidence saved locally for this profile.
              </p>
            ) : (
              <p className="empty-state">
                Evidence remains incomplete until the authorized sample is tested
                in the browser.
              </p>
            )}
          </div>
          <dl>
            <div>
              <dt>Type</dt>
              <dd>{activeItem.type}</dd>
            </div>
            <div>
              <dt>Runtime</dt>
              <dd>{formatRuntime(activeItem.runtimeMinutes)}</dd>
            </div>
            <div>
              <dt>Year</dt>
              <dd>{activeItem.metadata.releaseYear}</dd>
            </div>
            <div>
              <dt>Rating</dt>
              <dd>{activeItem.metadata.rating}</dd>
            </div>
            <div>
              <dt>Genres</dt>
              <dd>{activeItem.metadata.genres.join(" / ")}</dd>
            </div>
            <div>
              <dt>Library</dt>
              <dd>{formatLibraryStatus(activeItem.metadata.libraryStatus)}</dd>
            </div>
            <div>
              <dt>Source</dt>
              <dd>{activeItem.mediaSource}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd className={`source-status source-status-${sourceStatus}`}>
                {sourceStatus === "ready"
                  ? "Ready"
                  : sourceStatus === "checking"
                    ? "Checking local file"
                    : sourceStatus === "missing"
                      ? "Missing local file"
                      : "Waiting to load"}
              </dd>
            </div>
          </dl>
          {activeProgressLabel ? (
            <p className="resume-label">{activeProgressLabel}</p>
          ) : (
            <p className="empty-state">No saved timestamp yet for this profile.</p>
          )}
          <button
            className="primary-button"
            type="button"
            onClick={() => handleToggleWatchlist(activeItem.id)}
          >
            {profileState.watchlistIds.includes(activeItem.id)
              ? "Remove from Watchlist"
              : "Add to Watchlist"}
          </button>
        </div>
        <div className="video-wrap">
          <video
            key={`${selectedProfileId}-${activeItem.id}`}
            ref={videoRef}
            controls
            preload="metadata"
            src={activeItem.mediaSource}
            onCanPlay={() => setSourceStatus("ready")}
            onError={() => setSourceStatus("missing")}
            onLoadStart={() => setSourceStatus("checking")}
            onLoadedMetadata={handleLoadedMetadata}
            onPause={(event) => persistProgress(event.currentTarget.currentTime)}
            onSeeked={(event) => persistProgress(event.currentTarget.currentTime)}
            onTimeUpdate={handleTimeUpdate}
          />
          <p className={sourceStatus === "missing" ? "missing-media" : "media-note"}>
            {sourceStatus === "ready"
              ? "Authorized local source loaded in the browser-native video player."
              : sourceStatus === "missing"
                ? `Missing media file. Add an authorized MP4 or WebM that Britton owns, created, or has permission to use at ${getPublicMediaPath(activeItem.mediaSource)}.`
                : "Using browser-native video controls with local placeholder source paths."}
          </p>
        </div>
        </section>
      <style
        dangerouslySetInnerHTML={{
          __html: `
        .media-page {
          width: 100%;
          min-width: 0;
          min-height: 100vh;
          box-sizing: border-box;
          background: #10141c;
          color: #f7f3ea;
          padding: 32px clamp(18px, 4vw, 48px);
          overflow-x: hidden;
        }

        .hero-band,
        .media-section {
          width: min(1180px, 100%);
          margin: 0 auto 24px;
        }

        .hero-band {
          padding: 28px 0 8px;
        }

        .hero-band h1 {
          margin: 0 0 10px;
          font-size: clamp(2.2rem, 7vw, 4.5rem);
          line-height: 0.95;
        }

        .hero-band p,
        .profile-gate p,
        .player-copy p,
        .player-copy li,
        .show-list p {
          max-width: 760px;
          color: #c8d1dc;
          line-height: 1.55;
          overflow-wrap: anywhere;
        }

        .media-section {
          border: 1px solid rgba(247, 243, 234, 0.14);
          border-radius: 8px;
          background: #171d27;
          padding: 20px;
        }

        .profile-gate,
        .player-section,
        .persistence-gate,
        .readiness-summary,
        .manual-harness-panel,
        .manual-evidence-summary,
        .dexie-promotion-decision,
        .browser-evidence-archive,
        .browser-evidence-export,
        .evidence-copy-template,
        .evidence-fill-procedure,
        .evidence-browser-checklist,
        .browser-run-notes,
        .acceptance-freeze {
          display: grid;
          grid-template-columns: minmax(0, 0.9fr) minmax(220px, 0.7fr) minmax(260px, 0.8fr);
          gap: 20px;
          align-items: start;
        }

        .player-section,
        .persistence-gate,
        .readiness-summary,
        .manual-harness-panel,
        .manual-evidence-summary,
        .dexie-promotion-decision,
        .browser-evidence-archive,
        .browser-evidence-export,
        .evidence-copy-template,
        .evidence-fill-procedure,
        .evidence-browser-checklist,
        .browser-run-notes,
        .acceptance-freeze {
          grid-template-columns: minmax(0, 0.9fr) minmax(320px, 1.1fr);
        }

        .section-heading {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          align-items: baseline;
          margin-bottom: 14px;
        }

        h2,
        h3,
        p {
          margin-top: 0;
        }

        h2 {
          margin-bottom: 8px;
          font-size: 1.3rem;
        }

        h3 {
          margin-bottom: 6px;
          font-size: 1rem;
        }

        .eyebrow,
        .meta,
        .metadata-line,
        .section-heading span,
        dt {
          color: #91a4b8;
          font-size: 0.78rem;
          font-weight: 700;
          letter-spacing: 0;
          text-transform: uppercase;
        }

        .metadata-line {
          margin-bottom: 0;
          text-transform: none;
        }

        .card-row {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
          gap: 14px;
        }

        .media-card {
          contain: layout paint;
          display: grid;
          grid-template-rows: auto 1fr;
          min-width: 0;
          min-height: 100%;
          overflow: hidden;
          border: 1px solid rgba(247, 243, 234, 0.12);
          border-radius: 8px;
          background: #202938;
        }

        .poster-button {
          width: 100%;
          aspect-ratio: 16 / 9;
          padding: 0;
          border: 0;
          background: #273343;
          color: #f7f3ea;
          cursor: pointer;
        }

        .poster-button img {
          display: block;
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .poster-fallback {
          display: grid;
          height: 100%;
          place-items: center;
          padding: 16px;
          color: #c8d1dc;
        }

        .card-copy {
          display: flex;
          min-height: 172px;
          flex-direction: column;
          justify-content: space-between;
          gap: 12px;
          padding: 14px;
        }

        .card-copy h3,
        .meta,
        .metadata-line {
          overflow-wrap: anywhere;
        }

        .profile-buttons {
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
        }

        .primary-button,
        .secondary-button,
        .danger-button {
          min-height: 40px;
          border-radius: 6px;
          padding: 10px 14px;
          font: inherit;
          font-weight: 700;
          line-height: 1.2;
          cursor: pointer;
          white-space: normal;
        }

        .primary-button:disabled,
        .secondary-button:disabled,
        .danger-button:disabled {
          cursor: wait;
          opacity: 0.72;
        }

        .primary-button {
          border: 1px solid #ffe08a;
          background: #ffe08a;
          color: #17202c;
        }

        .secondary-button {
          border: 1px solid rgba(247, 243, 234, 0.24);
          background: #111923;
          color: #f7f3ea;
        }

        .danger-button {
          border: 1px solid rgba(255, 178, 178, 0.42);
          background: rgba(255, 106, 106, 0.14);
          color: #ffd6d6;
        }

        button:focus-visible,
        video:focus-visible {
          outline: 3px solid #6dd6ff;
          outline-offset: 3px;
        }

        .empty-state,
        .media-note {
          margin-bottom: 0;
          color: #aebdca;
        }

        .show-list {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
          gap: 14px;
          margin-top: 16px;
        }

        .show-list article {
          border-top: 1px solid rgba(247, 243, 234, 0.12);
          padding-top: 14px;
        }

        .acceptance-panel {
          margin-top: 18px;
          border-top: 1px solid rgba(247, 243, 234, 0.12);
          padding-top: 16px;
        }

        .browser-acceptance-panel {
          margin-top: 16px;
          border-top: 1px solid rgba(247, 243, 234, 0.12);
          padding-top: 16px;
        }

        .acceptance-panel p,
        .acceptance-panel li,
        .browser-acceptance-panel li,
        .acceptance-freeze li {
          color: #c8d1dc;
          line-height: 1.55;
          overflow-wrap: anywhere;
        }

        .acceptance-panel ul,
        .browser-acceptance-panel ol,
        .acceptance-freeze ul {
          margin: 10px 0 0;
          padding-left: 18px;
        }

        .acceptance-freeze ul {
          margin-top: 0;
        }

        .player-copy dl {
          display: grid;
          gap: 8px;
          margin: 16px 0;
        }

        .player-copy dl div,
        .persistence-gate dl div {
          display: grid;
          grid-template-columns: 80px minmax(0, 1fr);
          gap: 10px;
        }

        .persistence-gate dl {
          display: grid;
          gap: 10px;
          margin: 0;
        }

        .readiness-grid {
          display: grid;
          gap: 10px;
        }

        .manual-harness-actions {
          display: grid;
          gap: 10px;
          align-content: start;
        }

        .note-capture-list {
          display: grid;
          gap: 10px;
        }

        .note-capture-item {
          display: grid;
          gap: 8px;
          border: 1px solid rgba(247, 243, 234, 0.12);
          border-radius: 8px;
          background: rgba(255, 255, 255, 0.035);
          padding: 12px;
        }

        .note-capture-item div {
          display: flex;
          gap: 10px;
          align-items: baseline;
          justify-content: space-between;
        }

        .note-capture-item span,
        .note-capture-item strong {
          color: #91a4b8;
          font-size: 0.78rem;
          font-weight: 800;
          text-transform: uppercase;
        }

        .note-capture-item h3,
        .note-capture-item p {
          margin: 0;
        }

        .note-capture-item p {
          color: #c8d1dc;
          line-height: 1.45;
        }

        .readiness-row {
          display: grid;
          grid-template-columns: minmax(110px, 0.4fr) minmax(0, 1fr);
          gap: 10px;
          align-items: center;
          border: 1px solid rgba(247, 243, 234, 0.12);
          border-radius: 8px;
          padding: 10px 12px;
        }

        .readiness-row span {
          color: #91a4b8;
          font-size: 0.78rem;
          font-weight: 800;
          text-transform: uppercase;
        }

        .readiness-row strong {
          overflow-wrap: anywhere;
        }

        .readiness-row-good {
          border-color: rgba(152, 255, 181, 0.22);
          background: rgba(152, 255, 181, 0.08);
        }

        .readiness-row-warn {
          border-color: rgba(255, 208, 166, 0.24);
          background: rgba(255, 208, 166, 0.08);
        }

        .readiness-row-quiet {
          border-color: rgba(247, 243, 234, 0.12);
          background: rgba(255, 255, 255, 0.035);
        }

        dd {
          margin: 0;
          overflow-wrap: anywhere;
          color: #f7f3ea;
        }

        code {
          display: inline-block;
          max-width: 100%;
          border-radius: 4px;
          background: rgba(255, 255, 255, 0.08);
          padding: 2px 5px;
          color: #ffe08a;
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
            "Liberation Mono", "Courier New", monospace;
          font-size: 0.92em;
          overflow-wrap: anywhere;
        }

        .source-contract {
          margin: 14px 0;
          border-left: 3px solid #6dd6ff;
          padding-left: 12px;
        }

        .curation-panel {
          margin: 14px 0;
          border: 1px solid rgba(247, 243, 234, 0.14);
          border-radius: 8px;
          background: rgba(255, 255, 255, 0.035);
          padding: 14px;
        }

        .reset-panel {
          border: 1px solid rgba(255, 178, 178, 0.16);
          border-radius: 8px;
          background: rgba(255, 106, 106, 0.055);
          padding: 14px;
        }

        .reset-panel p {
          margin-bottom: 12px;
        }

        .playback-acceptance-panel {
          margin: 14px 0;
          border: 1px solid rgba(109, 214, 255, 0.2);
          border-radius: 8px;
          background: rgba(109, 214, 255, 0.055);
          padding: 14px;
        }

        .curation-panel ol {
          margin: 10px 0 14px;
          padding-left: 20px;
        }

        .curation-panel li {
          color: #c8d1dc;
          line-height: 1.5;
        }

        .curation-confirm {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          margin: 10px 0;
          color: #f7f3ea;
          font-weight: 700;
          line-height: 1.45;
        }

        .curation-confirm input {
          margin-top: 3px;
          accent-color: #ffe08a;
        }

        .curation-saved {
          margin: 10px 0 0;
          color: #b8ffc8;
          font-weight: 800;
        }

        .source-contract p {
          margin-bottom: 6px;
        }

        .source-status {
          display: inline-flex;
          max-width: 100%;
          width: fit-content;
          border-radius: 999px;
          padding: 3px 9px;
          font-weight: 800;
          overflow-wrap: anywhere;
        }

        .source-status-idle,
        .source-status-checking {
          background: rgba(109, 214, 255, 0.14);
          color: #b9ecff;
        }

        .source-status-ready {
          background: rgba(152, 255, 181, 0.14);
          color: #b8ffc8;
        }

        .source-status-missing {
          background: rgba(255, 208, 166, 0.14);
          color: #ffd0a6;
        }

        .resume-label {
          font-weight: 800;
          color: #ffe08a;
        }

        .video-wrap {
          min-width: 0;
        }

        video {
          display: block;
          width: 100%;
          max-height: 68vh;
          aspect-ratio: 16 / 9;
          border-radius: 8px;
          background: #05070a;
        }

        .missing-media {
          margin-bottom: 0;
          color: #ffd0a6;
          font-weight: 700;
        }

        @media (max-width: 760px) {
          .media-page {
            padding: 18px 12px 28px;
          }

          .media-section {
            padding: 16px;
          }

          .profile-gate,
          .player-section,
          .persistence-gate,
          .readiness-summary,
          .manual-harness-panel,
          .manual-evidence-summary,
          .dexie-promotion-decision,
          .browser-evidence-archive,
          .browser-evidence-export,
          .evidence-copy-template,
          .evidence-fill-procedure,
          .evidence-browser-checklist,
          .browser-run-notes,
          .acceptance-freeze {
            grid-template-columns: 1fr;
          }

          .section-heading {
            align-items: flex-start;
            flex-direction: column;
          }

          .card-row {
            grid-template-columns: 1fr;
          }

          .player-copy dl div,
          .persistence-gate dl div {
            grid-template-columns: 1fr;
            gap: 2px;
          }

          .readiness-row {
            grid-template-columns: 1fr;
            gap: 3px;
          }

          .profile-buttons {
            display: grid;
            grid-template-columns: 1fr;
          }
        }

        @media (min-width: 761px) and (max-width: 1040px) {
          .profile-gate,
          .player-section,
          .persistence-gate,
          .readiness-summary,
          .manual-evidence-summary,
          .dexie-promotion-decision,
          .browser-evidence-archive,
          .browser-evidence-export,
          .evidence-copy-template,
          .evidence-fill-procedure,
          .evidence-browser-checklist,
          .browser-run-notes,
          .acceptance-freeze {
            grid-template-columns: 1fr;
          }

          .profile-buttons {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }
        }
      `,
        }}
      />
      </main>
  );
}
