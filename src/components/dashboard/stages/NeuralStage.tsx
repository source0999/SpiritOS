"use client";

// ── NeuralStage - DEPRECATED: root no longer mounts this; Neural isn’t a “stage”.
// > Legacy lazy boundary kept so git blame doesn’t murder us mid-migration.
// ── Was: lazy boundary: pulls in SpiritChat + AI SDK only when selected ────────
import { SpiritChat } from "@/components/chat/SpiritChat";

export default function NeuralStage() {
  return (
    <SpiritChat variant="embedded" footerHint="Same wire as `/chat`" />
  );
}
