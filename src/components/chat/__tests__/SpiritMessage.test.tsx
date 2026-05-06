import { fireEvent, render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { SpiritMessage } from "../SpiritMessage";

const noopDelete = () => {};

describe("SpiritMessage", () => {
  it("renders user message on the right", () => {
    const userMessage = {
      id: "1",
      role: "user" as const,
      parts: [{ type: "text" as const, text: "Hello Spirit" }],
    };

    render(<SpiritMessage message={userMessage} onDelete={noopDelete} />);

    expect(screen.getByText("You")).toBeInTheDocument();
    expect(screen.getByText("Hello Spirit")).toBeInTheDocument();
    expect(screen.getByText("Hello Spirit").className).toContain(
      "[overflow-wrap:anywhere]",
    );
  });

  it("renders Spirit message on the left with markdown", () => {
    const spiritMessage = {
      id: "2",
      role: "assistant" as const,
      parts: [{ type: "text" as const, text: "**Hello** from the void." }],
    };

    render(<SpiritMessage message={spiritMessage} onDelete={noopDelete} />);

    expect(screen.getByText("Spirit")).toBeInTheDocument();
    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText(/from the void/i)).toBeInTheDocument();
  });

  it("shows streaming cursor when isStreamingLatest", () => {
    const spiritMessage = {
      id: "2",
      role: "assistant" as const,
      parts: [{ type: "text" as const, text: "Streaming…" }],
    };
    const { container } = render(
      <SpiritMessage
        message={spiritMessage}
        onDelete={noopDelete}
        isStreamingLatest
      />,
    );
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });

  it("user edit opens textarea and cancel restores", () => {
    const userMessage = {
      id: "9",
      role: "user" as const,
      parts: [{ type: "text" as const, text: "Original" }],
    };
    const onSave = vi.fn();
    render(
      <SpiritMessage
        message={userMessage}
        onDelete={noopDelete}
        onEditSave={onSave}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /^Edit$/i }));
    expect(screen.getByRole("textbox", { name: /edit message/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /cancel edit/i }));
    expect(screen.queryByRole("textbox", { name: /edit message/i })).not.toBeInTheDocument();
    expect(onSave).not.toHaveBeenCalled();
  });

  it("does not render leaked Sassy mode contract in assistant markdown", () => {
    const open = "<" + "redacted_thinking" + ">";
    const close = "<" + "/" + "redacted_thinking" + ">";
    const raw = ["Hi.", open, 'Respond in "Sassy mode" only', close, "Bye."].join("\n");
    const spiritMessage = {
      id: "2",
      role: "assistant" as const,
      parts: [{ type: "text" as const, text: raw }],
    };
    render(<SpiritMessage message={spiritMessage} onDelete={noopDelete} />);
    expect(screen.queryByText(/Sassy mode/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Hi/i)).toBeInTheDocument();
    expect(screen.getByText(/Bye/i)).toBeInTheDocument();
  });

  it("keeps message actions inside the bubble wrapper", () => {
    const userMessage = {
      id: "z",
      role: "user" as const,
      parts: [{ type: "text" as const, text: "Body" }],
    };
    const { container } = render(
      <SpiritMessage
        message={userMessage}
        onDelete={vi.fn()}
        onEditSave={vi.fn()}
      />,
    );
    const root = container.querySelector("[data-role='user']");
    expect(root?.className).toContain("group/message");
    const bubble = root?.querySelector(".relative.flex.min-w-0.flex-col");
    expect(bubble).toBeTruthy();
    expect(bubble!.contains(screen.getByRole("button", { name: /^Copy$/i }))).toBe(true);
  });
});
