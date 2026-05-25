import { describe, expect, it } from "vitest";

import type { MediaProfileState } from "@/components/media/media-types";
import { createMediaLocalStorageMigrationPlan } from "@/lib/media/media-local-storage-migration";

const migratedAt = "2026-05-23T19:45:00.000Z";

function createProfileState(
  profileState: Partial<MediaProfileState> & Pick<MediaProfileState, "profileId">,
): MediaProfileState {
  return {
    watchlistIds: [],
    progress: {},
    curationChecks: {},
    playbackAcceptance: {},
    ...profileState,
  };
}

describe("createMediaLocalStorageMigrationPlan", () => {
  it("maps local profile state into durable user-state records", () => {
    const profileState = createProfileState({
      profileId: "britton",
      watchlistIds: ["movie-local-lights"],
      progress: {
        "movie-local-lights": {
          itemId: "movie-local-lights",
          seconds: 42,
          updatedAt: "2026-05-22T10:00:00.000Z",
        },
      },
      curationChecks: {
        "movie-local-lights": {
          itemId: "movie-local-lights",
          authorizedFileConfirmed: true,
          updatedAt: "2026-05-22T10:01:00.000Z",
        },
      },
      playbackAcceptance: {
        "movie-local-lights": {
          itemId: "movie-local-lights",
          sourceReadyConfirmed: true,
          refreshProgressConfirmed: true,
          profileIsolationConfirmed: false,
          updatedAt: "2026-05-22T10:02:00.000Z",
        },
      },
    });

    expect(
      createMediaLocalStorageMigrationPlan(
        {
          selectedProfileId: "britton",
          profileStates: [profileState],
        },
        {
          migratedAt,
          catalogItemIds: ["movie-local-lights"],
        },
      ),
    ).toEqual({
      source: "media-local-storage",
      selectedProfileId: "britton",
      migratedAt,
      profileCount: 1,
      records: {
        watchlistEntries: [
          {
            profileId: "britton",
            catalogItemId: "movie-local-lights",
            createdAt: migratedAt,
          },
        ],
        playbackProgress: [
          {
            profileId: "britton",
            catalogItemId: "movie-local-lights",
            seconds: 42,
            updatedAt: "2026-05-22T10:00:00.000Z",
          },
        ],
        curationChecks: [
          {
            profileId: "britton",
            catalogItemId: "movie-local-lights",
            authorizedFileConfirmed: true,
            updatedAt: "2026-05-22T10:01:00.000Z",
          },
        ],
        playbackAcceptance: [
          {
            profileId: "britton",
            catalogItemId: "movie-local-lights",
            sourceReadyConfirmed: true,
            refreshProgressConfirmed: true,
            profileIsolationConfirmed: false,
            updatedAt: "2026-05-22T10:02:00.000Z",
          },
        ],
      },
      skippedEntries: [],
    });
  });

  it("keeps profile state isolated across profiles", () => {
    const plan = createMediaLocalStorageMigrationPlan(
      {
        selectedProfileId: "friend",
        profileStates: [
          createProfileState({
            profileId: "britton",
            watchlistIds: ["movie-local-lights"],
          }),
          createProfileState({
            profileId: "friend",
            watchlistIds: ["movie-local-lights"],
          }),
        ],
      },
      {
        migratedAt,
        catalogItemIds: ["movie-local-lights"],
      },
    );

    expect(plan.selectedProfileId).toBe("friend");
    expect(plan.records.watchlistEntries).toEqual([
      {
        profileId: "britton",
        catalogItemId: "movie-local-lights",
        createdAt: migratedAt,
      },
      {
        profileId: "friend",
        catalogItemId: "movie-local-lights",
        createdAt: migratedAt,
      },
    ]);
  });

  it("reports duplicate local entries without duplicating durable records", () => {
    const plan = createMediaLocalStorageMigrationPlan(
      {
        selectedProfileId: "britton",
        profileStates: [
          createProfileState({
            profileId: "britton",
            watchlistIds: ["movie-local-lights", "movie-local-lights"],
          }),
        ],
      },
      {
        migratedAt,
        catalogItemIds: ["movie-local-lights"],
      },
    );

    expect(plan.records.watchlistEntries).toHaveLength(1);
    expect(plan.skippedEntries).toEqual([
      {
        profileId: "britton",
        catalogItemId: "movie-local-lights",
        tableName: "watchlistEntries",
        reason: "duplicate-entry",
      },
    ]);
  });

  it("reports unknown catalog items instead of migrating them", () => {
    const plan = createMediaLocalStorageMigrationPlan(
      {
        selectedProfileId: "guest",
        profileStates: [
          createProfileState({
            profileId: "guest",
            progress: {
              "missing-item": {
                itemId: "missing-item",
                seconds: 12,
                updatedAt: "2026-05-22T10:00:00.000Z",
              },
            },
          }),
        ],
      },
      {
        migratedAt,
        catalogItemIds: ["movie-local-lights"],
      },
    );

    expect(plan.records.playbackProgress).toEqual([]);
    expect(plan.skippedEntries).toEqual([
      {
        profileId: "guest",
        catalogItemId: "missing-item",
        tableName: "playbackProgress",
        reason: "unknown-catalog-item",
      },
    ]);
  });

  it("does not read localStorage or IndexedDB directly", () => {
    const plan = createMediaLocalStorageMigrationPlan(
      {
        selectedProfileId: "britton",
        profileStates: [createProfileState({ profileId: "britton" })],
      },
      {
        migratedAt,
      },
    );

    expect(plan.profileCount).toBe(1);
    expect(typeof globalThis.indexedDB).toBe("undefined");
  });
});
