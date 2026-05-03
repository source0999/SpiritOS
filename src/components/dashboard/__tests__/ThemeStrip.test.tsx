import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ThemeStrip } from "../ThemeStrip";

// Mock the theme hook
vi.mock("@/theme/useSpiritTheme", () => ({
  useSpiritTheme: vi.fn(() => ({
    theme: "dark-node",
    setTheme: vi.fn(),
  })),
}));

describe("ThemeStrip", () => {
  it("renders all three theme options", () => {
    render(<ThemeStrip />);

    expect(screen.getByText("Slate")).toBeInTheDocument();
    expect(screen.getByText("Node")).toBeInTheDocument();
    expect(screen.getByText("Violet")).toBeInTheDocument();
  });

  it("highlights the active theme", () => {
    render(<ThemeStrip />);

    const activeButton = screen.getByText("Node");
    expect(activeButton).toHaveClass("text-[color:var(--spirit-accent-strong)]");
  });
});
