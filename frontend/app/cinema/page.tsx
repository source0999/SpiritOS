"use client";

/**
 * Sovereign Cinema — UI shell (Netflix / HBO Max style).
 *
 * Future TMDB wiring: inject `process.env.NEXT_PUBLIC_TMDB_API_KEY` in a Server
 * Component or route handler to fetch poster paths, backdrops, and discovery
 * feeds; pass resolved URLs as props into this page or a child layout. Do not
 * expose the key to the client bundle except via prefixed public env at build time.
 */

import { useState, useCallback, useMemo, type TouchEvent } from "react";
import Link from "next/link";
import {
  Search,
  Play,
  Plus,
  ChevronRight,
  Film,
  Sparkles,
} from "lucide-react";

// ─── Mock data ───────────────────────────────────────────────────────────────

type Profile = { id: string; name: string; color: string };

const PROFILES: Profile[] = [
  { id: "p1", name: "Source",   color: "bg-violet-500" },
  { id: "p2", name: "Guest",    color: "bg-sky-500" },
  { id: "p3", name: "Homelab",  color: "bg-emerald-500" },
  { id: "p4", name: "Archive",  color: "bg-amber-500" },
];

const HERO_MOVIE = {
  title:    "Neon Drift Protocol",
  synopsis:
    "A rogue archivist races zero-trust firewalls to recover the last honest feed before the mesh goes dark. Spirit-approved cynicism sold separately.",
  tags:     ["Top 10 in Homelab", "Sci-Fi", "4K HDR", "Dolby Vision"] as const,
  /** Solid gradient stack — no backdrop-blur; simulates key art wash */
  bgLayers: "from-indigo-950 via-zinc-900 to-zinc-950",
};

type ContinueItem = {
  id: string;
  title: string;
  episodeLabel: string;
  progress: number;
};

const CONTINUE_WATCHING: ContinueItem[] = [
  { id: "cw1", title: "Signal & Silence",   episodeLabel: "S2 E4 · Next: S2 E5 →", progress: 0.62 },
  { id: "cw2", title: "Ghost Node Diaries", episodeLabel: "S1 E9 · ARP Cache Poison",   progress: 0.28 },
  { id: "cw3", title: "Radarr After Dark",  episodeLabel: "S3 E1 · Queue Anxiety",      progress: 0.91 },
];

type MovieCard = {
  id: string;
  title: string;
  year: number;
  rating?: string;
  genre?: string;
};

const RECENTLY_ADDED: MovieCard[] = [
  { id: "ra1", title: "Glass Orchard",     year: 2025, rating: "TV-MA", genre: "Thriller" },
  { id: "ra2", title: "Iron Lullaby",      year: 2024, rating: "PG-13", genre: "Drama" },
  { id: "ra3", title: "Satellite Saints",  year: 2023, rating: "R",     genre: "Sci-Fi" },
  { id: "ra4", title: "Midnight Ledger",   year: 2025, rating: "TV-14", genre: "Mystery" },
];

const MY_LIST: MovieCard[] = [
  { id: "ml1", title: "Void Cartographer", year: 2022, genre: "Sci-Fi" },
  { id: "ml2", title: "Paper Tigers",      year: 2021, genre: "Action" },
  { id: "ml3", title: "Slow Burn Relay",   year: 2024, genre: "Drama" },
  { id: "ml4", title: "Cinder & Code",     year: 2023, genre: "Thriller" },
  { id: "ml5", title: "North Star Noir",   year: 2020, genre: "Crime" },
];

type CustomFolder = {
  id: string;
  name: string;
  sub: string;
  accent: string;
};

const CUSTOM_FOLDERS: CustomFolder[] = [
  { id: "f1", name: "Sunday Night Thrillers", sub: "12 titles · curated", accent: "from-red-950/80 to-zinc-900" },
  { id: "f2", name: "Anime Vault",            sub: "24 titles · synced",  accent: "from-violet-950/80 to-zinc-900" },
  { id: "f3", name: "4K Reference Stack",     sub: "8 titles · HDR only",  accent: "from-sky-950/80 to-zinc-900" },
];

const CATEGORIES: Record<"trending" | "sciFi" | "action" | "drama", MovieCard[]> = {
  trending: [
    { id: "t1", title: "Pulsewidth",       year: 2025, rating: "TV-MA" },
    { id: "t2", title: "Harbor Lights",    year: 2024, rating: "PG-13" },
    { id: "t3", title: "Rust & Ritual",    year: 2023, rating: "R" },
    { id: "t4", title: "Echo Chamber",     year: 2025, rating: "TV-14" },
    { id: "t5", title: "Parallel Harvest", year: 2022, rating: "PG-13" },
    { id: "t6", title: "Cold Storage",     year: 2021, rating: "R" },
  ],
  sciFi: [
    { id: "s1", title: "Orbital Debt",      year: 2024, genre: "Sci-Fi" },
    { id: "s2", title: "Dust Arithmetic",   year: 2023, genre: "Sci-Fi" },
    { id: "s3", title: "Tidal Memory",      year: 2025, genre: "Sci-Fi" },
    { id: "s4", title: "Quantum Etiquette", year: 2022, genre: "Sci-Fi" },
    { id: "s5", title: "Lagrange Suite",    year: 2021, genre: "Sci-Fi" },
  ],
  action: [
    { id: "a1", title: "Brass Circuit",   year: 2024, genre: "Action" },
    { id: "a2", title: "Redline Sunday",  year: 2023, genre: "Action" },
    { id: "a3", title: "Concrete Saints", year: 2025, genre: "Action" },
    { id: "a4", title: "Smoke Signal",    year: 2022, genre: "Action" },
    { id: "a5", title: "Velvet Hammer",   year: 2020, genre: "Action" },
  ],
  drama: [
    { id: "d1", title: "Winter Ledger",   year: 2024, genre: "Drama" },
    { id: "d2", title: "Paperweight",     year: 2023, genre: "Drama" },
    { id: "d3", title: "The Quiet Index", year: 2025, genre: "Drama" },
    { id: "d4", title: "Salt & Ceremony", year: 2021, genre: "Drama" },
    { id: "d5", title: "Blue Hour",       year: 2022, genre: "Drama" },
  ],
};

// ─── Utilities ───────────────────────────────────────────────────────────────

function cn(...classes: (string | undefined | false | null)[]) {
  return classes.filter(Boolean).join(" ");
}

function touchEnd(
  handler: () => void,
): (e: TouchEvent) => void {
  return (e) => {
    e.preventDefault();
    handler();
  };
}

// ─── Carousel row ────────────────────────────────────────────────────────────

function CarouselRow({
  title,
  actionLabel = "See all",
  children,
}: {
  title: string;
  actionLabel?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mb-8 md:mb-10">
      <div className="mb-3 flex items-end justify-between gap-3 px-4 md:px-8">
        <h2 className="text-sm font-semibold tracking-tight text-zinc-100 md:text-base">{title}</h2>
        <button
          type="button"
          onClick={() => {}}
          onTouchEnd={touchEnd(() => {})}
          className="flex cursor-pointer touch-manipulation items-center gap-0.5 text-[11px] font-medium text-zinc-500 transition-colors hover:text-violet-400 active:[transform:scale3d(0.97,0.97,1)]"
        >
          {actionLabel}
          <ChevronRight size={12} className="pointer-events-none" aria-hidden />
        </button>
      </div>
      <div
        className="flex gap-3 overflow-x-auto overscroll-x-none scroll-smooth px-4 pb-1 md:px-8 [scrollbar-width:thin]"
        style={{ WebkitOverflowScrolling: "touch" }}
      >
        {children}
      </div>
    </section>
  );
}

function PosterCard({
  movie,
  className,
}: {
  movie: MovieCard;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={() => {}}
      onTouchEnd={touchEnd(() => {})}
      className={cn(
        "group relative w-[120px] flex-shrink-0 cursor-pointer touch-manipulation overflow-hidden rounded-2xl border border-white/[0.06] bg-zinc-800 text-left transition-transform duration-200 sm:w-[132px] md:w-[148px]",
        "hover:[transform:scale3d(1.05,1.05,1)] active:[transform:scale3d(0.98,0.98,1)]",
        className,
      )}
    >
      <div className="aspect-[2/3] w-full bg-zinc-800" />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-zinc-950/90 via-transparent to-transparent opacity-0 transition-opacity duration-200 group-hover:opacity-100" />
      <div className="absolute bottom-0 left-0 right-0 p-2">
        <p className="line-clamp-2 text-[10px] font-medium leading-tight text-zinc-100 sm:text-xs">{movie.title}</p>
        <p className="mt-0.5 text-[9px] text-zinc-500">{movie.year}</p>
        {movie.rating && (
          <span className="mt-1 inline-block rounded border border-white/10 bg-black/40 px-1 py-0.5 text-[8px] text-zinc-400">
            {movie.rating}
          </span>
        )}
      </div>
    </button>
  );
}

function ContinueCard({ item }: { item: ContinueItem }) {
  return (
    <button
      type="button"
      onClick={() => {}}
      onTouchEnd={touchEnd(() => {})}
      className={cn(
        "group relative w-[220px] flex-shrink-0 cursor-pointer touch-manipulation overflow-hidden rounded-xl border border-white/[0.07] bg-zinc-800 text-left sm:w-[260px] md:w-[280px]",
        "hover:[transform:scale3d(1.05,1.05,1)] active:[transform:scale3d(0.98,0.98,1)]",
      )}
    >
      <div className="aspect-video w-full bg-zinc-800" />
      <div className="absolute bottom-0 left-0 right-0 border-t border-white/5 bg-zinc-950/95 px-2 py-1.5">
        <p className="truncate text-[11px] font-semibold text-zinc-100">{item.title}</p>
        <p className="truncate text-[10px] text-zinc-500">{item.episodeLabel}</p>
        <div className="relative mt-1.5 h-1 w-full overflow-hidden rounded-full bg-white/10">
          <div
            className="absolute inset-y-0 left-0 origin-left rounded-full bg-red-600"
            style={{ transform: `scaleX(${item.progress})`, transition: "transform 400ms ease-out" }}
          />
        </div>
      </div>
    </button>
  );
}

function FolderCard({ folder }: { folder: CustomFolder }) {
  return (
    <button
      type="button"
      onClick={() => {}}
      onTouchEnd={touchEnd(() => {})}
      className={cn(
        "group relative w-[200px] flex-shrink-0 cursor-pointer touch-manipulation overflow-hidden rounded-xl border border-white/[0.07] text-left sm:w-[240px]",
        "bg-gradient-to-br hover:[transform:scale3d(1.05,1.05,1)] active:[transform:scale3d(0.98,0.98,1)]",
        folder.accent,
      )}
    >
      <div className="aspect-[21/9] min-h-[88px] w-full bg-zinc-900/50" />
      <div className="absolute inset-0 flex flex-col justify-end p-3">
        <Film size={14} className="mb-1 text-zinc-300 opacity-80" aria-hidden />
        <p className="text-xs font-semibold text-zinc-100">{folder.name}</p>
        <p className="text-[10px] text-zinc-500">{folder.sub}</p>
      </div>
    </button>
  );
}

// ─── Profile gate ─────────────────────────────────────────────────────────────

function ProfileGate({
  onSelect,
}: {
  onSelect: (id: string) => void;
}) {
  return (
    <div className="fixed inset-0 z-[99996] flex min-h-[100dvh] flex-col items-center justify-center bg-zinc-950 px-6 pt-[60px] md:z-50 md:pt-0">
      <div className="mb-10 text-center">
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-violet-400">Sovereign Cinema</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-zinc-100 md:text-3xl">Who&apos;s watching?</h1>
        <p className="mt-2 text-sm text-zinc-500">Isolated watch history · Jellyfin-ready</p>
      </div>

      <div className="flex max-w-lg flex-wrap items-start justify-center gap-6 md:gap-8">
        {PROFILES.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => onSelect(p.id)}
            onTouchEnd={touchEnd(() => onSelect(p.id))}
            className="flex flex-col items-center gap-2 touch-manipulation transition-transform duration-200 hover:[transform:scale3d(1.06,1.06,1)] active:[transform:scale3d(0.96,0.96,1)]"
          >
            <div
              className={cn(
                "flex h-24 w-24 items-center justify-center rounded-lg border-2 border-transparent md:h-28 md:w-28",
                "hover:border-white/20",
                p.color,
              )}
              aria-hidden
            >
              <span className="text-2xl font-bold text-white/90">{p.name.slice(0, 1)}</span>
            </div>
            <span className="text-sm text-zinc-400">{p.name}</span>
          </button>
        ))}

        <button
          type="button"
          onClick={() => {}}
          onTouchEnd={touchEnd(() => {})}
          className="flex flex-col items-center gap-2 touch-manipulation text-zinc-500 transition-transform duration-200 hover:[transform:scale3d(1.06,1.06,1)] hover:text-zinc-300 active:[transform:scale3d(0.96,0.96,1)]"
        >
          <div className="flex h-24 w-24 items-center justify-center rounded-lg border-2 border-dashed border-zinc-600 bg-zinc-900 md:h-28 md:w-28">
            <Plus size={28} className="pointer-events-none" strokeWidth={1.5} aria-hidden />
          </div>
          <span className="text-sm">Add Profile</span>
        </button>
      </div>
    </div>
  );
}

// ─── Main cinema shell ─────────────────────────────────────────────────────────

function CinemaMain({
  activeProfileId,
  onExitProfile,
}: {
  activeProfileId: string;
  onExitProfile: () => void;
}) {
  const profile = useMemo(
    () => PROFILES.find((p) => p.id === activeProfileId) ?? PROFILES[0],
    [activeProfileId],
  );

  return (
    <div className="min-h-[100dvh] bg-zinc-950 pb-16 md:pb-12">
      {/* Transparent top bar — solid transparent via bg-zinc-950/0 is invisible; use gradient for readability */}
      <header className="fixed left-0 right-0 top-[60px] z-40 flex h-14 items-center justify-between bg-gradient-to-b from-zinc-950/95 to-zinc-950/0 px-4 md:top-0 md:h-16 md:px-8">
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold tracking-tight text-zinc-100 md:hidden">Cinema</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            aria-label="Search"
            onClick={() => {}}
            onTouchEnd={touchEnd(() => {})}
            className="flex h-10 w-10 cursor-pointer touch-manipulation items-center justify-center rounded-lg text-zinc-300 transition-transform active:[transform:scale3d(0.94,0.94,1)]"
          >
            <Search size={18} className="pointer-events-none" aria-hidden />
          </button>
          <button
            type="button"
            aria-label="Switch profile"
            onClick={onExitProfile}
            onTouchEnd={touchEnd(onExitProfile)}
            className={cn(
              "flex h-9 w-9 cursor-pointer touch-manipulation items-center justify-center overflow-hidden rounded-md border border-white/10 ring-2 ring-violet-400 transition-transform active:[transform:scale3d(0.94,0.94,1)]",
              profile.color,
            )}
          >
            <span className="text-xs font-bold text-white">{profile.name.slice(0, 1)}</span>
          </button>
        </div>
      </header>

      {/* Hero — 60dvh–75dvh band; trailer placeholder = solid zinc + pulse strip */}
      <section
        className={cn(
          "relative flex min-h-[60dvh] max-h-[75dvh] flex-col justify-end overflow-hidden bg-gradient-to-br",
          HERO_MOVIE.bgLayers,
        )}
      >
        <div className="absolute inset-0 bg-zinc-900">
          <div className="h-full w-full animate-pulse bg-zinc-800/80" aria-hidden />
        </div>
        <div
          className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/40 to-zinc-950/10"
          aria-hidden
        />

        <div className="relative z-10 px-4 pb-10 pt-24 md:px-12 md:pb-16 md:pt-28">
          <div className="mb-3 inline-flex items-center gap-2 rounded border border-amber-500/30 bg-amber-500/10 px-2 py-1">
            <Sparkles size={11} className="text-amber-400" aria-hidden />
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-200">Top 10</span>
          </div>
          <h1 className="max-w-xl text-3xl font-bold tracking-tight text-zinc-50 md:text-5xl md:leading-tight">
            {HERO_MOVIE.title}
          </h1>
          <p className="mt-3 max-w-lg text-sm leading-relaxed text-zinc-400 md:text-base">{HERO_MOVIE.synopsis}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {HERO_MOVIE.tags.map((t) => (
              <span
                key={t}
                className="rounded-md border border-white/10 bg-black/30 px-2 py-0.5 text-[10px] font-medium text-zinc-400"
              >
                {t}
              </span>
            ))}
          </div>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => {}}
              onTouchEnd={touchEnd(() => {})}
              className="flex cursor-pointer touch-manipulation items-center gap-2 rounded-md bg-white px-5 py-2.5 text-sm font-semibold text-zinc-950 transition-transform active:[transform:scale3d(0.97,0.97,1)]"
            >
              <Play size={16} className="pointer-events-none fill-zinc-950" aria-hidden />
              Play
            </button>
            <button
              type="button"
              onClick={() => {}}
              onTouchEnd={touchEnd(() => {})}
              className="rounded-md border border-white/15 bg-zinc-800/90 px-5 py-2.5 text-sm font-semibold text-zinc-100 transition-transform active:[transform:scale3d(0.97,0.97,1)]"
            >
              My List
            </button>
            <Link
              href="/requests"
              prefetch={false}
              className="inline-flex cursor-pointer touch-manipulation items-center justify-center rounded-md border border-violet-500/40 bg-transparent px-5 py-2.5 text-sm font-semibold text-violet-300 transition-transform active:[transform:scale3d(0.97,0.97,1)]"
            >
              Request
            </Link>
          </div>
          <p className="mt-4 text-[10px] text-zinc-600">
            Request → future Jellyseerr / Cinema Concierge portal (placeholder link)
          </p>
        </div>
      </section>

      <div className="-mt-6 relative z-10">
        <CarouselRow title="Continue Watching">
          {CONTINUE_WATCHING.map((item) => (
            <ContinueCard key={item.id} item={item} />
          ))}
        </CarouselRow>

        <CarouselRow title="Your Playlists" actionLabel="Manage">
          {CUSTOM_FOLDERS.map((f) => (
            <FolderCard key={f.id} folder={f} />
          ))}
        </CarouselRow>

        <CarouselRow title="My List">
          {MY_LIST.map((m) => (
            <PosterCard key={m.id} movie={m} />
          ))}
        </CarouselRow>

        <CarouselRow title="Recently Added">
          {RECENTLY_ADDED.map((m) => (
            <PosterCard key={m.id} movie={m} />
          ))}
        </CarouselRow>

        <CarouselRow title="Trending Now">
          {CATEGORIES.trending.map((m) => (
            <PosterCard key={m.id} movie={m} />
          ))}
        </CarouselRow>

        <CarouselRow title="Sci-Fi">
          {CATEGORIES.sciFi.map((m) => (
            <PosterCard key={m.id} movie={m} />
          ))}
        </CarouselRow>

        <CarouselRow title="Action">
          {CATEGORIES.action.map((m) => (
            <PosterCard key={m.id} movie={m} />
          ))}
        </CarouselRow>

        <CarouselRow title="Drama">
          {CATEGORIES.drama.map((m) => (
            <PosterCard key={m.id} movie={m} />
          ))}
        </CarouselRow>
      </div>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function CinemaPage() {
  const [activeProfile, setActiveProfile] = useState<string | null>(null);

  const selectProfile = useCallback((id: string) => {
    setActiveProfile(id);
  }, []);

  const exitProfile = useCallback(() => {
    setActiveProfile(null);
  }, []);

  return (
    <>
      {activeProfile === null ? (
        <ProfileGate onSelect={selectProfile} />
      ) : (
        <CinemaMain activeProfileId={activeProfile} onExitProfile={exitProfile} />
      )}
    </>
  );
}
