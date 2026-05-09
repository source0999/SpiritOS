import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ChatThread } from "@/lib/chat-db.types";

import { usePersistentChat } from "../usePersistentChat";

vi.mock("dexie-react-hooks", () => ({
  useLiveQuery: <T,>(factory: () => T) => factory(),
}));

// usePersistentChat's message live-query guards on `db`; without this, selecting a thread touches Dexie in jsdom.
vi.mock("@/lib/chat-db", () => ({
  db: null,
  isBrowserChatDbAvailable: false,
}));

const mockUseChatThreads = vi.fn();
const mockUseChatFolders = vi.fn();

vi.mock("@/hooks/useChatThreads", () => ({
  useChatThreads: (...args: unknown[]) => mockUseChatThreads(...args),
}));

vi.mock("@/hooks/useChatFolders", () => ({
  useChatFolders: (...args: unknown[]) => mockUseChatFolders(...args),
}));

function threadStub(overrides: Partial<ChatThread> = {}): ChatThread {
  return {
    id: "thr_a",
    title: "Saved lane",
    createdAt: 1,
    updatedAt: 2,
    ...overrides,
  };
}

function stubFoldersApi() {
  mockUseChatFolders.mockReturnValue({
    folders: [],
    isLoading: false,
    createNewFolder: vi.fn(),
    renameFolder: vi.fn(),
    removeFolder: vi.fn(),
    toggleFolderCollapsed: vi.fn(),
    setFolderCollapsed: vi.fn(),
  });
}

describe("usePersistentChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    stubFoldersApi();
    mockUseChatThreads.mockReturnValue({
      threads: [],
      isLoading: false,
      createNewThread: vi.fn(),
      renameThread: vi.fn(),
      removeThread: vi.fn(),
    });
  });

  it("bootstraps into draft lane when saved threads exist (no auto-open latest)", async () => {
    mockUseChatThreads.mockReturnValue({
      threads: [threadStub({ id: "thr_first" }), threadStub({ id: "thr_second" })],
      isLoading: false,
      createNewThread: vi.fn(),
      renameThread: vi.fn(),
      removeThread: vi.fn(),
    });

    const { result } = renderHook(() => usePersistentChat(true));

    await waitFor(() => {
      expect(result.current.draftLaneActive).toBe(true);
      expect(result.current.activeThreadId).toBeNull();
    });
    expect(result.current.visibleThreads).toHaveLength(2);
  });

  it("selectPersistedThread opens that thread; beginNewDraftChat returns to draft", async () => {
    mockUseChatThreads.mockReturnValue({
      threads: [threadStub({ id: "thr_pick" })],
      isLoading: false,
      createNewThread: vi.fn(),
      renameThread: vi.fn(),
      removeThread: vi.fn(),
    });

    const { result } = renderHook(() => usePersistentChat(true));

    await waitFor(() => expect(result.current.draftLaneActive).toBe(true));

    act(() => {
      result.current.selectPersistedThread("thr_pick");
    });

    expect(result.current.draftLaneActive).toBe(false);
    expect(result.current.activeThreadId).toBe("thr_pick");

    act(() => {
      result.current.beginNewDraftChat();
    });

    expect(result.current.draftLaneActive).toBe(true);
    expect(result.current.activeThreadId).toBeNull();
  });
});
