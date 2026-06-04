import { buildYtmcloneSummary, type YtmcloneEvent } from "@/lib/ytmclone/stats-store";

export const dynamic = "force-dynamic";

export default async function StatsPage() {
  const summary = await buildYtmcloneSummary();

  return (
    <main className="min-h-screen bg-zinc-950 px-4 py-6 text-zinc-100 sm:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <header className="flex flex-col gap-2 border-b border-zinc-800 pb-4">
          <p className="text-sm uppercase tracking-wide text-cyan-300">YTMClone tracking</p>
          <h1 className="text-3xl font-semibold">Stats</h1>
          <p className="break-all text-sm text-zinc-400">Storage: {summary.storagePath}</p>
        </header>

        <section className="grid gap-4 md:grid-cols-4">
          <Metric label="Total events" value={summary.totalEvents} />
          <Metric label="Now-playing changes" value={summary.totalNowPlayingChanges} />
          <Metric label="Unique songs" value={summary.uniqueSongs} />
          <Metric label="Recent raw events" value={summary.rawRecentEvents.length} />
        </section>

        <section className="border border-zinc-800 bg-zinc-900/40 p-4">
          <h2 className="mb-3 text-xl font-semibold">Latest detected track</h2>
          {summary.latestTrack ? <TrackBlock event={summary.latestTrack} /> : <p className="text-zinc-400">No track events yet.</p>}
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <List title="Top songs" rows={summary.topSongs.map((song) => [song.title, song.artist, song.count])} />
          <List title="Top artists" rows={summary.topArtists.map((artist) => [artist.artist, "", artist.count])} />
          <List title="Possible skips" rows={summary.possibleSkips.map(eventRow)} />
          <List title="Possible replays" rows={summary.possibleReplays.map(eventRow)} />
          <List title="Events by source" rows={Object.entries(summary.eventsBySource).map(([key, value]) => [key, "", value])} />
          <List title="Events by day" rows={Object.entries(summary.eventsByDay).map(([key, value]) => [key, "", value])} />
          <List title="Events by hour" rows={Object.entries(summary.eventsByHour).map(([key, value]) => [key, "", value])} />
          <List title="Recent plays" rows={summary.recentPlays.map(eventRow)} />
        </section>

        <section className="overflow-x-auto border border-zinc-800 bg-zinc-900/40 p-4">
          <h2 className="mb-3 text-xl font-semibold">Raw recent events</h2>
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="text-zinc-400">
              <tr>
                <th className="p-2">Captured</th>
                <th className="p-2">Type</th>
                <th className="p-2">Title</th>
                <th className="p-2">Artist</th>
                <th className="p-2">State</th>
                <th className="p-2">Source</th>
                <th className="p-2">Video</th>
              </tr>
            </thead>
            <tbody>
              {summary.rawRecentEvents.map((event, index) => (
                <tr key={`${event.eventId ?? event.capturedAt}-${index}`} className="border-t border-zinc-800">
                  <td className="p-2">{event.capturedAt}</td>
                  <td className="p-2">{event.eventType}</td>
                  <td className="p-2">{event.title ?? ""}</td>
                  <td className="p-2">{event.artist ?? ""}</td>
                  <td className="p-2">{event.playbackState ?? ""}</td>
                  <td className="p-2">{event.source ?? ""}</td>
                  <td className="max-w-64 break-all p-2">{event.videoId ?? event.watchUrl ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-zinc-800 bg-zinc-900/40 p-4">
      <div className="text-sm text-zinc-400">{label}</div>
      <div className="mt-2 text-3xl font-semibold">{value}</div>
    </div>
  );
}

function TrackBlock({ event }: { event: YtmcloneEvent }) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row">
      {event.thumbnailUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img alt="" className="h-24 w-24 object-cover" src={event.thumbnailUrl} />
      ) : null}
      <div>
        <p className="text-2xl font-semibold">{event.title ?? "Unknown title"}</p>
        <p className="text-zinc-300">{event.artist ?? "Unknown artist"}</p>
        <p className="mt-2 text-sm text-zinc-400">{event.playbackState ?? "unknown state"} at {event.capturedAt}</p>
      </div>
    </div>
  );
}

function List({ title, rows }: { title: string; rows: Array<[string, string, string | number]> }) {
  return (
    <section className="border border-zinc-800 bg-zinc-900/40 p-4">
      <h2 className="mb-3 text-xl font-semibold">{title}</h2>
      {rows.length === 0 ? (
        <p className="text-sm text-zinc-400">No data yet.</p>
      ) : (
        <div className="flex flex-col divide-y divide-zinc-800">
          {rows.slice(0, 25).map(([primary, secondary, count], index) => (
            <div key={`${title}-${primary}-${index}`} className="grid grid-cols-[1fr_auto] gap-3 py-2 text-sm">
              <div>
                <div>{primary}</div>
                {secondary ? <div className="text-zinc-400">{secondary}</div> : null}
              </div>
              <div className="text-zinc-300">{count}</div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function eventRow(event: YtmcloneEvent): [string, string, string] {
  return [event.title ?? event.videoId ?? event.eventType, event.artist ?? event.capturedAt, event.playbackState ?? ""];
}
