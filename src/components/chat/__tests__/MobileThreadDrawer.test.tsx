import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ChatThreadSidebar } from "@/components/chat/ChatThreadSidebar";
import { MobileThreadDrawer } from "@/components/chat/MobileThreadDrawer";
import type { ChatThread } from "@/lib/chat-db.types";

function threadStub(overrides: Partial<ChatThread> = {}): ChatThread {
  return {
    id: "thr_drawer",
    title: "Sheet thread",
    createdAt: 1,
    updatedAt: Date.now(),
    ...overrides,
  };
}

const noop = () => {};

describe("MobileThreadDrawer", () => {
  it("uses Chats title and renders children when open", async () => {
    render(
      <MobileThreadDrawer open onClose={vi.fn()}>
        <p data-testid="rail-child">sidebar</p>
      </MobileThreadDrawer>,
    );
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Chats/i })).toBeInTheDocument();
    });
    expect(screen.getByTestId("rail-child")).toBeInTheDocument();
  });

  it("hosts trinity ChatThreadSidebar with handle-only row drag (grip), not whole-row", async () => {
    render(
      <MobileThreadDrawer open onClose={vi.fn()}>
        <ChatThreadSidebar
          savedThreadCount={1}
          rootThreads={[threadStub()]}
          folderSections={[]}
          allFolders={[]}
          activeThreadId={null}
          layoutVariant="drawer"
          chromeVariant="trinity"
          mobileDndEnabled
          onCommitThreadDrag={noop}
          onNewChat={noop}
          onCreateFolder={noop}
          onSelectThread={noop}
          onRenameThread={noop}
          onDeleteThread={noop}
          onMoveThreadToFolder={noop}
          onRenameFolder={noop}
          onDeleteFolder={noop}
          onToggleFolderCollapsed={noop}
        />
      </MobileThreadDrawer>,
    );
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Chats/i })).toBeInTheDocument();
    });
    expect(
      screen.getByRole("button", { name: /drag to reorder sheet thread/i }),
    ).toBeInTheDocument();
  });
});
