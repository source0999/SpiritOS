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
    expect(screen.getByRole("complementary", { name: "Coding chats" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "New chat" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Task Composer" })).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "Review pane" })).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Describe what you want SpiritOS to change."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start coding" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy current task diagnostics" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Reversible trial runner" })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Trial category" })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Trial count" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "10" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run reversible trial suite" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Diagnostics" })).not.toBeInTheDocument();
    expect(screen.queryByText("Evidence trail and logs")).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Diagnostics" })).not.toBeInTheDocument();
  });
});
