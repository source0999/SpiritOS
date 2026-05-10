import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ChatThreadSidebar } from "@/components/chat/ChatThreadSidebar";

vi.mock("@/lib/hooks/useMediaMinWidthLg", () => ({
  useMediaMinWidthLg: vi.fn(() => true),
}));
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

  it('uses placeholder exactly "Search chats..." when search is enabled', () => {
    render(
      <ChatThreadSidebar
        savedThreadCount={1}
        rootThreads={[threadStub({ id: "z" })]}
        folderSections={[]}
        allFolders={[]}
        activeThreadId="z"
        chromeVariant="trinity"
        searchQuery=""
        onSearchQueryChange={noop}
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
    expect(screen.getByPlaceholderText("Search chats...")).toBeInTheDocument();
  });

  it("does not ship localhost debug ingest or agentDebugLog in sidebar source", () => {
    const p = resolve(process.cwd(), "src/components/chat/ChatThreadSidebar.tsx");
    const src = readFileSync(p, "utf8");
    expect(src).not.toMatch(/localhost:7644|\/ingest\//);
    expect(src).not.toMatch(/agentDebugLog/);
  });

  it('uses handle-only thread drag layout (const threadDragLayout = "handle")', () => {
    const p = resolve(process.cwd(), "src/components/chat/ChatThreadSidebar.tsx");
    const src = readFileSync(p, "utf8");
    expect(src).toContain('const threadDragLayout = "handle"');
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
    const labelTexts = Array.from(
      rail.querySelectorAll("[data-sidebar-section-label]"),
    ).map((node) => node.textContent?.trim() ?? "");

    expect(labelTexts).toEqual(["Pinned", "Folders", "Recent"]);
  });

  it("does not list pinned root threads under Recent (only under Pinned)", () => {
    render(
      <ChatThreadSidebar
        savedThreadCount={2}
        rootThreads={[
          threadStub({ id: "unpinned", title: "Only in recent" }),
          threadStub({ id: "pinned-id", title: "Pinned title", pinned: true }),
        ]}
        folderSections={[]}
        allFolders={[]}
        activeThreadId={null}
        pinnedThreads={[
          threadStub({ id: "pinned-id", title: "Pinned title", pinned: true }),
        ]}
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

    const recent = document.querySelector('[data-sidebar-section="recent"]');
    const pinned = document.querySelector('[data-sidebar-section="pinned"]');
    expect(recent).toBeTruthy();
    expect(pinned).toBeTruthy();
    expect(within(recent as HTMLElement).getByText("Only in recent")).toBeInTheDocument();
    expect(within(recent as HTMLElement).queryByText("Pinned title")).not.toBeInTheDocument();
    expect(within(pinned as HTMLElement).getByText("Pinned title")).toBeInTheDocument();
  });

  it("collapses pinned and folders bodies when section toggles are clicked", () => {
    const folder: ChatFolder = {
      id: "fld",
      name: "Work",
      createdAt: 1,
      updatedAt: 2,
      order: 0,
      collapsed: false,
    };
    render(
      <ChatThreadSidebar
        savedThreadCount={2}
        rootThreads={[threadStub({ id: "r1", title: "Root row" })]}
        folderSections={[{ folder, threads: [] }]}
        allFolders={[folder]}
        activeThreadId={null}
        pinnedThreads={[threadStub({ id: "p1", title: "Pinned row", pinned: true })]}
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

    const pinnedBody = document.getElementById("sidebar-section-body-pinned");
    const foldersBody = document.getElementById("sidebar-section-body-folders");
    expect(pinnedBody).toBeTruthy();
    expect(foldersBody).not.toHaveAttribute("hidden");

    fireEvent.click(screen.getByRole("button", { name: /^pinned$/i }));
    expect(document.getElementById("sidebar-section-body-pinned")).toBeNull();
    expect(screen.queryByText("Pinned row")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /^folders$/i }));
    expect(foldersBody).toHaveAttribute("hidden");
  });

  it("trinity desktop: first click on title selects; drag handle exists (no row-wide drag surface)", () => {
    const onSelectThread = vi.fn();
    render(
      <ChatThreadSidebar
        savedThreadCount={1}
        rootThreads={[threadStub({ id: "thr_pick", title: "Pick me first" })]}
        folderSections={[]}
        allFolders={[]}
        activeThreadId={null}
        chromeVariant="trinity"
        onCommitThreadDrag={noop}
        onNewChat={noop}
        onCreateFolder={noop}
        onSelectThread={onSelectThread}
        onRenameThread={noop}
        onDeleteThread={noop}
        onMoveThreadToFolder={noop}
        onRenameFolder={noop}
        onDeleteFolder={noop}
        onToggleFolderCollapsed={noop}
      />,
    );

    const titleBtn = screen.getByRole("button", {
      name: /Open conversation · Pick me first/i,
    });
    const edgeBtn = screen.getByRole("button", {
      name: /^Drag to reorder Pick me first$/i,
    });
    expect(titleBtn).not.toBe(edgeBtn);
    expect(document.querySelector('[data-drag-handle="thread-edge"]')).toBeTruthy();
    expect(document.querySelector('[data-drag-surface="thread-row"]')).toBeNull();

    fireEvent.click(titleBtn);
    expect(onSelectThread).toHaveBeenCalledTimes(1);
    expect(onSelectThread).toHaveBeenCalledWith("thr_pick");
  });

  it("trinity drawer with mobileDndEnabled: exposes drag handle (not row surface)", () => {
    render(
      <ChatThreadSidebar
        savedThreadCount={1}
        rootThreads={[threadStub({ id: "drawer-row", title: "Drawer thread" })]}
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
      />,
    );

    expect(
      screen.getByRole("button", {
        name: /^Drag to reorder Drawer thread$/i,
      }),
    ).toBeInTheDocument();
    expect(document.querySelector('[data-drag-handle="thread-edge"]')).toBeTruthy();
    expect(document.querySelector('[data-drag-surface="thread-row"]')).toBeNull();
  });

  it("pinned rows expose drag handle when DnD is enabled", () => {
    render(
      <ChatThreadSidebar
        savedThreadCount={1}
        rootThreads={[threadStub({ id: "r1", title: "Recent only" })]}
        folderSections={[]}
        allFolders={[]}
        activeThreadId={null}
        pinnedThreads={[threadStub({ id: "p1", title: "Pinned row", pinned: true })]}
        chromeVariant="trinity"
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
      />,
    );

    const pinned = document.querySelector('[data-sidebar-section="pinned"]');
    const recent = document.querySelector('[data-sidebar-section="recent"]');
    expect(pinned).toBeTruthy();
    expect(recent).toBeTruthy();
    expect(
      within(pinned as HTMLElement).getByRole("button", {
        name: /^Drag to reorder Pinned row$/i,
      }),
    ).toBeInTheDocument();
    expect(
      within(recent as HTMLElement).getByRole("button", {
        name: /^Drag to reorder Recent only$/i,
      }),
    ).toBeInTheDocument();
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
