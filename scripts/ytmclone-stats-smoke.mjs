const baseUrl = process.env.YTMCLONE_STATS_BASE_URL ?? "http://127.0.0.1:3000";
const eventId = `smoke-${Date.now()}`;

const event = {
  eventId,
  eventType: "now_playing",
  capturedAt: new Date().toISOString(),
  deviceId: "dell-smoke",
  sessionId: "smoke-session",
  source: "smoke",
  title: "Smoke Test Track",
  artist: "SpiritOS",
  playbackState: "playing",
};

const post = await fetch(`${baseUrl}/api/ytmclone/stats/events`, {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify(event),
});

const postJson = await post.json();
console.log("POST /api/ytmclone/stats/events", post.status, postJson);

const summary = await fetch(`${baseUrl}/api/ytmclone/stats/summary`);
const summaryJson = await summary.json();
console.log("GET /api/ytmclone/stats/summary", summary.status, {
  ok: summaryJson.ok,
  totalEvents: summaryJson.totalEvents,
  latestTrack: summaryJson.latestTrack,
  storagePath: summaryJson.storagePath,
});

if (!post.ok || !summary.ok || !summaryJson.ok) {
  process.exitCode = 1;
}
