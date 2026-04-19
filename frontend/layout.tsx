"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Music2,
  Film,
  FlaskConical,
  ChevronLeft,
  ChevronRight,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { label: "Dashboard",        icon: LayoutDashboard, href: "/" },
  { label: "YTM Hub",          icon: Music2,           href: "/ytm" },
  { label: "Sovereign Cinema", icon: Film,             href: "/cinema" },
  { label: "Research Lab",     icon: FlaskConical,     href: "/research" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <html lang="en" className="dark">
      <body className="bg-zinc-950 text-zinc-100 antialiased min-h-screen flex overflow-hidden">

        {/* ── Sidebar ── */}
        <motion.aside
          animate={{ width: collapsed ? 72 : 220 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="relative flex-shrink-0 flex flex-col h-screen border-r border-white/10 bg-zinc-950/80 backdrop-blur-md z-20"
        >
          {/* Logo */}
          <div className="flex items-center gap-3 px-4 py-5 border-b border-white/10">
            <div className="w-8 h-8 rounded-full bg-violet-500/20 border border-violet-500/40 flex items-center justify-center flex-shrink-0">
              <Zap size={14} className="text-violet-400" />
            </div>
            <AnimatePresence>
              {!collapsed && (
                <motion.span
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -8 }}
                  transition={{ duration: 0.15 }}
                  className="text-sm font-semibold tracking-tight text-zinc-100 whitespace-nowrap"
                >
                  Spirit OS
                </motion.span>
              )}
            </AnimatePresence>
          </div>

          {/* Nav */}
          <nav className="flex-1 py-4 space-y-1 px-2">
            {NAV_ITEMS.map(({ label, icon: Icon, href }) => (
              <a
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium",
                  "text-zinc-400 hover:text-zinc-100 hover:bg-white/5 transition-colors duration-150",
                  "group relative"
                )}
              >
                <Icon size={18} className="flex-shrink-0" />
                <AnimatePresence>
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -6 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -6 }}
                      transition={{ duration: 0.12 }}
                      className="whitespace-nowrap"
                    >
                      {label}
                    </motion.span>
                  )}
                </AnimatePresence>
                {/* Tooltip when collapsed */}
                {collapsed && (
                  <span className="absolute left-14 bg-zinc-800 text-zinc-100 text-xs px-2 py-1 rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap border border-white/10">
                    {label}
                  </span>
                )}
              </a>
            ))}
          </nav>

          {/* Collapse toggle */}
          <button
            onClick={() => setCollapsed((c) => !c)}
            className="m-3 flex items-center justify-center h-9 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-zinc-100 transition-colors"
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </motion.aside>

        {/* ── Main content ── */}
        <main className="flex-1 overflow-y-auto h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}
