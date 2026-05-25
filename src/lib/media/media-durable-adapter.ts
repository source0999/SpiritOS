import type {
  CatalogGroup,
  CatalogItem,
  EpisodeItem,
  MediaProfile,
  MediaProfileId,
  MediaProfileState,
  MovieItem,
  Season,
  ShowItem,
} from "@/components/media/media-types";
import type {
  DurableMediaAdapterResult,
  DurableMediaCatalogItemRecord,
  DurableMediaEpisodePlacementRecord,
  DurableMediaLibraryRecords,
  DurableMediaSourceRecord,
} from "@/lib/media/media-durable-types";

export class DurableMediaAdapterError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DurableMediaAdapterError";
  }
}

function sortByOrder<T extends { sortOrder?: number }>(items: T[]): T[] {
  return [...items].sort((a, b) => (a.sortOrder ?? 0) - (b.sortOrder ?? 0));
}

function indexById<T extends { id: string }>(items: T[], label: string): Map<string, T> {
  const indexed = new Map<string, T>();

  for (const item of items) {
    if (indexed.has(item.id)) {
      throw new DurableMediaAdapterError(`Duplicate ${label} id: ${item.id}`);
    }

    indexed.set(item.id, item);
  }

  return indexed;
}

function getRequired<T>(items: Map<string, T>, id: string, label: string): T {
  const item = items.get(id);
  if (!item) {
    throw new DurableMediaAdapterError(`Missing ${label}: ${id}`);
  }

  return item;
}

function buildGenreNames(
  records: DurableMediaLibraryRecords,
  catalogItemId: string,
): string[] {
  const genresById = indexById(records.genres, "genre");
  return records.catalogItemGenres
    .filter((itemGenre) => itemGenre.catalogItemId === catalogItemId)
    .sort((a, b) => a.sortOrder - b.sortOrder)
    .map((itemGenre) => {
      return getRequired(genresById, itemGenre.genreId, "genre").name;
    });
}

function toCatalogItemBase(
  records: DurableMediaLibraryRecords,
  item: DurableMediaCatalogItemRecord,
  source: DurableMediaSourceRecord,
) {
  return {
    id: item.id,
    title: item.title,
    description: item.description,
    runtimeMinutes: item.runtimeMinutes,
    posterPath: item.posterPath,
    mediaSource: source.sourcePath,
    sourceKind: source.sourceKind,
    sourceLabel: source.sourceLabel,
    metadata: {
      releaseYear: item.releaseYear,
      genres: buildGenreNames(records, item.id),
      rating: item.rating,
      libraryStatus: item.libraryStatus,
      localFileStrategy: source.localFileStrategy,
      curation: {
        expectedFileName: source.expectedFileName,
        rightsReminder: source.rightsReminder,
        checklist: source.curationChecklist,
      },
    },
  };
}

function assertEpisodePlacement(
  catalogItemsById: Map<string, DurableMediaCatalogItemRecord>,
  showsById: Map<string, { id: string }>,
  seasonsById: Map<string, { id: string; showId: string }>,
  placement: DurableMediaEpisodePlacementRecord,
): void {
  const item = getRequired(catalogItemsById, placement.catalogItemId, "episode item");
  if (item.type !== "episode") {
    throw new DurableMediaAdapterError(
      `Episode placement points to non-episode item: ${placement.catalogItemId}`,
    );
  }

  getRequired(showsById, placement.showId, "show");
  const season = getRequired(seasonsById, placement.seasonId, "season");
  if (season.showId !== placement.showId) {
    throw new DurableMediaAdapterError(
      `Episode placement season ${placement.seasonId} does not belong to show ${placement.showId}`,
    );
  }
}

function buildMovieItem(
  records: DurableMediaLibraryRecords,
  item: DurableMediaCatalogItemRecord,
  source: DurableMediaSourceRecord,
): MovieItem {
  return {
    ...toCatalogItemBase(records, item, source),
    type: "movie",
  };
}

function buildEpisodeItem(
  records: DurableMediaLibraryRecords,
  item: DurableMediaCatalogItemRecord,
  source: DurableMediaSourceRecord,
  placement: DurableMediaEpisodePlacementRecord,
): EpisodeItem {
  return {
    ...toCatalogItemBase(records, item, source),
    type: "episode",
    showId: placement.showId,
    seasonId: placement.seasonId,
    episodeNumber: placement.episodeNumber,
  };
}

function defaultProfileState(profileId: MediaProfileId): MediaProfileState {
  return {
    profileId,
    watchlistIds: [],
    progress: {},
    curationChecks: {},
    playbackAcceptance: {},
  };
}

function buildProfileStates(
  records: DurableMediaLibraryRecords,
): Record<MediaProfileId, MediaProfileState> {
  const states = Object.fromEntries(
    records.profiles.map((profile) => [profile.id, defaultProfileState(profile.id)]),
  ) as Record<MediaProfileId, MediaProfileState>;

  for (const entry of records.watchlistEntries) {
    states[entry.profileId].watchlistIds.push(entry.catalogItemId);
  }

  for (const progress of records.playbackProgress) {
    states[progress.profileId].progress[progress.catalogItemId] = {
      itemId: progress.catalogItemId,
      seconds: Math.max(0, Math.floor(progress.seconds)),
      updatedAt: progress.updatedAt,
    };
  }

  for (const curationCheck of records.curationChecks) {
    states[curationCheck.profileId].curationChecks[curationCheck.catalogItemId] = {
      itemId: curationCheck.catalogItemId,
      authorizedFileConfirmed: curationCheck.authorizedFileConfirmed,
      updatedAt: curationCheck.updatedAt,
    };
  }

  for (const evidence of records.playbackAcceptance) {
    states[evidence.profileId].playbackAcceptance[evidence.catalogItemId] = {
      itemId: evidence.catalogItemId,
      sourceReadyConfirmed: evidence.sourceReadyConfirmed,
      refreshProgressConfirmed: evidence.refreshProgressConfirmed,
      profileIsolationConfirmed: evidence.profileIsolationConfirmed,
      updatedAt: evidence.updatedAt,
    };
  }

  return states;
}

export function adaptDurableMediaLibrary(
  records: DurableMediaLibraryRecords,
): DurableMediaAdapterResult {
  const sourcesById = indexById(records.sources, "source");
  const catalogItemsById = indexById(records.catalogItems, "catalog item");
  const showsById = indexById(records.shows, "show");
  const seasonsById = indexById(records.seasons, "season");

  for (const item of records.catalogItems) {
    getRequired(sourcesById, item.mediaSourceId, "media source");
  }

  for (const placement of records.episodePlacements) {
    assertEpisodePlacement(catalogItemsById, showsById, seasonsById, placement);
  }

  const episodePlacementsByItemId = new Map(
    records.episodePlacements.map((placement) => [placement.catalogItemId, placement]),
  );

  const catalogItems = records.catalogItems.map((item) => {
    const source = getRequired(sourcesById, item.mediaSourceId, "media source");

    if (item.type === "movie") {
      return buildMovieItem(records, item, source);
    }

    const placement = episodePlacementsByItemId.get(item.id);
    if (!placement) {
      throw new DurableMediaAdapterError(
        `Missing episode placement for item: ${item.id}`,
      );
    }

    return buildEpisodeItem(records, item, source, placement);
  });

  const catalogItemsByItemId = new Map(catalogItems.map((item) => [item.id, item]));
  const movies = catalogItems.filter((item): item is MovieItem => item.type === "movie");
  const shows: ShowItem[] = records.shows.map((show) => {
    const seasons: Season[] = records.seasons
      .filter((season) => season.showId === show.id)
      .sort((a, b) => a.seasonNumber - b.seasonNumber)
      .map((season) => {
        const episodes = records.episodePlacements
          .filter((placement) => placement.seasonId === season.id)
          .sort((a, b) => a.episodeNumber - b.episodeNumber)
          .map((placement) => {
            const item = catalogItemsByItemId.get(placement.catalogItemId);
            if (!item || item.type !== "episode") {
              throw new DurableMediaAdapterError(
                `Missing adapted episode item: ${placement.catalogItemId}`,
              );
            }

            return item;
          });

        return {
          id: season.id,
          seasonNumber: season.seasonNumber,
          title: season.title,
          episodes,
        };
      });

    return {
      id: show.id,
      type: "show",
      title: show.title,
      description: show.description,
      posterPath: show.posterPath,
      seasons,
    };
  });

  const demoCatalog: CatalogGroup = {
    movies,
    shows,
  };
  const flattenedCatalogItems: CatalogItem[] = [
    ...demoCatalog.movies,
    ...demoCatalog.shows.flatMap((show) =>
      show.seasons.flatMap((season) => season.episodes),
    ),
  ];
  const profileStates = buildProfileStates(records);
  const mediaProfiles: MediaProfile[] = sortByOrder(records.profiles).map(
    (profile) => ({
      id: profile.id,
      name: profile.name,
    }),
  );

  return {
    mediaProfiles,
    demoCatalog,
    flattenedCatalogItems,
    profileStates,
    getCatalogItemById: (itemId: string) =>
      flattenedCatalogItems.find((item) => item.id === itemId),
    loadProfileState: (profileId: MediaProfileId) =>
      profileStates[profileId] ?? defaultProfileState(profileId),
  };
}
