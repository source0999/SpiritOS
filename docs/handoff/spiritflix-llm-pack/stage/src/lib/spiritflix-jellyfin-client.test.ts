import { afterEach, describe, expect, it, vi } from "vitest";
import { JellyfinClient } from "./spiritflix-jellyfin-client";

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

    const hlsUrl = new URL(client.getHlsUrl("item-1"), "https://100.111.32.31:3000/spiritflix");
    expect(hlsUrl.pathname).toBe("/api/spiritflix/hls");
    expect(hlsUrl.searchParams.get("serverUrl")).toBe("http://100.111.32.31:8096");
    expect(hlsUrl.searchParams.get("token")).toBe("token-1");
    expect(hlsUrl.searchParams.get("path")).toContain("/Videos/item-1/master.m3u8");
    expect(hlsUrl.searchParams.get("path")).toContain("VideoBitrate=4000000");
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
