"use client";

// ── NeuralStage — lazy boundary: pulls in SpiritChat + AI SDK only when selected ─
import { SpiritChat } from "@/components/chat/SpiritChat";

export default function NeuralStage() {
  return (
    <SpiritChat variant="embedded" footerHint="Same wire as `/chat`" />
  );
}
