import { afterEach, describe, expect, it, vi } from "vitest";
import { JellyfinClient, isPlayableItem, isSpiritFlixTrashPath, isVisibleSpiritFlixItem } from "./spiritflix-jellyfin-client";

const originalViewport = {
  devicePixelRatio: window.devicePixelRatio,
  innerHeight: window.innerHeight,
  innerWidth: window.innerWidth,
};

function setViewport(width: number, height: number, devicePixelRatio: number) {
  Object.defineProperty(window, "innerWidth", { configurable: true, writable: true, value: width });
  Object.defineProperty(window, "innerHeight", { configurable: true, writable: true, value: height });
  Object.defineProperty(window, "devicePixelRatio", { configurable: true, writable: true, value: devicePixelRatio });
}

describe("JellyfinClient playback URLs", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    setViewport(originalViewport.innerWidth, originalViewport.innerHeight, originalViewport.devicePixelRatio);
  });

  it("uses same-origin stream and HLS proxies on HTTPS pages", () => {
    vi.spyOn(window, "location", "get").mockReturnValue({
      ...window.location,
      protocol: "https:",
      hostname: "100.111.32.31",
      href: "https://100.111.32.31:3000/spiritflix",
    } as Location);
    const client = new JellyfinClient("http://spirit.tailb69ea6.ts.net:8096", "token-1", "user-1");

    const streamUrl = new URL(client.getStreamUrl("item-1"), "https://100.111.32.31:3000/spiritflix");
    expect(streamUrl.pathname).toBe("/api/spiritflix/stream");
    expect(streamUrl.searchParams.get("serverUrl")).toBe("http://100.111.32.31:8096");
    expect(streamUrl.searchParams.get("itemId")).toBe("item-1");
    expect(streamUrl.searchParams.get("token")).toBe("token-1");
    expect(streamUrl.searchParams.get("audioStreamIndex")).toBe(null);

    const hlsUrl = new URL(client.getHlsUrl("item-1"), "https://100.111.32.31:3000/spiritflix");
    expect(hlsUrl.pathname).toBe("/api/spiritflix/hls");
    expect(hlsUrl.searchParams.get("serverUrl")).toBe("http://100.111.32.31:8096");
    expect(hlsUrl.searchParams.get("token")).toBe("token-1");
    expect(hlsUrl.searchParams.get("path")).toContain("/Videos/item-1/master.m3u8");
    expect(hlsUrl.searchParams.get("path")).toContain("VideoBitrate=4000000");
  });

  it("passes requested audio stream index through playback URLs", () => {
    vi.spyOn(window, "location", "get").mockReturnValue({
      ...window.location,
      protocol: "https:",
      hostname: "10.0.0.186",
      href: "https://10.0.0.186:3000/spiritflix",
    } as Location);
    const client = new JellyfinClient("http://spirit.tailb69ea6.ts.net:8096", "token-1", "user-1");

    const streamUrl = new URL(client.getStreamUrl("item-1", { audioStreamIndex: 2 }), "https://10.0.0.186:3000/spiritflix");
    const hlsUrl = new URL(client.getHlsUrl("item-1", { audioStreamIndex: 2 }), "https://10.0.0.186:3000/spiritflix");

    expect(streamUrl.searchParams.get("audioStreamIndex")).toBe("2");
    expect(hlsUrl.searchParams.get("path")).toContain("AudioStreamIndex=2");
  });

  it("requests a higher HLS profile on unfolded high-density screens", () => {
    setViewport(842, 1030, 2.6);
    vi.spyOn(window, "location", "get").mockReturnValue({
      ...window.location,
      protocol: "https:",
      hostname: "100.111.32.31",
      href: "https://100.111.32.31:3000/spiritflix",
    } as Location);
    const client = new JellyfinClient("http://spirit.tailb69ea6.ts.net:8096", "token-1", "user-1");

    const hlsUrl = new URL(client.getHlsUrl("item-1"), "https://100.111.32.31:3000/spiritflix");
    const path = hlsUrl.searchParams.get("path");

    expect(path).toContain("VideoBitrate=10000000");
    expect(path).toContain("AudioBitrate=256000");
    expect(path).toContain("MaxWidth=1920");
    expect(path).toContain("MaxHeight=1080");
  });

  it("keeps narrow high-density phone screens on the baseline HLS profile", () => {
    setViewport(360, 800, 3);
    vi.spyOn(window, "location", "get").mockReturnValue({
      ...window.location,
      protocol: "https:",
      hostname: "100.111.32.31",
      href: "https://100.111.32.31:3000/spiritflix",
    } as Location);
    const client = new JellyfinClient("http://spirit.tailb69ea6.ts.net:8096", "token-1", "user-1");

    const hlsUrl = new URL(client.getHlsUrl("item-1"), "https://100.111.32.31:3000/spiritflix");
    const path = hlsUrl.searchParams.get("path");

    expect(path).toContain("VideoBitrate=4000000");
    expect(path).toContain("MaxWidth=1280");
    expect(path).toContain("MaxHeight=720");
  });

  it("keeps direct Jellyfin URLs on HTTP pages", () => {
    vi.spyOn(window, "location", "get").mockReturnValue({
      ...window.location,
      protocol: "http:",
      hostname: "100.111.32.31",
      href: "http://100.111.32.31:3000/spiritflix",
    } as Location);
    const client = new JellyfinClient("http://spirit.tailb69ea6.ts.net:8096", "token-1", "user-1");

    expect(client.getStreamUrl("item-1")).toContain("http://100.111.32.31:8096/Videos/item-1/Stream");
    expect(client.getHlsUrl("item-1")).toContain("http://100.111.32.31:8096/Videos/item-1/master.m3u8");
  });

  it("uses the LAN Jellyfin host when the app is opened from the LAN address", () => {
    vi.spyOn(window, "location", "get").mockReturnValue({
      ...window.location,
      protocol: "https:",
      hostname: "10.0.0.186",
      href: "https://10.0.0.186:3000/spiritflix",
    } as Location);
    const client = new JellyfinClient("http://spirit.tailb69ea6.ts.net:8096", "token-1", "user-1");

    const streamUrl = new URL(client.getStreamUrl("item-1"), "https://10.0.0.186:3000/spiritflix");
    const hlsUrl = new URL(client.getHlsUrl("item-1"), "https://10.0.0.186:3000/spiritflix");

    expect(streamUrl.searchParams.get("serverUrl")).toBe("http://10.0.0.186:8096");
    expect(hlsUrl.searchParams.get("serverUrl")).toBe("http://10.0.0.186:8096");
  });
});

describe("SpiritFlix trash filtering", () => {
  it("recognizes SpiritFlix trash paths across path separators", () => {
    expect(isSpiritFlixTrashPath("/mnt/spirit-8tb/media/.trash/20260621/yes/clip.mp4")).toBe(true);
    expect(isSpiritFlixTrashPath("Z:\\media\\.trash\\20260621\\yes\\clip.mp4")).toBe(true);
    expect(isSpiritFlixTrashPath("/mnt/spirit-8tb/media/yes/models/clip.mp4")).toBe(false);
  });

  it("treats trashed Jellyfin items as hidden and not playable", () => {
    const trashed = {
      Id: "trash-1",
      Name: "Trashed",
      Type: "Video",
      MediaType: "Video",
      Path: "/mnt/spirit-8tb/media/.trash/20260621/yes/Trashed.mp4",
    };
    const active = {
      Id: "active-1",
      Name: "Active",
      Type: "Video",
      MediaType: "Video",
      Path: "/mnt/spirit-8tb/media/yes/Active.mp4",
    };

    expect(isVisibleSpiritFlixItem(trashed)).toBe(false);
    expect(isPlayableItem(trashed)).toBe(false);
    expect(isVisibleSpiritFlixItem(active)).toBe(true);
    expect(isPlayableItem(active)).toBe(true);
  });
});

describe("JellyfinClient paged card queries", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("times out stalled proxied Jellyfin requests instead of leaving the loader pending", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: string, init?: RequestInit) =>
        new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
        }),
      ),
    );
    const client = new JellyfinClient("http://spirit.tailb69ea6.ts.net:8096", "token-1", "user-1");

    const request = client.getLibraries();
    const expectation = expect(request).rejects.toThrow("Jellyfin request timed out while loading library data.");
    await vi.advanceTimersByTimeAsync(10000);

    await expectation;
  });

  it("requests a compact bounded page for the mobile library load", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({
        Items: [{ Id: "item-1", Name: "Scene 1", Type: "Video", MediaType: "Video" }],
        TotalRecordCount: 99,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new JellyfinClient("http://spirit.tailb69ea6.ts.net:8096", "token-1", "user-1");

    const page = await client.getLibraryItemsPage("library-1", {
      searchTerm: "fold",
      limit: 24,
      startIndex: 48,
    });

    const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string) as { path: string };
    const path = new URL(`http://jellyfin.local${body.path}`);
    expect(path.searchParams.get("Limit")).toBe("24");
    expect(path.searchParams.get("StartIndex")).toBe("48");
    expect(path.searchParams.get("SearchTerm")).toBe("fold");
    expect(path.searchParams.get("Fields")).not.toContain("Overview");
    expect(page.items).toHaveLength(1);
    expect(page.totalRecordCount).toBe(99);
    expect(page.hasMore).toBe(true);
  });

  it("pages Favorites instead of requesting the whole favorite set on mobile first load", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({
        Items: [{ Id: "fav-1", Name: "Favorite 1", Type: "Video", MediaType: "Video" }],
        TotalRecordCount: 42,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new JellyfinClient("http://spirit.tailb69ea6.ts.net:8096", "token-1", "user-1");

    const page = await client.getFavoritesPage({ limit: 10 });

    const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string) as { path: string };
    const path = new URL(`http://jellyfin.local${body.path}`);
    expect(path.searchParams.get("Filters")).toBe("IsFavorite");
    expect(path.searchParams.get("Limit")).toBe("10");
    expect(path.searchParams.get("StartIndex")).toBe("0");
    expect(page.hasMore).toBe(true);
  });

  it("pages Continue Watching with compact card fields", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({
        Items: [{ Id: "resume-1", Name: "Resume 1", Type: "Video", MediaType: "Video" }],
        TotalRecordCount: 31,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new JellyfinClient("http://spirit.tailb69ea6.ts.net:8096", "token-1", "user-1");

    const page = await client.getContinueWatchingPage("library-1", {
      limit: 10,
      startIndex: 20,
    });

    const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string) as { path: string };
    const path = new URL(`http://jellyfin.local${body.path}`);
    expect(path.pathname).toBe("/Users/user-1/Items/Resume");
    expect(path.searchParams.get("ParentId")).toBe("library-1");
    expect(path.searchParams.get("Limit")).toBe("10");
    expect(path.searchParams.get("StartIndex")).toBe("20");
    expect(path.searchParams.get("Fields")).not.toContain("Overview");
    expect(page.items).toHaveLength(1);
    expect(page.hasMore).toBe(true);
  });

  it("pages watch history by playback activity instead of fully played state only", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({
        Items: [{ Id: "history-1", Name: "History 1", Type: "Video", MediaType: "Video" }],
        TotalRecordCount: 42,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new JellyfinClient("http://spirit.tailb69ea6.ts.net:8096", "token-1", "user-1");

    const page = await client.getWatchHistoryPage("library-1", {
      limit: 10,
      startIndex: 20,
    });

    const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string) as { path: string };
    const path = new URL(`http://jellyfin.local${body.path}`);
    expect(path.pathname).toBe("/Users/user-1/Items");
    expect(path.searchParams.get("ParentId")).toBe("library-1");
    expect(path.searchParams.get("Filters")).toBeNull();
    expect(path.searchParams.get("SortBy")).toBe("DatePlayed");
    expect(path.searchParams.get("SortOrder")).toBe("Descending");
    expect(path.searchParams.get("Limit")).toBe("10");
    expect(path.searchParams.get("StartIndex")).toBe("20");
    expect(page.items).toHaveLength(1);
    expect(page.hasMore).toBe(true);
  });

  it("keeps the Home Videos shell visible so the navbar can label it Library", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        Response.json({
          Items: [
            {
              Id: "shell-fixture-id",
              Name: "Home Videos and Photos",
              Type: "MediaBrowser.Controller.Entities.CollectionFolder",
              Path: "/config/root/default/Home Videos and Photos",
            },
          ],
        }),
      )
      .mockResolvedValueOnce(
        Response.json({
          Items: [
            {
              Id: "yes-folder",
              Name: "yes",
              Type: "Folder",
              Path: "/media/yes",
            },
          ],
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    const client = new JellyfinClient("http://spirit.tailb69ea6.ts.net:8096", "token-1", "user-1");

    const libraries = await client.getLibraries();

    expect(libraries.map((library) => library.Id)).toEqual(["shell-fixture-id", "yes-folder"]);
    const folderCallBody = JSON.parse(fetchMock.mock.calls[1][1]?.body as string) as { path: string };
    const folderPath = new URL(`http://jellyfin.local${folderCallBody.path}`);
    expect(folderPath.pathname).toBe("/Users/user-1/Items");
    expect(folderPath.searchParams.get("Recursive")).toBe("false");
    expect(folderPath.searchParams.get("IncludeItemTypes")).toBe("Folder");
  });

  it("keeps the Home Videos shell when Jellyfin exposes it without real folders", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        Response.json({
          Items: [
            {
              Id: "shell-1",
              Name: "Home Videos and Photos",
              Type: "MediaBrowser.Controller.Entities.CollectionFolder",
              Path: "/config/root/default/Home Videos and Photos",
            },
          ],
        }),
      )
      .mockResolvedValueOnce(Response.json({ Items: [] }));
    vi.stubGlobal("fetch", fetchMock);
    const client = new JellyfinClient("http://spirit.tailb69ea6.ts.net:8096", "token-1", "user-1");

    const libraries = await client.getLibraries();

    expect(libraries.map((library) => library.Id)).toEqual(["shell-1"]);
  });
});
