"use client";

import "@/styles/spiritflix.css";
import { useCallback, useEffect, useMemo, useState } from "react";
import { flushSync } from "react-dom";
import { Folder, HardDrive, Info, RefreshCw } from "lucide-react";
import { getStoredSession, JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem, SpiritFlixSession } from "@/lib/spiritflix-types";
import { activeAdminNavPath, SPIRITFLIX_ADMIN_NAV, SPIRITFLIX_MEDIA_ROOT } from "@/lib/spiritflix/admin/constants";
import { isMetadataSidecar } from "@/lib/spiritflix/admin/format";
import { matchJellyfinItemForAdminFile } from "@/lib/spiritflix/admin/jellyfin-match";
import type {
  SpiritFlixAdminFsResponse,
  SpiritFlixAdminItem,
  SpiritFlixAdminActionName,
  SpiritFlixAdminSortBy,
  SpiritFlixAdminSortOrder,
} from "@/lib/spiritflix/admin/types";
import { SpiritFlixAdminToolbar, type SpiritFlixAdminViewMode } from "./SpiritFlixAdminToolbar";
import { SpiritFlixAdminExplorer } from "./SpiritFlixAdminExplorer";
import { SpiritFlixAdminDetailsPanel } from "./SpiritFlixAdminDetailsPanel";
import { SpiritFlixAdminActionDialog } from "./SpiritFlixAdminActionDialog";
import { SpiritFlixSmartReviewPanel } from "./SpiritFlixSmartReviewPanel";
import { buildAdminBreadcrumbSegments } from "./SpiritFlixAdminBreadcrumbs";
import { menuActionToDialogAction, type SpiritFlixAdminMenuActionId } from "./item-menu";
import { useAdminScrollRestore } from "./useAdminScrollRestore";

const VIDEO_EXTENSIONS = new Set([".avi", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".webm", ".wmv"]);

export function SpiritFlixAdminApp() {
  const [session, setSession] = useState<SpiritFlixSession | null>(null);
  const [items, setItems] = useState<SpiritFlixAdminItem[]>([]);
  const [jellyfinItems, setJellyfinItems] = useState<JellyfinItem[]>([]);
  const [currentPath, setCurrentPath] = useState(SPIRITFLIX_MEDIA_ROOT);
  const [includeMetadataFiles, setIncludeMetadataFiles] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState<SpiritFlixAdminSortBy>("title");
  const [sortOrder, setSortOrder] = useState<SpiritFlixAdminSortOrder>("asc");
  const [viewMode, setViewMode] = useState<SpiritFlixAdminViewMode>("grid");
  const [selectedItem, setSelectedItem] = useState<SpiritFlixAdminItem | null>(null);
  const [detailsItem, setDetailsItem] = useState<SpiritFlixAdminItem | null>(null);
  const [actionDialog, setActionDialog] = useState<{
    open: boolean;
    item: SpiritFlixAdminItem | null;
    initialAction?: SpiritFlixAdminActionName;
  }>({ open: false, item: null });
  const [status, setStatus] = useState("Loading media folders");
  const [thumbnailStatus, setThumbnailStatus] = useState("Loading Jellyfin metadata index");
  const [serverImageProxy, setServerImageProxy] = useState(false);
  const [showJellyfinDebug, setShowJellyfinDebug] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [actionToast, setActionToast] = useState<string | null>(null);
  const [smartReviewItem, setSmartReviewItem] = useState<SpiritFlixAdminItem | null>(null);

  useEffect(() => {
    setSession(getStoredSession());
  }, []);

  const jellyfinClient = useMemo(() => (session ? new JellyfinClient(session.serverUrl, session.accessToken, session.userId) : undefined), [session]);

  const loadJellyfinIndex = useCallback(async () => {
    try {
      const serverResponse = await fetch("/api/spiritflix/admin/jellyfin-index", {
        method: "GET",
        cache: "no-store",
        headers: { Accept: "application/json" },
      });

      if (serverResponse.ok) {
        const serverPayload = (await serverResponse.json()) as { items?: JellyfinItem[]; source?: string };
        if (serverPayload.items?.length) {
          setJellyfinItems(serverPayload.items);
          setServerImageProxy(true);
          setThumbnailStatus(`${serverPayload.items.length} Jellyfin metadata matches available`);
          return;
        }
      }
    } catch {
      // Background enrichment only — filesystem view stays primary.
    }

    setServerImageProxy(false);

    if (!session) {
      setJellyfinItems([]);
      setThumbnailStatus("Jellyfin metadata unavailable; local video previews enabled");
      return;
    }

    try {
      const response = await fetch("/api/spiritflix/admin/library", {
        method: "POST",
        cache: "no-store",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          serverUrl: session.serverUrl,
          accessToken: session.accessToken,
          userId: session.userId,
          recursive: true,
          sortBy: "title",
          sortOrder: "asc",
          limit: 500,
          includeItemTypes: "Movie,Episode,Video",
        }),
      });

      if (!response.ok) throw new Error("Jellyfin metadata index unavailable.");
      const payload = (await response.json()) as { items: Array<{ jellyfinItem?: JellyfinItem }> };
      const indexedItems = payload.items.map((item) => item.jellyfinItem).filter(Boolean) as JellyfinItem[];
      setJellyfinItems(indexedItems);
      setThumbnailStatus(indexedItems.length ? `${indexedItems.length} Jellyfin metadata matches` : "No Jellyfin metadata matches; local previews enabled");
    } catch {
      setJellyfinItems([]);
      setThumbnailStatus("Jellyfin metadata unavailable; local video previews enabled");
    }
  }, [session]);

  useEffect(() => {
    void loadJellyfinIndex();
  }, [loadJellyfinIndex]);

  const loadFilesystem = useCallback(
    async (path: string) => {
      setLoading(true);
      setError("");
      try {
        const query = new URLSearchParams({
          path,
          sortBy,
          sortOrder,
          limit: "250",
        });
        const response = await fetch(`/api/spiritflix/admin/fs?${query.toString()}`, {
          method: "GET",
          cache: "no-store",
          headers: {
            Accept: "application/json",
          },
        });

        if (!response.ok) {
          const failure = (await response.json().catch(() => ({}))) as { error?: string };
          throw new Error(failure.error ?? "SpiritFlix folder listing is unavailable.");
        }

        const payload = (await response.json()) as SpiritFlixAdminFsResponse;
        setItems(payload.items);
        setCurrentPath(payload.currentPath);
        setStatus(`${payload.items.length} of ${payload.totalRecordCount} files and folders`);
      } catch (caught) {
        const message = caught instanceof Error ? caught.message : "SpiritFlix filesystem listing failed.";
        const onHttp = typeof window !== "undefined" && window.location.protocol === "http:";
        setError(
          onHttp
            ? `SpiritFlix folder listing failed over HTTP. Use HTTPS: https://${window.location.host}/spiritflix/admin`
            : message,
        );
        setItems([]);
      } finally {
        setLoading(false);
      }
    },
    [sortBy, sortOrder],
  );

  const refresh = useCallback(() => {
    void loadFilesystem(currentPath);
  }, [currentPath, loadFilesystem]);

  useEffect(() => {
    void loadFilesystem(currentPath);
  }, [currentPath, sortBy, sortOrder, loadFilesystem]);

  const navigateFilesystem = useCallback((path: string) => {
    setCurrentPath(path);
  }, []);

  const enrichedItems = useMemo(() => {
    return items.map((item) => {
      if (item.type === "folder" || !item.playable) return item;
      const match = matchJellyfinItemForAdminFile(item.path, jellyfinItems);
      return {
        ...item,
        jellyfinId: match.itemId,
        jellyfinItemId: match.itemId,
        jellyfinItem: match.item,
        imageType: match.imageType,
        imageStatus: match.imageStatus,
        jellyfinMatchedBy: match.matchedBy,
        jellyfinMatchCandidateCount: match.candidateCount,
        hasImage: match.imageStatus === "available",
        dateAdded: match.item?.DateCreated ?? item.dateAdded,
      };
    });
  }, [items, jellyfinItems]);

  const displayedItems = useMemo(() => {
    const search = searchTerm.trim().toLowerCase();
    const filtered = enrichedItems.filter((item) => {
      const extension = item.extension?.toLowerCase() ?? "";
      const isMetadata = isMetadataSidecar(item.name);
      const isVideo = item.type === "folder" || item.playable || VIDEO_EXTENSIONS.has(extension);

      if (!isVideo && !(includeMetadataFiles && isMetadata)) return false;
      if (isMetadata && !includeMetadataFiles) return false;
      if (!search) return true;

      const jellyfinTitle = item.jellyfinItem?.Name;
      return [item.name, jellyfinTitle, item.path, item.parentPath, item.extension, item.libraryName, item.itemType, item.mediaType, item.modelNames?.join(" ")]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(search));
    });

    return filtered;
  }, [enrichedItems, includeMetadataFiles, searchTerm]);

  const { scrollRef, saveScroll, requestRestore } = useAdminScrollRestore(`${currentPath}:${displayedItems.length}:${loading}`);

  const copyText = useCallback((value?: string) => {
    if (!value || typeof navigator === "undefined") return;
    void navigator.clipboard?.writeText(value);
  }, []);

  const openActionDialog = useCallback(
    (item: SpiritFlixAdminItem | null, initialAction?: SpiritFlixAdminActionName) => {
      saveScroll();
      flushSync(() => {
        setActionDialog({ open: true, item, initialAction });
      });
    },
    [saveScroll],
  );

  const openManageDialog = useCallback(() => {
    saveScroll();
    setActionDialog({ open: true, item: selectedItem, initialAction: undefined });
  }, [saveScroll, selectedItem]);

  const closeActionDialog = useCallback(() => {
    setActionDialog({ open: false, item: null });
    requestRestore();
  }, [requestRestore]);

  const openDetails = useCallback(
    (item: SpiritFlixAdminItem) => {
      saveScroll();
      setDetailsItem(item);
    },
    [saveScroll],
  );

  const closeDetails = useCallback(() => {
    setDetailsItem(null);
    requestRestore();
  }, [requestRestore]);

  const openSmartReview = useCallback(
    (item: SpiritFlixAdminItem) => {
      saveScroll();
      setSmartReviewItem(item);
    },
    [saveScroll],
  );

  const closeSmartReview = useCallback(() => {
    setSmartReviewItem(null);
    requestRestore();
  }, [requestRestore]);

  const handleMenuAction = useCallback(
    (actionId: SpiritFlixAdminMenuActionId, item: SpiritFlixAdminItem | null) => {
      if (item) setSelectedItem(item);

      switch (actionId) {
        case "openFolder":
          if (item?.path) navigateFilesystem(item.path);
          break;
        case "openViewer":
          if (item?.jellyfinItemId || item?.jellyfinId) {
            window.location.assign(`/spiritflix?item=${encodeURIComponent(item.jellyfinItemId ?? item.jellyfinId ?? "")}`);
          }
          break;
        case "info":
          if (item) openDetails(item);
          break;
        case "smartTags":
          if (item) openSmartReview(item);
          break;
        case "copyPath":
          copyText(item?.path);
          break;
        case "copyFilename":
        case "copyFolderName":
          copyText(item?.name);
          break;
        case "refresh":
          saveScroll();
          requestRestore();
          refresh();
          break;
        case "newFolder":
          openActionDialog(item, "createFolder");
          break;
        case "softDelete":
          if (item) openActionDialog(item, "softDelete");
          break;
        case "restore":
          if (item) openActionDialog(item, "restore");
          break;
        case "rename":
          if (item) openActionDialog(item, "rename");
          break;
        case "move":
          if (item) openActionDialog(item, "move");
          break;
        case "editMetadata":
          if (item) openActionDialog(item, "writeMetadata");
          break;
        default: {
          const dialogAction = menuActionToDialogAction(actionId);
          if (dialogAction) openActionDialog(item, dialogAction);
        }
      }
    },
    [copyText, navigateFilesystem, openActionDialog, openDetails, openSmartReview, refresh, requestRestore, saveScroll],
  );

  const handleActionComplete = useCallback((message: string) => {
    saveScroll();
    requestRestore();
    setSelectedItem(null);
    setActionToast(message);
    refresh();
  }, [refresh, requestRestore, saveScroll]);

  useEffect(() => {
    if (!actionToast) return;
    const timer = window.setTimeout(() => setActionToast(null), 8000);
    return () => window.clearTimeout(timer);
  }, [actionToast]);

  const selectedCount = useMemo(() => (selectedItem ? 1 : 0), [selectedItem]);
  const activeNav = activeAdminNavPath(currentPath);
  const breadcrumbTail = buildAdminBreadcrumbSegments(currentPath).map((crumb) => crumb.name).join(" > ");

  return (
    <main className="spiritflix-shell spiritflix-admin-shell">
      <aside className="spiritflix-admin-sidebar" aria-label="SpiritFlix files navigation">
        <div className="spiritflix-brand">
          <span className="spiritflix-brand__sigil">SF</span>
          <span>SpiritFlix Files</span>
        </div>
        <nav className="spiritflix-admin-nav">
          <button className="is-active" type="button" aria-current="page">
            <HardDrive size={18} aria-hidden="true" />
            Media
          </button>
        </nav>
        <div className="spiritflix-admin-root-list" aria-label="Media folders">
          {SPIRITFLIX_ADMIN_NAV.map((entry) => (
            <button
              className={activeNav === entry.path ? "is-active" : ""}
              key={entry.path}
              type="button"
              onClick={() => navigateFilesystem(entry.path)}
            >
              <Folder size={15} aria-hidden="true" />
              {entry.label}
            </button>
          ))}
        </div>
        <div className="spiritflix-admin-sidebar-footer">
          <button className="spiritflix-admin-debug-toggle" type="button" onClick={() => setShowJellyfinDebug((value) => !value)}>
            <Info size={15} aria-hidden="true" />
            Jellyfin metadata
          </button>
          {showJellyfinDebug ? <p className="spiritflix-admin-debug-status">{thumbnailStatus}</p> : null}
        </div>
      </aside>

      <section className="spiritflix-admin-workspace">
        <SpiritFlixAdminToolbar
          includeMetadataFiles={includeMetadataFiles}
          loading={loading}
          searchTerm={searchTerm}
          sortBy={sortBy}
          sortOrder={sortOrder}
          viewMode={viewMode}
          onIncludeMetadataFilesChange={setIncludeMetadataFiles}
          onManage={openManageDialog}
          onRefresh={refresh}
          onSearchTermChange={setSearchTerm}
          onSortByChange={setSortBy}
          onSortOrderChange={setSortOrder}
          onViewModeChange={setViewMode}
        />
        {error ? <p className="spiritflix-admin-error">{error}</p> : null}
        {actionToast ? (
          <p className="spiritflix-admin-toast" role="status">
            {actionToast}
          </p>
        ) : null}
        <SpiritFlixAdminExplorer
          currentPath={currentPath}
          items={displayedItems}
          jellyfinClient={jellyfinClient}
          loading={loading}
          selectedItem={selectedItem}
          serverImageProxy={serverImageProxy}
          viewMode={viewMode}
          scrollRef={scrollRef}
          onBrowsePath={navigateFilesystem}
          onSelectItem={setSelectedItem}
          onMenuAction={handleMenuAction}
        />
        <footer className="spiritflix-admin-status">
          <span>{displayedItems.length} shown · {status}</span>
          <span>{selectedCount} selected</span>
          <span>{breadcrumbTail}</span>
          <span>{thumbnailStatus}</span>
          <button type="button" onClick={refresh} aria-label="Refresh file listing">
            <RefreshCw size={16} aria-hidden="true" />
          </button>
        </footer>
      </section>

      {detailsItem ? (
        <SpiritFlixAdminDetailsPanel
          item={detailsItem}
          jellyfinClient={jellyfinClient}
          serverImageProxy={serverImageProxy}
          onClose={closeDetails}
          onBrowsePath={navigateFilesystem}
        />
      ) : null}

      {actionDialog.open ? (
        <SpiritFlixAdminActionDialog
          key={`action-${actionDialog.item?.id ?? "folder"}-${actionDialog.initialAction ?? "manage"}`}
          item={actionDialog.item ?? selectedItem}
          currentPath={currentPath}
          initialAction={actionDialog.initialAction}
          onClose={closeActionDialog}
          onComplete={handleActionComplete}
        />
      ) : null}

      {smartReviewItem ? (
        <SpiritFlixSmartReviewPanel item={smartReviewItem} open onClose={closeSmartReview} />
      ) : null}
    </main>
  );
}
