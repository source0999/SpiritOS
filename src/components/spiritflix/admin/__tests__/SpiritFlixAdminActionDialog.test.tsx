import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SpiritFlixAdminActionDialog } from "../SpiritFlixAdminActionDialog";
import type { SpiritFlixAdminItem } from "@/lib/spiritflix/admin/types";

vi.mock("@/lib/spiritflix/admin/approved-mutation-client", () => ({
  fetchApprovedSpiritFlixAdminMutation: async (
    _writer: string,
    url: string,
    mutation: Record<string, unknown>,
    init: RequestInit = {},
  ) => fetch(url, {
    ...init,
    body: JSON.stringify({ ...mutation, approval_id: "approval-component-test" }),
    headers: { "Content-Type": "application/json", ...init.headers },
    method: init.method ?? "POST",
  }),
}));

const folderItem: SpiritFlixAdminItem = {
  id: "folder:smoke",
  name: "cursor-smoke-folder",
  type: "folder",
  path: "/mnt/spirit-8tb/media/other/.spiritflix-admin-smoke/cursor-smoke-folder",
  parentPath: "/mnt/spirit-8tb/media/other/.spiritflix-admin-smoke",
};

describe("SpiritFlixAdminActionDialog", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("requires preview before execute for new folder", async () => {
    const onComplete = vi.fn();
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(
        Response.json({
          schema: "spiritflix-admin-action/v1",
          action: "createFolder",
          phase: "preview",
          previewId: "preview-1",
          allowed: true,
          message: "Create folder nested",
          preview: { affectedPaths: ["/mnt/spirit-8tb/media/other/.spiritflix-admin-smoke/nested"], warnings: [] },
        }),
      )
      .mockResolvedValueOnce(
        Response.json({
          schema: "spiritflix-admin-action/v1",
          action: "createFolder",
          phase: "execute",
          previewId: "preview-1",
          allowed: true,
          message: "Folder created.",
          receipt: { id: "rcpt-1", status: "executed", affectedPaths: [] },
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    const onClose = vi.fn();
    render(
      <SpiritFlixAdminActionDialog
        item={null}
        currentPath="/mnt/spirit-8tb/media/other/.spiritflix-admin-smoke"
        onClose={onClose}
        onComplete={onComplete}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("folder-name"), { target: { value: "nested" } });
    fireEvent.click(screen.getByRole("button", { name: "Preview new folder" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Confirm execute" })).toBeEnabled();
    });

    fireEvent.click(screen.getByRole("button", { name: "Confirm execute" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(2);
      expect(onComplete).toHaveBeenCalledWith("Folder created.", expect.anything());
      expect(onClose).toHaveBeenCalled();
    });
  });

  it("shows soft delete warning and disables execute before preview", async () => {
    render(
      <SpiritFlixAdminActionDialog
        item={folderItem}
        currentPath={folderItem.parentPath as string}
        onClose={() => undefined}
        onComplete={() => undefined}
      />,
    );

    expect(screen.getByText(/Soft delete moves items to SpiritFlix trash/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Confirm execute" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /hard delete/i })).not.toBeInTheDocument();
  });

  it("requires selection context for rename preview", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({
        schema: "spiritflix-admin-action/v1",
        action: "rename",
        phase: "preview",
        previewId: "preview-rename",
        allowed: true,
        message: "Rename",
        preview: { affectedPaths: [], warnings: [] },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(
      <SpiritFlixAdminActionDialog
        item={folderItem}
        currentPath={folderItem.parentPath as string}
        onClose={() => undefined}
        onComplete={() => undefined}
      />,
    );

    fireEvent.change(screen.getByLabelText("Rename to"), { target: { value: "cursor-smoke-renamed" } });
    fireEvent.click(screen.getByRole("button", { name: "Preview rename" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/spiritflix/admin/actions",
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining("cursor-smoke-renamed"),
        }),
      );
    });
  });
});
