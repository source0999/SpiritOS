// ── spirit-chat-request-body — JSON validation (client-safe; no server-only) ────
import type { UIMessage } from "ai";

import type { SpiritRuntimeSurface } from "@/lib/spirit/spirit-runtime-surface";
import {
  DEFAULT_MODEL_PROFILE_ID,
  type ModelProfileId,
} from "@/lib/spirit/model-profile.types";
import { isModelProfileId } from "@/lib/spirit/model-profiles";

export class SpiritRequestValidationError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "SpiritRequestValidationError";
  }
}

export const SPIRIT_PERSONALIZATION_SUMMARY_MAX = 1500;
export const SPIRIT_RESEARCH_PLAN_SUMMARY_MAX = 4000;

export type SpiritChatRequestBody = {
  messages: UIMessage[];
  modelProfileId: ModelProfileId;
  /** Optional: `/oracle` passes `"oracle"` for ORACLE_OLLAMA_MODEL lane. */
  runtimeSurface: SpiritRuntimeSurface;
  /** Optional local profile slice; server validates length + type */
  personalizationSummary?: string;
  /** Prompt 10B — extra deliberation + modest token bump */
  deepThinkEnabled: boolean;
  /**
   * Researcher only: when true, skip OpenAI web prefetch. Default false (web ON).
   * Legacy clients sent `webSearchRequested`; we map `webSearchRequested: false` → opt-out true.
   */
  webSearchOptOut: boolean;
  /** Teacher-only: opt-in OpenAI web prefetch for current-data prompts. */
  teacherWebSearchEnabled: boolean;
  /** Optional approved research plan text (Stage 5 stub). */
  researchPlanSummary?: string;
};

function assertMessagesShape(raw: unknown[]): void {
  for (let i = 0; i < raw.length; i++) {
    const m = raw[i];
    if (!m || typeof m !== "object") {
      throw new SpiritRequestValidationError(400, "Each message must be an object");
    }
    const msg = m as Record<string, unknown>;
    if (typeof msg.role !== "string" || msg.role.length === 0) {
      throw new SpiritRequestValidationError(
        400,
        "Each message must have a non-empty string role",
      );
    }
    if (!Array.isArray(msg.parts)) {
      throw new SpiritRequestValidationError(
        400,
        "Each message must include a parts array",
      );
    }
  }
}

function normalizeModelProfileId(raw: unknown): ModelProfileId {
  if (raw === undefined || raw === null) return DEFAULT_MODEL_PROFILE_ID;
  if (isModelProfileId(raw)) return raw;
  return DEFAULT_MODEL_PROFILE_ID;
}

function normalizeRuntimeSurface(raw: unknown): SpiritRuntimeSurface {
  if (raw === "oracle") return "oracle";
  return "chat";
}

function normalizeBool(raw: unknown, field: string, defaultVal: boolean): boolean {
  if (raw === undefined || raw === null) return defaultVal;
  if (raw === true) return true;
  if (raw === false) return false;
  throw new SpiritRequestValidationError(400, `${field} must be a boolean`);
}

/** Prefer explicit opt-out; else map deprecated `webSearchRequested` (inverted). */
function normalizeWebSearchOptOut(record: Record<string, unknown>): boolean {
  if (typeof record.webSearchOptOut === "boolean") return record.webSearchOptOut;
  if (typeof record.webSearchRequested === "boolean") {
    return !record.webSearchRequested;
  }
  return false;
}

function normalizePersonalizationSummary(raw: unknown): string | undefined {
  if (raw === undefined || raw === null) return undefined;
  if (typeof raw !== "string") {
    throw new SpiritRequestValidationError(
      400,
      "personalizationSummary must be a string when provided",
    );
  }
  const t = raw.trim();
  if (!t) return undefined;
  if (t.length > SPIRIT_PERSONALIZATION_SUMMARY_MAX) {
    throw new SpiritRequestValidationError(
      400,
      `personalizationSummary exceeds ${SPIRIT_PERSONALIZATION_SUMMARY_MAX} characters`,
    );
  }
  return t;
}

function normalizeResearchPlanSummary(raw: unknown): string | undefined {
  if (raw === undefined || raw === null) return undefined;
  if (typeof raw !== "string") {
    throw new SpiritRequestValidationError(400, "researchPlanSummary must be a string when provided");
  }
  const t = raw.trim();
  if (!t) return undefined;
  if (t.length > SPIRIT_RESEARCH_PLAN_SUMMARY_MAX) {
    throw new SpiritRequestValidationError(
      400,
      `researchPlanSummary exceeds ${SPIRIT_RESEARCH_PLAN_SUMMARY_MAX} characters`,
    );
  }
  return t;
}

/** Validates POST JSON for /api/spirit (messages + optional modelProfileId). */
export function parseSpiritChatRequestBody(body: unknown): SpiritChatRequestBody {
  if (!body || typeof body !== "object") {
    throw new SpiritRequestValidationError(400, "Request body must be an object");
  }

  const record = body as Record<string, unknown>;
  const maybeMessages = record.messages;

  if (!Array.isArray(maybeMessages)) {
    throw new SpiritRequestValidationError(400, "Request body must include messages[]");
  }

  if (maybeMessages.length === 0) {
    throw new SpiritRequestValidationError(400, "messages[] cannot be empty");
  }

  assertMessagesShape(maybeMessages);

  const modelProfileId = normalizeModelProfileId(record.modelProfileId);
  const runtimeSurface = normalizeRuntimeSurface(record.runtimeSurface);
  const personalizationSummary = normalizePersonalizationSummary(
    record.personalizationSummary,
  );
  const deepThinkEnabled = normalizeBool(record.deepThinkEnabled, "deepThinkEnabled", false);
  const webSearchOptOut = normalizeWebSearchOptOut(record);
  const teacherWebSearchEnabled = normalizeBool(
    record.teacherWebSearchEnabled,
    "teacherWebSearchEnabled",
    true,
  );
  const researchPlanSummary = normalizeResearchPlanSummary(record.researchPlanSummary);

  return {
    messages: maybeMessages as UIMessage[],
    modelProfileId,
    runtimeSurface,
    personalizationSummary,
    deepThinkEnabled,
    webSearchOptOut,
    teacherWebSearchEnabled,
    researchPlanSummary,
  };
}
