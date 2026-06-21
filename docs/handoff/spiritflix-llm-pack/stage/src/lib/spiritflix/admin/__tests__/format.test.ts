import { describe, expect, it } from "vitest";
import { SPIRITFLIX_MEDIA_ROOT } from "../constants";
import { formatItemDateLabel, isMetadataSidecar } from "../format";
import type { SpiritFlixAdminItem } from "../types";

describe("SpiritFlix admin format helpers", () => {
  it("labels Jellyfin dates as added", () => {
    const item: SpiritFlixAdminItem = {
      id: "jellyfin:1",
      name: "Clip",
      type: "jellyfin-item",
      jellyfinId: "1",
      dateAdded: "2026-06-15T12:00:00.000Z",
    };
    expect(formatItemDateLabel(item)).toEqual({ label: "Added", text: expect.any(String) });
  });

  it("labels filesystem-only dates as modified", () => {
    const item: SpiritFlixAdminItem = {
      id: "file:1",
      name: "Clip.mkv",
      type: "file",
      dateModified: "2026-06-15T12:00:00.000Z",
    };
    expect(formatItemDateLabel(item)).toEqual({ label: "Modified", text: expect.any(String) });
  });

  it("hides metadata sidecars by default", () => {
    expect(isMetadataSidecar("Alpha Clip.media-ingest.json")).toBe(true);
    expect(isMetadataSidecar("Alpha Clip.face-meta.json")).toBe(true);
    expect(isMetadataSidecar(".hidden")).toBe(true);
    expect(isMetadataSidecar("Clip.mkv")).toBe(false);
  });
});

describe("SpiritFlix admin defaults", () => {
  it("uses the media root as the default landing path", () => {
    expect(SPIRITFLIX_MEDIA_ROOT).toBe("/mnt/spirit-8tb/media");
  });
});
