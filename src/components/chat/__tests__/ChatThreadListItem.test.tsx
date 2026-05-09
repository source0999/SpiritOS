import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ChatThreadListItem } from "@/components/chat/ChatThreadListItem";
import type { ChatThread } from "@/lib/chat-db.types";

const thread: ChatThread = {
  id: "t1",
  title: "Hello",
  createdAt: 1,
  updatedAt: 2,
};

const moveSelect = {
  value: "__root__",
  options: [
    { value: "__root__", label: "Chats" },
    { value: "f1", label: "Folder A" },
  ],
};

describe("ChatThreadListItem", () => {
  it("hides move select by default", () => {
    render(
      <ChatThreadListItem
        thread={thread}
        active={false}
        updatedLabel="now"
        onSelect={vi.fn()}
        onRename={vi.fn()}
        onDelete={vi.fn()}
        moveSelect={moveSelect}
        onMoveThread={vi.fn()}
      />,
    );
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("clicking Move reveals select; choosing folder calls onMoveThread and closes", () => {
    const onMove = vi.fn();
    render(
      <ChatThreadListItem
        thread={thread}
        active={false}
        updatedLabel="now"
        onSelect={vi.fn()}
        onRename={vi.fn()}
        onDelete={vi.fn()}
        moveSelect={moveSelect}
        onMoveThread={onMove}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Move thread/i }));
    const sel = screen.getByRole("combobox");
    expect(sel).toBeInTheDocument();
    fireEvent.change(sel, { target: { value: "f1" } });
    expect(onMove).toHaveBeenCalledWith("f1");
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("drawer handle mode exposes Drag to reorder control", () => {
    const dragHandleProps = {
      onPointerDown: vi.fn(),
    } as unknown as import("@/components/chat/ChatThreadListItem").ChatThreadDragActivatorProps;

    render(
      <ChatThreadListItem
        thread={thread}
        active={false}
        updatedLabel="now"
        onSelect={vi.fn()}
        onRename={vi.fn()}
        onDelete={vi.fn()}
        dragHandleProps={dragHandleProps}
      />,
    );
    expect(
      screen.getByRole("button", { name: /Drag to reorder Hello/i }),
    ).toBeInTheDocument();
  });

  it("desktop row mode has no drag handle when only dragActivatorProps would be used", () => {
    const dragActivatorProps = {
      onPointerDown: vi.fn(),
    } as unknown as import("@/components/chat/ChatThreadListItem").ChatThreadDragActivatorProps;

    render(
      <ChatThreadListItem
        thread={thread}
        active={false}
        updatedLabel="now"
        onSelect={vi.fn()}
        onRename={vi.fn()}
        onDelete={vi.fn()}
        dragActivatorProps={dragActivatorProps}
      />,
    );
    expect(
      screen.queryByRole("button", { name: /Drag to reorder/i }),
    ).not.toBeInTheDocument();
  });
});
