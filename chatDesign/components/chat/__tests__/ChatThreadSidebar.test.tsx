import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ChatThreadSidebar } from "@/components/chat/ChatThreadSidebar";
import type { ChatFolder, ChatThread } from "@/lib/chat-db.types";

function threadStub(overrides: Partial<ChatThread> = {}): ChatThread {
  return {
    id: "thr_x",
    title: "Smoke test lane",
    createdAt: 1,
    updatedAt: Date.now(),
    ...overrides,
  };
}

const noop = () => {};

describe("ChatThreadSidebar", () => {
  it("uses hydration-safe useMediaMinWidthLg for desktop breakpoint (not lying sync store)", () => {
    const p = resolve(process.cwd(), "src/components/chat/ChatThreadSidebar.tsx");
    const src = readFileSync(p, "utf8");
    expect(src).toContain("useMediaMinWidthLg");
    expect(src).not.toContain("useSyncExternalStore");
  });

  it("does not render the under-search draft status card when draftActive and trinity", () => {
    render(
      <ChatThreadSidebar
        savedThreadCount={1}
        rootThreads={[threadStub({ id: "z" })]}
        folderSections={[]}
        allFolders={[]}
        activeThreadId="z"
        draftActive
        chromeVariant="trinity"
        onNewChat={noop}
        onCreateFolder={noop}
        onSelectThread={noop}
        onRenameThread={noop}
        onDeleteThread={noop}
        onMoveThreadToFolder={noop}
        onRenameFolder={noop}
        onDeleteFolder={noop}
        onToggleFolderCollapsed={noop}
      />,
    );

    expect(
      screen.queryByText(/draft · clears on first send/i),
    ).not.toBeInTheDocument();
  });

  it("orders trinity nav sections as Pinned, Folders, then Recent", () => {
    const folder: ChatFolder = {
      id: "fld_projects",
      name: "Projects",
      createdAt: 1,
      updatedAt: 2,
      order: 0,
      collapsed: false,
    };

    render(
      <ChatThreadSidebar
        savedThreadCount={3}
        rootThreads={[threadStub({ id: "recent", title: "Recent thread" })]}
        folderSections={[
          {
            folder,
            threads: [
              threadStub({
                id: "foldered",
                title: "Foldered thread",
                folderId: folder.id,
              }),
            ],
          },
        ]}
        allFolders={[folder]}
        activeThreadId="recent"
        pinnedThreads={[threadStub({ id: "pinned", title: "Pinned thread", pinned: true })]}
        chromeVariant="trinity"
        onNewChat={noop}
        onCreateFolder={noop}
        onSelectThread={noop}
        onRenameThread={noop}
        onDeleteThread={noop}
        onMoveThreadToFolder={noop}
        onRenameFolder={noop}
        onDeleteFolder={noop}
        onToggleFolderCollapsed={noop}
      />,
    );

    const rail = screen.getByRole("complementary", {
      name: /saved chat threads/i,
    });
    const labels = Array.from(
      rail.querySelectorAll("[data-sidebar-section-label]"),
    ).map((node) => node.getAttribute("data-sidebar-section-label"));

    expect(labels).toEqual(["pinned", "folders", "recent"]);
  });

  it('uses handle-only thread drag layout (const threadDragLayout = "handle")', () => {
    const p = resolve(process.cwd(), "src/components/chat/ChatThreadSidebar.tsx");
    const src = readFileSync(p, "utf8");
    expect(src).toContain('const threadDragLayout = "handle"');
  });

  it("pins New chat disabled while muted without firing handlers", () => {
    const onNewChat = vi.fn();
    render(
      <ChatThreadSidebar
        savedThreadCount={0}
        rootThreads={[]}
        folderSections={[]}
        allFolders={[]}
        activeThreadId={null}
        draftActive={false}
        muteNewChatButton
        onNewChat={onNewChat}
        onCreateFolder={noop}
        onSelectThread={noop}
        onRenameThread={noop}
        onDeleteThread={noop}
        onMoveThreadToFolder={noop}
        onRenameFolder={noop}
        onDeleteFolder={noop}
        onToggleFolderCollapsed={noop}
      />,
    );

    const ctrl = screen.getByRole("button", { name: /new chat/i });
    expect(ctrl).toBeDisabled();
    fireEvent.click(ctrl);
    expect(onNewChat).not.toHaveBeenCalled();
  });

  it("shows inline folder name input when Folder is clicked", () => {
    render(
      <ChatThreadSidebar
        savedThreadCount={0}
        rootThreads={[]}
        folderSections={[]}
        allFolders={[]}
        activeThreadId={null}
        onNewChat={noop}
        onCreateFolder={noop}
        onSelectThread={noop}
        onRenameThread={noop}
        onDeleteThread={noop}
        onMoveThreadToFolder={noop}
        onRenameFolder={noop}
        onDeleteFolder={noop}
        onToggleFolderCollapsed={noop}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /new folder/i }));
    expect(screen.getByPlaceholderText(/new folder/i)).toBeInTheDocument();
  });

  it("Escape cancels folder creation without calling onCreateFolder", () => {
    const onCreateFolder = vi.fn();
    render(
      <ChatThreadSidebar
        savedThreadCount={0}
        rootThreads={[]}
        folderSections={[]}
        allFolders={[]}
        activeThreadId={null}
        onNewChat={noop}
        onCreateFolder={onCreateFolder}
        onSelectThread={noop}
        onRenameThread={noop}
        onDeleteThread={noop}
        onMoveThreadToFolder={noop}
        onRenameFolder={noop}
        onDeleteFolder={noop}
        onToggleFolderCollapsed={noop}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /new folder/i }));
    const input = screen.getByPlaceholderText(/new folder/i);
    fireEvent.change(input, { target: { value: "  " } });
    fireEvent.keyDown(input, { key: "Escape" });
    expect(onCreateFolder).not.toHaveBeenCalled();
    expect(screen.queryByPlaceholderText(/new folder/i)).not.toBeInTheDocument();
  });

  it("Enter with custom name calls onCreateFolder", () => {
    const onCreateFolder = vi.fn();
    render(
      <ChatThreadSidebar
        savedThreadCount={0}
        rootThreads={[]}
        folderSections={[]}
        allFolders={[]}
        activeThreadId={null}
        onNewChat={noop}
        onCreateFolder={onCreateFolder}
        onSelectThread={noop}
        onRenameThread={noop}
        onDeleteThread={noop}
        onMoveThreadToFolder={noop}
        onRenameFolder={noop}
        onDeleteFolder={noop}
        onToggleFolderCollapsed={noop}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /new folder/i }));
    const input = screen.getByPlaceholderText(/new folder/i);
    fireEvent.change(input, { target: { value: "  Alpha  " } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onCreateFolder).toHaveBeenCalledWith("Alpha");
  });

  it("does not create folder for empty name on blur", () => {
    const onCreateFolder = vi.fn();
    render(
      <ChatThreadSidebar
        savedThreadCount={0}
        rootThreads={[]}
        folderSections={[]}
        allFolders={[]}
        activeThreadId={null}
        onNewChat={noop}
        onCreateFolder={onCreateFolder}
        onSelectThread={noop}
        onRenameThread={noop}
        onDeleteThread={noop}
        onMoveThreadToFolder={noop}
        onRenameFolder={noop}
        onDeleteFolder={noop}
        onToggleFolderCollapsed={noop}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /new folder/i }));
    const input = screen.getByPlaceholderText(/new folder/i);
    fireEvent.change(input, { target: { value: "   " } });
    fireEvent.blur(input);
    expect(onCreateFolder).not.toHaveBeenCalled();
  });
});
