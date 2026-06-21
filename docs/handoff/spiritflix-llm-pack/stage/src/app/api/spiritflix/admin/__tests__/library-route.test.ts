import { afterEach, describe, expect, it, vi } from "vitest";
import { POST } from "../library/route";

describe("SpiritFlix admin library API", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("returns stable normalized Jellyfin item records", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (url.includes("/Views")) {
        return Response.json({
          Items: [{ Id: "library-1", Name: "Movies", CollectionType: "movies" }],
        });
      }
      return Response.json({
        TotalRecordCount: 1,
        Items: [
          {
            Id: "item-1",
            Name: "Admin Clip",
            Type: "Video",
            MediaType: "Video",
            Path: "/mnt/spirit-8tb/media/movies/Admin Clip.mp4",
            DateCreated: "2026-06-16T12:00:00.000Z",
            RunTimeTicks: 1200000000,
            ImageTags: { Primary: "tag" },
            UserData: {
              IsFavorite: true,
              Played: false,
              PlaybackPositionTicks: 10000000,
            },
            MediaSources: [
              {
                Path: "/mnt/spirit-8tb/media/movies/Admin Clip.mp4",
                Size: 1024,
                RunTimeTicks: 1200000000,
              },
            ],
          },
        ],
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    const response = await POST(
      new Request("http://localhost/api/spiritflix/admin/library", {
        method: "POST",
        body: JSON.stringify({
          serverUrl: "http://127.0.0.1:8096",
          accessToken: "token",
          userId: "user-1",
          searchTerm: "Admin",
          sortBy: "dateAdded",
          sortOrder: "desc",
        }),
      }) as never,
    );
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.schema).toBe("spiritflix-admin-library/v1");
    expect(body.items[0]).toEqual(
      expect.objectContaining({
        id: "jellyfin:item-1",
        name: "Admin Clip",
        type: "jellyfin-item",
        jellyfinId: "item-1",
        jellyfinItemId: "item-1",
        imageType: "Primary",
        imageStatus: "available",
        extension: ".mp4",
        playable: true,
        favorite: true,
      }),
    );
    expect(body.items[0].jellyfinItem).toEqual(expect.objectContaining({ Id: "item-1", ImageTags: { Primary: "tag" } }));
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("SearchTerm=Admin"), expect.any(Object));
  });
});
