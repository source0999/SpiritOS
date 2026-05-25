import type {
  CatalogGroup,
  CatalogItem,
  MediaProfile,
} from "@/components/media/media-types";

export const mediaProfiles: MediaProfile[] = [
  { id: "britton", name: "Britton" },
  { id: "friend", name: "Friend" },
  { id: "guest", name: "Guest" },
];

export const demoCatalog: CatalogGroup = {
  movies: [
    {
      id: "movie-they-were-right",
      type: "movie",
      title: "They Were Right",
      description:
        "A locally supplied MP4 served directly from public/media and listed through the manual media catalog.",
      runtimeMinutes: 60,
      posterPath: "/media/poster-they-were-right.jpg",
      mediaSource: "/media/they-were-right.mp4",
      sourceKind: "authorized-local-sample",
      sourceLabel: "Manual local MP4 catalog entry",
      metadata: {
        releaseYear: 2026,
        genres: ["Local Library", "Movie"],
        rating: "Unrated",
        libraryStatus: "ready-for-owned-file",
        localFileStrategy: "manual-public-media-match",
        curation: {
          expectedFileName: "they-were-right.mp4",
          rightsReminder:
            "Use only the local MP4 Britton owns, created, or has permission to test.",
          checklist: [
            "Confirm /media/they-were-right.mp4 plays directly in the browser.",
            "Open /media and select They Were Right.",
            "Play, seek, and refresh to confirm Continue Watching persists.",
          ],
        },
      },
    },
    {
      id: "movie-survivors-of-saturn",
      type: "movie",
      title: "Survivors of Saturn",
      description:
        "A locally supplied MP4 served directly from public/media and listed through the manual media catalog.",
      runtimeMinutes: 60,
      posterPath: "/media/poster-survivors-of-saturn.jpg",
      mediaSource: "/media/survivors-of-saturn.mp4",
      sourceKind: "authorized-local-sample",
      sourceLabel: "Manual local MP4 catalog entry",
      metadata: {
        releaseYear: 2026,
        genres: ["Local Library", "Movie"],
        rating: "Unrated",
        libraryStatus: "ready-for-owned-file",
        localFileStrategy: "manual-public-media-match",
        curation: {
          expectedFileName: "survivors-of-saturn.mp4",
          rightsReminder:
            "Use only the local MP4 Britton owns, created, or has permission to test.",
          checklist: [
            "Confirm /media/survivors-of-saturn.mp4 plays directly in the browser.",
            "Open /media and select Survivors of Saturn.",
            "Play, seek, and refresh to confirm Continue Watching persists.",
          ],
        },
      },
    },
    {
      id: "movie-kabbalah-intro",
      type: "movie",
      title: "Kabbalah Intro",
      description:
        "A locally supplied MP4 served directly from public/media and listed through the manual media catalog.",
      runtimeMinutes: 60,
      posterPath: "/media/poster-kabbalah-intro.jpg",
      mediaSource: "/media/kabbalah-intro.mp4",
      sourceKind: "authorized-local-sample",
      sourceLabel: "Manual local MP4 catalog entry",
      metadata: {
        releaseYear: 2026,
        genres: ["Local Library", "Movie"],
        rating: "Unrated",
        libraryStatus: "ready-for-owned-file",
        localFileStrategy: "manual-public-media-match",
        curation: {
          expectedFileName: "kabbalah-intro.mp4",
          rightsReminder:
            "Use only the local MP4 Britton owns, created, or has permission to test.",
          checklist: [
            "Confirm /media/kabbalah-intro.mp4 plays directly in the browser.",
            "Open /media and select Kabbalah Intro.",
            "Play, seek, and refresh to confirm Continue Watching persists.",
          ],
        },
      },
    },
    {
      id: "movie-jesus-was-not-a-christian",
      type: "movie",
      title: "Jesus Was Not a Christian",
      description:
        "A locally supplied MP4 served directly from public/media and listed through the manual media catalog.",
      runtimeMinutes: 60,
      posterPath: "/media/poster-jesus-was-not-a-christian.jpg",
      mediaSource: "/media/jesus-was-not-a-christian.mp4",
      sourceKind: "authorized-local-sample",
      sourceLabel: "Manual local MP4 catalog entry",
      metadata: {
        releaseYear: 2026,
        genres: ["Local Library", "Movie"],
        rating: "Unrated",
        libraryStatus: "ready-for-owned-file",
        localFileStrategy: "manual-public-media-match",
        curation: {
          expectedFileName: "jesus-was-not-a-christian.mp4",
          rightsReminder:
            "Use only the local MP4 Britton owns, created, or has permission to test.",
          checklist: [
            "Confirm /media/jesus-was-not-a-christian.mp4 plays directly in the browser.",
            "Open /media and select Jesus Was Not a Christian.",
            "Play, seek, and refresh to confirm Continue Watching persists.",
          ],
        },
      },
    },
    {
      id: "movie-local-lights",
      type: "movie",
      title: "Local Lights",
      description:
        "A placeholder feature used to prove native playback, resume, and watchlist behavior inside the isolated media route.",
      runtimeMinutes: 92,
      posterPath: "/media/poster-local-lights.jpg",
      mediaSource: "/media/sample-movie.mp4",
      sourceKind: "authorized-local-sample",
      sourceLabel: "Authorized local MP4 sample",
      metadata: {
        releaseYear: 2026,
        genres: ["Drama", "Local Demo"],
        rating: "PG",
        libraryStatus: "ready-for-owned-file",
        localFileStrategy: "manual-public-media-match",
        curation: {
          expectedFileName: "sample-movie.mp4",
          rightsReminder:
            "Use only an MP4 Britton owns, created, or has permission to test.",
          checklist: [
            "Place the file at public/media/sample-movie.mp4.",
            "Open /media and select Local Lights.",
            "Confirm the source status changes to Ready after playback can load.",
          ],
        },
      },
    },
    {
      id: "movie-workbench-weekend",
      type: "movie",
      title: "Workbench Weekend",
      description:
        "A quiet demo movie entry for testing missing poster and missing video states without shipping media files.",
      runtimeMinutes: 78,
      posterPath: "/media/poster-workbench-weekend.jpg",
      mediaSource: "/media/sample-workbench.webm",
      sourceKind: "authorized-local-sample",
      sourceLabel: "Authorized local WebM sample",
      metadata: {
        releaseYear: 2026,
        genres: ["Documentary", "Local Demo"],
        rating: "Unrated",
        libraryStatus: "demo-placeholder",
        localFileStrategy: "manual-public-media-match",
        curation: {
          expectedFileName: "sample-workbench.webm",
          rightsReminder:
            "Use only a WebM Britton owns, created, or has permission to test.",
          checklist: [
            "Place the file at public/media/sample-workbench.webm.",
            "Open /media and select Workbench Weekend.",
            "Confirm missing state becomes Ready when the browser can load it.",
          ],
        },
      },
    },
  ],
  shows: [
    {
      id: "show-signal-house",
      type: "show",
      title: "Signal House",
      description:
        "A starter show with local placeholder episodes for proving show, season, and episode relationships.",
      posterPath: "/media/poster-signal-house.jpg",
      seasons: [
        {
          id: "signal-house-season-1",
          seasonNumber: 1,
          title: "Season 1",
          episodes: [
            {
              id: "episode-signal-house-s1e1",
              type: "episode",
              showId: "show-signal-house",
              seasonId: "signal-house-season-1",
              episodeNumber: 1,
              title: "Pilot Light",
              description:
                "The first placeholder episode for testing episode playback and per-profile progress.",
              runtimeMinutes: 28,
              posterPath: "/media/poster-signal-house-e1.jpg",
              mediaSource: "/media/sample-episode-1.mp4",
              sourceKind: "authorized-local-sample",
              sourceLabel: "Authorized local MP4 episode sample",
              metadata: {
                releaseYear: 2026,
                genres: ["Series", "Local Demo"],
                rating: "TV-PG",
                libraryStatus: "ready-for-owned-file",
                localFileStrategy: "manual-public-media-match",
                curation: {
                  expectedFileName: "sample-episode-1.mp4",
                  rightsReminder:
                    "Use only an episode sample Britton owns, created, or has permission to test.",
                  checklist: [
                    "Place the file at public/media/sample-episode-1.mp4.",
                    "Open /media and select Pilot Light.",
                    "Seek and refresh to confirm progress persists.",
                  ],
                },
              },
            },
            {
              id: "episode-signal-house-s1e2",
              type: "episode",
              showId: "show-signal-house",
              seasonId: "signal-house-season-1",
              episodeNumber: 2,
              title: "Second Signal",
              description:
                "A second placeholder episode so Continue Watching and Watchlist can cover episodic media.",
              runtimeMinutes: 31,
              posterPath: "/media/poster-signal-house-e2.jpg",
              mediaSource: "/media/sample-episode-2.mp4",
              sourceKind: "authorized-local-sample",
              sourceLabel: "Authorized local MP4 episode sample",
              metadata: {
                releaseYear: 2026,
                genres: ["Series", "Local Demo"],
                rating: "TV-PG",
                libraryStatus: "demo-placeholder",
                localFileStrategy: "manual-public-media-match",
                curation: {
                  expectedFileName: "sample-episode-2.mp4",
                  rightsReminder:
                    "Use only an episode sample Britton owns, created, or has permission to test.",
                  checklist: [
                    "Place the file at public/media/sample-episode-2.mp4.",
                    "Open /media and select Second Signal.",
                    "Confirm Watchlist and progress remain profile-specific.",
                  ],
                },
              },
            },
          ],
        },
      ],
    },
  ],
};

export const flattenedCatalogItems: CatalogItem[] = [
  ...demoCatalog.movies,
  ...demoCatalog.shows.flatMap((show) =>
    show.seasons.flatMap((season) => season.episodes),
  ),
];

export function getCatalogItemById(itemId: string): CatalogItem | undefined {
  return flattenedCatalogItems.find((item) => item.id === itemId);
}
