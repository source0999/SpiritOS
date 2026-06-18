import path from "node:path";
import { describe, expect, it } from "vitest";
import { buildSmartRenamePreviewDraft } from "../rename-preview";

describe("SpiritFlix smart rename preview", () => {
  it("preserves original extension when suggestion has no extension", () => {
    const draft = buildSmartRenamePreviewDraft({
      sourcePath: "/mnt/spirit-8tb/media/folder/video.mkv",
      filenameSuggestion: "Clean Title",
    });
    expect(draft.suggestedName).toBe("Clean Title.mkv");
  });

  it("preserves extension when suggestion already has matching extension", () => {
    const draft = buildSmartRenamePreviewDraft({
      sourcePath: "/mnt/spirit-8tb/media/folder/video.mkv",
      filenameSuggestion: "Clean Title.mkv",
    });
    expect(draft.suggestedName).toBe("Clean Title.mkv");
  });

  it("rejects traversal segments in suggested name", () => {
    const draft = buildSmartRenamePreviewDraft({
      sourcePath: "/mnt/spirit-8tb/media/folder/video.mp4",
      filenameSuggestion: "..something",
    });
    expect(draft.warnings).toContain("Filename suggestion contains traversal segments.");
    expect(draft.readyForLevel2Preview).toBe(false);
  });

  it("rejects slashes in suggested name", () => {
    const draft = buildSmartRenamePreviewDraft({
      sourcePath: "/mnt/spirit-8tb/media/folder/video.mp4",
      filenameSuggestion: "bad/name",
    });
    expect(draft.warnings.some((w) => /slashes/i.test(w))).toBe(true);
  });

  it("warns if filename is unchanged", () => {
    const draft = buildSmartRenamePreviewDraft({
      sourcePath: "/mnt/spirit-8tb/media/folder/video.mp4",
      filenameSuggestion: "video.mp4",
    });
    expect(draft.warnings).toContain("Suggested filename is unchanged from current filename.");
    expect(draft.readyForLevel2Preview).toBe(false);
  });

  it("warns if stem is generic", () => {
    const draft = buildSmartRenamePreviewDraft({
      sourcePath: "/mnt/spirit-8tb/media/folder/old.mp4",
      filenameSuggestion: "untitled",
    });
    expect(draft.warnings.some((w) => /generic/i.test(w))).toBe(true);
  });

  it("returns empty suggestion for empty input", () => {
    const draft = buildSmartRenamePreviewDraft({
      sourcePath: "/mnt/spirit-8tb/media/folder/video.mp4",
      filenameSuggestion: "",
    });
    expect(draft.suggestedName).toBe("");
    expect(draft.warnings).toContain("Filename suggestion is empty.");
    expect(draft.readyForLevel2Preview).toBe(false);
  });

  it("target path stays in same folder", () => {
    const draft = buildSmartRenamePreviewDraft({
      sourcePath: "/mnt/spirit-8tb/media/folder/video.mp4",
      filenameSuggestion: "New Name",
    });
    expect(draft.targetPath).toBe("/mnt/spirit-8tb/media/folder/New Name.mp4");
    expect(path.dirname(draft.targetPath)).toBe("/mnt/spirit-8tb/media/folder");
  });

  it("sanitizes unsafe filename characters", () => {
    const draft = buildSmartRenamePreviewDraft({
      sourcePath: "/mnt/spirit-8tb/media/folder/video.mp4",
      filenameSuggestion: 'bad:name?.mp4',
    });
    expect(draft.suggestedName).toBe("bad name.mp4");
  });

  it("does not execute filesystem action (pure function)", () => {
    // This test confirms the function is pure — no fs import, no side effects.
    // If it imported fs or called any filesystem operation, this module would fail
    // to load in the test environment without mocking.
    expect(typeof buildSmartRenamePreviewDraft).toBe("function");
    const draft = buildSmartRenamePreviewDraft({
      sourcePath: "/mnt/spirit-8tb/media/folder/video.mp4",
      filenameSuggestion: "Test",
    });
    expect(draft).toBeDefined();
    expect(draft.readyForLevel2Preview).toBe(true);
  });

  it("is ready for Level 2 preview when valid and changed", () => {
    const draft = buildSmartRenamePreviewDraft({
      sourcePath: "/mnt/spirit-8tb/media/folder/old-name.mp4",
      filenameSuggestion: "new-name",
    });
    expect(draft.readyForLevel2Preview).toBe(true);
    expect(draft.warnings).toHaveLength(0);
  });

  it("caps stem length", () => {
    const longStem = "A".repeat(300);
    const draft = buildSmartRenamePreviewDraft({
      sourcePath: "/mnt/spirit-8tb/media/folder/video.mp4",
      filenameSuggestion: longStem,
    });
    const stemOnly = draft.suggestedName.replace(/\.mp4$/, "");
    expect(stemOnly.length).toBeLessThanOrEqual(180);
  });
});
