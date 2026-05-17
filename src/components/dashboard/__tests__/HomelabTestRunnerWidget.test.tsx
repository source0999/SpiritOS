/// <reference types="vitest/globals" />

import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { HomelabTestRunnerWidget } from "../HomelabTestRunnerWidget";

const fetchMock = vi.fn();

function mockJsonResponse(body: unknown, init?: ResponseInit): Response {
  return {
    ok: init?.status ? init.status >= 200 && init.status < 300 : true,
    status: init?.status ?? 200,
    json: async () => body,
  } as Response;
}

describe("HomelabTestRunnerWidget", () => {
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("runs a read-only runner profile through the coding self-tests route", async () => {
    fetchMock.mockResolvedValueOnce(
      mockJsonResponse({
        applied_anything: false,
        mode: "dry_run",
        profile: "proxy-smoke",
        recommendation: "ready for next increment",
        result: "pass",
        smoke_harness: {
          summary: { failed: 0, passed: 3, skipped: 0 },
        },
      }),
    );

    render(<HomelabTestRunnerWidget />);

    fireEvent.click(screen.getByRole("button", { name: /proxy smoke/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/v1/coding/self-tests/run",
        expect.objectContaining({
          body: JSON.stringify({ mode: "dry_run", profile: "proxy-smoke" }),
          method: "POST",
        }),
      );
    });
    expect(await screen.findByText(/proxy-smoke: pass/i)).toBeInTheDocument();
    expect(screen.getAllByText(/ready for next increment/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/"profile": "proxy-smoke"/i)).toBeInTheDocument();
  });

  it("runs the Cartographer safety profile as a read-only manual check", async () => {
    fetchMock.mockResolvedValueOnce(
      mockJsonResponse({
        applied_anything: false,
        checks: {
          pytest_passed: true,
          no_unapproved_writes: true,
          no_unapproved_commits: true,
          no_unapproved_pushes: true,
        },
        mode: "dry_run",
        profile: "cartographer-safety",
        recommendation: "ready for next increment",
        result: "pass",
      }),
    );

    render(<HomelabTestRunnerWidget />);

    fireEvent.click(screen.getByRole("button", { name: /cartographer safety/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/v1/coding/self-tests/run",
        expect.objectContaining({
          body: JSON.stringify({ mode: "dry_run", profile: "cartographer-safety" }),
          method: "POST",
        }),
      );
    });
    expect(await screen.findByText(/cartographer-safety: pass/i)).toBeInTheDocument();
    expect(screen.getByText(/"profile": "cartographer-safety"/i)).toBeInTheDocument();
  });

  it("asks before running bounded Scout search smoke", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValueOnce(false);
    render(<HomelabTestRunnerWidget />);

    fireEvent.click(screen.getByRole("button", { name: /search smoke/i }));

    expect(confirm).toHaveBeenCalledWith(expect.stringContaining("bounded discovery job"));
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("renders route errors from Source Proxy", async () => {
    fetchMock.mockResolvedValueOnce(
      mockJsonResponse(
        { error: "SPIRIT_CODING_USE_PROXY is not true" },
        { status: 409 },
      ),
    );

    render(<HomelabTestRunnerWidget />);

    fireEvent.click(screen.getByRole("button", { name: /scout smoke/i }));

    expect(
      await screen.findByText("SPIRIT_CODING_USE_PROXY is not true"),
    ).toBeInTheDocument();
  });

  it("counts runner checks when profile summaries do not include pass totals", async () => {
    fetchMock.mockResolvedValueOnce(
      mockJsonResponse({
        applied_anything: false,
        checks: {
          health: { ok: true },
          source_candidates: { ok: true },
          sources: { ok: true },
          discovery_jobs: { ok: true },
        },
        mode: "dry_run",
        profile: "scout-soak-snapshot",
        recommendation: "ready for next increment",
        result: "pass",
      }),
    );
    vi.spyOn(window, "confirm").mockReturnValueOnce(true);

    render(<HomelabTestRunnerWidget />);

    fireEvent.click(screen.getByRole("button", { name: /soak snapshot/i }));

    expect(await screen.findByText(/scout-soak-snapshot: pass/i)).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("requires confirmation before running the phase closeout profile", async () => {
    fetchMock.mockResolvedValueOnce(
      mockJsonResponse({
        applied_anything: false,
        checks: {
          proxy_closeout: true,
          runner_self_tests: true,
          scout_search_diagnostics: true,
          scout_smoke: true,
          scout_soak_snapshot: true,
          scout_source_gate: true,
        },
        mode: "dry_run",
        profile: "phase-4f-closeout",
        recommendation: "ready for 4F closeout",
        result: "pass",
      }),
    );
    const confirm = vi.spyOn(window, "confirm").mockReturnValueOnce(true);

    render(<HomelabTestRunnerWidget />);

    fireEvent.click(screen.getByRole("button", { name: /4f closeout/i }));

    expect(confirm).toHaveBeenCalledWith(expect.stringContaining("Phase 4F closeout"));
    expect(await screen.findByText(/phase-4f-closeout: pass/i)).toBeInTheDocument();
    expect(screen.getByText("6")).toBeInTheDocument();
  });

  it("requires confirmation before writing a Cartographer soak snapshot", async () => {
    fetchMock.mockResolvedValueOnce(
      mockJsonResponse({
        applied_anything: false,
        checks: {
          snapshot_log_only: true,
          head_changed: false,
        },
        mode: "dry_run",
        profile: "cartographer-soak-snapshot",
        recommendation: "ready for next increment",
        result: "pass",
      }),
    );
    const confirm = vi.spyOn(window, "confirm").mockReturnValueOnce(true);

    render(<HomelabTestRunnerWidget />);

    fireEvent.click(screen.getByRole("button", { name: /cartographer soak/i }));

    expect(confirm).toHaveBeenCalledWith(expect.stringContaining("Cartographer soak snapshot"));
    expect(await screen.findByText(/cartographer-soak-snapshot: pass/i)).toBeInTheDocument();
  });
});
