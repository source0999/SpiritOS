import { describe, expect, it } from "vitest";
import type { JellyfinItem } from "@/lib/spiritflix-types";
import { matchJellyfinItemForAdminFile, preferredAdminImageType } from "../jellyfin-match";

function item(id: string, path?: string, extra: Partial<JellyfinItem> = {}): JellyfinItem {
  return {
    Id: id,
    Name: path ? path.split("/").pop() ?? id : id,
    Type: "Video",
    MediaType: "Video",
    Path: path,
    ...extra,
  };
}

describe("SpiritFlix admin Jellyfin matching", () => {
  it("prefers exact path over basename matches", () => {
    const match = matchJellyfinItemForAdminFile("/mnt/spirit-8tb/media/yes/Clip.mp4", [
      item("same-name", "/mnt/spirit-8tb/media/other/Clip.mp4", { ImageTags: { Primary: "primary" } }),
      item("exact", "/mnt/spirit-8tb/media/yes/Clip.mp4", { ImageTags: { Thumb: "thumb" } }),
    ]);

    expect(match.itemId).toBe("exact");
    expect(match.matchedBy).toBe("exact-path");
    expect(match.imageStatus).toBe("available");
    expect(match.imageType).toBe("Thumb");
  });

  it("matches container Jellyfin paths against host filesystem paths", () => {
    const match = matchJellyfinItemForAdminFile("/mnt/spirit-8tb/media/yes/Clip.mp4", [
      item("container", "/media/yes/Clip.mp4", { ImageTags: { Primary: "primary" } }),
    ]);

    expect(match.itemId).toBe("container");
    expect(match.matchedBy).toBe("exact-path");
    expect(match.imageStatus).toBe("available");
  });

  it("prefers exact alias path over basename-only matches", () => {
    const match = matchJellyfinItemForAdminFile("/mnt/spirit-8tb/media/yes/Clip.mp4", [
      item("basename", undefined, { Name: "Clip.mp4", ImageTags: { Primary: "primary" } }),
      item("alias", "/media/yes/Clip.mp4", { ImageTags: { Thumb: "thumb" } }),
    ]);

    expect(match.itemId).toBe("alias");
    expect(match.matchedBy).toBe("exact-path");
  });

  it("rejects ambiguous basename-only matches", () => {
    const match = matchJellyfinItemForAdminFile("/mnt/spirit-8tb/media/yes/Clip.mp4", [
      item("one", undefined, { Name: "Clip.mp4", ImageTags: { Primary: "primary" } }),
      item("two", undefined, { Name: "Clip.mp4", ImageTags: { Primary: "primary" } }),
    ]);

    expect(match.itemId).toBeUndefined();
    expect(match.matchedBy).toBe("ambiguous");
    expect(match.imageStatus).toBe("ambiguous");
  });

  it("uses Primary, Thumb, Backdrop image order", () => {
    expect(preferredAdminImageType(item("primary", "/media/a.mp4", { ImageTags: { Primary: "p", Thumb: "t" } }))).toBe("Primary");
    expect(preferredAdminImageType(item("thumb", "/media/b.mp4", { ImageTags: { Thumb: "t" } }))).toBe("Thumb");
    expect(preferredAdminImageType(item("backdrop", "/media/c.mp4", { BackdropImageTags: ["b"] }))).toBe("Backdrop");
    expect(preferredAdminImageType(item("none", "/media/d.mp4"))).toBeUndefined();
  });
});
