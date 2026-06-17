import { describe, expect, it } from "vitest";
import { buildItemMenuItems } from "../item-menu";
import type { SpiritFlixAdminItem } from "@/lib/spiritflix/admin/types";

const video: SpiritFlixAdminItem = {
  id: "file:video",
  name: "3869.mp4",
  type: "file",
  path: "/mnt/spirit-8tb/media/yes/3869.mp4",
  parentPath: "/mnt/spirit-8tb/media/yes",
  playable: true,
  jellyfinItemId: "jf-1",
};

const folder: SpiritFlixAdminItem = {
  id: "folder:child",
  name: "Series",
  type: "folder",
  path: "/mnt/spirit-8tb/media/yes/Series",
  parentPath: "/mnt/spirit-8tb/media/yes",
};

describe("buildItemMenuItems", () => {
  it("includes CRUD actions for video files without hard delete", () => {
    const items = buildItemMenuItems(video, "");
    const labels = items.map((entry) => entry.label);
    expect(labels).toEqual(expect.arrayContaining(["Rename", "Move", "Soft delete", "Edit metadata", "Info", "Open viewer"]));
    expect(labels).not.toEqual(expect.arrayContaining(["Hard delete", "Delete permanently"]));
  });

  it("includes folder actions", () => {
    const labels = buildItemMenuItems(folder, "").map((entry) => entry.label);
    expect(labels).toEqual(expect.arrayContaining(["Open folder", "Rename", "Move", "Soft delete", "Copy folder name"]));
  });
});
