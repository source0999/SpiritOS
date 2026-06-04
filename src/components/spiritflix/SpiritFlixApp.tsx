"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  clearStoredSession,
  getStoredSession,
  JellyfinClient,
  isPlayableItem,
  isPlaylistItem,
  normalizeJellyfinServerUrl,
  SPIRITFLIX_DEFAULT_SERVER,
  storeSession,
} from "@/lib/spiritflix/jellyfin-client";
import type {
  JellyfinItem,
  SpiritFlixHomeData,
  SpiritFlixServerInfo,
  SpiritFlixSession,
} from "@/lib/spiritflix/types";
import { SpiritFlixHome } from "./SpiritFlixHome";
import { SpiritFlixLogin } from "./SpiritFlixLogin";
import { SpiritFlixDetailsModal } from "./SpiritFlixDetailsModal";
import { SpiritFlixPlayer } from "./SpiritFlixPlayer";

const emptyHome: SpiritFlixHomeData = {
  libraries: [],
  playlists: [],
  selectedLibraryId: null,
  libraryItems: [],
  continueWatching: [],
  latestAdded: [],
  favorites: [],
};

const OTHER_LIBRARY_NAME = "Other";

export function SpiritFlixApp() {
  const [session, setSession] = useState<SpiritFlixSession | null>(null);
  const [isRestoringSession, setIsRestoringSession] = useState(true);
  const [serverUrl, setServerUrl] = useState(SPIRITFLIX_DEFAULT_SERVER);
  const [serverInfo, setServerInfo] = useState<SpiritFlixServerInfo | null>(null);
  const [serverError, setServerError] = useState("");
  const [homeData, setHomeData] = useState<SpiritFlixHomeData>(emptyHome);
  const [selectedItem, setSelectedItem] = useState<JellyfinItem | null>(null);
  const [playingItem, setPlayingItem] = useState<JellyfinItem | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [loadingHome, setLoadingHome] = useState(false);
  const [homeError, setHomeError] = useState("");

  const client = useMemo(
    () => new JellyfinClient(session?.serverUrl ?? serverUrl, session?.accessToken, session?.userId),
    [serverUrl, session],
  );

  const checkServer = useCallback(
    async (target = serverUrl) => {
      setServerError("");
      try {
        const info = await new JellyfinClient(target).checkPublicInfo();
        setServerInfo(info);
        setServerUrl(normalizeJellyfinServerUrl(target));
      } catch {
        setServerInfo(null);
        setServerError("SpiritFlix cannot reach that Jellyfin server from this browser right now.");
      }
    },
    [serverUrl],
  );

  const loadHome = useCallback(
    async (libraryId?: string | null, term = searchTerm) => {
      if (!session) return;
      setLoadingHome(true);
      setHomeError("");
      try {
        const libraries = await client.getLibraries();
        const otherLibrary = libraries.find((library) => library.Name.toLowerCase() === OTHER_LIBRARY_NAME.toLowerCase());
        const selectedLibraryId = libraryId ?? homeData.selectedLibraryId ?? otherLibrary?.Id ?? libraries[0]?.Id ?? null;
        const [libraryItems, continueWatching, latestAdded, favorites] = await Promise.all([
          selectedLibraryId ? client.getLibraryItems(selectedLibraryId, term) : Promise.resolve([]),
          client.getContinueWatching(),
          client.getLatestAdded(),
          client.getFavorites(),
        ]);
        setHomeData({
          libraries,
          playlists: [],
          selectedLibraryId,
          libraryItems,
          continueWatching,
          latestAdded,
          favorites,
        });
      } catch {
        setHomeError("Could not load your Jellyfin library. Log out and back in if the token expired.");
      } finally {
        setLoadingHome(false);
      }
    },
    [client, homeData.selectedLibraryId, searchTerm, session],
  );

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const stored = getStoredSession();
      if (stored) {
        setSession(stored);
        setServerUrl(stored.serverUrl);
      }
      setIsRestoringSession(false);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (isRestoringSession) return undefined;
    const timer = window.setTimeout(() => {
      void checkServer(serverUrl);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [checkServer, isRestoringSession, serverUrl]);

  useEffect(() => {
    if (!session) return undefined;
    const timer = window.setTimeout(() => {
      void loadHome(null);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadHome, session]);

  const handleLogin = async (username: string, password: string, targetServerUrl: string) => {
    const authClient = new JellyfinClient(targetServerUrl);
    const nextSession = await authClient.login(username, password);
    storeSession(nextSession);
    setSession(nextSession);
    setServerUrl(nextSession.serverUrl);
    await checkServer(nextSession.serverUrl);
  };

  const handleLogout = () => {
    clearStoredSession();
    setSession(null);
    setHomeData(emptyHome);
    setSelectedItem(null);
    setPlayingItem(null);
  };

  const shuffleItems = (items: JellyfinItem[]) => {
    return [...items].sort(() => Math.random() - 0.5);
  };

  const handlePlay = async (item: JellyfinItem) => {
    if (isPlayableItem(item)) {
      setPlayingItem(item);
      return;
    }

    if (isPlaylistItem(item)) {
      setLoadingHome(true);
      setHomeError("");
      try {
        const playlistItems = (await client.getPlaylistItems(item.Id)).filter(isPlayableItem);
        if (!playlistItems.length) {
          setHomeError(`Playlist "${item.Name}" has no playable video items.`);
          return;
        }
        setHomeData((current) => ({
          ...current,
          libraryItems: playlistItems,
          selectedLibraryId: current.selectedLibraryId,
        }));
        setPlayingItem(shuffleItems(playlistItems)[0]);
      } catch {
        setHomeError(`Could not load playlist "${item.Name}" from Jellyfin.`);
      } finally {
        setLoadingHome(false);
      }
    }
  };

  const handleOpenDetails = async (item: JellyfinItem) => {
    setSelectedItem(item);
    if (!isPlaylistItem(item)) return;

    setLoadingHome(true);
    setHomeError("");
    try {
      const playlistItems = (await client.getPlaylistItems(item.Id)).filter(isPlayableItem);
      setHomeData((current) => ({
        ...current,
        libraryItems: playlistItems,
      }));
      if (!playlistItems.length) {
        setHomeError(`Playlist "${item.Name}" has no playable video items.`);
      }
    } catch {
      setHomeError(`Could not load playlist "${item.Name}" from Jellyfin.`);
    } finally {
      setLoadingHome(false);
    }
  };

  const handleSearch = (term: string) => {
    setSearchTerm(term);
    void loadHome(homeData.selectedLibraryId, term);
  };

  return (
    <main className="spiritflix-shell">
      {isRestoringSession ? (
        <section className="spiritflix-restore">
          <div className="spiritflix-brand">
            <span className="spiritflix-brand__sigil">SF</span>
            <span>SpiritFlix</span>
          </div>
        </section>
      ) : !session ? (
        <SpiritFlixLogin
          serverUrl={serverUrl}
          serverInfo={serverInfo}
          serverError={serverError}
          onServerUrlChange={setServerUrl}
          onRetry={() => checkServer(serverUrl)}
          onLogin={handleLogin}
        />
      ) : (
        <SpiritFlixHome
          client={client}
          data={homeData}
          loading={loadingHome}
          error={homeError}
          session={session}
          searchTerm={searchTerm}
          serverInfo={serverInfo}
          onLogout={handleLogout}
          onRefresh={() => loadHome(homeData.selectedLibraryId)}
          onSearch={handleSearch}
          onOpenDetails={handleOpenDetails}
          onPlay={handlePlay}
        />
      )}

      {selectedItem ? (
        <SpiritFlixDetailsModal
          client={client}
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
          onPlay={(item) => {
            setSelectedItem(null);
            void handlePlay(item);
          }}
        />
      ) : null}

      {playingItem ? (
        <SpiritFlixPlayer client={client} item={playingItem} onClose={() => setPlayingItem(null)} />
      ) : null}
    </main>
  );
}
