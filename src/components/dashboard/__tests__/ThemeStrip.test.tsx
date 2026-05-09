import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ThemeStrip } from "../ThemeStrip";
import { SPIRIT_PALETTES, DEFAULT_THEME_ID } from "@/theme/spiritPalettes";
import { useSpiritTheme } from "@/theme/useSpiritTheme";

const mockSetTheme = vi.fn();

vi.mock("@/theme/useSpiritTheme", () => ({
  useSpiritTheme: vi.fn(() => ({
    theme: DEFAULT_THEME_ID,
    setTheme: mockSetTheme,
  })),
}));

describe("ThemeStrip", () => {
  beforeEach(() => {
    mockSetTheme.mockClear();
  });

  it("renders one control per registry palette (add palette = add button, no ThemeStrip edit)", () => {
    render(<ThemeStrip />);
    for (const p of SPIRIT_PALETTES) {
      expect(
        screen.getByRole("button", { name: new RegExp(`${p.label} palette`, "i") }),
      ).toBeInTheDocument();
    }
    expect(SPIRIT_PALETTES.length).toBeGreaterThan(0);
  });

  it("uses frozen-water as the active palette when the hook says so", () => {
    render(<ThemeStrip />);
    const ice = SPIRIT_PALETTES.find((p) => p.id === DEFAULT_THEME_ID)!;
    const btn = screen.getByRole("button", { name: new RegExp(`${ice.label} palette`, "i") });
    expect(btn).toHaveAttribute("aria-pressed", "true");
  });

  it("clicking another palette calls setTheme with that id", () => {
    render(<ThemeStrip />);
    const sky = SPIRIT_PALETTES.find((p) => p.id === "deep-sky")!;
    fireEvent.click(
      screen.getByRole("button", { name: new RegExp(`${sky.label} palette`, "i") }),
    );
    expect(mockSetTheme).toHaveBeenCalledWith("deep-sky");
  });

  it("highlights the active palette from the hook", () => {
    vi.mocked(useSpiritTheme).mockReturnValueOnce({
      theme: "alice-seagrass",
      setTheme: mockSetTheme,
    });
    render(<ThemeStrip />);
    const sea = SPIRIT_PALETTES.find((p) => p.id === "alice-seagrass")!;
    const btn = screen.getByRole("button", { name: new RegExp(`${sea.label} palette`, "i") });
    expect(btn).toHaveAttribute("aria-pressed", "true");
    expect(btn).toHaveClass("text-[color:var(--spirit-accent-strong)]");
  });
});
