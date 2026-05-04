import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MobileThreadDrawer } from "@/components/chat/MobileThreadDrawer";

describe("MobileThreadDrawer", () => {
  it("uses Threads title and renders children when open", async () => {
    render(
      <MobileThreadDrawer open onClose={vi.fn()}>
        <p data-testid="rail-child">sidebar</p>
      </MobileThreadDrawer>,
    );
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Threads/i })).toBeInTheDocument();
    });
    expect(screen.getByTestId("rail-child")).toBeInTheDocument();
  });
});
