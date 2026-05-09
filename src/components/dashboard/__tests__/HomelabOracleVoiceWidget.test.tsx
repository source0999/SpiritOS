import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { HomelabOracleVoiceWidget } from "@/components/dashboard/HomelabOracleVoiceWidget";

const origFetch = globalThis.fetch;

describe("HomelabOracleVoiceWidget", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ model: "test-model" }), { status: 200 }),
    );
  });

  afterEach(() => {
    globalThis.fetch = origFetch;
  });

  it("renders Oracle Voice copy and Open Oracle link", async () => {
    render(<HomelabOracleVoiceWidget />);
    expect(screen.getByRole("region", { name: /oracle voice/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^Oracle Voice$/i })).toBeInTheDocument();
    expect(screen.getByText(/Hands-free/i)).toBeInTheDocument();
    expect(screen.getByText(/Whisper backend/i)).toBeInTheDocument();
    expect(screen.getByText(/\/api\/tts/i)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText(/test-model/i)).toBeInTheDocument());
    const link = screen.getByRole("link", { name: /open oracle/i });
    expect(link).toHaveAttribute("href", "/oracle");
  });

  it("includes orb sprite and voice visualizer", () => {
    render(<HomelabOracleVoiceWidget />);
    expect(document.querySelector('[data-testid="oracle-orb-sprite"]')).not.toBeNull();
    expect(document.querySelector('[data-testid="oracle-voice-visualizer"]')).not.toBeNull();
  });
});
