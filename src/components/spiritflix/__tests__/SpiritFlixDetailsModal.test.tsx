import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SpiritFlixDetailsModal } from "../SpiritFlixDetailsModal";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix-types";

const item: JellyfinItem = {
  Id: "details-1",
  Name: "Details Close Test",
  Type: "Video",
  MediaType: "Video",
  RunTimeTicks: 1200000000,
  Overview: "A test video.",
  UserData: {
    Played: false,
    PlaybackPositionTicks: 0,
    PlayCount: 0,
  },
};

function createClient(): JellyfinClient {
  return {
    getImageObjectUrl: vi.fn().mockRejectedValue(new Error("No image in test")),
  } as unknown as JellyfinClient;
}

describe("SpiritFlixDetailsModal", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("closes when Escape is pressed", async () => {
    const onClose = vi.fn();

    render(<SpiritFlixDetailsModal client={createClient()} item={item} onClose={onClose} onPlay={vi.fn()} />);

    expect(screen.getByRole("dialog", { name: "Details Close Test details" })).toBeInTheDocument();

    fireEvent.keyDown(window, { key: "Escape" });

    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1));
  });
});
