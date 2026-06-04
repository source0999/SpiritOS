"use client";

import { LogOut, RefreshCw, Search } from "lucide-react";
import type { JellyfinClient } from "@/lib/spiritflix/jellyfin-client";
import type {
  JellyfinItem,
  SpiritFlixHomeData,
  SpiritFlixServerInfo,
  SpiritFlixSession,
} from "@/lib/spiritflix/types";
import { SpiritFlixRail } from "./SpiritFlixRail";
import { SpiritFlixImage } from "./SpiritFlixImage";

interface SpiritFlixHomeProps {
  client: JellyfinClient;
  data: SpiritFlixHomeData;
  loading: boolean;
  error: string;
  session: SpiritFlixSession;
  searchTerm: string;
  serverInfo: SpiritFlixServerInfo | null;
  onLogout: () => void;
  onRefresh: () => void;
  onSearch: (term: string) => void;
  onOpenDetails: (item: JellyfinItem) => void;
  onPlay: (item: JellyfinItem) => void;
}

export function SpiritFlixHome({
  client,
  data,
  loading,
  error,
  session,
  searchTerm,
  serverInfo,
  onLogout,
  onRefresh,
  onSearch,
  onOpenDetails,
  onPlay,
}: SpiritFlixHomeProps) {
  const hero = data.libraryItems[0] ?? null;
  const selectedLibrary = data.libraries.find((library) => library.Id === data.selectedLibraryId);
  const libraryTitle = selectedLibrary?.Name ?? "Other";

  return (
    <section className="spiritflix-home">
      <header className="spiritflix-topbar">
        <div className="spiritflix-brand spiritflix-brand--compact">
          <span className="spiritflix-brand__sigil">SF</span>
          <span>SpiritFlix</span>
        </div>
        <div className="spiritflix-search">
          <Search size={17} aria-hidden="true" />
          <input
            value={searchTerm}
            onChange={(event) => onSearch(event.target.value)}
            placeholder="Search your Jellyfin library"
          />
        </div>
        <button className="spiritflix-icon-button" type="button" onClick={onRefresh} aria-label="Refresh library">
          <RefreshCw size={18} aria-hidden="true" />
        </button>
        <button className="spiritflix-logout" type="button" onClick={onLogout}>
          <LogOut size={17} aria-hidden="true" />
          <span>{session.username}</span>
        </button>
      </header>

      <section className="spiritflix-hero">
        {hero ? (
          <SpiritFlixImage client={client} item={hero} type="Backdrop" width={1600} className="spiritflix-hero__image" />
        ) : null}
        <div className="spiritflix-hero__shade" />
        <div className="spiritflix-hero__content">
          <span className="spiritflix-kicker">
            {serverInfo?.ServerName ? `${serverInfo.ServerName} / ${libraryTitle}` : libraryTitle}
          </span>
          <h1>{hero?.Name ?? "Your cinema is waiting"}</h1>
          <p>{hero?.Overview || "Sign in, choose a library, and stream from your real Jellyfin server."}</p>
          <div className="spiritflix-hero__actions">
            {hero ? (
              <>
                <button className="spiritflix-primary-button" type="button" onClick={() => onPlay(hero)}>
                  Play
                </button>
                <button className="spiritflix-secondary-button" type="button" onClick={() => onOpenDetails(hero)}>
                  Details
                </button>
              </>
            ) : null}
          </div>
        </div>
      </section>

      {error ? <p className="spiritflix-error spiritflix-error--home">{error}</p> : null}
      {loading ? <div className="spiritflix-loading">Loading Jellyfin rows...</div> : null}

      <div className="spiritflix-rows">
        <SpiritFlixRail
          title={libraryTitle}
          client={client}
          items={data.libraryItems}
          onOpenDetails={onOpenDetails}
          onPlay={onPlay}
          emptyText={`${libraryTitle} has no playable videos yet.`}
        />
      </div>
    </section>
  );
}
