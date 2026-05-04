import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import type { ReactNode } from "react";
import SpiritDashboardHome from "../SpiritDashboardHome";

vi.mock("@/components/dashboard/SpiritDiagnosticsLive", () => ({
  SpiritDiagnosticsLive: () => <div data-testid="diag-stub" />,
}));

vi.mock("@/theme/useSpiritTheme", () => ({
  useSpiritTheme: vi.fn(() => ({
    theme: "dark-node",
    setTheme: vi.fn(),
  })),
}));

const navMock = vi.hoisted(() => ({ path: "/" }));

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

describe("SpiritDashboardHome", () => {
  beforeEach(() => {
    navMock.path = "/";
  });

  it("routes Quick Chat Core and Quarantine Lab CTAs honestly", () => {
    render(<SpiritDashboardHome />);

    const chat = screen.getByRole("link", { name: /^open chat$/i });
    expect(chat).toHaveAttribute("href", "/chat");

    const q = screen.getByRole("link", { name: /^open quarantine$/i });
    expect(q).toHaveAttribute("href", "/quarantine");
  });

  it("exposes ThemeStrip Slate / Node / Violet in the header", () => {
    render(<SpiritDashboardHome />);

    expect(screen.getByRole("button", { name: /^Slate$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Node$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Violet$/i })).toBeInTheDocument();
  });
});
