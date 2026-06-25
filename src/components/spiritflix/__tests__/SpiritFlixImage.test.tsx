import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ImgHTMLAttributes } from "react";
import { SpiritFlixImage } from "../SpiritFlixImage";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix-types";

vi.mock("next/image", () => ({
  default: ({
    alt,
    fetchPriority: _fetchPriority,
    onError,
    onLoad,
    src,
    unoptimized: _unoptimized,
    ...props
  }: ImgHTMLAttributes<HTMLImageElement> & { fetchPriority?: string; unoptimized?: boolean }) => (
    <img alt={alt} src={src} onError={onError} onLoad={onLoad} {...props} />
  ),
}));

const imageItem: JellyfinItem = {
  Id: "image-1",
  Name: "Fallback Scene",
  Type: "Video",
  MediaType: "Video",
  ImageTags: {
    Primary: "primary-tag",
    Thumb: "thumb-tag",
  },
};

function createClient(): JellyfinClient {
  return {
    getImageProxyUrl: vi.fn((_item: JellyfinItem, type: "Primary" | "Backdrop" | "Thumb") => `/proxy/${type}`),
  } as unknown as JellyfinClient;
}

describe("SpiritFlixImage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("tries the next Jellyfin image type before falling back", async () => {
    const client = createClient();
    render(<SpiritFlixImage client={client} item={imageItem} type="Primary" width={320} alt={imageItem.Name} priority />);

    expect(client.getImageProxyUrl).toHaveBeenLastCalledWith(imageItem, "Primary", 320);
    expect(screen.getByAltText(imageItem.Name)).toHaveAttribute("src", "/proxy/Primary");

    fireEvent.error(screen.getByAltText(imageItem.Name));

    await waitFor(() => {
      expect(client.getImageProxyUrl).toHaveBeenLastCalledWith(imageItem, "Thumb", 320);
      expect(screen.getByAltText(imageItem.Name)).toHaveAttribute("src", "/proxy/Thumb");
    });

    fireEvent.error(screen.getByAltText(imageItem.Name));

    await waitFor(() => {
      expect(screen.getByLabelText(imageItem.Name)).toHaveClass("spiritflix-image-fallback");
    });
  });

  it("waits to request offscreen thumbnails until they approach the viewport", async () => {
    const client = createClient();
    let intersect: ((entries: Array<{ isIntersecting: boolean }>) => void) | null = null;
    const observe = vi.fn();
    const disconnect = vi.fn();

    class MockIntersectionObserver {
      constructor(callback: (entries: Array<{ isIntersecting: boolean }>) => void) {
        intersect = callback;
      }

      observe = observe;
      disconnect = disconnect;
    }

    vi.stubGlobal("IntersectionObserver", MockIntersectionObserver);

    render(<SpiritFlixImage client={client} item={imageItem} type="Primary" width={320} alt={imageItem.Name} />);

    expect(observe).toHaveBeenCalledTimes(1);
    expect(client.getImageProxyUrl).not.toHaveBeenCalled();

    act(() => {
      intersect?.([{ isIntersecting: true }]);
    });

    await waitFor(() => {
      expect(client.getImageProxyUrl).toHaveBeenCalledWith(imageItem, "Primary", 320);
      expect(screen.getByAltText(imageItem.Name)).toHaveAttribute("src", "/proxy/Primary");
    });
    expect(disconnect).toHaveBeenCalled();
  });
});
