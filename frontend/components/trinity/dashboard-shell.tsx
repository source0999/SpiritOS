"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  Activity,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  Newspaper,
  Settings,
  Sparkles,
  Terminal,
  Zap,
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const nav = [
  { icon: LayoutDashboard, label: "Dashboard" },
  { icon: Sparkles, label: "Oracle" },
  { icon: Zap, label: "Energy" },
  { icon: Newspaper, label: "6 AM Brief" },
  { icon: Terminal, label: "Toxic Grader" },
  { icon: Activity, label: "System" },
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex min-h-0 flex-1 bg-zinc-950 text-zinc-100">
      <motion.aside
        initial={false}
        animate={{ width: collapsed ? 72 : 240 }}
        transition={{ type: "spring", stiffness: 420, damping: 34 }}
        className="relative z-20 flex shrink-0 flex-col border-r border-zinc-800/80 bg-zinc-950/95 backdrop-blur"
      >
        <div className="flex h-14 items-center justify-between gap-2 border-b border-zinc-800/80 px-3">
          <AnimatePresence mode="wait" initial={false}>
            {!collapsed ? (
              <motion.span
                key="full"
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -6 }}
                transition={{ duration: 0.15 }}
                className="truncate pl-1 text-sm font-semibold tracking-tight text-zinc-100"
              >
                Trinity
              </motion.span>
            ) : (
              <motion.span
                key="mark"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="mx-auto text-xs font-bold uppercase tracking-widest text-cyan-400"
              >
                T
              </motion.span>
            )}
          </AnimatePresence>
          <button
            type="button"
            onClick={() => setCollapsed((c) => !c)}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900/80 text-zinc-400 transition hover:border-zinc-700 hover:text-zinc-100"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </button>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-2">
          {nav.map(({ icon: Icon, label }) => (
            <div key={label} className="group relative">
              <button
                type="button"
                title={collapsed ? label : undefined}
                className={cn(
                  "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-zinc-400 transition",
                  "hover:bg-zinc-900 hover:text-zinc-100",
                  collapsed && "justify-center px-0",
                )}
              >
                <Icon className="h-5 w-5 shrink-0 text-cyan-400/90" />
                <AnimatePresence initial={false}>
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: "auto" }}
                      exit={{ opacity: 0, width: 0 }}
                      transition={{ type: "spring", stiffness: 400, damping: 38 }}
                      className="truncate font-medium"
                    >
                      {label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </button>
              {collapsed && (
                <div
                  className={cn(
                    "pointer-events-none absolute left-full top-1/2 z-50 ml-3 -translate-y-1/2 rounded-lg border border-zinc-700 bg-zinc-900 px-2.5 py-1 text-xs font-medium text-zinc-100 opacity-0 shadow-xl",
                    "transition-opacity group-hover:pointer-events-auto group-hover:opacity-100",
                  )}
                >
                  {label}
                </div>
              )}
            </div>
          ))}
        </nav>
        <div className="border-t border-zinc-800/80 p-2">
          <div className="group relative">
            <button
              type="button"
              title={collapsed ? "Settings" : undefined}
              className={cn(
                "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-zinc-500 transition hover:bg-zinc-900 hover:text-zinc-200",
                collapsed && "justify-center px-0",
              )}
            >
              <Settings className="h-5 w-5 shrink-0" />
              {!collapsed && <span className="truncate">Settings</span>}
            </button>
            {collapsed && (
              <div className="pointer-events-none absolute left-full top-1/2 z-50 ml-3 -translate-y-1/2 rounded-lg border border-zinc-700 bg-zinc-900 px-2.5 py-1 text-xs font-medium text-zinc-100 opacity-0 shadow-xl transition-opacity group-hover:pointer-events-auto group-hover:opacity-100">
                Settings
              </div>
            )}
          </div>
        </div>
      </motion.aside>
      <main className="min-h-0 flex-1 overflow-auto p-6 lg:p-8">{children}</main>
    </div>
  );
}
