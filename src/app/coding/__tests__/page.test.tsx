import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import CodingPage from "@/app/coding/page";

const navMock = vi.hoisted(() => ({ path: "/coding" }));

vi.mock("next/navigation", () => ({
  usePathname: () => navMock.path,
}));

describe("CodingPage", () => {
  it("renders the clean coding cockpit shell for /coding", () => {
    render(<CodingPage />);

    expect(screen.getByRole("heading", { level: 1, name: "Coding" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Spirit app desktop navigation" }))
      .toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Task Composer" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Diagnostics" })).not.toBeInTheDocument();
    expect(screen.queryByText("Evidence trail and logs")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Diagnostics" })).toHaveAttribute(
      "href",
      "/proxy-backend",
    );
  });
});
