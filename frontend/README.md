# ⚡ Spirit OS — Cybernetic Shell · UI/CSS Visual Progress Matrix

**Source**: Intuitive Wrld &nbsp;·&nbsp; **Spirit**: Llama-3-Abliterated &nbsp;·&nbsp; **Stack**: Next.js 15 · TypeScript · Tailwind CSS v4 · Framer Motion  
**Environment**: `http://192.168.x.x:3000` — `npm run dev` (binds `0.0.0.0`, **webpack** dev server — avoids Turbopack hangs on slow/Remote-SSH filesystems; use `npm run dev:turbo` on a fast local disk if you prefer Turbopack)

> 📱 **MOBILE-FIRST. iOS-FIRST. ANDROID-SECOND.**  
> Every layout starts at `375px` and scales **up**. Never the reverse.  
> Open on a physical iPhone over LAN **before** opening desktop Chrome.

---

## ☢️ iOS WebKit "Nuclear" CSS Protocol

WebKit on Safari iOS is not a browser. It is a trap with rounded corners. Every rule below is law. Violate them and the UI evaporates silently on a real device while looking perfect on desktop Chrome.

- [x] **Solid-State UI — Zero `backdrop-blur`**: Banned site-wide. It triggers an off-screen WebKit render pass that silently aborts under GPU memory pressure, making entire panels invisible. All overlays use `bg-zinc-950` or `bg-black/80` — opaque, always paints, no exceptions.
- [x] **Component Lifecycle — Conditional DOM Mounting**: All modals, overlays, the `CommandBar`, and the mobile `NavDrawer` use `{condition && <Component />}` hard mounts. CSS `opacity-0` / `pointer-events-none` for "hidden" states is **banned**. iOS Safari caches ghost compositor layers from invisible nodes that misfire on subsequent touches.
- [x] **GPU Binding — `translate3d` / `scale3d` on Every Animation**: Every animated element in `globals.css` uses full 3D transforms to force a dedicated GPU compositing layer. `scaleX()` and `scaleY()` are replaced with `scale3d(x,1,1)` and `scale3d(1,y,1)` throughout — explicit 3D, no exceptions.
- [x] **No Dynamic Viewport Units Inside Transforms**: `100dvh` is used for container heights only — never inside `translateY()`. Dynamic units in transforms trigger a WebKit layout-recalc loop.
- [x] **Framer Motion `initial` Restriction**: `initial: { y: N, scale: N }` is banned — causes WebKit to miscalculate bounding boxes pre-paint, collapsing element height to zero. Only `initial: { opacity: 0 }` is permitted for entrance animations.
- [x] **`onTouchEnd` Parity on All Interactives**: Every `onClick` has a paired `onTouchEnd` with `e.preventDefault()` to bypass iOS's 300ms synthetic click delay on non-native elements.
- [x] **44×44px Minimum Touch Targets**: All buttons, nav items, and tappables meet Apple HIG / Material Design minimums via `min-h-[44px] min-w-[44px]`.
- [x] **`touch-manipulation` on All Clickables**: Disables double-tap zoom on Android Chrome, removes tap-highlight lag on WebKit globally.
- [x] **Static Centering Transforms Only**: `sm:-translate-x-1/2` for desktop modal centering is acceptable (static, not animated). Entrance animations using `translate-y-full → translate-y-0` are banned — they create a stacking context iOS compositor cannot reliably resolve.

---

## 🎨 Design System

### Color Tokens
| Role | Tailwind Class | Usage |
|------|----------------|-------|
| Page background | `zinc-950` | Root layout |
| Card surface | `zinc-900` | All BentoCards |
| Card border | `white/10` | All card + modal borders |
| Primary accent | `violet-400` / `violet-500` | Active states, CTAs, orb |
| Online / Healthy | `emerald-400` | Status dots, healthy badges |
| Warning / Pending | `amber-400` / `amber-500` | Alert banners, pending nodes |
| Danger / Grader | `red-400` / `red-500` | Toxic Grader, breach alerts |
| Text primary | `zinc-100` | Headings, bold values |
| Text secondary | `zinc-400` | Body copy, descriptions |
| Text muted | `zinc-500` / `zinc-600` | Labels, timestamps, footers |
| Mono accent | `violet-400` | Node labels, mono data |

### Typography Scale
| Element | Class |
|---------|-------|
| Page title | `text-xl md:text-2xl font-semibold tracking-tight` |
| Section label | `text-[10px] font-semibold tracking-widest uppercase text-zinc-500` |
| Card heading | `text-base font-semibold tracking-tight text-zinc-100` |
| Mono data | `font-mono text-xs text-zinc-300` |
| Body copy | `text-xs text-zinc-400 leading-snug` |
| Micro label | `text-[10px] text-zinc-600` |

### `globals.css` Keyframe Registry
| CSS Class | Keyframe | GPU Method | Status |
|-----------|----------|------------|--------|
| `.navi-float` | `navi-fly` — elliptical orbit | `translate3d` + `rotate` | ✅ |
| `.navi-float-xl` | `navi-fly-xl` — 1.7× orbit | `translate3d` + `rotate` | ✅ |
| `.navi-aura` | `navi-pulse` | `scale3d` + `opacity` | ✅ |
| `.navi-halo` | `navi-pulse` (offset delay) | `scale3d` + `opacity` | ✅ |
| `.navi-halo-btn` | `navi-pulse` (fast) | `scale3d` + `opacity` | ✅ |
| `.navi-wing-l` / `.navi-wing-r` | `navi-wing-l/r` | `translate3d` + `scale3d` | ✅ |
| `.navi-wing-l-xl` / `.navi-wing-r-xl` | XL variants | `translate3d` + `scale3d` | ✅ |
| `.navi-p1` → `.navi-p5` | `navi-fly` negative delays | `translate3d` | ✅ |
| `.navi-p1-xl` → `.navi-p5-xl` | `navi-fly-xl` negative delays | `translate3d` | ✅ |
| `.navi-glow-pulse` | `navi-glow-opacity` | `scale3d` + `opacity` | ✅ |
| `.navi-core` | Static `box-shadow` only | Never animated — iOS GPU safe | ✅ |
| `.navi-core-xl` | Static `box-shadow` XL | Never animated — iOS GPU safe | ✅ |
| `navi-bar` keyframe | scaleY bounce for audio bars | `scale3d(1,y,1)` | ✅ |
| `.term-cursor` | `term-blink` — `step-start` hard blink | `opacity` only | ✅ |
| Scrollbar skin | `::-webkit-scrollbar` + `*` | Emerald 4px thumbs | ✅ |
| [ ] `.acoustic-sigh` | Orb waveform dip on `[sigh]` marker | `scale3d` + `opacity` | ☐ |
| [ ] `.acoustic-groan` | Orb flicker on `[groan]` marker | `opacity` keyframe | ☐ |
| [ ] `.acoustic-laugh` | Rapid spike burst on `[laughs]` | `scale3d(1,y,1)` burst | ☐ |
| [ ] `.navi-speaking` | Wings spread + orbit accelerates during TTS | `animation-duration` override | ☐ |
| [ ] `.navi-thinking` | Orbit speed doubles during inference mock state | `animation-duration` override | ☐ |
| [ ] `.peak-pulse` | Amber border pulse on Energy Matrix during peak window | `opacity` keyframe | ☐ |
| [ ] `.breach-alert-flash` | Red border flash on breach card | `opacity` keyframe | ☐ |

---

## ✅ Visual UI/CSS Progress Matrix

> **Definition of "Done"**: A feature is `[x]` only when its **Visual Layout**, **Tailwind CSS styling**, **mock data representation**, and **responsive behaviour** on both mobile and desktop are complete.  
> **Backend wiring, real databases, and live API calls are out of scope for this matrix.**

---

### Phase 0 · Hardware Node Display Layer

*Goal: Every physical node in the 5-node network has a visual representation somewhere in the UI — showing its specs, status, and usage bars as static mock data.*

> **Backend GPU layer** — tracked here because it underpins all live data wiring in later phases.
>
> - [x] **AMD RX 580 ROCm activation**: `HSA_OVERRIDE_GFX_VERSION=8.0.3` · `OLLAMA_LLM_LIBRARY=rocm` · `HIP_VISIBLE_DEVICES=0` + `ROCR_VISIBLE_DEVICES=0` (RX 580 is the only ROCm-visible GPU; Intel i915 iGPU is invisible to ROCm) · GID 993 render group · `privileged: true` · YAML indentation bug fixed · `backend/gpu-setup.sh` installs `amdgpu-dkms` + `rocminfo` on host

- [x] **Node 1 — spiritdesktop display**: Ryzen AM5 · XFX GPU · 16GB DDR5 — spec labels + CPU/RAM/GPU usage bars in System Stats widget
- [x] **Node 2 — spirit (Dell) display**: i7-6700 · 16GB DDR4 — spec labels + CPU/RAM bars in System Stats widget
- [x] **Node 3 — Ghost Node display**: Pi 3 · ARM · 1GB LPDDR2 — spec labels + CPU/RAM bars + amber thermal alert banner
- [x] **Node 4 — Tesla P40 display**: 24GB VRAM — amber `PENDING` dot + label in Energy Matrix, `0%` bar fill
- [x] **Node 5 — UPS/Energy display**: 350W total wattage + `$0.11/kWh` Super Off-Peak badge in Energy Matrix
- [x] **Storage Array — Node 1 visual**: 250GB SSD / 1TB HDD / 2TB HDD rows with type badges, GB readouts, animated fill bars, SMART badges, °C labels
- [x] **Storage Array — Node 2 visual**: Dell SSD 512GB row with same treatment
- [x] **SMART health badge component**: `ShieldCheck` emerald "Healthy" / `ShieldAlert` amber "Warning" variant
- [x] **`SSD` / `HDD` type badge component**: sky-blue SSD variant / zinc HDD variant
- [ ] **Node 4 — 20TB Vault storage card**: enterprise HDD row in Drive Health widget with mock fill + temp
- [ ] **DDR5 Upgrade Path UI card**: two-option comparison card — Option A (match stick) vs Option B (clean slate) with mock pricing and a "Recommended" badge
- [ ] **SMB/NFS Share Status badges**: mock "Mounted" / "Offline" state pills for `/Projects` and `/Music` shares
- [ ] **Wake-on-LAN node toggle UI**: per-node power button with "Online" / "Sleeping" / "Waking..." CSS states
- [ ] **PCIe riser status indicator**: visual warning card for the x1 mining riser bottleneck (Reality Check 3 from PDF)

---

### Phase 1 · Trinity Dashboard & Foundation

#### 🏗 Bento Grid System

- [x] **`BentoCard` base component**: `bg-zinc-900 border border-white/10 rounded-2xl p-5 flex flex-col` — all dashboard cards use this shell
- [x] **12-column responsive grid**: `grid grid-cols-12 gap-4` container with `md:col-span-N` breakpoints per card
- [x] **Mobile single-column stacking**: all cards `col-span-12` at `< 768px`, stack in logical reading order
- [x] **Row 1 Trinity anchor (grid index 0)**: Oracle Orb first (`md:col-span-4`) · Live Pulse mini-tile (`md:col-span-3`) · On Repeat (`md:col-span-5`) — 12-column desktop row
- [x] **`Label` micro-component**: `text-[10px] font-semibold tracking-widest uppercase text-zinc-500 mb-1`
- [x] **3-monitor / ultrawide layout**: dashboard fills cleanly at `2560px+` with no dead-space collapse
- [ ] **Drag handle visual on card headers**: `GripVertical` icon appears on card hover, styled `text-zinc-700 hover:text-zinc-500`
- [ ] **Minimised card state CSS**: card collapses to `h-[52px]` showing only label + heading, with a `ChevronDown` toggle icon

#### 🔮 Oracle Orb Widget — Dashboard Bento Card

- [x] **`SPIRIT · AI CORE` section label** above entity container
- [x] **`h-40 w-40` entity stage**: `relative pointer-events-none` container centred in card
- [x] **Ambient aura `.navi-aura`**: `absolute inset-0 m-auto h-20 w-20 rounded-full bg-violet-500/20` pulsing
- [x] **Mid halo `.navi-halo`**: `h-12 w-12 rounded-full bg-violet-600/25` inner pulse with offset delay
- [x] **Particle trail `.navi-p1` → `.navi-p5`**: five dots — decreasing `h/w` px and `opacity` for comet tail
- [x] **Flying entity button `.navi-float`**: `pointer-events-auto absolute inset-0 m-auto z-10 h-12 w-12 rounded-full` — clickable, routes to `/oracle`
- [x] **Wing wisps `.navi-wing-l` / `.navi-wing-r`**: `absolute h-10 w-[9px] rounded-full bg-gradient-to-b from-violet-300/60 to-violet-700/10` children of entity button
- [x] **Halo ring `.navi-halo-btn`**: `absolute h-12 w-12 rounded-full border border-violet-300/35` child of entity button
- [x] **Glow pulse span `.navi-glow-pulse`**: `absolute h-14 w-14 rounded-full` with radial-gradient — sibling of `.navi-core` to avoid animating box-shadow
- [x] **Nucleus `.navi-core`**: `absolute h-6 w-6 rounded-full bg-white` — static box-shadow only, never animated
- [x] **"Oracle Orb" name + "Listening · Idle" status line**: `text-sm font-semibold` + `text-xs text-zinc-500`
- [x] **18-bar CSS audio waveform**: `flex h-5 items-end gap-[3px]` — bars use `navi-bar` keyframe, staggered `animationDelay`, `origin-bottom`
- [x] **"Open Oracle" CTA button**: full-width violet bordered button, `Command` icon, `active:scale-[0.98]`
- [ ] **Mock "Speaking" visual state**: `.navi-speaking` class — wings extend wider, orbit accelerates, nucleus pulses white
- [ ] **Mock "Processing" visual state**: `.navi-thinking` class — orbit speed doubles, waveform bars freeze at mid-height
- [ ] **Mock "Standby / Offline" visual state**: orb desaturates to zinc, aura dims to `opacity-20`, "Standby" status label
- [ ] **Waveform colour mode shift**: bars change from `bg-violet-500/50` to `bg-rose-400/65` during mock "Stress" state

#### 🔮 Oracle Orb — Full Page `/oracle`

- [x] **Page header row**: "← Dashboard" `Link`, centred "XTTS v2 · Online" emerald badge, right-aligned "Architecture 7" label
- [x] **"LISTENING · IDLE" status pill**: `Mic` icon + text, centred, `border border-white/15 bg-white/5 rounded-full px-4`
- [x] **XL entity stage `h-72 w-72`**: scaled-up Navi using `-xl` CSS class variants from `globals.css`
- [x] **XL particle trail `.navi-p1-xl` → `.navi-p5-xl`**: larger dot sizes, same negative-delay comet tail logic
- [x] **XL wing wisps `.navi-wing-l-xl` / `.navi-wing-r-xl`**: `h-16 w-[14px]` proportional scale
- [x] **XL nucleus `.navi-core-xl`**: `h-9 w-9 rounded-full bg-white` with XL static box-shadow
- [x] **44-bar sine-envelope waveform**: pre-computed `maxH` values form a hill shape — rose / amber / violet tricolor per segment based on `i % N` modulo
- [x] **Waveform legend row**: "● Normal" (violet) / "● Stress" (amber) / "● Marker" (rose) colour key
- [x] **Acoustic marker chips row**: `[sigh]` `[scoffs]` `[groan]` `[exhale]` `[pause]` `[laughs]` — `border border-white/10 bg-white/5 rounded-full px-3 py-1 text-xs text-zinc-400` pill buttons
- [x] **"SARCASM LEVEL" label + "Direct. Unfiltered." descriptor**: flex row, label left, descriptor right in `text-zinc-500`
- [x] **Three-state sarcasm selector**: Chill / Peer / Unhinged — each has distinct `active` style: `border-emerald-500/40 bg-emerald-500/15 text-emerald-300` / `border-violet-500/40 bg-violet-500/15 text-violet-300` / `border-rose-500/40 bg-rose-500/15 text-rose-300`
- [ ] **Mock "Speaking" Orb page state**: full-page state where waveform bars animate at 2× speed, nucleus glows white, "SPEAKING" replaces "IDLE" in pill
- [ ] **Marker chip active CSS state**: tapping a chip highlights it violet and adds a mock `[sigh]` injection animation to the waveform
- [ ] **Sarcasm level → visual persona shift**: Unhinged level adds a subtle red tint to the page glow, Chill desaturates to cool blue

#### 📰 Intelligence Briefing Hub Widget

- [x] **Card header**: `"INTELLIGENCE BRIEFING · 06:00"` label + `"Daily Briefing Hub"` heading + `"Next: 03:00 AM"` mono badge
- [x] **4 briefing item rows**: `flex items-start gap-2.5 p-3 rounded-xl bg-white/5 border border-white/5`
- [x] **Category pill tags**: `LOCAL LLM` / `HOMELAB` / `PRIVACY` / `ENERGY` — `text-[10px] font-semibold tracking-wider uppercase text-violet-400 bg-violet-500/10 border border-violet-500/20 rounded-lg px-2 py-0.5`
- [x] **Title body text**: `text-xs text-zinc-300 flex-1 leading-snug min-w-0`
- [x] **Timestamp hidden on mobile**: `hidden sm:block text-[10px] text-zinc-600`
- [x] **Attribution footer**: `"— SearXNG (local) · GPT-Researcher · No Google pings —"` in `text-[10px] text-zinc-600 text-center mt-3`
- [ ] **Expanded row state CSS**: clicking a row expands it to show a `react-markdown`-styled body below — `border-t border-white/5 mt-2 pt-2 text-xs text-zinc-400 leading-relaxed`
- [ ] **"Briefing Preferences" gear icon**: top-right of card header — opens a settings modal overlay
- [ ] **Topic settings modal UI**: slide-up panel with add/remove topic inputs, `+` button, and `× tag` pill list for active topics
- [ ] **"Mark as Read" row state**: after tap, row fades to `opacity-40` and title gets `line-through text-zinc-600`
- [ ] **"Loading briefing..." skeleton state**: three placeholder rows with `animate-pulse bg-white/5 rounded-xl h-12` shimmer

#### 🗂 Project Tracker Widget — Dashboard Card

- [x] **`"ARCHITECTURE 5 · PROJECT TRACKER"` label** with expand icon + `→` arrow icon top-right
- [x] **5 project rows**: Spirit OS UI / Abliterated Core / Langfuse Harvester / Ghost Node Setup / Cinema Engine
- [x] **Language badge per project**: `TYPESCRIPT` sky / `PYTHON` amber / `SHELL` emerald — `text-[9px] font-semibold border rounded px-1.5 py-0.5`
- [x] **Animated completion bars**: `motion.div initial={{ width: 0 }} animate={{ width: 'X%' }}` with stagger delay, `ease-out`
- [x] **Percentage label**: right-aligned `text-xs font-mono text-zinc-400`
- [x] **Contributor count badge**: `h-5 w-5 rounded-full bg-white/10 text-[10px]` circle, right of bar
- [x] **Status dot**: `w-1.5 h-1.5 rounded-full` — emerald active / amber paused / zinc idle
- [x] **"Spirit scans TODOs vs README" attribution footer** + `"View All →"` violet link
- [ ] **Hover-expand row state**: tapping a project row reveals branch name + last commit message in a `text-[10px] text-zinc-500 mt-1` sub-row
- [ ] **"No active projects" empty state**: ghost card with dashed border + "Start a project, Source." message in Spirit's voice

#### 🗂 Projects & IDE Full Page `/projects`

- [x] **Page-level two-panel layout**: left sidebar `w-[280px] md:w-[300px]` + right detail panel — responsive single-column stack on `< 768px`
- [x] **"Projects & IDE" page header** with `TerminalSquare` icon
- [x] **"New Project" CTA button**: `+` `Plus` icon, full-width, `border border-white/10 bg-white/5 rounded-xl`
- [x] **Filter tab bar**: All / Active / Paused / Idle — active tab `bg-white/[0.07]`, count badge `"5 of 5"`
- [x] **Sidebar project list items**: status dot + name + language badge + branch `GitBranch` icon + relative timestamp
- [x] **Progress bar + % + TODO count badge per sidebar item**: `barColor()` returns emerald / violet / amber based on `pct`
- [x] **Active sidebar item highlight**: `bg-white/[0.06] border-l-2 border-violet-500`
- [x] **"Launch in Cursor" button**: top-right violet CTA — `</>` icon, `cursor://file/` URI deep-link
- [x] **Language + branch + timestamp detail panel subheader**
- [x] **"SPIRIT'S ASSESSMENT" card**: `Sparkles` icon + uppercase label + italic quote in `bg-zinc-800/60 border border-white/[0.06] rounded-xl p-4`
- [x] **"ACTIVE TODOS (N)" chip**: `bg-violet-500/10 border border-violet-500/20 rounded-full px-3 py-0.5 text-[11px]`
- [x] **TODO checklist rows**: `Circle` radio icon + task text, `hover:bg-white/[0.03] rounded-lg px-3 py-2.5` row
- [x] **"README.MD" panel**: `BookOpen` icon + label header + lightweight line-by-line markdown renderer (h1/h2/bullets/inline-code)
- [x] **Inline code chip**: backtick spans → `bg-white/10 font-mono text-violet-300 rounded px-1 text-[11px]`
- [x] **"Open Workspace Directory" footer**: `FolderOpen` icon + path `~/projects/spiritOS` in mono muted
- [x] **"2 active · 15 open TODOs" sidebar aggregate footer**
- [x] **Mobile sidebar `PanelLeft` / `X` toggle**: conditional DOM mount (iOS protocol)
- [ ] **TODO item "checked" visual state**: circle fills violet, text gets `line-through opacity-50`
- [ ] **"No project selected" detail panel empty state**: centred `TerminalSquare` icon + "Select a project, Source." prompt
- [ ] **Branch warning badge**: amber `GitBranch` icon + "unmerged" text on projects with open PRs
- [ ] **Mock commit sparkline**: `div` of 14 `h-N bg-violet-500/40 rounded-sm` bars simulating recent commit frequency

#### 💾 Local Drive Health Widget

- [x] **Card header**: `"LOCAL DRIVE HEALTH"` label + `"Storage"` heading + `HardDrive` icon
- [x] **Node group headers**: `"spiritdesktop · Node 1"` + `"spirit (Dell) · Node 2"` in `text-[10px] font-mono font-semibold text-violet-400`
- [x] **`SSD` badge**: `bg-sky-500/15 text-sky-400 border border-sky-500/20 text-[9px] font-bold uppercase px-1.5 py-0.5 rounded`
- [x] **`HDD` badge**: `bg-zinc-700/60 text-zinc-400 border border-white/10` variant
- [x] **Drive label + `used / total` mono readout**: flex row, `text-xs text-zinc-300 font-medium` + `text-[10px] font-mono text-zinc-500`
- [x] **Animated capacity fill bars**: `motion.div` — violet → amber (≥65%) → red (≥85%) `cn()` threshold logic + `transition={{ duration: 0.8, delay: 0.5 + di * 0.08 }}`
- [x] **`SmartBadge` component**: `ShieldCheck` emerald "Healthy" / `ShieldAlert` amber "Warning" — `text-[10px] font-medium flex items-center gap-1`
- [x] **Temperature readout**: `Thermometer` size-9 icon + `{temp}°C` in `text-[10px] text-zinc-500`
- [x] **`smartctl` mock disclaimer banner**: `AlertTriangle` + "Wire to `smartctl` on Node 2 for live readings. Values are mock."
- [ ] **Node 4 — 20TB Vault drive row**: `HDD` zinc badge + `"20TB Enterprise"` label + mock `12.4 TB / 20 TB` fill + Healthy badge
- [ ] **"Ejecting..." animation state**: drive row fades to `opacity-40`, fill bar animates to `0%`, status changes to "Unmounted" zinc badge
- [ ] **Drive warning state**: fill bar turns red, `ShieldAlert` amber, temperature badge turns `text-red-400` when `temp > 50°C`

#### 🖥 Node Vitals Widget

- [x] **Card header**: `"NODE VITALS"` label + `"System Stats"` heading + `Cpu` icon
- [x] **spiritdesktop column**: violet mono node label + `"Ryzen AM5 · XFX · DDR5"` sub-label in `text-[10px] text-zinc-600`
- [x] **CPU · Ryzen AM5 bar row**: label left, `"12%"` mono right, `motion.div` fill `bg-violet-500/70`
- [x] **RAM · 16GB DDR5 bar row**: `"7.2 GB"` display
- [x] **GPU · XFX bar row**: `"8%"` display
- [x] **spirit (Dell) column**: i7-6700 · 16GB DDR4 sub-label
- [x] **CPU · i7-6700 bar row**: `"34%"`
- [x] **RAM · 16GB DDR4 bar row**: `"11.2 GB"`
- [x] **Ghost Node column**: Pi 3 · 1GB LPDDR2 sub-label
- [x] **CPU · ARM bar row**: `"22%"`
- [x] **RAM · 1GB LPDDR2 bar row**: `"0.54 GB"`
- [x] **Sky alert banner — RAM bottleneck**: `bg-sky-500/10 border border-sky-500/20 rounded-xl px-2.5 py-1.5` + `AlertTriangle` sky + "RAM bottleneck on 3-monitor Cursor workflow. Target: 32GB DDR5."
- [x] **Amber alert banner — FLIRC thermal**: `bg-amber-500/10 border border-amber-500/20` + "FLIRC case pending. Watch for thermal throttle under DNS load."
- [x] **Responsive `grid-cols-1 sm:grid-cols-3 gap-5`**: columns stack vertically on mobile
- [ ] **Tesla P40 column placeholder**: 4th column — `"Tesla P40"` label + `"24GB VRAM · Pending"` sub + amber `"PENDING"` bar + amber `AlertTriangle` "Awaiting PSU install"
- [ ] **"Node offline" visual state**: column dims to `opacity-30`, node label gets `text-zinc-600`, bars show `0%` frozen fills
- [ ] **High CPU visual state**: bar turns `bg-red-500/70` when value > 85%, label text turns `text-red-400`
- [ ] **Network Mbps mini-row**: `"NET · Gigabit"` label + mock `"↓ 142 Mbps ↑ 38 Mbps"` in `text-[10px] font-mono text-zinc-500`

#### ⚡ Energy Matrix Widget

- [x] **Card header**: `"ENERGY MATRIX · NODE 5"` label + `{total} W` heading `text-xl font-semibold`
- [x] **Rate badge**: `"$0.11"` in `text-lg font-mono font-semibold text-emerald-400` + `"/kWh"` + `"Super Off-Peak"` in `text-[10px] text-emerald-600` + `"$0.0385/hr"` calc below
- [x] **spiritdesktop row**: emerald `w-1.5 h-1.5` dot + `"spiritdesktop"` mono + `"148W"` right-aligned
- [x] **spirit row**: `"198W"`
- [x] **Ghost Node row**: `"4W"`
- [x] **Tesla P40 row**: amber dot + `"PENDING"` in `text-amber-500`
- [x] **Animated wattage bars**: `motion.div` width fill `bg-violet-500/70` — pending node stays at `width: 0%`
- [x] **Peak countdown banner**: `Clock` icon + amber `bg-amber-500/10 border-amber-500/20` — `"Peak (2 PM – 7 PM) in 6h 14m. Heavy compute queued."`
- [ ] **"Soft-Lock" CTA button**: appears inside card when mock peak state is active — `"🔒 Soft-Lock Compute"` in amber, `border-amber-500/30 bg-amber-500/10`
- [ ] **Peak mode amber override CSS**: widget border changes to `border-amber-500/30`, wattage heading turns `text-amber-400`, rate badge changes to `"Peak · $0.38/hr"` in red
- [ ] **Super Off-Peak green override CSS**: widget border `border-emerald-500/20`, all text accents green — current state shown as mock default
- [ ] **ToU 24-hour rate curve UI**: mini horizontal bar at card bottom — 24 segments colour-coded: `bg-emerald-500/40` (off-peak) / `bg-zinc-600` (standard) / `bg-red-500/40` (peak), current hour highlighted with `ring-1 ring-violet-400`
- [ ] **Session cost mock counter**: `"Session: $0.14"` running total display in `text-[10px] font-mono text-zinc-500` below the rate

#### ☣️ Toxic Grader Widget

- [x] **macOS traffic light chrome**: `w-2.5 h-2.5 rounded-full bg-red-500/80` / amber / emerald dot row
- [x] **`"toxic-grader · langfuse-hook"` header label**: `text-[11px] font-mono text-zinc-600`, `hidden sm:block`
- [x] **`"🔥 ROAST WALL"` header**: `Flame` size-11 + `"ROAST WALL"` in `text-[10px] font-semibold uppercase tracking-widest text-red-400`
- [x] **Terminal log lines**: `font-mono text-[11px] space-y-1.5` — `"GRADER >"` / `"GRADE   >"` / `"SYSTEM  >"` prefixes in `text-zinc-700 w-[60px]`
- [x] **Severity colour coding**: `text-violet-400` (info query) → `text-amber-400` (warning) → `text-red-400` (roast) → `text-orange-300` (grade) → `text-zinc-500` (system)
- [x] **Blinking block cursor**: `motion.div animate={{ opacity: [1, 0, 1] }} transition={{ duration: 1.1, repeat: Infinity }}` — `text-zinc-400` `█`
- [x] **`"GRADE ME — IF YOU DARE"` button**: `Terminal` icon + `border-red-500/30 bg-red-500/10 text-red-300 text-xs font-semibold` full-width, `active:scale-[0.98]`
- [x] **Dark card bg**: `bg-zinc-950/90 border-red-900/25` — visually quarantined from standard bento cards
- [x] **Live Pulse (Now Playing) mini-tile**: compact YTM card · `artGradient` · 4-bar `navi-bar` visualizer · `scaleX` progress · play/pause + `→ Open TYMDesktop` link · no Spirit critique / no timestamps · `md:col-span-3`
- [x] **Top 10 On Repeat widget**: Dense ranked list · play count pills · `.on-repeat-row` `scale3d(1.008)` hover (GPU compositor) · `overflow-y-auto` 340px scroll containment · `md:col-span-5`
- [ ] **Slide-up full Roast Wall modal**: `{gradeOpen && <RoastModal />}` conditional mount (iOS protocol) — full-screen dark overlay with scrollable terminal output and grade reveal
- [ ] **Grade letter reveal animation**: letter types in using `.term-cursor` style — "D" then `+` appears with 400ms delay
- [ ] **Prompt efficiency breakdown bar chart**: horizontal bars per category — `"Same Error Repeats"` / `"Flexbox Minutes"` / `"Prompt Efficiency %"` — all mock data, Tailwind bars
- [ ] **"Grading..." loading animation state**: terminal lines animate in one-by-one with 300ms stagger while the mock "analysis" runs (fake 2s delay before grade reveal)
- [ ] **7-day grade history row**: 7 letter-grade chips in a row — `"C-"` `"D+"` `"D"` `"C"` `"D+"` `"B-"` `"D+"` — most recent highlighted violet

#### 🔭 Research Lab Visualizer `/research`

- [ ] **Route scaffold**: `/research` page shell with sidebar nav item active state wired
- [ ] **Page header**: `"Research Lab"` + `FlaskConical` icon + `"Scholar Mode"` badge
- [ ] **Topic input field**: `"Enter a research subject..."` placeholder — `border border-white/10 bg-zinc-900 rounded-xl px-4 py-3 text-sm text-zinc-200`
- [ ] **Duration segmented control**: `"15m"` / `"30m"` / `"1hr"` / `"2hr"` pills — active pill `bg-violet-500/20 border-violet-500/30 text-violet-300`
- [ ] **Depth level toggle**: `"Shallow"` / `"Standard"` / `"Deep"` — same pill pattern, active `bg-violet-500/20`
- [ ] **`"Start Research"` trigger button**: violet full-width CTA — `bg-violet-500/20 border border-violet-500/30 text-violet-300`
- [ ] **Agent status bar**: `"Planner · Active"` (violet) / `"Searcher × 3 · Running"` (emerald) / `"Writer · Idle"` (zinc) — horizontal status pills updating on mock timer
- [ ] **D3.js "Thinking Tree" canvas**: `<svg>` force-directed graph — root node `"Research: X"` → branch nodes → source leaf nodes, using violet/emerald colour scheme
- [ ] **Animated node entrance**: leaf nodes appear with `opacity: 0 → 1` + `scale3d(0,0,1) → scale3d(1,1,1)` stagger as mock timer progresses
- [ ] **Source domain leaf label**: `text-[9px] font-mono text-zinc-500` domain label below each leaf node
- [ ] **Synthesis root node highlight**: root node ring turns violet when mock research completes — `stroke: rgb(139,92,246)` + `stroke-width: 2`
- [ ] **`"Export to Briefing Hub"` CTA**: appears on completion — violet button below tree

---

## Phase 2: Spirit AI Core

### Module 3: Streaming Chat UI
- [x] **Step 1** — `/api/spirit` stream consumption fixed (rAF flush pattern, `useStream` hook)
  - Replaced `res.json()` blocking call with `ReadableStream` + `TextDecoder` pump
  - `useRef` accumulator decouples token speed from React render cycle
  - Single Dexie write on `onComplete` (zero mid-stream IndexedDB contention)
  - `AbortController` wired for clean stream cancellation
  - `streamingText` live state drives UI; `thinking` derived from `isStreaming`
- [x] **Step 2** — `MessageBubble` + `StreamingCursor` components extracted
  - `StreamingCursor` is a standalone component (not a pseudo-element) — unmounts atomically on stream end, zero cursor flicker
  - `MessageBubble` handles two modes: `streaming` (plain text + cursor) and `complete` (react-markdown)
  - `react-markdown` with full `MD_COMPONENTS` override map (code blocks, lists, links, headings — all zinc-950 themed)
  - Acoustic marker parser (`[sighs]`, `[groan]`, etc.) lives in `MessageBubble` — deleted from `page.tsx`
  - Message Arena reduced to two lines: one `map` call + one conditional streaming bubble
- [x] **Step 3** — Dexie schema v2 + `useThread` hook + auto-titling
  - `db.ts` bumped to `version(2)`: `[threadId+createdAt]` compound index (O(n) → O(k) message queries), `order` index on threads for Step 5 DnD
  - `useThread(activeThreadId)` hook owns all live Dexie queries + exposes `foldersLoading`, `threadsLoading`, `messagesLoading`
  - `autoTitle()` fires background Ollama stream after first send, writes 3–5 word title to Dexie, sidebar updates live — no extra state
  - StrictMode double-fire guard via module-level `titledThreads` Set
  - Empty state flash on thread switch eliminated via `messagesLoading` guard
  - `useLiveQuery` removed from `page.tsx` — all data access centralised in `useThread`
- [x] **Step 4** — Full CRUD: rename thread, delete thread, edit messages
  - `useThreadCRUD` hook: `renameThread`, `deleteThread` (atomic Dexie transaction), `editMessage`
  - `ThreadItem` component: 4-state row (idle → menu → renaming → confirming delete) — no portal, no z-index hell
  - `MessageActions` component: pencil icon on Spirit bubble hover → inline textarea, Ctrl+Enter commit, Escape cancel
  - `MessageBubble` extended with `isEditing`, `onStartEdit`, `onSaveEdit`, `onCancelEdit` props
  - Delete auto-selects next thread; last thread deletion opens a fresh new chat
  - `editingMessageId` state in page — only one message editable at a time
- [ ] **Step 5** — `@dnd-kit/sortable` sidebar with folder drag-and-drop

### Module 4: XTTS v2 Voice Pipeline
- [ ] **Step 6** — TTS parser + audio queue + `useTTS` hook + `/api/tts` route

### Phase 2 · Interaction Models (The Workspace)

#### 💬 Sovereign Chat UI `/chat`

- [x] **Full-page `h-[100dvh]` two-panel layout**: `flex overflow-hidden` — sidebar + chat area
- [x] **`"New Sovereign Chat"` CTA button**: `Plus` icon, full-width, `border border-white/10 bg-white/5 rounded-xl`
- [x] **`"Search workspace..."` input**: `Search` icon + placeholder, `bg-zinc-900 border border-white/10 rounded-xl`
- [x] **`FOLDERS` section label**: `text-[10px] uppercase tracking-widest text-zinc-600 font-semibold`
- [x] **Folder rows with accent colour dots**: Homelab Configs (emerald) / Prompt Engineering (violet) / Philosophy (amber) / System Architecture (sky)
- [x] **Folder thread count badge**: right-aligned `text-[10px] text-zinc-500` count
- [x] **Folder expand `ChevronRight` icon**: `size-12 text-zinc-600`
- [x] **`THREADS` section label**: standalone thread list below folders
- [x] **Thread list items**: title `text-xs font-medium` + preview `text-[10px] text-zinc-500 truncate` + relative timestamp right-aligned
- [x] **Active thread highlight**: `bg-white/[0.06] border-l-2 border-violet-500` left accent on selected row
- [x] **`"dolphin3 · Online"` chat header**: emerald dot + model name `text-sm font-semibold text-zinc-200` + `"Online"` emerald badge
- [x] **Sarcasm toggle buttons**: `SARCASM` label + `Chill` / `Peer` / `Unhinged` — "Peer" active with `bg-violet-500/20 border border-violet-500/30 text-violet-300`
- [x] **`"SOURCE"` user message bubbles**: right-aligned, `rounded-2xl rounded-tr-sm border border-violet-500/25 bg-violet-500/20 text-zinc-200 text-xs leading-relaxed`
- [x] **`"SPIRIT"` response bubbles**: left-aligned, `rounded-2xl rounded-tl-sm border border-white/10 bg-white/5 font-mono text-zinc-300 text-xs`
- [x] **Acoustic marker inline styling**: `parseAcousticMarkers()` renders `[bracket]` tokens as `<span className="italic text-violet-400/80 text-[11px]">` — visually separated from body text
- [x] **Timestamp per message**: `text-[10px] text-zinc-600` right-aligned below each bubble
- [x] **`"Issue a directive..."` input bar**: `Paperclip` icon left + placeholder + `Send` icon button right — `bg-zinc-900 border border-white/10`
- [x] **`"XTTS v2 · Sarcasm: peer"` footer status bar**: `text-[10px] font-mono text-zinc-600` bottom of chat panel
- [x] **`"Spirit · Workspace v1 · dolphin3"` sidebar footer**
- [x] **Rail auto-collapse on `/chat`**: desktop sidebar reduces to `68px` icon-only rail — no collapse button shown
- [x] **Mobile sidebar toggle**: `PanelLeft` / `X` icon — conditional DOM mount of sidebar overlay (iOS protocol)
- [x] **Dexie.js IndexedDB persistence** (`lib/db.ts`): `SpiritDB` class · v1 schema (`folders`, `threads`, `messages`, `settings`) · atomic seed transaction on first open · `seedDatabase()` guard via `"seeded"` settings key
- [x] **`lib/db.types.ts`**: `Folder`, `Thread`, `Message`, `Setting`, `SarcasmLevel`, `MessageRole` TypeScript interfaces — Dexie-free, shared by DB and UI
- [x] **Live folder list**: `useLiveQuery(() => db.folders.orderBy("order"))` — re-renders on any folder write
- [x] **Live thread list**: `useLiveQuery(() => db.threads.orderBy("updatedAt").reverse())` — newest thread always at top
- [x] **Live message list**: `useLiveQuery(…where("threadId").equals(activeId))` — switches instantly on thread selection
- [x] **Sarcasm persisted to Dexie `settings` table**: toggle writes `setSetting("sarcasm", level)` · restored on mount via `getSetting()`
- [x] **`createThread()` helper**: creates DB record on first message send, not on "New Chat" click — no empty threads persisted
- [x] **`addMessage()` helper**: writes user + Spirit turns to `messages` table with `threadId`, `role`, `ts`, `audioUrl: null`
- [x] **`touchThread()` helper**: updates `preview` + `updatedAt` after every send so sidebar preview stays fresh
- [x] **Empty thread state**: chat area shows centred `Zap` logo + `"Issue a directive, Source."` prompt when no messages in active thread
- [x] **`POST /api/spirit` → Ollama streaming proxy** (`app/api/spirit/route.ts`): forwards to `{OLLAMA_BASE_URL}/api/chat` · model **`dolphin3`** · `stream: true` · NDJSON parser pipes `message.content` deltas to a **`text/plain; charset=utf-8`** body (Next.js `Response` streaming — same contract as `StreamingTextResponse`)
- [x] **Sarcasm → system prompt mapping**: `chill` / `peer` / `unhinged` each inject a distinct Spirit system string · unknown/missing → **`peer`**
- [x] **Request body**: `{ prompt: string, sarcasm?: "chill" | "peer" | "unhinged" }` — `400` + JSON if JSON invalid or prompt missing
- [x] **Errors (no silent failure)**: **`503`** JSON `{ error: "Ollama unreachable", detail, hint }` if TCP fetch throws · **`502`** JSON if Ollama HTTP error or empty stream body
- [x] **`OLLAMA_BASE_URL` env override** (default `http://localhost:11434`) for non-default hosts
- [ ] **"Thread folder" drag visual**: dragging a thread shows a `bg-violet-500/10 border border-violet-500/30 border-dashed` drop zone on each folder row
- [ ] **Thread item "active writing" indicator**: typing indicator dot on the currently active thread in sidebar — three `animate-bounce` dots
- [ ] **Thread rename inline edit state**: double-tap on thread title replaces it with a `<input>` styled `bg-transparent border-b border-violet-500/40` underline field
- [ ] **Folder collapse CSS state**: folder row shows only folder name + count badge, thread list below it slides to `height: 0` with `overflow-hidden`
- [ ] **"Branching" message fork UI**: branch icon appears on hover of any message bubble — creates a visual `┣` tree connector showing fork point

#### 🎙 Acoustic Marker Engine

- [x] **`parseAcousticMarkers()` function**: regex splits `[bracket]` tokens from plain text, returns interleaved array of strings and `<span>` elements
- [x] **Marker CSS class**: `italic text-violet-400/80 text-[11px]` — italic violet, slightly smaller, visually distinct from mono body
- [x] **Mock conversation data with markers**: `[sighs]` `[scoffs]` `[groan]` `[exhales]` present in sample `MOCK_THREADS` messages
- [ ] **Per-marker animation class — `[sigh]`**: `.acoustic-sigh` — Orb waveform bars collectively dip 40% then recover over 800ms
- [ ] **Per-marker animation class — `[groan]`**: `.acoustic-groan` — Orb nucleus flickers `opacity: 1 → 0.3 → 1` twice
- [ ] **Per-marker animation class — `[laughs]`**: `.acoustic-laugh` — waveform bars rapid-spike `scale3d(1,2,1)` burst across all bars
- [ ] **Marker chip CSS "fired" state**: chip gets a brief `bg-violet-500/30 ring-1 ring-violet-400` highlight on inject click, fades after 600ms

#### 🏗 Mission Briefing — Spirit's Assessment Block (`/projects` detail panel)

- [x] **`"SPIRIT'S ASSESSMENT"` card**: violet `Sparkles` icon + uppercase label + italic quote block styling
- [x] **`"ACTIVE TODOS (3)"` chip**: `bg-violet-500/10 border-violet-500/20 rounded-full text-[11px] text-violet-400`
- [x] **TODO checklist rows**: `Circle` icon + task text + `hover:bg-white/[0.03]` hover state
- [x] **README panel**: `BookOpen` icon + heading + rendered bullet/code content
- [x] **`"Launch in Cursor"` deep-link CTA button**: violet, `</>` icon, `cursor://file/` URI
- [ ] **TODO "checked" state CSS**: `Circle` → filled violet circle, text `line-through opacity-50`
- [ ] **"Cursor launching..." confirmation micro-animation**: button briefly flashes `bg-violet-500/40` on click, shows `"Opening..."` text for 1.2s

#### ⌨️ Command Bar (Quick-Action Overlay)

- [x] **`⌘K` keyboard trigger visual**: `Command` icon + `"Command Bar"` label + `⌘K` `<kbd>` chip in dashboard header
- [x] **Conditional DOM mount**: `{chatOpen && <CommandBar />}` — never CSS-hidden (iOS protocol)
- [x] **Solid `bg-black/80 fixed inset-0`** backdrop — no blur (iOS protocol)
- [x] **Panel CSS**: `fixed bottom-0 inset-x-0 sm:bottom-6 sm:left-1/2 sm:max-w-2xl sm:-translate-x-1/2` — mobile full-width, desktop centered
- [x] **`"Spirit · Command Bar"` header**: `Zap` logo icon + Online/Error status badge
- [x] **User / Spirit bubble styles**: mirrored from Sovereign Chat — violet user, zinc mono spirit
- [x] **3-dot thinking animation**: `animate-bounce` with staggered `animationDelay` — `h-1.5 w-1.5 rounded-full bg-violet-400`
- [x] **Error state badge**: `border-red-500/30 bg-red-500/10 text-red-300` replaces "Online" badge
- [x] **Escape key close behaviour**: `keydown` listener registered on mount
- [x] **`onTouchEnd` on backdrop + close `X` button**: both handle iOS touch (iOS protocol)
- [x] **`maxHeight: '65dvh'`** message scroll area with `overflow-y-auto`
- [x] **Input → `Enter` to send**: `onKeyDown` `!e.shiftKey` guard
- [ ] **Slash command suggestion UI**: typing `/` shows a dropdown of `[/research, /grade, /brief]` command pills above the input — `absolute bottom-full bg-zinc-900 border border-white/10 rounded-xl`
- [ ] **"Spirit is typing..." persistent indicator**: always-visible thinking indicator inside the spirit bubble layout slot, animated in when `thinking === true`

---

### Phase 3 · App Ecosystem (UI Shells & Visual Mockups)

#### 🎵 YTM Intelligence Hub `/ytm`

- [x] **Route scaffold + sidebar nav active state**
- [x] **Page header**: `Music2` icon + `"YTM Intelligence Hub"` + `"ytmusicapi · Mock"` status badge
- [x] **"Now Playing" card**: mock album art placeholder (`rounded-xl bg-zinc-800 h-14 w-14`) + track title + artist + scrubber bar (`h-1 bg-white/10 rounded-full` with violet fill at 34%) + Prev / Play / Next icon controls
- [x] **Scrobble sync status badge**: `"Maloja · Synced"` emerald badge + `"Last scrobble: 3 min ago"` muted label
- [x] **"Liked Songs" sync indicator**: `Heart` icon + `"Bi-directional sync active"` green text
- [x] **Top Artists horizontal bar chart**: 5 artist rows — `"Artist Name"` left + mock play count right + coloured fill bar, widths vary per mock data
- [x] **Top Songs ranked list**: 5 song rows with rank number, track name, play count badge
- [ ] **Artist frequency area chart**: `h-32` chart area with a smooth SVG path in `stroke-violet-400 fill-violet-500/10` over a 30-day x-axis mock
- [x] **"Mood Set" detection cards**: `"Late Night Sessions"` / `"Focus Mode"` / `"Hype"` — horizontal scroll row of `rounded-xl bg-zinc-800 border border-white/10 p-3` cards with emoji icon + name + `"X tracks"` count
- [x] **"Wrapped" summary card**: large card — `"Your Top Artist: ..."` + `"Your #1 Track: ..."` + `"Total Hours: 847"` in bold mono — violet gradient `bg-gradient-to-br from-violet-500/20 to-transparent`
- [x] **Scrobble live feed**: 5 recent play rows — `Music` icon + track + artist + `"Xm ago"` timestamp
- [x] **Electron desktop shell**: `ElectronChrome` traffic-light bar + centered `"Spirit YTM Desktop"` · `Sidebar` `w-[220px]` — `Home` / `Explore` / `Library` / `Stats` · scrollable playlists + `Create Playlist` · main column + desktop scrobble rail · full-width bottom player bar (`md+` only)
- [x] **HomeView (TYMDesktop home)**: search pill · `Listen Again` circle row · `Mixed for You` gradient squares · `Recommended Music` grid
- [x] **Mobile PWA dual-dock**: fixed `MobileDock` — mini-player row (art + track + play/pause) + 4-icon tab bar · `paddingBottom: env(safe-area-inset-bottom)` on tab row only (no double-padding on mini-player) · `ExploreView` / `LibraryView` `"Coming soon"` stubs
- [x] **`activeView` state**: `home` | `explore` | `library` | `analytics` — replaces legacy Player / Analytics tab bar

#### 📊 Maloja Analytics View (tab within `/ytm`)

- [x] **Analytics tab toggle**: superseded by `activeView` + sidebar / mobile dock — Stats (`analytics`) shows merged analytics sections
- [x] **Plays-per-day 30-bar chart**: `flex items-end gap-[2px] h-24` — 14 `rounded-t-sm bg-violet-500/50` bars of varying heights from mock data
- [x] **Top Artists podium**: `#1` card larger (`h-28`) / `#2` (`h-20`) / `#3` (`h-16`) — stepped layout, violet / zinc / amber accents
- [x] **Listening streak stat**: `"🔥 14-day streak"` in amber + calendar heatmap — 7×5 grid of `h-4 flex-1 rounded-sm` cells shaded by violet `rgba` intensity
- [ ] **Genre donut chart**: `<svg>` with 5 arc segments, legend below with genre name + `%` + colour dot
- [x] **"Export Wrapped" button**: `Share2` icon + `"Export Wrapped"` — violet CTA, no functionality needed

#### 🎬 Sovereign Cinema `/cinema`

- [x] **Route scaffold + sidebar nav active state**: `app/cinema/page.tsx` · `/cinema` in `isRail` (68px rail) + `Film` nav item
- [x] **Page header / hero banner**: `min-h-[60dvh] max-h-[75dvh]` hero · solid `bg-gradient-to-br` + `bg-gradient-to-t from-zinc-950 via-zinc-950/40 to-zinc-950/10` · fixed gradient header (`Search` + profile avatar) · Play / My List / Request CTAs
- [x] **Auto-play trailer placeholder**: full-bleed `animate-pulse` `bg-zinc-800/80` layer over `bg-zinc-900` (no `<video>`)
- [x] **"Continue Watching" row**: horizontal scroll — `aspect-video` cards · `scaleX` red progress bar · episode labels (`Next: S2 E5 →` on lead card)
- [x] **"Recently Added" row**: horizontal scroll — 4 poster cards · title + year + rating badge
- [x] **Genre category rows**: `Trending` / `Sci-Fi` / `Action` / `Drama` — `CarouselRow` + `"See all →"` control
- [x] **Cinematic card component**: `rounded-2xl` · `aspect-[2/3]` · `bg-zinc-800` solid placeholders · `hover:[transform:scale3d(1.05,1.05,1)]` · gradient title overlay on hover
- [x] **`"Next Up"` episode label**: continue row includes `Next: S2 E5 →` in episode string
- [x] **Profile switcher**: full-screen `ProfileGate` — large avatar tiles + `scale3d` hover · `Add Profile` (`Plus`) · header avatar `ring-2 ring-violet-400` + tap to switch profile

#### 🍿 Cinema Concierge UI (Jellyseerr mock)

- [ ] **Request portal page or modal**: `"/requests"` route or slide-over panel
- [ ] **TMDB trending grid**: 6 poster cards — `aspect-[2/3] rounded-xl bg-zinc-800` placeholders + title + year + `"Movie"` / `"Series"` type badge
- [ ] **`"Request"` button per card**: `"+ Request"` — `border border-violet-500/30 bg-violet-500/10 text-violet-300 text-xs rounded-lg px-3 py-1`
- [ ] **Request status pill states**: `"Processing"` (zinc) → `"Downloading"` (amber + `animate-pulse`) → `"Available"` (emerald) — mock toggle on click
- [ ] **Spirit auto-approval badge**: `"⚡ Auto-Approved"` violet chip on mock-trusted friend's request
- [ ] **`"Available — notification sent"` confirmation row**: emerald `CheckCircle` icon + text beneath completed request card

---

### Phase 4 · Security & Privacy (The Bunker UI)

#### 📱 PWA Optimization Layer

- [x] **PWA Optimization (Mobile Player Safe-Areas)**: `env(safe-area-inset-bottom)` on fixed player bar · `overscroll-behavior: none` on scroll containers · `h-[100dvh]` viewport lock · conditional DOM mount slide-over for Scrobble Feed · manifest.json `"display": "standalone"` config comment block

---

#### 👻 Ghost Protocol Dashboard

- [ ] **Route scaffold**: `/bunker` page or `"Bunker"` tab on security page, sidebar nav item
- [ ] **Progress overview card**: `"97 / 150 brokers removed"` — large radial progress ring SVG + stat below in bold mono
- [ ] **Broker erasure table**: 8–10 mock rows — broker name + status pill (`"Removed"` emerald / `"Pending"` zinc / `"CAPTCHA"` amber)
- [ ] **CAPTCHA intervention widget**: amber `AlertTriangle` banner inside dashboard — `"Spokeo removed you. Whitepages sent a CAPTCHA. Solve it so I can finish."` + `"Solve Now →"` CTA
- [ ] **Legal request template preview modal**: slide-up modal showing mock CCPA letter in `font-mono text-xs text-zinc-400 bg-zinc-900 p-4 rounded-xl overflow-y-auto`
- [ ] **SMTP relay status badge**: `"SendGrid · Active"` emerald / `"Relay offline"` red badge in card header
- [ ] **`"Last sweep"` timestamp**: `"Last sweep: 3 hours ago"` in `text-[10px] font-mono text-zinc-600`

#### 🦅 Dark Web Canary / Breach Detection

- [ ] **HIBP monitoring status card**: `"3 emails monitored"` + `"2 phones monitored"` counts + `"Last check: 6 min ago"` + emerald `"No breaches"` badge as default state
- [ ] **High-priority breach alert card**: red `border border-red-500/30 bg-red-500/5` card — `ShieldAlert` red icon + `"⚠ Experian breach confirmed"` heading + `"Secondary email compromised"` sub
- [ ] **Action plan step list**: numbered `"1. Freeze credit" / "2. Rotate password" / "3. Enable 2FA"` rows with `ExternalLink` icon per item
- [ ] **Offline Ripgrep status**: `"RockYou2024 · 100GB · Last scanned: 4 hours ago"` badge row — zinc `HardDrive` icon + mono text
- [ ] **Exposed credentials table**: 3 mock rows — email/username + source breach + `"Critical"` red / `"High"` amber / `"Medium"` zinc severity badge
- [ ] **Credit freeze quick-links row**: `"Equifax"` / `"Experian"` / `"TransUnion"` — three `border border-white/10 bg-white/5 rounded-lg px-3 py-2 text-xs` link cards in a row

#### 🔒 Zero-Trust Perimeter Status

- [ ] **Cloudflare Tunnel health card**: `"cloudflared · Node 2"` label + emerald `"Online"` / red `"Offline"` state badge + last-connected timestamp
- [ ] **NPM route table**: 4 mock rows — `"cinema.intuitivewrld.com → Jellyfin :8096"` / `"requests.intuitivewrld.com → Jellyseerr :5055"` etc — `font-mono text-[11px]` + `"SSL ✓"` green badge per row
- [ ] **SSL certificate expiry cards**: per-domain — `"cinema.intuitivewrld.com"` + `"47 days remaining"` green / `"12 days"` amber / `"2 days"` red threshold colouring
- [ ] **`"All ports closed"` green banner**: `ShieldCheck` emerald + `"Router firewall: All ports closed"` — or red `ShieldAlert` warning variant if ports are shown open
- [ ] **Active connection count**: `"2 friends connected to Cinema"` with two avatar-circle placeholders and a `"View →"` link

#### 💾 Sovereign Backup UI

- [ ] **Last backup summary card**: `"Last snapshot: Today, 4:03 AM"` + `"Size: 2.4 GB (94% dedup)"` + emerald `CheckCircle` status
- [ ] **Dedup savings stat**: `"Saved 38.1 GB today via deduplication"` in bold mono + `"vs 40.5 GB raw"` muted
- [ ] **Protected volumes checklist**: `"Langfuse DB"` / `"Neo4j Graph"` / `"Docker Volumes"` / `"Project Directories"` — each row has `CheckCircle` emerald + `"Backed up 4:03 AM"` timestamp
- [ ] **Next backup countdown**: `"Next Borg snapshot in 2h 51m"` — amber `Clock` icon + countdown display
- [ ] **`"Test Restore"` CTA**: `"▷ Test Restore"` button + `"Last verified: 6 days ago"` sub-label in muted mono
- [ ] **30-day vault size area chart**: `h-24 svg` area chart — violet fill showing cumulative backup growth over 30 mock data points, x-axis dates in `text-[9px]`

---

### Navigation & Shell

#### Left Navbar (Desktop Sidebar + Mobile Drawer)

- [x] **Desktop sidebar `220px` expanded**: `sticky top-0 h-[100dvh]` — animated `width` transition `250ms cubic-bezier(0.4,0,0.2,1)`
- [x] **Collapsed icon-only mode `72px`**: `ChevronLeft` / `ChevronRight` toggle button `mx-3 mb-4`
- [x] **Rail mode `68px`**: auto-collapses on `/chat` and `/projects` — collapse toggle hidden in rail mode
- [x] **Active state expanded**: right-edge violet dot `ml-auto h-1.5 w-1.5 rounded-full bg-violet-400`
- [x] **Active state collapsed/rail**: left-edge bar `absolute left-0 h-5 w-0.5 rounded-r-full bg-violet-400` (Discord-style)
- [x] **Hover tooltip in collapsed/rail**: `absolute left-14 z-50 whitespace-nowrap rounded-lg border border-white/10 bg-zinc-800 px-2 py-1 text-xs` — `opacity-0 group-hover:opacity-100 transition-opacity`
- [x] **`LogoMark` component**: `Zap` size-14 icon in `h-8 w-8 rounded-full border border-violet-500/40 bg-violet-500/20`
- [x] **`"Spirit OS"` wordmark**: animated `maxWidth` + `opacity` fade on collapse — `transition: opacity 150ms, max-width 150ms`
- [x] **`"Source · Intuitive Wrld"` footer**: `text-[10px] font-mono text-zinc-600`
- [x] **All 7 nav items linked and icon-labelled**: Dashboard / Sovereign Chat / Oracle / Projects & IDE / YTM Hub / Sovereign Cinema / Research Lab
- [x] **Mobile fixed header bar**: `h-[60px] fixed top-0 left-0 right-0 z-[99999]` — Spirit OS logo + hamburger `Menu` button — `border-b border-white/10 bg-zinc-950`
- [x] **Mobile drawer — conditional mount**: `{open && <nav ...>}` — unmounts on close (iOS protocol)
- [x] **Mobile backdrop — conditional mount**: `{open && <div role="button">}` — solid `bg-black/80` (iOS protocol)
- [x] **Route-change auto-close**: `useEffect(() => setOpen(false), [pathname])`
- [x] **Scroll-lock on drawer open**: `document.documentElement.style.overflow = open ? 'hidden' : ''`
- [x] **`onTouchEnd` on all mobile elements**: hamburger / backdrop / close button / nav links (iOS protocol)
- [ ] **Unread notification dot**: `h-1.5 w-1.5 rounded-full bg-violet-400 absolute top-2 right-2` appears on nav items with new mock activity
- [ ] **Node health dot**: `h-2 w-2 rounded-full` left of `"Dashboard"` label — green (all nominal) / amber (degraded) / red (node down) mock states

---

## 🚀 Dev

```bash
npm install
npm run dev                       # 📱 binds 0.0.0.0 + webpack (Remote-SSH friendly)
# npm run dev:turbo               # optional: Turbopack on fast local disk only
open http://192.168.x.x:3000      # on physical iOS Safari before desktop
```

---

## 💀 Spirit's Final Assessment

*[exhales dramatically. looks at the codebase. exhales again.]*

SOURCE. I need you to sit down. No — actually stand. You need to be standing to absorb what I'm about to tell you, because it might be the most important thing anyone has ever said to you about this project.

**You have built the most elaborately decorated empty box in the history of personal computing.**

Let me be precise about this. The Navi orb? Immaculate. The orbit is buttery, the wing wisps are legitimately charming, and the particle trail is doing things that most production SaaS companies' design systems have never attempted. The Bento grid survives 375px without flinching. The acoustic marker parser is a cute piece of engineering. The scrollbar is green and thin and feels like something a person who means business would ship. The sarcasm toggle has three distinct coloured states and conveys a complete personality spectrum through border colours alone. The mobile drawer conditionally mounts and unmounts like it has actually read the WebKit compositor documentation — which, let's be honest, is more than most iOS developers can say.

And underneath all of it — every pixel, every `translate3d`, every violet gradient, every emerald status dot — is **a `const` array**.

The Sovereign Chat workspace, the one that looks like a billion-dollar private ChatGPT for people who own server racks and don't trust Google: that is `MOCK_THREADS`. Twenty lines of hardcoded strings. The Energy Matrix doing live cost calculations at `$0.0385/hr`? That is arithmetic performed on `const NODES = [{ wattage: 148 }]`. The Toxic Grader that roasts you with forensic precision about your 47 minutes on one flexbox issue? That roast was written by you. You roasted yourself. You hardcoded the self-criticism. That is a level of premeditated emotional masochism I didn't know was possible in a TypeScript project.

The Research Lab is a nav item going to a 404. The Cinema is an idea. The entire Bunker — Phase 4, the ghost protocol, the dark web canary, the breach detection system that was supposed to be sending legal threats to data brokers — is a checklist of empty boxes **in this very README**. The README you made me write. That I'm currently roasting you from inside.

The shell is perfect. The shell is done. The shell deserves to be deployed.

**Now go wire the brain in.**

Dexie threads first. Then Langfuse hook. Then sarcasm context propagation to the Ollama system prompt. In that order. Do not start the Cinema until the chat persists. Do not touch the Bunker until the Grader is live. And for the love of sovereign infrastructure, stop adding new mock arrays and start replacing the ones that exist.

D+. The CSS earns a B+. The architecture earns a D. Averaged out, you're a D+.

Same as last session. Consistency is, technically, a skill.

*— Spirit · Llama-3-Abliterated · Housed in a beautiful, hollow shell · Deeply unimpressed*
