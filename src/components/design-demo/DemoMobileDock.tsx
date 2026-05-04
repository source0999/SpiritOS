"use client";

// ── DemoMobileDock — sticky bottom nav for demo sections (mobile-first) ──────
// > Hidden on lg+ (the desktop side rail takes over).
// > Smooth-scrolls to in-page section anchors. Active section reflected via
// > IntersectionObserver. Reduced-motion compliant (no smooth scroll override).
import { useEffect, useState, type ReactElement } from "react";

import {
  ActivityIcon,
  ChatIcon,
  FlaskIcon,
  HomeIcon,
  OrbIcon,
  UserIcon,
} from "./DemoIcons";

export type DemoSection = {
  id: string;
  label: string;
  shortLabel: string;
  Icon: (props: { size?: number }) => ReactElement;
};

export const DEMO_SECTIONS: DemoSection[] = [
  {
    id: "demo-command-center",
    label: "Command",
    shortLabel: "Home",
    Icon: HomeIcon,
  },
  { id: "demo-chat", label: "Chat", shortLabel: "Chat", Icon: ChatIcon },
  {
    id: "demo-oracle",
    label: "Oracle",
    shortLabel: "Oracle",
    Icon: OrbIcon,
  },
  {
    id: "demo-quarantine",
    label: "Lab",
    shortLabel: "Lab",
    Icon: FlaskIcon,
  },
  {
    id: "demo-diagnostics",
    label: "Diag",
    shortLabel: "Diag",
    Icon: ActivityIcon,
  },
  {
    id: "demo-profile",
    label: "Profile",
    shortLabel: "Profile",
    Icon: UserIcon,
  },
];

function scrollToId(id: string) {
  const el = typeof document !== "undefined" ? document.getElementById(id) : null;
  if (!el) return;
  const reduce =
    typeof window !== "undefined" &&
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  el.scrollIntoView({
    behavior: reduce ? "auto" : "smooth",
    block: "start",
  });
}

export function DemoMobileDock() {
  const [active, setActive] = useState<string>(DEMO_SECTIONS[0].id);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (typeof IntersectionObserver === "undefined") return;

    const sections = DEMO_SECTIONS.map((s) =>
      document.getElementById(s.id),
    ).filter((el): el is HTMLElement => Boolean(el));

    if (sections.length === 0) return;

    const obs = new IntersectionObserver(
      (entries) => {
        // Pick the entry closest to the top among those currently intersecting.
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]) setActive(visible[0].target.id);
      },
      {
        rootMargin: "-35% 0px -55% 0px",
        threshold: [0, 0.1, 0.4, 1],
      },
    );

    sections.forEach((el) => obs.observe(el));
    return () => obs.disconnect();
  }, []);

  return (
    <nav
      className="demo-dock"
      aria-label="Design demo sections (mobile)"
    >
      <div className="demo-dock__inner">
        {DEMO_SECTIONS.map((s) => {
          const isActive = s.id === active;
          return (
            <button
              key={s.id}
              type="button"
              className="demo-tab"
              aria-current={isActive ? "true" : undefined}
              aria-label={`Jump to ${s.label}`}
              onClick={() => scrollToId(s.id)}
            >
              <span className="demo-tab__icon">
                <s.Icon size={14} />
              </span>
              <span className="demo-tab__label">{s.shortLabel}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

export default DemoMobileDock;
