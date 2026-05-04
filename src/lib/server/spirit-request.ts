import "server-only";

import type { UIMessage } from "ai";

import { ApiError } from "@/lib/server/api-errors";
import {
  parseSpiritChatRequestBody,
  SpiritRequestValidationError,
} from "@/lib/spirit/spirit-chat-request-body";
import type { ModelProfileId } from "@/lib/spirit/model-profile.types";

import type { SpiritRuntimeSurface } from "@/lib/spirit/spirit-runtime-surface";

export type SpiritRequestBody = {
  messages: UIMessage[];
  modelProfileId: ModelProfileId;
  runtimeSurface: SpiritRuntimeSurface;
  personalizationSummary?: string;
  deepThinkEnabled: boolean;
  webSearchOptOut: boolean;
  teacherWebSearchEnabled: boolean;
  researchPlanSummary?: string;
};

export async function readSpiritRequest(req: Request): Promise<SpiritRequestBody> {
  let body: unknown;

  try {
    body = await req.json();
  } catch {
    throw new ApiError(400, "Invalid JSON body");
  }

  try {
    return parseSpiritChatRequestBody(body);
  } catch (e) {
    if (e instanceof SpiritRequestValidationError) {
      throw new ApiError(e.status, e.message);
    }
    throw e;
  }
}
