import { mkdir, readFile, stat, writeFile } from "node:fs/promises";
import path from "node:path";

export type YtmcloneEvent = {
  eventId?: string;
  eventType: string;
  capturedAt: string;
  deviceId: string;
  sessionId: string;
  source?: string;
  title?: string;
  artist?: string;
  album?: string;
  thumbnailUrl?: string;
  videoId?: string;
  watchUrl?: string;
  sourceUrl?: string;
  playbackState?: string;
  positionSeconds?: number;
  durationSeconds?: number;
  raw?: unknown;
};

export type YtmcloneStatsSummary = {
  storagePath: string;
  latestTrack: YtmcloneEvent | null;
  totalEvents: number;
  totalNowPlayingChanges: number;
  uniqueSongs: number;
  topSongs: Array<{ key: string; title: string; artist: string; count: number }>;
  topArtists: Array<{ artist: string; count: number }>;
  recentPlays: YtmcloneEvent[];
  possibleSkips: YtmcloneEvent[];
  possibleReplays: YtmcloneEvent[];
  eventsBySource: Record<string, number>;
  eventsByDay: Record<string, number>;
  eventsByHour: Record<string, number>;
  rawRecentEvents: YtmcloneEvent[];
};

const PRIMARY_LOG_PATH = "/mnt/spirit-8tb/ytmclone-tracking/events.jsonl";
const FALLBACK_LOG_PATH = path.join(process.cwd(), ".spirit-backups", "ytmclone-tracking", "events.jsonl");

export async function getYtmcloneEventLogPath() {
  const primaryDir = path.dirname(PRIMARY_LOG_PATH);

  try {
    const info = await stat(primaryDir);
    if (info.isDirectory()) {
      return PRIMARY_LOG_PATH;
    }
  } catch {
    // The Dell 8TB mount is optional; the fallback remains durable in-repo.
  }

  return FALLBACK_LOG_PATH;
}

export function normalizeYtmcloneEvent(input: unknown): YtmcloneEvent | null {
  if (!input || typeof input !== "object") {
    return null;
  }

  const candidate = input as Record<string, unknown>;
  const eventType = asNonEmptyString(candidate.eventType);
  const deviceId = asNonEmptyString(candidate.deviceId);
  const sessionId = asNonEmptyString(candidate.sessionId);
  const capturedAt = asNonEmptyString(candidate.capturedAt) ?? new Date().toISOString();

  if (!eventType || !deviceId || !sessionId) {
    return null;
  }

  return {
    eventId: asNonEmptyString(candidate.eventId),
    eventType,
    capturedAt,
    deviceId,
    sessionId,
    source: asNonEmptyString(candidate.source) ?? "android-webview",
    title: asNonEmptyString(candidate.title),
    artist: asNonEmptyString(candidate.artist),
    album: asNonEmptyString(candidate.album),
    thumbnailUrl: asNonEmptyString(candidate.thumbnailUrl),
    videoId: asNonEmptyString(candidate.videoId),
    watchUrl: asNonEmptyString(candidate.watchUrl),
    sourceUrl: asNonEmptyString(candidate.sourceUrl),
    playbackState: asNonEmptyString(candidate.playbackState),
    positionSeconds: asFiniteNumber(candidate.positionSeconds),
    durationSeconds: asFiniteNumber(candidate.durationSeconds),
    raw: candidate.raw,
  };
}

export async function appendYtmcloneEvents(inputs: unknown[]) {
  const events = inputs.map(normalizeYtmcloneEvent).filter((event): event is YtmcloneEvent => Boolean(event));
  const logPath = await getYtmcloneEventLogPath();
  const existingIds = await readEventIds(logPath);
  const accepted: YtmcloneEvent[] = [];
  let duplicateCount = 0;

  for (const event of events) {
    if (event.eventId && existingIds.has(event.eventId)) {
      duplicateCount += 1;
      continue;
    }

    if (event.eventId) {
      existingIds.add(event.eventId);
    }
    accepted.push(event);
  }

  if (accepted.length > 0) {
    await mkdir(path.dirname(logPath), { recursive: true });
    const lines = accepted.map((event) => JSON.stringify(event)).join("\n") + "\n";
    await writeFile(logPath, lines, { flag: "a" });
  }

  return {
    storagePath: logPath,
    accepted: accepted.length,
    duplicateCount,
    rejected: inputs.length - events.length,
  };
}

export async function readYtmcloneEvents(): Promise<YtmcloneEvent[]> {
  const logPath = await getYtmcloneEventLogPath();

  try {
    const text = await readFile(logPath, "utf8");
    return text
      .split("\n")
      .filter(Boolean)
      .map((line) => {
        try {
          return JSON.parse(line) as YtmcloneEvent;
        } catch {
          return null;
        }
      })
      .filter((event): event is YtmcloneEvent => Boolean(event));
  } catch {
    return [];
  }
}

export async function buildYtmcloneSummary(): Promise<YtmcloneStatsSummary> {
  const storagePath = await getYtmcloneEventLogPath();
  const events = await readYtmcloneEvents();
  const plays = events.filter((event) => isTrackEvent(event));
  const songCounts = new Map<string, { title: string; artist: string; count: number }>();
  const artistCounts = new Map<string, number>();
  const eventsBySource: Record<string, number> = {};
  const eventsByDay: Record<string, number> = {};
  const eventsByHour: Record<string, number> = {};

  for (const event of events) {
    increment(eventsBySource, event.source ?? "unknown");
    const date = safeDate(event.capturedAt);
    if (date) {
      increment(eventsByDay, date.toISOString().slice(0, 10));
      increment(eventsByHour, date.toISOString().slice(0, 13));
    }
  }

  for (const event of plays) {
    const title = event.title ?? "Unknown title";
    const artist = event.artist ?? "Unknown artist";
    const key = `${title.toLowerCase()}|${artist.toLowerCase()}`;
    const current = songCounts.get(key) ?? { title, artist, count: 0 };
    current.count += 1;
    songCounts.set(key, current);
    incrementMap(artistCounts, artist);
  }

  return {
    storagePath,
    latestTrack: [...plays].reverse().find((event) => Boolean(event.title || event.videoId)) ?? null,
    totalEvents: events.length,
    totalNowPlayingChanges: plays.length,
    uniqueSongs: songCounts.size,
    topSongs: [...songCounts.entries()]
      .map(([key, value]) => ({ key, ...value }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 25),
    topArtists: [...artistCounts.entries()]
      .map(([artist, count]) => ({ artist, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 25),
    recentPlays: [...plays].reverse().slice(0, 25),
    possibleSkips: events.filter((event) => event.eventType === "possible_skip").reverse().slice(0, 25),
    possibleReplays: events.filter((event) => event.eventType === "possible_replay").reverse().slice(0, 25),
    eventsBySource,
    eventsByDay,
    eventsByHour,
    rawRecentEvents: [...events].reverse().slice(0, 75),
  };
}

async function readEventIds(logPath: string) {
  const ids = new Set<string>();
  const events = await readJsonl(logPath);

  for (const event of events) {
    if (typeof event.eventId === "string" && event.eventId.length > 0) {
      ids.add(event.eventId);
    }
  }

  return ids;
}

async function readJsonl(logPath: string): Promise<Array<Record<string, unknown>>> {
  try {
    const text = await readFile(logPath, "utf8");
    return text
      .split("\n")
      .filter(Boolean)
      .map((line) => {
        try {
          return JSON.parse(line) as Record<string, unknown>;
        } catch {
          return {};
        }
      });
  } catch {
    return [];
  }
}

function isTrackEvent(event: YtmcloneEvent) {
  return event.eventType === "now_playing" || event.eventType === "track_changed";
}

function asNonEmptyString(value: unknown) {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : undefined;
}

function asFiniteNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function increment(record: Record<string, number>, key: string) {
  record[key] = (record[key] ?? 0) + 1;
}

function incrementMap(map: Map<string, number>, key: string) {
  map.set(key, (map.get(key) ?? 0) + 1);
}

function safeDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? null : date;
}
