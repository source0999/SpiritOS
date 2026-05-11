import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardDemoV4FloatingNav } from "./DashboardDemoV4FloatingNav";
import { SPIRIT_PALETTES } from "@/theme/spiritPalettes";
import { useSpiritTheme } from "@/theme/useSpiritTheme";

const mockSetTheme = vi.fn();
const navMock = vi.hoisted(() => ({ path: "/" }));

vi.mock("@/theme/useSpiritTheme", () => ({
  useSpiritTheme: vi.fn(() => ({
    theme: "frozen-water",
    setTheme: mockSetTheme,
  })),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => navMock.path,
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...rest
  }: {
    href: string;
    children: ReactNode;
    [key: string]: unknown;
  }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

function openThemePickerFromMobileNav() {
  const mobileNav = screen.getByRole("navigation", {
    name: /dashboard mobile navigation/i,
  });
  fireEvent.click(
    within(mobileNav).getByRole("button", {
      name: /open interface theme picker/i,
    }),
  );
}

describe("DashboardDemoV4ThemePicker", () => {
  beforeEach(() => {
    navMock.path = "/";
    mockSetTheme.mockClear();
    vi.mocked(useSpiritTheme).mockReturnValue({
      theme: "frozen-water",
      setTheme: mockSetTheme,
    });
  });

  it("opens the Interface picker from the floating nav palette button", () => {
    render(<DashboardDemoV4FloatingNav />);

    openThemePickerFromMobileNav();

    expect(
      screen.getByRole("dialog", { name: /interface theme picker/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^interface$/i })).toBeInTheDocument();
  });

  it("renders one card per palette and marks the active palette", () => {
    render(<DashboardDemoV4FloatingNav />);
    openThemePickerFromMobileNav();

    for (const palette of SPIRIT_PALETTES) {
      expect(
        screen.getByRole("button", { name: new RegExp(palette.label, "i") }),
      ).toBeInTheDocument();
    }

    const active = SPIRIT_PALETTES.find((palette) => palette.id === "frozen-water")!;
    expect(
      screen.getByRole("button", { name: new RegExp(active.label, "i") }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("selecting a palette calls setTheme and closes the picker", async () => {
    render(<DashboardDemoV4FloatingNav />);
    openThemePickerFromMobileNav();

    const target = SPIRIT_PALETTES.find((palette) => palette.id === "deep-sky")!;
    fireEvent.click(screen.getByRole("button", { name: new RegExp(target.label, "i") }));

    expect(mockSetTheme).toHaveBeenCalledWith("deep-sky");
    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: /interface theme picker/i })).not.toBeInTheDocument();
    });
  });

  it("Escape closes the picker", async () => {
    render(<DashboardDemoV4FloatingNav />);
    openThemePickerFromMobileNav();

    fireEvent.keyDown(document, { key: "Escape" });

    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: /interface theme picker/i })).not.toBeInTheDocument();
    });
  });

  it("clicking the backdrop closes the picker", async () => {
    render(<DashboardDemoV4FloatingNav />);
    openThemePickerFromMobileNav();

    fireEvent.click(screen.getAllByRole("button", { name: /close interface theme picker/i })[0]);

    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: /interface theme picker/i })).not.toBeInTheDocument();
    });
  });

  it("keeps the nav links rendered", () => {
    render(<DashboardDemoV4FloatingNav />);
    const desktopNav = screen.getByRole("navigation", {
      name: /dashboard desktop navigation/i,
    });
    const mobileNav = screen.getByRole("navigation", {
      name: /dashboard mobile navigation/i,
    });

    for (const nav of [desktopNav, mobileNav]) {
      const hrefs = Array.from(nav.querySelectorAll("a")).map((a) => a.getAttribute("href"));
      expect(hrefs).toContain("/");
      expect(hrefs).toContain("/chat");
      expect(hrefs).toContain("/coding");
      expect(hrefs).toContain("/oracle");
    }
  });
});
