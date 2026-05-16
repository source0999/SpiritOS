import { fireEvent, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
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
  it("source uses flex thread rows, not grid column hacks", () => {
    const src = readFileSync(
      resolve(process.cwd(), "src/components/chat/ChatThreadListItem.tsx"),
      "utf8",
    );
    expect(src).not.toContain("spirit-chat-thread-row grid");
    expect(src).not.toContain("grid-cols-[2rem_minmax(0,1fr)_auto]");
    expect(src).not.toContain("col-start-");
    expect(src).not.toContain("row-start-");
  });

  it("inline row with drag handle: title opens once; edge has data-drag-handle thread-edge and touchAction none", () => {
    const onSelect = vi.fn();
    const dragHandleProps = {
      onPointerDown: vi.fn(),
    } as unknown as import("@/components/chat/ChatThreadListItem").ChatThreadDragActivatorProps;

    render(
      <ChatThreadListItem
        thread={thread}
        active={false}
        updatedLabel="now"
        onSelect={onSelect}
        onRename={vi.fn()}
        onDelete={vi.fn()}
        dragHandleProps={dragHandleProps}
      />,
    );

    const edge = screen.getByRole("button", { name: /Drag to reorder Hello/i });
    expect(edge).toHaveAttribute("data-drag-handle", "thread-edge");
    expect(edge.style.touchAction).toBe("none");

    fireEvent.click(screen.getByRole("button", { name: /Open conversation · Hello/i }));
    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it("source never uses row-wide data-drag-surface or GripVertical", () => {
    const src = readFileSync(
      resolve(process.cwd(), "src/components/chat/ChatThreadListItem.tsx"),
      "utf8",
    );
    expect(src).not.toContain('data-drag-surface="thread-row"');
    expect(src).not.toContain("GripVertical");
  });

  it("drag handle onPointerDown fires on edge only, not on title button", () => {
    const onSelect = vi.fn();
    const onPointerDown = vi.fn();
    const dragHandleProps = {
      onPointerDown,
    } as unknown as import("@/components/chat/ChatThreadListItem").ChatThreadDragActivatorProps;

    render(
      <ChatThreadListItem
        thread={thread}
        active={false}
        updatedLabel="now"
        onSelect={onSelect}
        onRename={vi.fn()}
        onDelete={vi.fn()}
        dragHandleProps={dragHandleProps}
      />,
    );

    const title = screen.getByRole("button", { name: /Open conversation · Hello/i });
    fireEvent.pointerDown(title);
    expect(onPointerDown).not.toHaveBeenCalled();

    fireEvent.pointerDown(
      screen.getByRole("button", { name: /Drag to reorder Hello/i }),
    );
    expect(onPointerDown).toHaveBeenCalledTimes(1);
  });

  it("trinity-recent opens ⋮ menu with Rename (portal)", () => {
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
        actionLayout="trinity-recent"
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Thread options/i }));
    expect(screen.getByRole("menuitem", { name: /^Rename$/ })).toBeInTheDocument();
  });

  it("trinity-recent row popout uses portal-safe liquid hook for global CSS", () => {
    const src = readFileSync(
      resolve(process.cwd(), "src/components/chat/ChatThreadListItem.tsx"),
      "utf8",
    );
    expect(src).toContain('data-trinity-liquid="popout"');
    expect(src).toContain("spirit-trinity-modal-glass");
  });

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

  it("trinity-recent with drag handle: first title click calls onSelect once; edge pointerdown does not select", () => {
    const onSelect = vi.fn();
    const dragHandleProps = {
      onPointerDown: vi.fn(),
    } as unknown as import("@/components/chat/ChatThreadListItem").ChatThreadDragActivatorProps;

    render(
      <ChatThreadListItem
        thread={thread}
        active={false}
        updatedLabel="now"
        onSelect={onSelect}
        onRename={vi.fn()}
        onDelete={vi.fn()}
        dragHandleProps={dragHandleProps}
        actionLayout="trinity-recent"
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: /Open conversation · Hello/i }),
    );
    expect(onSelect).toHaveBeenCalledTimes(1);

    fireEvent.pointerDown(
      screen.getByRole("button", { name: /Drag to reorder Hello/i }),
    );
    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it("trinity-recent: rendered tree has no GripVertical svg role noise (no grip icon)", () => {
    const dragHandleProps = {
      onPointerDown: vi.fn(),
    } as unknown as import("@/components/chat/ChatThreadListItem").ChatThreadDragActivatorProps;

    const { container } = render(
      <ChatThreadListItem
        thread={thread}
        active={false}
        updatedLabel="now"
        onSelect={vi.fn()}
        onRename={vi.fn()}
        onDelete={vi.fn()}
        dragHandleProps={dragHandleProps}
        actionLayout="trinity-recent"
      />,
    );
    expect(container.innerHTML).not.toMatch(/grip-vertical/i);
  });

  it("trinity-recent: kebab menu click does not call onSelect", () => {
    const onSelect = vi.fn();
    const dragHandleProps = {
      onPointerDown: vi.fn(),
    } as unknown as import("@/components/chat/ChatThreadListItem").ChatThreadDragActivatorProps;

    render(
      <ChatThreadListItem
        thread={thread}
        active={false}
        updatedLabel="now"
        onSelect={onSelect}
        onRename={vi.fn()}
        onDelete={vi.fn()}
        dragHandleProps={dragHandleProps}
        actionLayout="trinity-recent"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Thread options/i }));
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("trinity-recent drag handle sets touchAction none for TouchSensor", () => {
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
        actionLayout="trinity-recent"
      />,
    );

    const edge = screen.getByRole("button", { name: /Drag to reorder Hello/i });
    expect(edge.style.touchAction).toBe("none");
    expect(edge).toHaveAttribute("data-drag-handle", "thread-edge");
  });

  it("drawer handle mode exposes Drag to reorder edge control", () => {
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
