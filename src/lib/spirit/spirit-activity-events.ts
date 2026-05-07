// ── spirit-activity-events - workspace / tool telemetry for UI (no secrets, no raw root) ─

export const SPIRIT_ACTIVITY_EVENT_CAP = 20;

export type SpiritToolActivityKind =
  | "workspace_list"
  | "workspace_read"
  | "workspace_tail"
  | "file_edit_proposed"
  | "file_edit_applied"
  | "dev_command_started"
  | "dev_command_completed"
  | "dev_command_failed"
  | "tool_blocked"
  | "tool_unavailable";

export type SpiritToolActivityStatus =
  | "pending"
  | "completed"
  | "failed"
  | "blocked"
  | "confirmation_required";

export type SpiritToolActivityCard = {
  id: string;
  timestamp: number;
  kind: SpiritToolActivityKind;
  label: string;
  status: SpiritToolActivityStatus;
  target?: string;
  summary?: string;
  safeMessage?: string;
};

export type SpiritAssistantMessageMetadata = {
  spiritToolActivity?: SpiritToolActivityCard[];
};

export type SpiritActivityKind =
  | "message_submitted"
  | "assistant_finished"
  | "mode_changed"
  | "voice_played"
  | "voice_error"
  | "workflow_step"
  | "copy_feedback"
  | SpiritToolActivityKind;

export type SpiritActivityEvent = {
  id: string;
  at: number;
  kind: SpiritActivityKind;
  label: string;
  status?: SpiritToolActivityStatus;
  target?: string;
  summary?: string;
  safeMessage?: string;
};

export function createSpiritToolActivityCard(
  partial: Omit<SpiritToolActivityCard, "id" | "timestamp"> & {
    id?: string;
    timestamp?: number;
  },
): SpiritToolActivityCard {
  const summary =
    partial.summary != null ? partial.summary.slice(0, 320) : undefined;
  const safeMessage =
    partial.safeMessage != null ? partial.safeMessage.slice(0, 320) : undefined;
  return {
    id: partial.id ?? `ta_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
    timestamp: partial.timestamp ?? Date.now(),
    kind: partial.kind,
    label: partial.label,
    status: partial.status,
    target: partial.target,
    summary,
    safeMessage,
  };
}

export function spiritToolCardToActivityEvent(card: SpiritToolActivityCard): Omit<
  SpiritActivityEvent,
  never
> {
  return {
    id: card.id,
    at: card.timestamp,
    kind: card.kind,
    label: card.label,
    status: card.status,
    target: card.target,
    summary: card.summary,
    safeMessage: card.safeMessage,
  };
}

export function appendSpiritActivityEvent(
  prev: SpiritActivityEvent[],
  event: Omit<SpiritActivityEvent, "id" | "at"> & { id?: string; at?: number },
): SpiritActivityEvent[] {
  const row: SpiritActivityEvent = {
    id: event.id ?? `evt_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
    at: event.at ?? Date.now(),
    kind: event.kind,
    label: event.label,
    status: event.status,
    target: event.target,
    summary: event.summary,
    safeMessage: event.safeMessage,
  };
  const next = [...prev, row];
  if (next.length <= SPIRIT_ACTIVITY_EVENT_CAP) return next;
  return next.slice(-SPIRIT_ACTIVITY_EVENT_CAP);
}
