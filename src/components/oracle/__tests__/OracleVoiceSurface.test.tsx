import { render, renderHook, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { OracleVoiceSurface } from "@/components/oracle/OracleVoiceSurface";
import { useSpiritModeRuntime } from "@/hooks/useSpiritModeRuntime";

vi.mock("@/components/chat/VoiceControl", () => ({
  VoiceControl: () => <div data-testid="oracle-voice-output-stub" />,
}));

vi.mock("@/lib/hooks/useMounted", () => ({
  useMounted: () => true,
}));

describe("OracleVoiceSurface", () => {
  it("mounts voice-first Oracle chrome without SpiritChat or Voice on/off copy", () => {
    render(<OracleVoiceSurface />);

    expect(screen.getByTestId("oracle-voice-controls")).toBeInTheDocument();
    expect(screen.queryByTestId("mock-spirit-chat")).toBeNull();

    expect(screen.queryByText(/Voice on/i)).toBeNull();
    expect(screen.queryByText(/Voice off/i)).toBeNull();

    expect(screen.getByRole("region", { name: /oracle session/i })).toBeInTheDocument();
    expect(screen.getByTestId("oracle-voice-status-card")).toBeInTheDocument();
  });

  it("useSpiritModeRuntime oracle wiring (matches OracleVoiceSurface) exposes runtimeSurface oracle", () => {
    const { result } = renderHook(() =>
      useSpiritModeRuntime({
        runtimeSurface: "oracle",
        persistenceEnabled: false,
        threadRuntime: {
          activeModelProfileId: "normal-peer",
          setActiveModelProfile: async () => {},
        },
      }),
    );
    expect(result.current.requestBodyModeFields.runtimeSurface).toBe("oracle");
    expect(result.current.runtimeSurface).toBe("oracle");
  });
});
