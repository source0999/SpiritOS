import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ChatActiveModeBadge } from "@/components/chat/ChatActiveModeBadge";

describe("ChatActiveModeBadge", () => {
  it("renders Peer mode label", () => {
    render(<ChatActiveModeBadge profileId="normal-peer" />);
    expect(screen.getByText(/Mode:\s*Peer/i)).toBeInTheDocument();
    expect(screen.getByText(/grounded friend/i)).toBeInTheDocument();
  });

  it("updates when profile changes", () => {
    const { rerender } = render(<ChatActiveModeBadge profileId="normal-peer" />);
    expect(screen.getByText(/Peer/i)).toBeInTheDocument();
    rerender(<ChatActiveModeBadge profileId="teacher" />);
    expect(screen.getByText(/Mode:\s*Teacher/i)).toBeInTheDocument();
  });
});
