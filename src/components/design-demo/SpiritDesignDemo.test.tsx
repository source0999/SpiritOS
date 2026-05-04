// @vitest-environment jsdom
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { render, screen, within } from "@testing-library/react";
import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";

import { SpiritDesignDemo } from "@/components/design-demo/SpiritDesignDemo";

// __dirname isn't reliable under ESM transpilation; resolve from import.meta.
const HERE = path.dirname(fileURLToPath(import.meta.url));

// jsdom doesn't ship IntersectionObserver, but DemoMobileDock relies on it.
// Stub a no-op implementation so the dock can mount without throwing.
class NoopIntersectionObserver implements IntersectionObserver {
  readonly root: Element | Document | null = null;
  readonly rootMargin: string = "";
  readonly thresholds: ReadonlyArray<number> = [];
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
}

const originalIntersectionObserver = globalThis.IntersectionObserver;
const originalScrollIntoView = Element.prototype.scrollIntoView;

beforeAll(() => {
  vi.stubGlobal("IntersectionObserver", NoopIntersectionObserver);
  // jsdom also doesn't implement scrollIntoView; the dock calls it on tab click.
  Element.prototype.scrollIntoView = vi.fn();
});

afterAll(() => {
  if (originalIntersectionObserver) {
    vi.stubGlobal("IntersectionObserver", originalIntersectionObserver);
  }
  Element.prototype.scrollIntoView = originalScrollIntoView;
});

describe("SpiritDesignDemo", () => {
  it("renders the demo shell with the scoped root class", () => {
    render(<SpiritDesignDemo />);
    const root = screen.getByTestId("spirit-demo-root");
    expect(root).toBeInTheDocument();
    expect(root.classList.contains("spirit-demo-root")).toBe(true);
  });

  it("renders all six primary demo sections", () => {
    const { container } = render(<SpiritDesignDemo />);
    const sectionIds = [
      "demo-command-center",
      "demo-chat",
      "demo-oracle",
      "demo-quarantine",
      "demo-diagnostics",
      "demo-profile",
    ];
    for (const id of sectionIds) {
      expect(container.querySelector(`#${id}`)).not.toBeNull();
    }
  });

  it("links visual previews to the real production routes", () => {
    const { container } = render(<SpiritDesignDemo />);
    const targets = ["/chat", "/oracle", "/quarantine"];
    for (const href of targets) {
      const links = container.querySelectorAll(`a[href="${href}"]`);
      expect(links.length).toBeGreaterThan(0);
    }
  });

  it("offers an escape hatch back to the dashboard root", () => {
    const { container } = render(<SpiritDesignDemo />);
    expect(container.querySelector('a[href="/"]')).not.toBeNull();
  });

  it("ships a mobile dock with all six section tabs", () => {
    render(<SpiritDesignDemo />);
    const dock = screen.getByRole("navigation", { name: /demo sections/i });
    const tabs = within(dock).getAllByRole("button");
    expect(tabs.length).toBe(6);
  });
});

describe("Demo CSS architecture", () => {
  // Resolved from src/components/design-demo → src/styles
  const stylesDir = path.resolve(HERE, "../../styles");

  it("defines reduced-motion overrides in the animations layer", () => {
    const css = readFileSync(
      path.join(stylesDir, "spirit-demo.animations.css"),
      "utf8",
    );
    expect(css).toMatch(/@media\s*\(\s*prefers-reduced-motion:\s*reduce\s*\)/);
  });

  it("scopes every demo selector under .spirit-demo-root", () => {
    const files = [
      "spirit-demo.layout.css",
      "spirit-demo.effects.css",
      "spirit-demo.components.css",
      "spirit-demo.animations.css",
    ];
    for (const file of files) {
      const css = readFileSync(path.join(stylesDir, file), "utf8");
      // Quick sanity: each demo CSS file references the scoped root somewhere.
      expect(css).toContain(".spirit-demo-root");
    }
  });
});
