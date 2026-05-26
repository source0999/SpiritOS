import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import type { ReactNode } from "react";

import SpiritTrinityChatShell from "@/components/chat/SpiritTrinityChatShell";

const navMock = vi.hoisted(() => ({ path: "/chat" }));

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

vi.mock("@/theme/useSpiritTheme", () => ({
  useSpiritTheme: vi.fn(() => ({
    theme: "frozen-water",
    setTheme: vi.fn(),
  })),
}));

vi.mock("@/components/dashboard/demo-v4/DashboardDemoV4ThemePicker", () => ({
  DashboardDemoV4ThemePicker: () => null,
}));

vi.mock("@/components/chat/SpiritChat", () => ({
  SpiritChat: (props: Record<string, unknown>) => (
    <div
      data-testid="live-spirit-chat"
      data-persistence={String(props.persistence)}
      data-show-thread-sidebar={String(props.showThreadSidebar)}
      data-chrome-variant={String(props.chromeVariant)}
    />
  ),
}));

const shellPath = resolve(process.cwd(), "src/components/chat/SpiritTrinityChatShell.tsx");
const chatPath = resolve(process.cwd(), "src/components/chat/SpiritChat.tsx");
const messagePath = resolve(process.cwd(), "src/components/chat/SpiritMessage.tsx");
const navPath = resolve(
  process.cwd(),
  "src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx",
);
const cssPath = resolve(process.cwd(), "src/styles/spirit-trinity-chat.css");
const dashboardCssPath = resolve(process.cwd(), "src/styles/dashboard-demo-v4.css");
const chatPagePath = resolve(process.cwd(), "src/app/chat/page.tsx");
const chatThreadListItemPath = resolve(
  process.cwd(),
  "src/components/chat/ChatThreadListItem.tsx",
);
const chatThreadSidebarPath = resolve(
  process.cwd(),
  "src/components/chat/ChatThreadSidebar.tsx",
);

describe("SpiritTrinityChatShell dashboard v4 visual integration", () => {
  beforeEach(() => {
    navMock.path = "/chat";
  });

  it("keeps the real persistent SpiritChat runtime mounted", async () => {
    render(<SpiritTrinityChatShell />);
    const chat = await screen.findByTestId("live-spirit-chat");
    expect(chat).toHaveAttribute(
      "data-persistence",
      "true",
    );
    expect(chat).toHaveAttribute(
      "data-show-thread-sidebar",
      "true",
    );
    expect(chat).toHaveAttribute(
      "data-chrome-variant",
      "trinity",
    );
  });

  it("uses dashboard v4 nav links and marks Chat active", () => {
    render(<SpiritTrinityChatShell />);

    const desktopNav = screen.getByRole("navigation", {
      name: /spirit app desktop navigation/i,
    });
    const mobileNav = screen.getByRole("navigation", {
      name: /spirit app mobile navigation/i,
    });

    for (const nav of [desktopNav, mobileNav]) {
      const hrefs = Array.from(nav.querySelectorAll("a")).map((a) =>
        a.getAttribute("href"),
      );
      expect(hrefs).toContain("/");
      expect(hrefs).toContain("/chat");
      expect(hrefs).toContain("/oracle");
      expect(within(nav).getByRole("link", { name: /^chat$/i })).toHaveAttribute(
        "aria-current",
        "page",
      );
    }
  });

  it("does not use the old md rail/mobile breakpoint split", () => {
    const src = readFileSync(shellPath, "utf8");
    const css = readFileSync(cssPath, "utf8");

    expect(src).toContain('desktopVariant="full-height"');
    expect(src).not.toContain("hidden md:flex");
    expect(src).not.toContain("md:hidden");
    expect(src).not.toContain("md:ml-16");
    expect(css).toContain("@media (min-width: 1024px)");
    expect(css).toContain(".spirit-trinity-live-chat");
  });

  it("uses a full-height desktop app rail for chat without centered floating behavior", () => {
    const navSrc = readFileSync(navPath, "utf8");
    const dashboardCss = readFileSync(dashboardCssPath, "utf8");
    const fullHeightBlock = dashboardCss.match(
      /\.dashboard-demo-v4-desktop-rail-full-height\s*\{[^}]+\}/,
    )?.[0];

    expect(navSrc).toContain('desktopVariant = "full-height"');
    expect(navSrc).toContain("dashboard-demo-v4-mobile-pill-nav");
    expect(dashboardCss).toContain("--ddv4-app-rail-width: 12.5rem");
    expect(fullHeightBlock).toBeTruthy();
    expect(fullHeightBlock).toContain("var(--ddv4-app-rail-width");
    expect(fullHeightBlock).toContain("height: 100dvh");
    expect(fullHeightBlock).toContain("min-height: 100dvh");
    expect(fullHeightBlock).toContain("transform: none");
    expect(fullHeightBlock).not.toContain("15rem");
    expect(fullHeightBlock).not.toContain("top: 50%");
    expect(fullHeightBlock).not.toContain("translateY(-50%)");
    expect(fullHeightBlock).not.toContain("height: min(33rem");
  });

  it("mounts trinity atmosphere depth layers in the live shell", () => {
    const src = readFileSync(shellPath, "utf8");
    expect(src).toContain("spirit-trinity-atmosphere");
    expect(src).toContain("spirit-trinity-atmosphere__base");
    expect(src).toContain("spirit-trinity-atmosphere__grid");
    expect(src).toContain("spirit-trinity-atmosphere__wash");
    expect(src).toContain("spirit-trinity-atmosphere__veil");
  });

  it("loads trinity chat stylesheet from the /chat route entry", () => {
    const pageSrc = readFileSync(chatPagePath, "utf8");
    expect(pageSrc).toContain("@/styles/dashboard-demo-v4.css");
    expect(pageSrc).toContain("@/styles/spirit-trinity-chat.css");
    expect(pageSrc).toContain("SpiritTrinityChatShell");
  });

  it("scopes decorative motion freeze to .spirit-trinity-chat only", () => {
    const css = readFileSync(cssPath, "utf8");
    expect(css).toMatch(/\.spirit-trinity-chat\s*\*\s*,/);
    expect(css).toMatch(/\.spirit-trinity-chat\s*\*::before/);
    expect(css).toMatch(/animation:\s*none\s*!important/);
  });

  it("defines Unified Liquid Input Language C hooks for shared glass controls", () => {
    const css = readFileSync(cssPath, "utf8");
    expect(css).toContain("Unified Liquid Input Language C");
    expect(css).toContain(".spirit-trinity-modal-glass");
    expect(css).toContain("[data-trinity-liquid=\"popout\"]");
    expect(css).toContain(".spirit-trinity-glass-select");
  });

  it("locks trinity workspace composer under Demo Composer Rebuild D (pod + dock lane)", () => {
    const css = readFileSync(cssPath, "utf8");
    expect(css).toContain("Composer Border Cleanup B");
    expect(css).toContain("Composer Border Cleanup C");
    expect(css).toContain("Demo Composer Rebuild D");
    const head = css.indexOf("Composer Border Cleanup B");
    expect(head).toBeGreaterThan(-1);
    const tail = css.slice(head);
    const stop = tail.indexOf("@media (prefers-reduced-motion");
    const section = stop === -1 ? tail : tail.slice(0, stop);
    expect(section).toContain(".spirit-trinity-chat .spirit-trinity-chat__composer-dock");
    expect(section).toContain(".spirit-trinity-chat .spirit-trinity-chat__composer-surface:focus-within");
    expect(section).toContain(".spirit-trinity-chat .spirit-trinity-chat__panel");
    expect(section).toContain(".spirit-trinity-command-pod");
    expect(section).not.toMatch(
      /\.spirit-trinity-chat \.spirit-trinity-chat__composer-surface:focus-within[\s\S]{0,900}border-color:\s*rgba\(255,\s*255,\s*255,\s*0\.[5-9]/,
    );
    expect(section).toMatch(
      /\.spirit-trinity-chat \.spirit-trinity-chat__composer-dock[\s\S]{0,420}border-top-color:\s*transparent/,
    );
    const demo = css.indexOf("Demo Composer Rebuild D");
    expect(demo).toBeGreaterThan(-1);
    const demoTail = css.slice(demo);
    expect(demoTail).toMatch(
      /\.spirit-trinity-chat__composer-dock\.spirit-trinity-liquid-dock[\s\S]{0,520}background:\s*transparent/,
    );
    expect(demoTail).toMatch(
      /\.spirit-trinity-command-pod[\s\S]{0,900}\.spirit-trinity-chat__composer-surface[\s\S]{0,420}border-color:\s*transparent/,
    );
  });

  it("guards against the pale full-page trinity background regression", () => {
    const css = readFileSync(cssPath, "utf8");
    expect(css).toContain(".spirit-trinity-atmosphere__base");
    expect(css).toContain(".spirit-trinity-atmosphere__grid");
    expect(css).toContain(".spirit-trinity-atmosphere__wash");
    expect(css).toContain(".spirit-trinity-atmosphere__veil");
    expect(css).not.toMatch(/saturate\(0%\)/);
    expect(css).not.toMatch(/grayscale\(/);
    expect(css).not.toContain("#b7bcc1");
    expect(css).not.toContain(".spirit-trinity-chat__bg-grid");
    expect(css).not.toContain(".spirit-trinity-chat__bg-vignette");
    expect(css).not.toContain("--spirit-bg: #e2e7ed");
    expect(css).not.toContain("--spirit-bg-soft: #f3f6f9");
    expect(css).not.toContain("--spirit-bg: #929ca7");
    expect(css).not.toContain("--spirit-bg-soft: #a5aeb7");
    expect(css).not.toContain("background: #eaecef");
    expect(css).not.toContain("background: #e2e7ed");
    expect(css).not.toContain("background: white");
    expect(css).not.toContain("background: #ffffff");
    expect(css).toContain("--ddv4-atmos-foundation");
    expect(css).toContain("--ddv4-atmos-wash");
    expect(css).toContain("var(--ddv4-atmos-wash)");
    expect(css).toContain("--ddv4-glass-bg");
  });

  it("keeps the composer visible while preserving mobile textarea safety", () => {
    const chatSrc = readFileSync(chatPath, "utf8");
    const css = readFileSync(cssPath, "utf8");

    expect(chatSrc).toContain("spirit-trinity-command-pod");
    expect(chatSrc).toContain("spirit-trinity-chat__composer-surface");
    expect(chatSrc).toContain("max-lg:text-base");
    expect(chatSrc).toContain("max-lg:max-h-[120px]");
    expect(chatSrc).not.toContain("placeholder:text-chalk/20");
    expect(chatSrc).not.toContain("placeholder:text-chalk/30");
    expect(chatSrc).toContain("placeholder:text-chalk/65");
    expect(css).toContain(".spirit-trinity-chat__composer-surface:focus-within");
    expect(css).toContain("rgba(30, 41, 59, 0.68)");
    expect(css).toContain("--chat-composer-max-width");
  });

  it("keeps trinity chat voice, composer, and message bubble hooks visible", () => {
    const chatSrc = readFileSync(chatPath, "utf8");
    const messageSrc = readFileSync(messagePath, "utf8");
    const css = readFileSync(cssPath, "utf8");

    expect(chatSrc).toContain("spirit-trinity-chat__composer-voice-control");
    expect(chatSrc).toContain("<VoiceControl");
    expect(chatSrc).toContain("onToggleAutoSpeak={tts.toggleAutoSpeakAssistant}");
    expect(chatSrc).toContain("onRequestVoiceCatalog={tts.refreshElevenLabsVoices}");
    expect(chatSrc).toContain("onElevenLabsVoiceChange={tts.setElevenLabsVoiceFromPicker}");
    expect(chatSrc).toContain("spirit-trinity-chat__composer-surface");
    expect(css).toContain(".spirit-trinity-chat__composer-surface");
    expect(messageSrc).toContain("data-role={message.role}");
    expect(css).toContain('.spirit-trinity-chat [data-role="assistant"] > div > div');
    expect(css).toContain('.spirit-trinity-chat [data-role="user"] > div > div');
  });

  it("keeps the chat nav routes production-only and avoids transcript wording", () => {
    const shellSrc = readFileSync(shellPath, "utf8");
    const chatSrc = readFileSync(chatPath, "utf8");

    expect(shellSrc).not.toContain("design-demo");
    expect(shellSrc).not.toContain("DemoChat");
    expect(chatSrc).not.toMatch(/\bTranscripts?\b/);
  });

  it("ships no debug ingest probes and wires nav vs sidebar separation hooks", () => {
    const shellSrc = readFileSync(shellPath, "utf8");
    const css = readFileSync(cssPath, "utf8");
    const listSrc = readFileSync(chatThreadListItemPath, "utf8");
    const sidebarSrc = readFileSync(chatThreadSidebarPath, "utf8");

    expect(shellSrc).not.toMatch(/localhost:7644|trinity-dom-css-probe|#region agent log/);
    expect(css).toContain("margin-block: 1.125rem");
    expect(css).toContain("calc(100% - 2.25rem)");
    expect(css).toContain(".spirit-trinity-live-chat");
    expect(css).toMatch(/\.spirit-trinity-live-chat[\s\S]*box-sizing:\s*border-box/);
    expect(css).toContain("--trinity-sidebar-glass");
    expect(css).toContain("--trinity-sidebar-border");
    expect(css).toContain("--chat-nav-thread-gutter");
    expect(css).toContain("margin-inline-start: var(--chat-nav-thread-gutter)");
    expect(listSrc).toContain("spirit-chat-thread-row");
    expect(listSrc).toContain("spirit-thread-row-shell");
    expect(sidebarSrc).toContain("spirit-trinity-sidebar--trinity");
    expect(sidebarSrc).not.toContain("spirit-sidebar-draft-card");
    expect(sidebarSrc).not.toContain("Draft · clears on first send");
    expect(sidebarSrc).toContain('data-sidebar-action="new-chat"');
    expect(sidebarSrc).toContain('data-sidebar-action="new-folder"');
  });
});
