import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MobileSheet } from "@/components/chat/MobileSheet";

afterEach(() => {
  cleanup();
});

describe("MobileSheet", () => {
  it("closed renders nothing in the test container", () => {
    const { container } = render(
      <MobileSheet open={false} title="Nope" onClose={vi.fn()}>
        <p>Secret</p>
      </MobileSheet>,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("open renders dialog title and close button", async () => {
    render(
      <MobileSheet open title="Threads" onClose={vi.fn()}>
        <p>rail</p>
      </MobileSheet>,
    );
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(screen.getByRole("heading", { name: /Threads/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Close$/i })).toBeInTheDocument();
  });

  it("backdrop dismiss closes", async () => {
    const onClose = vi.fn();
    render(
      <MobileSheet open title="X" onClose={onClose}>
        hi
      </MobileSheet>,
    );
    await waitFor(() => expect(screen.getByRole("dialog")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /^Dismiss$/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
