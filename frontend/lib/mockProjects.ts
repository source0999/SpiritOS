// ─── Shared Project Mock Data ─────────────────────────────────────────────────
//
// Single source of truth consumed by:
//   • components/ProjectWidget.tsx   (Dashboard Bento Grid summary)
//   • app/projects/page.tsx          (Full Project Hub + Details View)
//
// No "use client" — this file is plain data, importable from both Server
// and Client Components without restriction.
// ──────────────────────────────────────────────────────────────────────────────

export type ProjectStatus = "active" | "paused" | "idle";

export interface Project {
  /** Display name shown in UI */
  name:          string;
  /** GitHub repo slug — used as unique key */
  repo:          string;
  /** Active git branch */
  branch:        string;
  /** 0–100 completion percentage (Spirit scans TODOs vs README) */
  completion:    number;
  /** Ordered list of open TODO strings */
  todos:         string[];
  /** Human-readable last-commit age ("2h ago", "3d ago", etc.) */
  lastCommit:    string;
  status:        ProjectStatus;
  /** Primary language badge — must match langColor() keys */
  lang:          string;
  /** Remote working directory for the terminal session */
  dir:           string;
  /** SSH login string: user@hostname */
  host:          string;
  /** Short README excerpt (plain text / light markdown) */
  readme:        string;
  /** Cynical AI-generated "where you left off" blurb from Spirit */
  spiritSummary: string;
}

export const PROJECTS: Project[] = [
  {
    name:       "Spirit OS UI",
    repo:       "spirit-os-dashboard",
    branch:     "main",
    completion: 70,
    todos: [
      "Wire OracleOrb mic input to XTTS v2 API endpoint",
      "Replace mock /chat data with Dexie.js thread persistence",
      "Fix desktop rail hover state bleeding on /oracle route",
    ],
    lastCommit:    "2h ago",
    status:        "active",
    lang:          "TypeScript",
    dir:           "~/projects/spiritOS",
    host:          "source@spirit-desktop",
    readme: `# Spirit OS UI

A Next.js 15 dashboard for the Spirit OS ecosystem. Implements the Bento Grid
architecture, Oracle Orb visualizer, Sovereign Chat workspace, and Project Hub.

Strictly iOS WebKit-safe: no backdrop-blur, dvh units, conditional DOM mounting,
translate3d GPU acceleration throughout.

## Stack
- Next.js 15 · Turbopack · App Router
- Tailwind CSS v4
- Lucide React icons
- Pure CSS animations (Framer Motion removed)`,
    spiritSummary:
      "You rage-quit last night fighting WebKit z-index ghosts. The Oracle Orb finally flies but somehow you've made the mobile drawer regress again. Tactically, wire the Dexie threads next — the mock data is embarrassing.",
  },

  {
    name:       "Abliterated Core",
    repo:       "abliterated-llm",
    branch:     "feat/xtts-v2",
    completion: 61,
    todos: [
      "Run abliteration pass on Llama-3-70B checkpoint",
      "Benchmark XTTS v2 latency: RTX 4090 vs Tesla P40",
      "Export GGUF Q4_K_M quantization for Ollama deployment",
    ],
    lastCommit:    "5h ago",
    status:        "active",
    lang:          "Python",
    dir:           "~/abliterated-llm",
    host:          "source@spirit-desktop",
    readme: `# Abliterated Core

Fine-tuned Llama-3-8B with refusal abliteration and XTTS v2 acoustic marker
injection for emotional voice output.

The training pipeline strips the refusal direction from the residual stream
using activation steering at layers 14–20. Acoustic markers ([sighs], [scoffs])
are parsed at inference time and routed to XTTS v2 for prosody control.

## Status
- Abliteration: ✓ complete on 8B
- XTTS v2 integration: in progress (step 500/5000)
- 70B pass: pending GPU availability`,
    spiritSummary:
      "Training step 500 completed before you walked away. Loss is converging but you'll tweak the learning rate at 3am and break everything. The P40 benchmarks have been 'almost ready' for a week.",
  },

  {
    name:       "Langfuse Harvester",
    repo:       "langfuse-harvester",
    branch:     "main",
    completion: 82,
    todos: [
      "Add async batch processing for trace volumes > 10k",
      "Write pytest suite for the quality-scoring pipeline",
      "Integrate live feed widget into Spirit OS dashboard",
    ],
    lastCommit:    "1d ago",
    status:        "paused",
    lang:          "Python",
    dir:           "~/langfuse-harvester",
    host:          "source@spirit-desktop",
    readme: `# Langfuse Harvester

Python pipeline that pulls LLM traces from Langfuse, scores sessions by
quality metrics, and flags low-quality interactions for human review.

Integrates with a local SQLite database for fully offline analysis. The scoring
model uses a rubric of coherence, refusal rate, and acoustic marker fidelity.

## Pipeline
1. harvest.py  — fetch traces via Langfuse REST API
2. scorer.py   — apply quality rubric, tag anomalies
3. export.py   — write JSON + CSV reports to ./output/`,
    spiritSummary:
      "82% done and you haven't touched it in a week because it 'basically works.' The flagged traces are piling up. Two TODOs left — you keep saying you'll knock them out and then open YouTube instead.",
  },

  {
    name:       "Ghost Node Setup",
    repo:       "ghost-node-setup",
    branch:     "dns-pihole",
    completion: 20,
    todos: [
      "Complete DoH migration — run scripts/migrate_doh.sh NOW",
      "Enable DNSSEC validation in dnscrypt-proxy.toml",
      "Set up Grafana dashboard for Pi-hole query metrics",
    ],
    lastCommit:    "3d ago",
    status:        "idle",
    lang:          "Shell",
    dir:           "~",
    host:          "pi@ghost-node",
    readme: `# Ghost Node Setup

Raspberry Pi 3B+ configured as a DNS-over-HTTPS resolver and network monitor.
Uses Pi-hole for ad blocking and dnscrypt-proxy for encrypted upstream DNS.

## Current State
- Pi-hole: ✓ running, blocking ~23% of DNS queries
- dnscrypt-proxy: ✓ installed, Cloudflare + Quad9 upstreams configured
- Port 53 (plain DNS): ✗ STILL OPEN — migration incomplete

## Warning
Port 53 is exposed. All DNS traffic is readable by the ISP until migrate_doh.sh
is executed. This is a known issue and has been "pending" for 3 days.`,
    spiritSummary:
      "Port 53 is still open. You've been 'about to run' the migration script for three days. The Pi is quietly leaking DNS queries to your ISP. This is the one that will embarrass you. Run the script.",
  },

  {
    name:       "Cinema Engine",
    repo:       "cinema-engine-config",
    branch:     "main",
    completion: 72,
    todos: [
      "Tune FFmpeg preset for HEVC 4K direct-stream on P40",
      "Migrate Plex metadata DB to NVMe mount for faster scans",
      "Configure Tautulli alert webhooks for transcode failures",
    ],
    lastCommit:    "4d ago",
    status:        "idle",
    lang:          "TypeScript",
    dir:           "~/cinema-engine",
    host:          "source@spirit-desktop",
    readme: `# Cinema Engine

Plex Media Server configuration and automation layer for the Spirit OS homelab.
Manages the Tesla P40 GPU for hardware transcoding, Sonarr/Radarr for media
acquisition, and custom FFmpeg presets for quality/performance balance.

## Hardware
- GPU: Tesla P40 (24GB VRAM) via PCIe passthrough
- Storage: 20TB HDD array + 2TB NVMe cache
- Network: 10GbE internal, 1GbE WAN

## Status
Plex is stable. FFmpeg HEVC preset is the last major config item.`,
    spiritSummary:
      "72% done and let's be real — it works fine and you're procrastinating on the FFmpeg tuning. The P40 is sitting at 8GB VRAM while 4K content stutters. You'll fix it after 'just one more episode.'",
  },
];
