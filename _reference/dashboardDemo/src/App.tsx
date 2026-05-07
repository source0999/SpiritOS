/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useMemo } from 'react';
import { 
  LayoutDashboard, 
  MessageSquare, 
  Sparkles, 
  Cpu, 
  HardDrive, 
  Clock, 
  Zap, 
  Palette,
  ChevronRight,
  ShieldCheck,
  Activity,
  ArrowRight,
  X,
  Volume2
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

// --- Types & Constants ---

type ThemePalette = {
  id: string;
  name: string;
  accent: string;
  glow: string;
  bg: string;
  panelClass: string;
  textClass: string;
  isDark?: boolean;
};

const PALETTES: ThemePalette[] = [
  { 
    id: 'smoked-pearl', 
    name: 'Smoked Pearl', 
    accent: '#0f172a', 
    glow: 'rgba(15, 23, 42, 0.4)', 
    bg: '#f1f5f9', 
    panelClass: 'glass-pearl',
    textClass: 'text-slate-900'
  },
  { 
    id: 'spirit-cyan', 
    name: 'Neural Cyan', 
    accent: '#0891b2', 
    glow: 'rgba(8, 145, 178, 0.5)', 
    bg: '#f0f9ff',
    panelClass: 'glass-pearl',
    textClass: 'text-slate-900',
  },
  { 
    id: 'legacy-violet', 
    name: 'Legacy Violet', 
    accent: '#9333ea', 
    glow: 'rgba(147, 51, 234, 0.5)', 
    bg: '#f5f3ff',
    panelClass: 'glass-pearl',
    textClass: 'text-slate-900',
  },
  { 
    id: 'dark-node', 
    name: 'Dark Node', 
    accent: '#818cf8', 
    glow: 'rgba(129, 140, 248, 0.5)', 
    bg: '#0f172a',
    panelClass: 'glass-smoke',
    textClass: 'text-white',
    isDark: true
  },
  { 
    id: 'solar-ember', 
    name: 'Solar Ember', 
    accent: '#ea580c', 
    glow: 'rgba(234, 88, 12, 0.5)', 
    bg: '#fff7ed',
    panelClass: 'glass-pearl',
    textClass: 'text-slate-900',
  },
];

// --- Utilities ---
const cn = (...classes: (string | boolean | undefined)[]) => classes.filter(Boolean).join(' ');

// --- Main App ---

export default function App() {
  const [theme, setTheme] = useState<ThemePalette>(PALETTES[0]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    document.documentElement.style.setProperty('--spirit-accent', theme.accent);
  }, [theme]);

  // Background Mesh Gradients - Multi-Layered Atmosphere for Visible Transparency
  const atmosphere = useMemo(() => (
    <div className="fixed inset-0 pointer-events-none z-[-2] overflow-hidden">
      {/* 1. DEPTH FOUNDATION — Silver-Air Mix */}
      <div className="absolute inset-0 bg-slate-200" />
      <div className="absolute inset-0 bg-gradient-to-tr from-slate-300 via-slate-100 to-white opacity-80" />

      {/* Theme tint — lowered opacity so it breathes */}
      <motion.div 
        initial={false}
        animate={{ 
          backgroundColor: theme.bg,
          opacity: theme.isDark ? 0.35 : 0.15
        }}
        transition={{ duration: 1.5 }}
        className="absolute inset-0"
      />

      {/* 2. ENVIRONMENTAL FORMS — Blurred shapes to provide transparency indicators */}
      <div className="absolute inset-x-0 h-screen overflow-hidden opacity-50 mix-blend-overlay">
        {/* Deep Haze Pocket */}
        <motion.div
          animate={{ 
            x: [0, 100, 0], 
            y: [0, 50, 0],
            rotate: [15, 20, 15] 
          }}
          transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
          className="absolute -top-[10%] left-[-5%] w-[70%] h-[80%] bg-slate-400/20 blur-[140px] rounded-[160px]"
        />
        {/* Soft Light Strike */}
        <motion.div
           animate={{ 
             x: [0, -120, 0], 
             y: [0, -40, 0],
             rotate: [-12, -18, -12] 
           }}
           transition={{ duration: 55, repeat: Infinity, ease: "linear" }}
           className="absolute bottom-[15%] right-[-10%] w-[80%] h-[60%] bg-white/40 blur-[160px] rounded-full"
        />
      </div>

      {/* 3. DYNAMIC GLOW — Controlled theme presence */}
      <motion.div
        animate={{ 
          x: [-200, 200, -200], 
          y: [-120, 120, -120],
          opacity: [0.1, 0.2, 0.1],
          scale: [1, 1.3, 1]
        }}
        transition={{ duration: 45, repeat: Infinity, ease: "linear" }}
        className="absolute top-[-25%] left-[-20%] w-[150%] h-[150%] rounded-full blur-[180px]"
        style={{ 
          background: `radial-gradient(circle at center, ${theme.accent}20, transparent 70%)`
        }}
      />

      {/* 4. SURFACE DETAIL — Ambient depth veil */}
      <div className="absolute inset-0 bg-gradient-to-br from-transparent via-white/10 to-transparent opacity-20" />

      {/* Lower Atmosphere Warmth/Coolness */}
      <motion.div
        animate={{ 
          opacity: [0.05, 0.15, 0.05],
          y: [0, 20, 0]
        }}
        transition={{ duration: 30, repeat: Infinity, ease: "easeInOut" }}
        className="absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t from-slate-200/30 to-transparent blur-[100px]"
      />

      {/* Finishing Grain */}
      <div 
        className="absolute inset-0 opacity-[0.02] mix-blend-overlay pointer-events-none" 
        style={{ backgroundImage: 'url("https://grainy-gradients.vercel.app/noise.svg")' }} 
      />
    </div>
  ), [theme.accent, theme.bg, theme.isDark]);

  return (
    <div className={cn("min-h-screen flex flex-col", theme.textClass)}>
      {atmosphere}

      <DashboardShell theme={theme} onThemeClick={() => setIsModalOpen(true)} />

      <ThemeModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        activeId={theme.id}
        onSelect={setTheme}
      />
    </div>
  );
}

// --- Layout Components ---

const DashboardShell = ({ theme, onThemeClick }: { theme: ThemePalette, onThemeClick: () => void }) => {
  return (
    <div className="flex-1 w-full p-4 sm:p-6 lg:p-10 flex flex-col space-y-8">
      {/* Header */}
      <header className="flex flex-col sm:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-6">
          <div className={cn("w-14 h-14 rounded-3xl flex items-center justify-center border", theme.isDark ? "bg-white/5 border-white/10" : "bg-white border-black/5 shadow-sm")}>
            <Zap size={28} style={{ color: theme.accent }} />
          </div>
          <div>
            <h2 className="text-3xl font-bold tracking-tighter uppercase font-mono">SpiritOS <span className="font-light opacity-50">Trinity</span></h2>
            <p className="text-[11px] font-mono font-bold uppercase tracking-[0.4em] opacity-40">Homelab Dashboard v4.5</p>
          </div>
        </div>

        <div className="flex items-center gap-8">
          <div className="hidden md:flex flex-col items-end gap-1">
             <span className="text-xl font-bold font-mono tracking-tighter">23:54:09</span>
             <div className="flex items-center gap-2 opacity-40">
                <Clock size={12} />
                <span className="text-[9px] font-bold uppercase tracking-widest">Local Time · Node Nominal</span>
             </div>
          </div>
          <div className={cn("px-6 py-2.5 rounded-full border border-black/5 flex items-center gap-3", theme.isDark ? "bg-white/10" : "bg-white/40")}>
             <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]" />
             <span className="text-[10px] font-bold font-mono uppercase tracking-[0.2em] opacity-60">Trinity Mesh Live</span>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <div className="flex-1 grid grid-cols-1 xl:grid-cols-12 gap-6 lg:gap-8">
        {/* Hero: Oracle Fairy */}
        <div className="xl:col-span-8 flex flex-col gap-6">
          <OracleFairyWidget theme={theme} />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
             <SystemStatsCard theme={theme} />
             <StorageCard theme={theme} />
          </div>
        </div>

        {/* Sidebar Style Right: Briefing */}
        <div className="xl:col-span-4 h-full">
           <DailyBriefingCard theme={theme} />
        </div>
      </div>

      <FloatingNavbar theme={theme} onThemeClick={onThemeClick} />
    </div>
  );
};

// --- Widget Components ---

const OracleFairyWidget = ({ theme }: { theme: ThemePalette }) => {
  return (
    <section className={cn(
      "rounded-[56px] p-8 sm:p-14 relative overflow-hidden flex flex-col items-center md:flex-row gap-14 transition-all duration-700",
      theme.panelClass
    )}>
      {/* Subtle Inner Reflection Highlighting */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/40 to-transparent pointer-events-none" />
      <div className="absolute inset-y-0 left-0 w-px bg-gradient-to-b from-transparent via-white/20 to-transparent pointer-events-none" />

      {/* Fairy Visualization */}
      <div className="relative w-64 h-64 sm:w-80 sm:h-80 flex items-center justify-center shrink-0">
        {/* Glow Aura - Participates in background bleed */}
        <div 
          className="absolute inset-0 rounded-full blur-[120px] opacity-30 animate-pulse"
          style={{ backgroundColor: theme.accent }}
        />
        
        {/* Living Wing Forms (Abstract & Luminous) */}
        {[0, 1].map((i) => (
          <motion.div
            key={i}
            animate={{ 
              rotate: i === 0 ? [-8, -20, -8] : [8, 20, 8],
              scale: [1, 1.08, 1],
              opacity: [0.3, 0.6, 0.3]
            }}
            transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: i * 0.5 }}
            className={cn(
              "absolute w-[160%] h-[100%] rounded-[100%] border-[0.5px]",
              i === 0 ? "-translate-x-1/2 -rotate-12" : "translate-x-1/2 rotate-12"
            )}
            style={{ 
              borderColor: `${theme.accent}60`,
              background: `radial-gradient(ellipse at center, ${theme.accent}10, transparent 75%)`,
              boxShadow: `0 0 30px ${theme.accent}10`
            }}
          />
        ))}

        {/* Floating System Spirits (Particles) */}
        {Array.from({ length: 15 }).map((_, i) => (
          <motion.div
            key={i}
            animate={{ 
              x: [0, (Math.random() - 0.5) * 180],
              y: [0, (Math.random() - 0.5) * 180],
              opacity: [0, 0.7, 0],
              scale: [0.8, 1.2, 0.8],
            }}
            transition={{ duration: 4 + Math.random() * 4, repeat: Infinity, delay: Math.random() * 5 }}
            className="absolute font-mono text-[9px] font-bold pointer-events-none select-none"
            style={{ color: theme.accent, opacity: 0.2 }}
          >
            {Math.random() > 0.5 ? '✧' : '⊹'}
          </motion.div>
        ))}

        {/* Central Intelligence Core */}
        <motion.div
           animate={{ 
             y: [0, -12, 0],
             scale: [1, 1.03, 1]
           }}
           transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
           className={cn(
             "relative w-28 h-28 sm:w-32 sm:h-32 rounded-full shadow-2xl flex items-center justify-center border border-white/40 z-10 backdrop-blur-3xl",
             theme.isDark ? "bg-black/30" : "bg-white/40"
           )}
           style={{ 
             boxShadow: `0 0 80px -15px ${theme.accent}, inset 0 2px 20px rgba(255,255,255,0.5)`,
             borderColor: `${theme.accent}40`
           }}
        >
          {/* Inner Core Pulse */}
          <motion.div 
            animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.6, 0.3] }}
            transition={{ duration: 3, repeat: Infinity }}
            className="absolute w-12 h-12 rounded-full blur-xl"
            style={{ backgroundColor: theme.accent }}
          />
          <Sparkles size={48} className="relative z-10" style={{ color: theme.isDark ? 'white' : theme.accent }} />
        </motion.div>

        {/* Status Hub */}
        <div className="absolute -bottom-8 flex items-center gap-2 h-8 px-6 rounded-full glass-pearl border-white/30 shadow-lg">
           <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
           <span className="text-[10px] font-mono font-bold uppercase tracking-widest opacity-80">Oracle v4.0 Active</span>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 text-center md:text-left space-y-8 z-10">
        <div className="space-y-4">
           <div className="flex items-center gap-2 justify-center md:justify-start">
             <SectionBadge label="Neural Mesh Nominal" color="bg-emerald-500" />
             <div className="p-1 rounded-lg bg-black/[0.03] dark:bg-white/5 flex items-center gap-1.5 px-3">
                <Volume2 size={12} className="opacity-40" />
                <div className="flex gap-1 h-3 items-center">
                  {[0.5, 0.8, 0.4, 0.6].map((h, i) => (
                    <motion.div 
                      key={i}
                      animate={{ height: [h*10, (1-h)*10, h*10] }}
                      transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.15 }}
                      className="w-0.5 rounded-full bg-slate-400"
                    />
                  ))}
                </div>
             </div>
           </div>
           
           <h1 className={cn(
             "text-5xl sm:text-7xl font-light tracking-tighter leading-[1.1] py-2",
             theme.isDark ? "text-white" : "text-slate-900"
           )}>
             Listening <span className="font-serif italic font-medium opacity-100 text-slate-500 dark:text-slate-400">Standby</span>
           </h1>
           
           <p className="text-xl max-w-xl opacity-50 font-medium leading-relaxed">
             SpiritOS Trinity is optimized. <br className="hidden sm:block" />
             How can I assist your homelab today?
           </p>
        </div>

        <div className="flex flex-wrap items-center justify-center md:justify-start gap-6 pt-4">
           <motion.button 
             whileHover={{ scale: 1.05, y: -2 }}
             whileTap={{ scale: 0.98 }}
             className={cn(
               "px-12 py-5 rounded-full font-bold text-sm shadow-2xl flex items-center gap-3 transition-all",
               theme.isDark ? "bg-white text-slate-950" : "bg-slate-950 text-white"
             )}
           >
             <MessageSquare size={18} />
             INITIATE COMMAND
           </motion.button>
           <button className={cn(
             "px-8 py-5 rounded-full border border-black/10 dark:border-white/10 font-bold text-xs uppercase tracking-[0.25em] transition-all", 
             theme.isDark ? "hover:bg-white/10 text-white" : "hover:bg-black/5 text-slate-950"
           )}>
             Neural Setup
           </button>
        </div>
      </div>
    </section>
  );
};

const DailyBriefingCard = ({ theme }: { theme: ThemePalette }) => (
  <aside className={cn("h-full rounded-[48px] p-8 flex flex-col shadow-2xl transition-all duration-700", theme.panelClass)}>
    <div className="flex items-center justify-between mb-10">
      <h3 className="text-2xl font-bold tracking-tight flex items-center gap-3">
        <ShieldCheck size={24} className="opacity-40" />
        Daily Briefing
      </h3>
      <span className="text-[10px] font-mono font-bold opacity-30 tracking-[0.3em]">05/07</span>
    </div>

    <div className="flex-1 space-y-4">
      {[
        { t: 'Local AI', m: 'Trinity STT models updated to v2.4. Zero latency drift detected.', s: 'good' },
        { t: 'Storage', m: 'Archive drive B is approaching 90% capacity limit.', s: 'warn' },
        { t: 'Energy', m: 'Current cluster pull 242W. Grid efficiency nominal.', s: 'good' },
        { t: 'Uptime', m: 'Ollama host Spirit-Dell has reached 14 days consecutive.', s: 'info' }
      ].map((item, i) => (
        <div key={i} className={cn(
          "p-6 rounded-[32px] border transition-all cursor-pointer group backdrop-blur-md",
          theme.isDark ? "bg-white/[0.03] border-white/5 hover:bg-white/[0.08]" : "bg-black/[0.01] border-black/5 hover:bg-black/[0.04]"
        )}>
          <div className="flex justify-between items-center mb-2">
            <span className={cn(
              "text-[9px] font-bold uppercase tracking-widest opacity-50 font-mono",
              item.s === 'warn' ? "text-amber-500 opacity-100" : ""
            )}>{item.t}</span>
            <ArrowRight size={14} className="opacity-0 group-hover:opacity-40 transition-all -translate-x-2 group-hover:translate-x-0" />
          </div>
          <p className="text-sm font-semibold leading-relaxed opacity-70 group-hover:opacity-100 transition-opacity">{item.m}</p>
        </div>
      ))}
    </div>

    <button className="w-full mt-8 py-5 rounded-3xl border border-dashed border-black/10 dark:border-white/10 text-[10px] font-bold uppercase tracking-[0.3em] opacity-40 hover:opacity-100 transition">
      Access system logs
    </button>
  </aside>
);

const SystemStatsCard = ({ theme }: { theme: ThemePalette }) => (
  <div className={cn("rounded-[40px] p-8 shadow-xl transition-all duration-700", theme.panelClass)}>
    <div className="flex justify-between items-start mb-8">
      <div className="flex items-center gap-3">
         <div className="p-2.5 rounded-2xl bg-black/[0.03] dark:bg-white/[0.05]">
            <Activity size={20} className="opacity-60" />
         </div>
         <div>
            <h4 className="font-bold text-lg">System vitals</h4>
            <p className="text-[10px] font-bold font-mono uppercase opacity-30">Trinity Node 1</p>
         </div>
      </div>
      <SectionBadge label="Synced" color="bg-cyan-500" />
    </div>

    <div className="space-y-6">
       <StatBar label="CPU" val="34.1%" width="34%" color="#6366f1" isDark={theme.isDark} />
       <StatBar label="RAM" val="9.2 GB" width="57%" color="#64748b" isDark={theme.isDark} />
    </div>

    <div className="mt-8 pt-6 border-t border-black/5 flex justify-between items-center">
       <div className="flex flex-col">
          <span className="text-[9px] font-bold uppercase opacity-30">GPU Load</span>
          <span className="font-mono text-xs font-bold">12% Standby</span>
       </div>
       <div className="flex flex-col items-end">
          <span className="text-[9px] font-bold uppercase opacity-30">Temp</span>
          <span className="font-mono text-xs font-bold">34°C</span>
       </div>
    </div>
  </div>
);

const StorageCard = ({ theme }: { theme: ThemePalette }) => (
  <div className={cn("rounded-[40px] p-8 shadow-xl transition-all duration-700", theme.panelClass)}>
    <div className="flex items-center gap-3 mb-8">
       <div className="p-2.5 rounded-2xl bg-black/[0.03] dark:bg-white/[0.05]">
          <HardDrive size={20} className="opacity-60" />
       </div>
       <div>
          <h4 className="font-bold text-lg">Storage pool</h4>
          <p className="text-[10px] font-bold font-mono uppercase opacity-30">ZFS Raid 0</p>
       </div>
    </div>

    <div className="space-y-5">
       {[
         { n: 'Root Drive', u: '20%', c: 'bg-emerald-500' },
         { n: 'Archive Drive', u: '85%', c: 'bg-amber-500' }
       ].map((drive, i) => (
         <div key={i} className="space-y-2">
            <div className="flex justify-between items-baseline">
               <span className="text-sm font-bold opacity-80">{drive.n}</span>
               <span className={cn("text-xs font-bold font-mono", drive.u === '85%' ? "text-amber-500" : "")}>{drive.u}</span>
            </div>
            <div className="h-1.5 w-full bg-black/5 dark:bg-white/5 rounded-full overflow-hidden">
               <div className={cn("h-full rounded-full transition-all duration-1000", drive.c)} style={{ width: drive.u }} />
            </div>
         </div>
       ))}
    </div>

    <div className="mt-8 flex justify-between items-center px-4 py-3 rounded-2xl bg-black/[0.03] dark:bg-white/[0.05] border border-black/5">
       <span className="text-[9px] font-bold opacity-40 uppercase tracking-widest font-mono">SMART STATUS</span>
       <span className="text-[9px] font-bold text-emerald-500 uppercase tracking-widest font-mono">HEALTHY</span>
    </div>
  </div>
);

const FloatingNavbar = ({ theme, onThemeClick }: { theme: ThemePalette, onThemeClick: () => void }) => {
  return (
    <nav className="fixed bottom-[max(1.5rem,env(safe-area-inset-bottom,0px))] left-1/2 -translate-x-1/2 z-50 w-auto">
      <div className={cn(
        "rounded-full p-2.5 flex items-center gap-1.5 shadow-2xl transition-all duration-700",
        theme.isDark ? "glass-nav-dark ring-1 ring-white/10" : "glass-nav-light ring-1 ring-black/5"
      )}>
        <div className="flex gap-1.5">
          {[
            { icon: LayoutDashboard, label: "Home", active: true },
            { icon: MessageSquare, label: "Chat" },
            { icon: Sparkles, label: "Oracle" },
          ].map((item, i) => (
            <button 
              key={i}
              className={cn(
                "flex items-center gap-2.5 px-7 py-3.5 rounded-full text-[11px] font-bold tracking-[0.1em] uppercase transition relative group",
                item.active 
                  ? (theme.isDark ? "text-slate-950" : "text-white")
                  : (theme.isDark ? "text-white/50 hover:text-white" : "text-slate-900/50 hover:text-slate-900")
              )}
            >
              {item.active && (
                <motion.div 
                  layoutId="nav-bg"
                  className={cn("absolute inset-0 z-0 shadow-lg", theme.isDark ? "bg-white" : "bg-slate-900")}
                  style={{ borderRadius: '999px' }}
                />
              )}
              <item.icon size={20} className="relative z-10" />
              <span className="relative z-10 hidden sm:inline">{item.label}</span>
            </button>
          ))}
        </div>
        
        <div className={cn("w-px h-8 mx-2", theme.isDark ? "bg-white/10" : "bg-black/10")} />

        <button 
          onClick={onThemeClick}
          className={cn(
            "w-14 h-14 flex items-center justify-center rounded-full transition relative group overflow-hidden",
            theme.isDark ? "bg-white/10 text-white" : "bg-black/5 text-slate-800"
          )}
        >
          <Palette size={22} className="relative z-10 group-hover:scale-110 transition-transform" />
          <motion.div 
             animate={{ rotate: 360 }}
             transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
             className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity"
             style={{ 
               background: `conic-gradient(from 0deg, transparent, ${theme.accent}40, transparent)` 
             }}
          />
          <div 
             className="absolute inset-0 rounded-full blur-lg opacity-0 group-hover:opacity-30 transition-opacity animate-pulse"
             style={{ backgroundColor: theme.accent }}
          />
        </button>
      </div>
    </nav>
  );
};

const ThemeModal = ({ isOpen, onClose, activeId, onSelect }: { isOpen: boolean, onClose: () => void, activeId: string, onSelect: (p: ThemePalette) => void }) => (
  <AnimatePresence>
    {isOpen && (
      <>
        <motion.div 
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          onClick={onClose} 
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[60]" 
        />
        <motion.div
           initial={{ opacity: 0, scale: 0.95, y: 40 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 40 }}
           className="fixed inset-x-4 bottom-[min(120px,25%)] mx-auto z-[70] w-[min(calc(100%-2rem),440px)] glass-pearl rounded-[48px] p-10 shadow-2xl border-white/40"
        >
           <div className="flex justify-between items-center mb-8">
              <h2 className="text-3xl font-bold tracking-tighter text-slate-900">Interface</h2>
              <button onClick={onClose} className="p-3 rounded-full hover:bg-black/5 transition text-slate-400 hover:text-slate-900">
                <X size={20} />
              </button>
           </div>

           <div className="grid grid-cols-2 gap-5">
              {PALETTES.map((p) => (
                <button
                  key={p.id}
                  onClick={() => { onSelect(p); onClose(); }}
                  className={cn(
                    "p-6 rounded-[36px] border transition-all text-left space-y-4 group relative overflow-hidden",
                    activeId === p.id 
                      ? "bg-slate-900 text-white shadow-2xl border-slate-900" 
                      : "bg-white/40 border-black/5 text-slate-800 hover:border-black/20 hover:bg-white/60"
                  )}
                >
                  <div className="flex justify-between items-center">
                    <div className="w-10 h-10 rounded-2xl shadow-sm border border-black/5" style={{ backgroundColor: p.bg }} />
                    <div className="w-3 h-3 rounded-full shadow-lg" style={{ backgroundColor: p.accent, boxShadow: `0 0 12px ${p.accent}` }} />
                  </div>
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold uppercase tracking-widest">{p.name}</span>
                    <p className="text-[9px] opacity-40 font-mono uppercase tracking-tighter">{p.isDark ? 'Smokey / Deep' : 'Pearl / Airy'}</p>
                  </div>
                </button>
              ))}
           </div>
           
           <p className="mt-10 text-[9px] font-bold text-center opacity-20 font-mono tracking-[0.5em] uppercase">Visual Redesign v1.5 Stable</p>
        </motion.div>
      </>
    )}
  </AnimatePresence>
);

// --- Small Primitives ---

const SectionBadge = ({ label, color }: { label: string, color: string }) => (
  <div className="flex items-center gap-1.5 px-3 py-1 rounded-full border border-black/5 bg-black/[0.03] w-fit">
     <div className={cn("w-1.5 h-1.5 rounded-full animate-pulse", color)} />
     <span className="text-[9px] font-bold font-mono uppercase tracking-[0.2em] opacity-50">{label}</span>
  </div>
);

const StatBar = ({ label, val, width, color, isDark }: { label: string, val: string, width: string, color: string, isDark?: boolean }) => (
  <div className="space-y-2">
     <div className="flex justify-between items-end">
        <span className="text-[10px] font-bold opacity-30 tracking-widest font-mono">{label}</span>
        <span className="text-sm font-bold font-mono">{val}</span>
     </div>
     <div className="h-1.5 w-full bg-black/5 dark:bg-white/5 rounded-full">
        <motion.div 
           initial={{ width: 0 }}
           animate={{ width }}
           className="h-full rounded-full"
           style={{ backgroundColor: color }}
        />
     </div>
  </div>
);
