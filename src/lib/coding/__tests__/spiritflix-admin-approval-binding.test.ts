import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { resolveSpiritFlixAdminApprovalBinding } from "../spiritflix-admin-approval-binding";
import { setSpiritFlixManualTagsForItem } from "@/lib/spiritflix/manual-tags";

describe("SpiritFlix exact administrative approval bindings", () => {
  let root: string;
  let previousTagRoot: string | undefined;
  let previousModelRoot: string | undefined;
  let previousRescanModelLimit: string | undefined;
  let previousRescanVideoLimit: string | undefined;
  let previousRescanContext: string | undefined;
  let previousRescanCpuSet: string | undefined;
  let previousRescanThreads: string | undefined;

  beforeEach(async () => {
    root = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-approval-binding-"));
    previousTagRoot = process.env.SPIRITFLIX_MANUAL_TAG_ROOT;
    previousModelRoot = process.env.SPIRITFLIX_MANUAL_MODEL_ROOT;
    previousRescanModelLimit = process.env.SPIRITFLIX_SMART_RESCAN_MODEL_LIMIT;
    previousRescanVideoLimit = process.env.SPIRITFLIX_SMART_RESCAN_VIDEO_LIMIT;
    previousRescanContext = process.env.SPIRITFLIX_FACE_ORGANIZER_CTX_ID;
    previousRescanCpuSet = process.env.SPIRITFLIX_FACE_ORGANIZER_CPUSET;
    previousRescanThreads = process.env.SPIRITFLIX_FACE_ORGANIZER_THREADS;
    process.env.SPIRITFLIX_MANUAL_TAG_ROOT = path.join(root, "tags");
    process.env.SPIRITFLIX_MANUAL_MODEL_ROOT = path.join(root, "models");
  });

  afterEach(async () => {
    if (previousTagRoot === undefined) delete process.env.SPIRITFLIX_MANUAL_TAG_ROOT;
    else process.env.SPIRITFLIX_MANUAL_TAG_ROOT = previousTagRoot;
    if (previousModelRoot === undefined) delete process.env.SPIRITFLIX_MANUAL_MODEL_ROOT;
    else process.env.SPIRITFLIX_MANUAL_MODEL_ROOT = previousModelRoot;
    if (previousRescanModelLimit === undefined) delete process.env.SPIRITFLIX_SMART_RESCAN_MODEL_LIMIT;
    else process.env.SPIRITFLIX_SMART_RESCAN_MODEL_LIMIT = previousRescanModelLimit;
    if (previousRescanVideoLimit === undefined) delete process.env.SPIRITFLIX_SMART_RESCAN_VIDEO_LIMIT;
    else process.env.SPIRITFLIX_SMART_RESCAN_VIDEO_LIMIT = previousRescanVideoLimit;
    if (previousRescanContext === undefined) delete process.env.SPIRITFLIX_FACE_ORGANIZER_CTX_ID;
    else process.env.SPIRITFLIX_FACE_ORGANIZER_CTX_ID = previousRescanContext;
    if (previousRescanCpuSet === undefined) delete process.env.SPIRITFLIX_FACE_ORGANIZER_CPUSET;
    else process.env.SPIRITFLIX_FACE_ORGANIZER_CPUSET = previousRescanCpuSet;
    if (previousRescanThreads === undefined) delete process.env.SPIRITFLIX_FACE_ORGANIZER_THREADS;
    else process.env.SPIRITFLIX_FACE_ORGANIZER_THREADS = previousRescanThreads;
    await fs.rm(root, { recursive: true, force: true });
  });

  it("binds exact tag values, item/path identity, and changes when current state drifts", async () => {
    const mutation = {
      itemId: "video-1",
      filePath: "/media/models/video-1.mkv",
      manualTags: ["Solo", "curvy"],
    };
    const before = await resolveSpiritFlixAdminApprovalBinding("manual-tags", mutation);
    expect(before.plan.mutation).toEqual(mutation);
    expect(before.plan.expected_current_state_hash).toMatch(/^[a-f0-9]{64}$/);
    expect(before.plan.expected_result_contract_hash).toMatch(/^[a-f0-9]{64}$/);

    await setSpiritFlixManualTagsForItem({
      itemId: "video-1",
      filePath: "/media/models/video-1.mkv",
      manualTags: ["different"],
    });
    const after = await resolveSpiritFlixAdminApprovalBinding("manual-tags", mutation);
    expect(after.plan.expected_current_state_hash).not.toBe(before.plan.expected_current_state_hash);
  });

  it("binds the model identity and complete known-model set instead of only a field label", async () => {
    const binding = await resolveSpiritFlixAdminApprovalBinding("manual-model", {
      itemId: "video-2",
      filePath: "/media/models/video-2.mkv",
      modelName: "Sava Schultz",
      knownModelNames: ["Sava Schultz", "Sava-Schultz", "Sava_Schultz"],
    });
    expect(binding.plan.mutation).toEqual({
      itemId: "video-2",
      filePath: "/media/models/video-2.mkv",
      modelName: "Sava Schultz",
      knownModelNames: ["Sava Schultz", "Sava-Schultz", "Sava_Schultz"],
    });
  });

  it("binds the full face-learning request and related item identities", async () => {
    const mutation = {
      itemId: "video-face",
      filePath: "/media/models/video-face.mkv",
      modelName: "Sava Schultz",
      sidecarPath: "/media/models/video-face.face-meta.json",
      faceGuess: { name: "Sava", confidence: 0.91 },
      relatedItems: [
        { itemId: "video-related-1", filePath: "/media/models/related-1.mkv" },
        { itemId: "video-related-2" },
      ],
    };
    const binding = await resolveSpiritFlixAdminApprovalBinding("face-learning", mutation);
    expect(binding.plan.mutation).toEqual(mutation);
    expect(binding.target).toBe("spiritflix:videos:video-face:face-learning");
  });

  it("binds the complete server-owned rescan configuration", async () => {
    process.env.SPIRITFLIX_SMART_RESCAN_MODEL_LIMIT = "17";
    process.env.SPIRITFLIX_SMART_RESCAN_VIDEO_LIMIT = "23";
    process.env.SPIRITFLIX_FACE_ORGANIZER_CTX_ID = "ctx-production";
    process.env.SPIRITFLIX_FACE_ORGANIZER_CPUSET = "4,5";
    process.env.SPIRITFLIX_FACE_ORGANIZER_THREADS = "3";

    const binding = await resolveSpiritFlixAdminApprovalBinding("library-smart-rescan", {});
    expect(binding.plan.mutation).toEqual({
      runner: "face-organizer",
      version: 2,
      source: "/mnt/spirit-8tb/media/yes",
      modelLimit: 17,
      videoLimit: 23,
      contextId: "ctx-production",
      cpuSet: "4,5",
      threads: 3,
    });
  });

  it("rejects unbound extra fields", async () => {
    await expect(resolveSpiritFlixAdminApprovalBinding("manual-tags", {
      itemId: "video-1",
      manualTags: ["solo"],
      unboundOverride: true,
    })).rejects.toThrow("spiritflix_admin_manual_tags_fields_invalid");
  });
});
