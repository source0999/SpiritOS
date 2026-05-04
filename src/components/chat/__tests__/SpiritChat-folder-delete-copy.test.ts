import { describe, expect, it } from "vitest";

/** Inline folder delete confirm — keep in sync with ChatFolderHeaderRow. */
export const FOLDER_DELETE_INLINE_COPY =
  "Delete folder? Chats move to Chats.";

describe("SpiritChat folder delete UX copy", () => {
  it("inline confirm warns chats are not deleted", () => {
    expect(FOLDER_DELETE_INLINE_COPY).toMatch(/Chats move to Chats/i);
    expect(FOLDER_DELETE_INLINE_COPY).toMatch(/Delete folder/i);
  });
});
