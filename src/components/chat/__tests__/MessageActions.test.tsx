import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";

import { MessageActions } from "@/components/chat/MessageActions";
import { useMediaMinWidthLg } from "@/lib/hooks/useMediaMinWidthLg";

vi.mock("@/lib/hooks/useMediaMinWidthLg", () => ({
  useMediaMinWidthLg: vi.fn(() => true),
}));

const mockedLg = vi.mocked(useMediaMinWidthLg);

describe("MessageActions", () => {
  it("copy calls clipboard.writeText with message text supplied by parent", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText } });

    render(
      <MessageActions
        role="user"
        onCopy={() => void navigator.clipboard.writeText("alpha")}
        onDelete={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /^Copy$/i }));
    expect(writeText).toHaveBeenCalledWith("alpha");
    vi.unstubAllGlobals();
  });

  it("shows edit for user when onEdit provided", () => {
    render(
      <MessageActions
        role="user"
        onCopy={vi.fn()}
        onDelete={vi.fn()}
        onEdit={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: /^Edit$/i })).toBeInTheDocument();
  });

  it("shows regenerate for assistant when onRegenerate provided", () => {
    render(
      <MessageActions
        role="assistant"
        onCopy={vi.fn()}
        onDelete={vi.fn()}
        onRegenerate={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: /^Regenerate$/i })).toBeInTheDocument();
  });

  it("Speak calls onSpeak when enabled", () => {
    const onSpeak = vi.fn();
    render(
      <MessageActions
        role="assistant"
        onCopy={vi.fn()}
        onDelete={vi.fn()}
        onRegenerate={vi.fn()}
        onSpeak={onSpeak}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /^Speak$/i }));
    expect(onSpeak).toHaveBeenCalledTimes(1);
  });

  it("exposes accessible names for Copy and Delete", () => {
    render(
      <MessageActions role="user" onCopy={vi.fn()} onDelete={vi.fn()} />,
    );
    expect(screen.getByRole("button", { name: /^Copy$/i })).toHaveAttribute(
      "title",
      "Copy",
    );
    expect(screen.getByRole("button", { name: /^Delete$/i })).toHaveAttribute(
      "title",
      "Delete",
    );
  });

  describe("useActionSheetBelowLg (mobile Dexie layout)", () => {
    beforeEach(() => {
      mockedLg.mockReturnValue(false);
    });

    afterEach(() => {
      mockedLg.mockReturnValue(true);
    });

    it("More opens compact tray with Copy / Speak / Delete", async () => {
      render(
        <MessageActions
          useActionSheetBelowLg
          role="assistant"
          onCopy={vi.fn()}
          onDelete={vi.fn()}
          onSpeak={vi.fn()}
          onRegenerate={vi.fn()}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: /Message actions/i }));
      await waitFor(() => {
        expect(screen.getByRole("dialog")).toBeInTheDocument();
      });
      expect(screen.getByRole("heading", { name: /^Actions$/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^Copy$/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^Speak$/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^Delete$/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^Regenerate$/i })).toBeInTheDocument();
    });

    it("Copy closes the tray", async () => {
      const onCopy = vi.fn();
      render(
        <MessageActions
          useActionSheetBelowLg
          role="assistant"
          onCopy={onCopy}
          onDelete={vi.fn()}
          onSpeak={vi.fn()}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: /Message actions/i }));
      await waitFor(() => expect(screen.getByRole("dialog")).toBeInTheDocument());
      fireEvent.click(screen.getByRole("button", { name: /^Copy$/i }));
      await waitFor(() => {
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
      });
      expect(onCopy).toHaveBeenCalled();
    });

    it("Edit appears for user only; Regenerate for assistant only", async () => {
      const { rerender } = render(
        <MessageActions
          useActionSheetBelowLg
          role="user"
          onCopy={vi.fn()}
          onDelete={vi.fn()}
          onEdit={vi.fn()}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: /Message actions/i }));
      await waitFor(() => expect(screen.getByRole("dialog")).toBeInTheDocument());
      expect(screen.getByRole("button", { name: /^Edit$/i })).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /^Regenerate$/i })).not.toBeInTheDocument();

      rerender(
        <MessageActions
          useActionSheetBelowLg
          role="assistant"
          onCopy={vi.fn()}
          onDelete={vi.fn()}
          onRegenerate={vi.fn()}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: /Message actions/i }));
      await waitFor(() => expect(screen.getByRole("dialog")).toBeInTheDocument());
      expect(screen.queryByRole("button", { name: /^Edit$/i })).not.toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^Regenerate$/i })).toBeInTheDocument();
    });

    it("user bubble-user sheet trigger is absolutely positioned (corner chip)", () => {
      render(
        <MessageActions
          useActionSheetBelowLg
          placement="bubble-user"
          role="user"
          onCopy={vi.fn()}
          onDelete={vi.fn()}
        />,
      );
      const btn = screen.getByRole("button", { name: /Message actions/i });
      expect(btn.parentElement?.className).toMatch(/absolute/);
    });
  });
});
