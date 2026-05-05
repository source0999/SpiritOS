import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OracleVoiceVisualizer } from "@/components/oracle/OracleVoiceVisualizer";

import type { OracleVisualState } from "@/lib/oracle/oracle-visual-state";

describe("OracleVoiceVisualizer", () => {
  const states: OracleVisualState[] = [
    "idle",
    "permission",
    "listening",
    "processing",
    "speaking",
    "error",
  ];

  it.each(states)("renders bars for state %s", (state) => {
    render(<OracleVoiceVisualizer state={state} />);
    const root = screen.getByTestId("oracle-voice-visualizer");
    expect(root.className).toContain(`oracle-viz--${state}`);
    expect(root.querySelectorAll(".oracle-viz__bar").length).toBeGreaterThan(10);
  });

  it("compact mode uses fewer bars than full", () => {
    const { rerender } = render(<OracleVoiceVisualizer state="idle" />);
    const full = screen.getByTestId("oracle-voice-visualizer").querySelectorAll(".oracle-viz__bar")
      .length;
    rerender(<OracleVoiceVisualizer state="idle" compact />);
    const compact = screen.getByTestId("oracle-voice-visualizer").querySelectorAll(".oracle-viz__bar")
      .length;
    expect(compact).toBeLessThan(full);
  });
});
