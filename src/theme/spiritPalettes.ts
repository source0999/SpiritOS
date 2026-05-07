// ── Spirit palette registry - add one object here, ThemeStrip follows ─────────
// > Hook applies cssVars to documentElement; :root mirrors default for SSR paint.
// > Extended vars drive dashboard v2 atmosphere + glass (_reference/dashboardDemo port).

export const DEFAULT_THEME_ID = "frozen-water" as const;

export type ThemeId =
  | "frozen-water"
  | "alice-seagrass"
  | "violet-twilight"
  | "deep-sky";

/** Keys we inject / clear so switching palettes cannot leave stale custom props */
export const SPIRIT_DOM_CSS_KEYS = [
  "--spirit-bg",
  "--spirit-bg-soft",
  "--spirit-panel",
  "--spirit-panel-strong",
  "--spirit-accent",
  "--spirit-accent-strong",
  "--spirit-glow",
  "--spirit-border",
  "--spirit-secondary-mix",
  // ── Dashboard atmosphere + glass (palette-driven; consumed under .spirit-dashboard-v2-root)
  "--spirit-atmosphere-base",
  "--spirit-atmosphere-a",
  "--spirit-atmosphere-b",
  "--spirit-glass-surface",
  "--spirit-glass-border",
  "--spirit-panel-glow",
  "--spirit-nav-glow",
  "--spirit-fairy-halo",
  "--spirit-progress-track",
  "--spirit-theme-chip-active-bg",
  "--spirit-theme-chip-active-glow",
] as const;

export type SpiritDomCssKey = (typeof SPIRIT_DOM_CSS_KEYS)[number];

export type SpiritPaletteCssVars = Record<SpiritDomCssKey, string>;

export type SpiritPalette = {
  id: ThemeId;
  label: string;
  shortLabel: string;
  colors: readonly { name: string; hex: string }[];
  cssVars: SpiritPaletteCssVars;
  /** dark-node lived here - alice-seagrass keeps mono rails */
  typography?: "sans" | "mono";
};

/** Old ThemeEngine ids → registry ids (localStorage migration) */
export const LEGACY_THEME_IDS: Readonly<Record<string, ThemeId>> = {
  "spirit-slate": "frozen-water",
  "dark-node": "alice-seagrass",
  "legacy-violet": "violet-twilight",
};

const FW = "#CDF7F6";
const BB = "#8FB8DE";
const LG = "#9A94BC";
const GS = "#9B5094";
const TG = "#6A605C";

const AB = "#E8F1F2";
const SG = "#439A86";
const SI = "#25283D";
const BO = "#228CDB";
const BL = "#AA7DCE";

const VT = "#454ADE";
const SI2 = "#1B1F3B";
const HM = "#B14AED";
const OM = "#C874D9";
const PP = "#E1BBC9";

const DSB = "#2EC0F9";
const CH = "#67AAF9";
const BBI = "#9BBDF9";
const PS = "#C4E0F9";
const FP = "#B95F89";

export const SPIRIT_PALETTES: readonly SpiritPalette[] = [
  {
    id: "frozen-water",
    label: "Frozen Water",
    shortLabel: "Ice",
    colors: [
      { name: "Frozen Water", hex: FW },
      { name: "Baby Blue Ice", hex: BB },
      { name: "Lavender Grey", hex: LG },
      { name: "Grape Soda", hex: GS },
      { name: "Taupe Grey", hex: TG },
    ],
    typography: "sans",
    cssVars: {
      "--spirit-bg": "#161413",
      "--spirit-bg-soft": "#1e1c1a",
      "--spirit-panel": "#242120",
      "--spirit-panel-strong": "#2e2b29",
      "--spirit-accent": BB,
      "--spirit-accent-strong": FW,
      "--spirit-glow": "rgba(143, 184, 222, 0.28)",
      "--spirit-border": "rgba(205, 247, 246, 0.11)",
      "--spirit-secondary-mix": LG,
      /** Icy pearl haze on charcoal — dash “silver-air” without blowing contrast */
      "--spirit-atmosphere-base":
        "linear-gradient(165deg, rgba(255,255,255,0.07) 0%, transparent 42%, rgba(0,0,0,0.18) 100%)",
      "--spirit-atmosphere-a": BB,
      "--spirit-atmosphere-b": LG,
      "--spirit-glass-surface":
        "linear-gradient(135deg, rgba(255,255,255,0.11) 0%, rgba(255,255,255,0.03) 55%, rgba(36,33,32,0.55) 100%)",
      "--spirit-glass-border": "rgba(255,255,255,0.22)",
      "--spirit-panel-glow":
        "0 48px 120px -32px rgba(0,0,0,0.72), inset 0 1px 0 rgba(255,255,255,0.14)",
      "--spirit-nav-glow": "0 0 40px -10px rgba(143, 184, 222, 0.42)",
      "--spirit-fairy-halo": "rgba(143, 184, 222, 0.44)",
      "--spirit-progress-track": "rgba(0,0,0,0.48)",
      "--spirit-theme-chip-active-bg": "rgba(143, 184, 222, 0.24)",
      "--spirit-theme-chip-active-glow": "0 0 28px -6px rgba(143, 184, 222, 0.38)",
    },
  },
  {
    id: "alice-seagrass",
    label: "Alice Seagrass",
    shortLabel: "Sea",
    colors: [
      { name: "Alice Blue", hex: AB },
      { name: "Seagrass", hex: SG },
      { name: "Space Indigo", hex: SI },
      { name: "Bright Ocean", hex: BO },
      { name: "Bright Lavender", hex: BL },
    ],
    typography: "mono",
    cssVars: {
      "--spirit-bg": "#0f1018",
      "--spirit-bg-soft": "#161828",
      "--spirit-panel": "#1c1e2e",
      "--spirit-panel-strong": SI,
      "--spirit-accent": SG,
      "--spirit-accent-strong": AB,
      "--spirit-glow": "rgba(67, 154, 134, 0.28)",
      "--spirit-border": "rgba(67, 154, 134, 0.14)",
      "--spirit-secondary-mix": BO,
      /** Dark Node heir — premium smoke, not mud */
      "--spirit-atmosphere-base":
        "linear-gradient(155deg, rgba(129,140,248,0.06) 0%, transparent 45%, rgba(0,0,0,0.35) 100%)",
      "--spirit-atmosphere-a": SG,
      "--spirit-atmosphere-b": BO,
      "--spirit-glass-surface":
        "linear-gradient(135deg, rgba(255,255,255,0.07) 0%, rgba(15,23,42,0.42) 55%, rgba(15,16,24,0.88) 100%)",
      "--spirit-glass-border": "rgba(255,255,255,0.2)",
      "--spirit-panel-glow":
        "0 56px 130px -36px rgba(0,0,0,0.78), inset 0 1px 0 rgba(255,255,255,0.1)",
      "--spirit-nav-glow": "0 0 42px -10px rgba(67, 154, 134, 0.45)",
      "--spirit-fairy-halo": "rgba(67, 154, 134, 0.4)",
      "--spirit-progress-track": "rgba(0,0,0,0.52)",
      "--spirit-theme-chip-active-bg": "rgba(67, 154, 134, 0.26)",
      "--spirit-theme-chip-active-glow": "0 0 28px -6px rgba(67, 154, 134, 0.4)",
    },
  },
  {
    id: "violet-twilight",
    label: "Violet Twilight",
    shortLabel: "Vio",
    colors: [
      { name: "Violet Twilight", hex: VT },
      { name: "Space Indigo", hex: SI2 },
      { name: "Hyper Magenta", hex: HM },
      { name: "Orchid Mist", hex: OM },
      { name: "Pastel Petal", hex: PP },
    ],
    typography: "sans",
    cssVars: {
      "--spirit-bg": "#0c0d14",
      "--spirit-bg-soft": SI2,
      "--spirit-panel": "#141628",
      "--spirit-panel-strong": "#1a1e36",
      "--spirit-accent": HM,
      "--spirit-accent-strong": OM,
      "--spirit-glow": "rgba(177, 74, 237, 0.26)",
      "--spirit-border": "rgba(200, 116, 217, 0.14)",
      "--spirit-secondary-mix": VT,
      "--spirit-atmosphere-base":
        "linear-gradient(160deg, rgba(200,116,217,0.07) 0%, transparent 48%, rgba(0,0,0,0.38) 100%)",
      "--spirit-atmosphere-a": HM,
      "--spirit-atmosphere-b": VT,
      "--spirit-glass-surface":
        "linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(69,74,222,0.12) 45%, rgba(12,13,20,0.92) 100%)",
      "--spirit-glass-border": "rgba(200, 116, 217, 0.26)",
      "--spirit-panel-glow":
        "0 52px 125px -34px rgba(0,0,0,0.82), inset 0 1px 0 rgba(255,255,255,0.09)",
      "--spirit-nav-glow": "0 0 44px -10px rgba(177, 74, 237, 0.42)",
      "--spirit-fairy-halo": "rgba(200, 116, 217, 0.42)",
      "--spirit-progress-track": "rgba(0,0,0,0.54)",
      "--spirit-theme-chip-active-bg": "rgba(177, 74, 237, 0.26)",
      "--spirit-theme-chip-active-glow": "0 0 30px -6px rgba(177, 74, 237, 0.38)",
    },
  },
  {
    id: "deep-sky",
    label: "Deep Sky",
    shortLabel: "Sky",
    colors: [
      { name: "Deep Sky Blue", hex: DSB },
      { name: "Cool Horizon", hex: CH },
      { name: "Baby Blue Ice", hex: BBI },
      { name: "Pale Sky", hex: PS },
      { name: "Fuchsia Plum", hex: FP },
    ],
    typography: "sans",
    cssVars: {
      "--spirit-bg": "#0a1018",
      "--spirit-bg-soft": "#0e1520",
      "--spirit-panel": "#121c28",
      "--spirit-panel-strong": "#152235",
      "--spirit-accent": DSB,
      "--spirit-accent-strong": CH,
      "--spirit-glow": "rgba(46, 192, 249, 0.28)",
      "--spirit-border": "rgba(103, 170, 249, 0.14)",
      "--spirit-secondary-mix": FP,
      "--spirit-atmosphere-base":
        "linear-gradient(150deg, rgba(103,170,249,0.08) 0%, transparent 46%, rgba(0,0,0,0.36) 100%)",
      "--spirit-atmosphere-a": DSB,
      "--spirit-atmosphere-b": CH,
      "--spirit-glass-surface":
        "linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(46,192,249,0.08) 42%, rgba(10,16,24,0.9) 100%)",
      "--spirit-glass-border": "rgba(155, 189, 249, 0.22)",
      "--spirit-panel-glow":
        "0 50px 118px -32px rgba(0,0,0,0.76), inset 0 1px 0 rgba(255,255,255,0.11)",
      "--spirit-nav-glow": "0 0 40px -10px rgba(46, 192, 249, 0.45)",
      "--spirit-fairy-halo": "rgba(103, 170, 249, 0.44)",
      "--spirit-progress-track": "rgba(0,0,0,0.50)",
      "--spirit-theme-chip-active-bg": "rgba(46, 192, 249, 0.24)",
      "--spirit-theme-chip-active-glow": "0 0 28px -6px rgba(46, 192, 249, 0.42)",
    },
  },
];

export const THEME_IDS = new Set<string>(SPIRIT_PALETTES.map((p) => p.id));

export function getPaletteById(id: ThemeId): SpiritPalette {
  const p = SPIRIT_PALETTES.find((x) => x.id === id);
  if (!p) throw new Error(`Unknown Spirit palette: ${id}`);
  return p;
}

/** Normalize stored string: migrate legacy ids, fall back to Frozen Water */
export function normalizeStoredThemeId(raw: string): ThemeId {
  const migrated = LEGACY_THEME_IDS[raw] ?? raw;
  if (THEME_IDS.has(migrated)) return migrated as ThemeId;
  return DEFAULT_THEME_ID;
}

export function applySpiritPaletteVars(root: HTMLElement, palette: SpiritPalette): void {
  for (const key of SPIRIT_DOM_CSS_KEYS) {
    root.style.setProperty(key, palette.cssVars[key]);
  }
}

export function applySpiritPaletteDom(root: HTMLElement, palette: SpiritPalette): void {
  root.setAttribute("data-theme", palette.id);
  root.setAttribute("data-spirit-typography", palette.typography ?? "sans");
  applySpiritPaletteVars(root, palette);
}
