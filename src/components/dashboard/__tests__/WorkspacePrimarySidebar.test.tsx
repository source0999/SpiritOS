import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { WorkspacePrimarySidebar } from "../WorkspacePrimarySidebar";

vi.mock("@/theme/useSpiritTheme", () => ({
  useSpiritTheme: vi.fn(() => ({
    theme: "alice-seagrass",
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

describe("WorkspacePrimarySidebar", () => {
  beforeEach(() => {
    navMock.path = "/";
  });

  it("separates dashboard home (/) from chat (/chat)", () => {
    render(<WorkspacePrimarySidebar />);

    const homeRails = screen.getAllByRole("link", {
      name: /dashboard home/i,
    });
    expect(homeRails.length).toBeGreaterThan(0);
    expect(homeRails.every((el) => el.getAttribute("href") === "/")).toBe(true);
    expect(
      screen.getAllByRole("link", { name: /chat workspace/i })[0],
    ).toHaveAttribute("href", "/chat");
  });

  it("keeps oracle route on the rail", () => {
    render(<WorkspacePrimarySidebar />);
    expect(screen.getAllByRole("link", { name: /^oracle$/i })[0]).toHaveAttribute(
      "href",
      "/oracle",
    );
  });

  it("does not link to /quarantine", () => {
    render(<WorkspacePrimarySidebar />);
    const quarantineLinks = screen.queryAllByRole("link", { name: /quarantine/i });
    expect(quarantineLinks.length).toBe(0);
  });
});
