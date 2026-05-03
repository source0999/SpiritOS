import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { SpiritHealthIndicator } from "../SpiritHealthIndicator";

// Mock fetch globally for this test file
beforeEach(() => {
  vi.spyOn(global, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ ok: true }), { status: 200 })
  );
});

describe("SpiritHealthIndicator", () => {
  it("renders 'Checking…' on initial load", async () => {
    render(<SpiritHealthIndicator />);

    // Initial render should show "Checking…"
    expect(screen.getByText("Checking…")).toBeInTheDocument();

    // Wait for the fetch to complete and state to update
    await waitFor(() => {
      expect(screen.getByText("Online")).toBeInTheDocument();
    });
  });

  it("shows 'Offline' when the backend is unreachable", async () => {
    // Override mock for this test
    vi.spyOn(global, "fetch").mockRejectedValue(new Error("Network error"));

    render(<SpiritHealthIndicator />);

    await waitFor(() => {
      expect(screen.getByText("Offline")).toBeInTheDocument();
    });
  });
});
