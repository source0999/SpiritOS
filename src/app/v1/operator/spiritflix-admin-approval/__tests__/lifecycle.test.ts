import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { POST as issueAdminApproval } from "../route";
import { PUT as putVideoModel } from "@/app/api/spiritflix/videos/[itemId]/model/route";
import { createOperatorSession, revokeOperatorSession } from "@/lib/coding/operator-approval-session";

const ORIGIN = "https://operator.campaign.test";

describe("SpiritFlix admin authenticated operator lifecycle", () => {
  let modelRoot: string;
  let stateRoot: string;
  let previous: Record<string, string | undefined>;

  beforeEach(async () => {
    modelRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-admin-model-"));
    stateRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-admin-operator-state-"));
    await fs.chmod(stateRoot, 0o700);
    previous = {
      SPIRITFLIX_MANUAL_MODEL_ROOT: process.env.SPIRITFLIX_MANUAL_MODEL_ROOT,
      SPIRITOS_OPERATOR_ALLOWED_ORIGINS: process.env.SPIRITOS_OPERATOR_ALLOWED_ORIGINS,
      SPIRITOS_OPERATOR_E2E_MODE: process.env.SPIRITOS_OPERATOR_E2E_MODE,
      SPIRITOS_OPERATOR_E2E_SECRET: process.env.SPIRITOS_OPERATOR_E2E_SECRET,
      SPIRITOS_OPERATOR_E2E_STATE_PATH: process.env.SPIRITOS_OPERATOR_E2E_STATE_PATH,
    };
    process.env.SPIRITFLIX_MANUAL_MODEL_ROOT = modelRoot;
    process.env.SPIRITOS_OPERATOR_ALLOWED_ORIGINS = ORIGIN;
    process.env.SPIRITOS_OPERATOR_E2E_MODE = "true";
    process.env.SPIRITOS_OPERATOR_E2E_SECRET = "campaign-operator-test-only";
    process.env.SPIRITOS_OPERATOR_E2E_STATE_PATH = path.join(stateRoot, "session.json");
  });

  afterEach(async () => {
    for (const [key, value] of Object.entries(previous)) {
      if (value === undefined) delete process.env[key]; else process.env[key] = value;
    }
    await fs.rm(modelRoot, { recursive: true, force: true });
    await fs.rm(stateRoot, { recursive: true, force: true });
  });

  async function session() {
    return createOperatorSession(new Request(ORIGIN, { headers: { host: "operator.campaign.test", origin: ORIGIN } }), "campaign-operator-test-only");
  }

  function operatorRequest(sessionState: { csrf: string; id: string }, body: Record<string, unknown>) {
    return new Request(`${ORIGIN}/v1/operator/spiritflix-admin-approval`, {
      body: JSON.stringify(body),
      headers: {
        cookie: `spiritos_operator_approval=${sessionState.id}`,
        host: "operator.campaign.test",
        origin: ORIGIN,
      },
      method: "POST",
    });
  }

  it("uses one authenticated server-issued approval for preview, writer consumption, and replay rejection", async () => {
    const current = await session();
    const previewResponse = await issueAdminApproval(operatorRequest(current, {
      action: "preview", writer: "manual-model",
      mutation: { itemId: "video-1", modelName: "Sava Schultz" },
    }));
    expect(previewResponse.status).toBe(200);
    const preview = await previewResponse.json() as { preview: { generation: number; preview_id: string } };

    const approvalResponse = await issueAdminApproval(operatorRequest(current, {
      action: "approve", generation: preview.preview.generation, preview_id: preview.preview.preview_id,
    }));
    expect(approvalResponse.status).toBe(200);
    const issued = await approvalResponse.json() as { approval: { value: { approval_id: string } } };

    const writerResponse = await putVideoModel(new NextRequest("http://localhost/api/spiritflix/videos/video-1/model", {
      body: JSON.stringify({ approval_id: issued.approval.value.approval_id, itemId: "video-1", modelName: "Sava Schultz" }), method: "PUT",
    }), { params: Promise.resolve({ itemId: "video-1" }) });
    expect(writerResponse.status).toBe(200);

    const replay = await putVideoModel(new NextRequest("http://localhost/api/spiritflix/videos/video-1/model", {
      body: JSON.stringify({ approval_id: issued.approval.value.approval_id, itemId: "video-1", modelName: "Sava Schultz" }), method: "PUT",
    }), { params: Promise.resolve({ itemId: "video-1" }) });
    expect(replay.status).toBe(422);
  });

  it("rejects preview issuance after revocation", async () => {
    const current = await session();
    await revokeOperatorSession({ id: current.id, operator: current.operator, origin: ORIGIN, role: current.role });
    const response = await issueAdminApproval(operatorRequest(current, {
      action: "preview", writer: "manual-model",
      mutation: { itemId: "video-1", modelName: "Sava Schultz" },
    }));
    expect(response.status).toBe(403);
    await expect(response.json()).resolves.toEqual({ reason_code: "operator_session_revoked" });
  });
});
