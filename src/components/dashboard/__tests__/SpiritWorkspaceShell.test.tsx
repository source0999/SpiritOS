import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import SpiritWorkspaceShell from "@/components/dashboard/SpiritWorkspaceShell";

vi.mock("@/components/chat/SpiritChat", () => ({
  SpiritChat: () => <div data-testid="spirit-chat-mock" />,
}));

describe("SpiritWorkspaceShell", () => {
  it("mounts chat workspace shell with SpiritChat", () => {
    const { container } = render(<SpiritWorkspaceShell />);
    expect(screen.getByTestId("spirit-chat-mock")).toBeInTheDocument();
    expect(container.querySelector('[data-layout="spirit-workspace"]')).toBeTruthy();
  });
});
