import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { SpiritMessage } from "../SpiritMessage";

describe("SpiritMessage", () => {
  it("renders user message on the right", () => {
    const userMessage = {
      id: "1",
      role: "user" as const,
      parts: [{ type: "text" as const, text: "Hello Spirit" }],
    };

    render(<SpiritMessage message={userMessage} />);

    expect(screen.getByText("You")).toBeInTheDocument();
    expect(screen.getByText("Hello Spirit")).toBeInTheDocument();
  });

  it("renders Spirit message on the left", () => {
    const spiritMessage = {
      id: "2",
      role: "assistant" as const,
      parts: [{ type: "text" as const, text: "Hello from the void." }],
    };

    render(<SpiritMessage message={spiritMessage} />);

    expect(screen.getByText("Spirit")).toBeInTheDocument();
    expect(screen.getByText("Hello from the void.")).toBeInTheDocument();
  });
});
