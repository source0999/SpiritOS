import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchApprovedSpiritFlixAdminMutation } from "../approved-mutation-client";

describe("approved SpiritFlix production mutation client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("runs authenticated preview and issuance before forwarding the unchanged exact payload", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(Response.json({ preview: { generation: 7, preview_id: "preview-7" } }))
      .mockResolvedValueOnce(Response.json({ approval: { value: { approval_id: "approval-7" } } }))
      .mockResolvedValueOnce(Response.json({ record: { modelName: "Sava Schultz" } }));
    vi.stubGlobal("fetch", fetchMock);
    const mutation = {
      itemId: "video-1",
      filePath: "/media/model/video.mkv",
      modelName: "Sava Schultz",
      knownModelNames: ["Sava Schultz", "Sava-Schultz"],
    };

    const response = await fetchApprovedSpiritFlixAdminMutation(
      "manual-model",
      "/api/spiritflix/videos/video-1/model",
      mutation,
      { method: "PUT" },
    );

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual({
      action: "preview",
      mutation,
      writer: "manual-model",
    });
    expect(JSON.parse(String(fetchMock.mock.calls[1][1]?.body))).toEqual({
      action: "approve",
      generation: 7,
      preview_id: "preview-7",
    });
    expect(fetchMock.mock.calls[2][0]).toBe("/api/spiritflix/videos/video-1/model");
    expect(JSON.parse(String(fetchMock.mock.calls[2][1]?.body))).toEqual({
      ...mutation,
      approval_id: "approval-7",
    });
  });

  it("does not call a writer when authenticated issuance is unavailable", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(Response.json(
      { reason_code: "operator_session_missing" },
      { status: 403 },
    ));
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchApprovedSpiritFlixAdminMutation(
      "manual-tags",
      "/api/spiritflix/videos/video-1/tags",
      { itemId: "video-1", manualTags: ["solo"] },
      { method: "PUT" },
    )).rejects.toThrow("operator_session_missing");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
