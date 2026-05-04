import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { WorkspaceDiagnosticsRail } from "../WorkspaceDiagnosticsRail";

vi.mock("@/components/dashboard/SpiritDiagnosticsLive", () => ({
  SpiritDiagnosticsLive: () => <div data-testid="diag-live-stub">stub</div>,
}));

const navMock = vi.hoisted(() => ({ path: "/" }));

vi.mock("next/navigation", () => ({
  usePathname: () => navMock.path,
}));

const LS_CHAT = "spirit:diagnosticsRailCollapsed:/chat";
const LS_DASH = "spirit:diagnosticsRailCollapsed:/";
const LS_DEFAULT = "spirit:diagnosticsRailCollapsed:default";
const LS_LEGACY = "spirit:diagnosticsRailCollapsed";

function clearDiagKeys() {
  for (const k of [LS_CHAT, LS_DASH, LS_DEFAULT, LS_LEGACY]) {
    try {
      window.localStorage.removeItem(k);
    } catch {
      /* jsdom */
    }
  }
}

describe("WorkspaceDiagnosticsRail", () => {
  beforeEach(() => {
    navMock.path = "/";
    clearDiagKeys();
  });

  function getDiagnosticsRail() {
    return screen.getByRole("complementary", { name: /^Diagnostics rail$/i });
  }

  it("defaults expanded on dashboard with Diagnostics panel + single toggle", async () => {
    render(<WorkspaceDiagnosticsRail />);

    const rail = getDiagnosticsRail();

    await waitFor(() => {
      expect(
        within(rail).getByRole("complementary", {
          name: /system diagnostics/i,
        }),
      ).toBeInTheDocument();
    });

    expect(within(rail).getByTestId("diag-live-stub")).toBeInTheDocument();
    expect(within(rail).getByText("Diagnostics")).toBeInTheDocument();
    expect(
      within(rail).getByRole("button", {
        name: /collapse diagnostics panel/i,
      }),
    ).toBeInTheDocument();

    expect(within(rail).getAllByRole("button")).toHaveLength(1);
  });

  it("defaults collapsed on /chat when no /chat localStorage key exists", async () => {
    navMock.path = "/chat";
    render(<WorkspaceDiagnosticsRail />);

    const rail = getDiagnosticsRail();

    await waitFor(() => {
      expect(
        within(rail).queryByRole("complementary", {
          name: /system diagnostics/i,
        }),
      ).toBeNull();
      expect(within(rail).queryByTestId("diag-live-stub")).toBeNull();
    });

    expect(
      within(rail).getByRole("button", { name: /expand diagnostics panel/i }),
    ).toBeInTheDocument();
    expect(within(rail).getAllByRole("button")).toHaveLength(1);
  });

  it("on / stays expanded even if /chat key says collapsed", async () => {
    window.localStorage.setItem(LS_CHAT, "true");
    navMock.path = "/";

    render(<WorkspaceDiagnosticsRail />);

    const rail = getDiagnosticsRail();

    await waitFor(() => {
      expect(
        within(rail).getByRole("complementary", {
          name: /system diagnostics/i,
        }),
      ).toBeInTheDocument();
    });
    expect(within(rail).getByTestId("diag-live-stub")).toBeInTheDocument();
    expect(
      within(rail).getByRole("button", { name: /collapse diagnostics panel/i }),
    ).toBeInTheDocument();
  });

  it("respects /chat-scoped localStorage when expanded on /chat", async () => {
    window.localStorage.setItem(LS_CHAT, "false");
    navMock.path = "/chat";

    render(<WorkspaceDiagnosticsRail />);

    const rail = getDiagnosticsRail();

    await waitFor(() => {
      expect(
        within(rail).getByRole("complementary", {
          name: /system diagnostics/i,
        }),
      ).toBeInTheDocument();
    });
    expect(within(rail).getByTestId("diag-live-stub")).toBeInTheDocument();
  });

  it("expanding /chat does not write the legacy global diagnostics key", async () => {
    navMock.path = "/chat";
    render(<WorkspaceDiagnosticsRail />);

    const rail = getDiagnosticsRail();

    await waitFor(() => {
      expect(
        within(rail).queryByRole("complementary", {
          name: /system diagnostics/i,
        }),
      ).toBeNull();
    });

    fireEvent.click(
      within(rail).getByRole("button", { name: /expand diagnostics panel/i }),
    );

    await waitFor(() => {
      expect(
        within(rail).getByRole("complementary", {
          name: /system diagnostics/i,
        }),
      ).toBeInTheDocument();
    });

    expect(window.localStorage.getItem(LS_LEGACY)).toBeNull();
    expect(window.localStorage.getItem(LS_CHAT)).toBe("false");
  });
});
