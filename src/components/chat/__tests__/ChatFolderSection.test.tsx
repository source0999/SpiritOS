import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ChatFolderSection } from "@/components/chat/ChatFolderSection";
import type { FolderSidebarSection } from "@/lib/chat-folder-utils";
import type { ChatFolder, ChatThread } from "@/lib/chat-db.types";

describe("ChatFolderSection", () => {
  it("hides thread rows when folder.collapsed is true", () => {
    const folder: ChatFolder = {
      id: "fld",
      name: "Archive",
      createdAt: 1,
      updatedAt: 2,
      order: 0,
      collapsed: true,
    };
    const threads: ChatThread[] = [
      {
        id: "thr",
        title: "Inside",
        createdAt: 1,
        updatedAt: 3,
        folderId: "fld",
      },
    ];
    const section: FolderSidebarSection = { folder, threads };
    render(
      <ChatFolderSection
        section={section}
        allFolders={[folder]}
        activeThreadId={null}
        onToggleCollapsed={vi.fn()}
        onRenameFolder={vi.fn()}
        onDeleteFolder={vi.fn()}
        onSelectThread={vi.fn()}
        onRenameThread={vi.fn()}
        onDeleteThread={vi.fn()}
        onMoveThread={vi.fn()}
      />,
    );
    expect(screen.queryByText("Inside")).toBeNull();
    expect(screen.getByText("Archive")).toBeInTheDocument();
  });

  it("shows thread rows when not collapsed", () => {
    const folder: ChatFolder = {
      id: "fld",
      name: "Live",
      createdAt: 1,
      updatedAt: 2,
      order: 0,
      collapsed: false,
    };
    const threads: ChatThread[] = [
      {
        id: "thr",
        title: "Visible",
        createdAt: 1,
        updatedAt: 3,
        folderId: "fld",
      },
    ];
    const section: FolderSidebarSection = { folder, threads };
    render(
      <ChatFolderSection
        section={section}
        allFolders={[folder]}
        activeThreadId={null}
        onToggleCollapsed={vi.fn()}
        onRenameFolder={vi.fn()}
        onDeleteFolder={vi.fn()}
        onSelectThread={vi.fn()}
        onRenameThread={vi.fn()}
        onDeleteThread={vi.fn()}
        onMoveThread={vi.fn()}
      />,
    );
    expect(screen.getByText("Visible")).toBeInTheDocument();
  });
});
