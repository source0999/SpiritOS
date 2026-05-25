// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import DashboardError from "@/app/(dashboard)/error";
import DashboardLoading from "@/app/(dashboard)/loading";
import NotFound from "@/app/not-found";
import ProxyBackendPage from "@/app/proxy-backend/page";

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

vi.mock("@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav", () => ({
  DashboardDemoV4FloatingNav: () => (
    <nav aria-label="Spirit app desktop navigation" data-testid="shared-nav" />
  ),
}));

function expectSharedShell(container: HTMLElement) {
  expect(container.querySelector(".dashboard-demo-v4-route-shell")).not.toBeNull();
  expect(screen.getByTestId("shared-nav")).toBeInTheDocument();
}

describe("static and fallback route shell adoption", () => {
  it("/proxy-backend renders the shared shell without live wiring", () => {
    const { container } = render(<ProxyBackendPage />);

    expectSharedShell(container);
    expect(screen.getByRole("heading", { name: /backend console/i })).toBeInTheDocument();
    expect(screen.getAllByText(/planned, not wired/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/no explicit go means no wiring/i).length).toBeGreaterThan(0);
    expect(container.innerHTML).toContain("--shell-mobile-bottom-reserved-height");
  });

  it("not-found renders the shared shell and dashboard recovery link", () => {
    const { container } = render(<NotFound />);

    expectSharedShell(container);
    expect(screen.getByRole("heading", { name: /signal lost in the void/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /return to dashboard/i })).toHaveAttribute("href", "/");
    expect(container.innerHTML).toContain("--shell-mobile-bottom-reserved-height");
  });

  it("dashboard loading renders inside the shared shell", () => {
    const { container } = render(<DashboardLoading />);

    expectSharedShell(container);
    expect(screen.getByText(/booting spirit os/i)).toHaveAttribute("aria-busy", "true");
  });

  it("dashboard error renders retry inside the shared shell", () => {
    const reset = vi.fn();
    const error = Object.assign(new Error("Static shell failure"), {
      digest: "phase-5",
    });
    const { container } = render(<DashboardError error={error} reset={reset} />);

    expectSharedShell(container);
    expect(screen.getByRole("alert")).toHaveTextContent("Static shell failure");
    expect(screen.getByRole("alert")).toHaveTextContent("phase-5");
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
    expect(container.innerHTML).toContain("--shell-mobile-bottom-reserved-height");
  });
});
