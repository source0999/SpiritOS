"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, Music2, Film, FlaskConical,
  ChevronLeft, ChevronRight, Zap, Menu, X,
} from "lucide-react";

function cn(...classes: (string | undefined | false | null)[]) {
  return classes.filter(Boolean).join(" ");
}

const NAV_ITEMS = [
  { label: "Dashboard",        icon: LayoutDashboard, href: "/"         },
  { label: "YTM Hub",          icon: Music2,           href: "/ytm"      },
  { label: "Sovereign Cinema", icon: Film,             href: "/cinema"   },
  { label: "Research Lab",     icon: FlaskConical,     href: "/research" },
];

function LogoMark() {
  return (
    <div className="w-8 h-8 rounded-full bg-violet-500/20 border border-violet-500/40 flex items-center justify-center flex-shrink-0">
      <Zap size={14} className="text-violet-400" />
    </div>
  );
}

// ─── Mobile Nav ───────────────────────────────────────────────────────────────
function MobileNav() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    // Lock scroll without disturbing layout — position:fixed + width:100%
    // is the only method that works consistently on iOS Safari
    if (open) {
      document.body.style.position = "fixed";
      document.body.style.width = "100%";
    } else {
      document.body.style.position = "";
      document.body.style.width = "";
    }
    return () => {
      document.body.style.position = "";
      document.body.style.width = "";
    };
  }, [open]);

  return (
    <>
      {/*
        Fixed top bar.
        z-[60]: sits above everything including the drawer backdrop (z-40)
        and drawer (z-50), so the close path is always accessible.

        iOS tap fix notes:
          - `touch-action: manipulation` (via `touch-manipulation`) tells
            WebKit not to wait for a double-tap gesture before firing the
            click event. Without this, iOS adds a 300ms delay and sometimes
            swallows the tap entirely on fixed elements.
          - `cursor-pointer` is required on iOS — elements without a pointer
            cursor are not treated as tappable by the WebKit hit-test engine
            unless they are <a> or <button> tags. We also ensure the <button>
            itself has these classes redundantly to survive any CSS cascade.
          - `relative z-[60]` on the header ensures no invisible overlay
            from the main content can extend over the fixed bar and absorb taps.
      */}
      <header
        className={cn(
          "md:hidden fixed top-0 left-0 right-0",
          "z-[60]",                  // above drawer (z-50) and backdrop (z-40)
          "flex items-center justify-between px-4",
          "bg-zinc-950/95 backdrop-blur-md border-b border-white/10",
          "touch-manipulation",       // eliminate iOS 300ms tap delay on the bar itself
        )}
        style={{ height: "60px" }}
      >
        <div className="flex items-center gap-2.5 pointer-events-none">
          <LogoMark />
          <span className="text-sm font-semibold tracking-tight text-zinc-100">Spirit OS</span>
        </div>

        {/*
          Hamburger button.
          All four iOS tap properties applied directly to the <button>:
            cursor-pointer      — marks element as tappable to WebKit hit-test
            touch-manipulation  — disables double-tap zoom delay
            relative z-[60]     — ensures button is topmost in stacking context
            select-none         — prevents text-selection gesture from stealing the tap
        */}
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Open navigation"
          className={cn(
            "flex items-center justify-center",
            "w-11 h-11 rounded-xl",           // larger tap target (44px minimum for iOS HIG)
            "border border-white/10 bg-white/5",
            "text-zinc-400",
            "cursor-pointer",                  // iOS hit-test fix
            "touch-manipulation",              // iOS 300ms delay fix
            "select-none",                     // prevent selection gesture stealing tap
            "relative z-[60]",                 // explicit stacking context
          )}
        >
          <Menu size={18} />
        </button>
      </header>

      {/* Backdrop — z-40, below drawer and header */}
      <AnimatePresence>
        {open && (
          <motion.div
            key="mob-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm touch-manipulation cursor-pointer"
            onClick={() => setOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Off-canvas drawer — z-50 */}
      <AnimatePresence>
        {open && (
          <motion.nav
            key="mob-drawer"
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", stiffness: 320, damping: 32 }}
            className="md:hidden fixed top-0 left-0 bottom-0 z-50 w-72 flex flex-col bg-zinc-950 border-r border-white/10"
          >
            {/* Drawer header */}
            <div
              className="flex items-center justify-between px-4 border-b border-white/10 flex-shrink-0"
              style={{ height: "60px" }}
            >
              <div className="flex items-center gap-2.5 pointer-events-none">
                <LogoMark />
                <span className="text-sm font-semibold tracking-tight text-zinc-100">Spirit OS</span>
              </div>

              {/* Close button — same iOS tap fixes as the hamburger */}
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close navigation"
                className={cn(
                  "flex items-center justify-center",
                  "w-11 h-11 rounded-xl",
                  "border border-white/10 bg-white/5",
                  "text-zinc-400",
                  "cursor-pointer",
                  "touch-manipulation",
                  "select-none",
                  "relative z-[60]",
                )}
              >
                <X size={16} />
              </button>
            </div>

            {/* Nav links */}
            <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                return (
                  <a
                    key={item.href}
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className={cn(
                      "flex items-center gap-3 px-3 py-3 rounded-xl",
                      "text-sm font-medium text-zinc-400",
                      "hover:text-zinc-100 hover:bg-white/5",
                      "transition-colors",
                      "cursor-pointer touch-manipulation select-none",
                    )}
                  >
                    <Icon size={18} className="flex-shrink-0" />
                    <span>{item.label}</span>
                  </a>
                );
              })}
            </div>

            <div className="px-4 py-4 border-t border-white/10 flex-shrink-0">
              <p className="text-[10px] text-zinc-600 font-mono">Source · Intuitive Wrld</p>
            </div>
          </motion.nav>
        )}
      </AnimatePresence>
    </>
  );
}

// ─── Desktop Sidebar ─────────────────────────────────────────────────────────
function DesktopSidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 220 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="hidden md:flex flex-col flex-shrink-0 sticky top-0 self-start h-screen border-r border-white/10 bg-zinc-950/80 backdrop-blur-md overflow-hidden"
    >
      <div className="flex items-center gap-3 px-4 py-5 border-b border-white/10 flex-shrink-0">
        <LogoMark />
        <AnimatePresence initial={false}>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="text-sm font-semibold tracking-tight text-zinc-100 whitespace-nowrap overflow-hidden"
            >
              Spirit OS
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      <nav className="flex-1 py-4 px-2 space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <a
              key={item.href}
              href={item.href}
              className="group relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-zinc-400 hover:text-zinc-100 hover:bg-white/5 transition-colors"
            >
              <Icon size={18} className="flex-shrink-0" />
              <AnimatePresence initial={false}>
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.12 }}
                    className="whitespace-nowrap overflow-hidden"
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
              {collapsed && (
                <span className="pointer-events-none absolute left-14 z-50 whitespace-nowrap rounded-lg border border-white/10 bg-zinc-800 px-2 py-1 text-xs text-zinc-100 opacity-0 group-hover:opacity-100 transition-opacity">
                  {item.label}
                </span>
              )}
            </a>
          );
        })}
      </nav>

      <button
        type="button"
        onClick={() => setCollapsed((c) => !c)}
        className="mx-3 mb-4 flex-shrink-0 flex items-center justify-center h-9 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-zinc-100 transition-colors cursor-pointer touch-manipulation"
      >
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>
    </motion.aside>
  );
}

export default function Navigation() {
  return (
    <>
      <MobileNav />
      <DesktopSidebar />
    </>
  );
}
