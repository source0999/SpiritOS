import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { UIMessage } from "ai";

import { OracleSessionTranscript } from "@/components/oracle/OracleSessionTranscript";

function msg(id: string, role: "user" | "assistant", text: string): UIMessage {
  return { id, role, parts: [{ type: "text", text }] };
}

describe("OracleSessionTranscript", () => {
  it("renders user and oracle rows from live messages", () => {
    const messages: UIMessage[] = [
      msg("1", "assistant", "Hello from Oracle."),
      msg("2", "user", "Hi there"),
    ];
    render(<OracleSessionTranscript messages={messages} activityLine="Ready" />);
    const region = screen.getByRole("region", { name: /oracle session/i });
    expect(within(region).getByText("Hello from Oracle.")).toBeInTheDocument();
    expect(within(region).getByText("Hi there")).toBeInTheDocument();
    const roles = within(region).getAllByText(/^Oracle$/i);
    expect(roles.length).toBeGreaterThanOrEqual(1);
    expect(within(region).getByText(/^You$/i)).toBeInTheDocument();
  });

  it("shows empty copy when no messages", () => {
    render(<OracleSessionTranscript messages={[]} activityLine="Idle" />);
    expect(screen.getByText(/No messages yet/i)).toBeInTheDocument();
  });
});
