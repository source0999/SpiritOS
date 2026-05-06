// ── spirit-activity-events - high-level workspace signals (no chain-of-thought) ─
// > Prompt 10A: capped ring buffer for UI; nothing sensitive belongs here.

export const SPIRIT_ACTIVITY_EVENT_CAP = 20;

export type SpiritActivityKind =
  | "message_submitted"
  | "assistant_finished"
  | "mode_changed"
  | "voice_played"
  | "voice_error"
  | "workflow_step"
  | "copy_feedback";

export type SpiritActivityEvent = {
  id: string;
  at: number;
  kind: SpiritActivityKind;
  label: string;
};

export function appendSpiritActivityEvent(
  prev: SpiritActivityEvent[],
  event: Omit<SpiritActivityEvent, "id" | "at"> & { id?: string; at?: number },
): SpiritActivityEvent[] {
  const row: SpiritActivityEvent = {
    id: event.id ?? `evt_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
    at: event.at ?? Date.now(),
    kind: event.kind,
    label: event.label,
  };
  const next = [...prev, row];
  if (next.length <= SPIRIT_ACTIVITY_EVENT_CAP) return next;
  return next.slice(-SPIRIT_ACTIVITY_EVENT_CAP);
}
