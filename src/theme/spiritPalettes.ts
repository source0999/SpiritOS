// Spirit palette registry. Theme UI reads this file; the hook applies cssVars
// to documentElement and preserves the html[data-theme] contract.

export const DEFAULT_THEME_ID = "frozen-water" as const;

export type ThemeId =
  | "frozen-water"
  | "frost-linen"
  | "ivory-mist"
  | "lunar-chalk"
  | "soft-ash"
  | "alice-seagrass"
  | "ember-circuit"
  | "violet-twilight"
  | "obsidian-plum"
  | "night-signal"
  | "deep-sky"
  | "solar-ember"
  | "orchid-smoke"
  | "aurora-slate";

export type SpiritPaletteFamily = "light" | "dark" | "hybrid";
export type SpiritPreviewPattern = "none" | "mesh" | "ember" | "violet" | "cyan";

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
  family: SpiritPaletteFamily;
  toneLabel: string;
  description: string;
  previewSurface: string;
  previewAccent: string;
  previewPattern?: SpiritPreviewPattern;
  colors: readonly { name: string; hex: string }[];
  cssVars: SpiritPaletteCssVars;
  typography?: "sans" | "mono";
};

export const LEGACY_THEME_IDS: Readonly<Record<string, ThemeId>> = {
  "spirit-slate": "frozen-water",
  "dark-node": "alice-seagrass",
  "legacy-violet": "violet-twilight",
  "frozen-water": "frozen-water",
  "alice-seagrass": "alice-seagrass",
  "deep-sky": "deep-sky",
};

type PaletteInput = Omit<SpiritPalette, "cssVars"> & {
  bg: string;
  bgSoft: string;
  panel: string;
  panelStrong: string;
  accent: string;
  accentStrong: string;
  secondary: string;
  glow: string;
  border: string;
  atmosphereBase: string;
  atmosphereA: string;
  atmosphereB: string;
  glassSurface: string;
  glassBorder: string;
  panelGlow: string;
  navGlow: string;
  progressTrack: string;
  chipBg: string;
  chipGlow: string;
};

function palette(input: PaletteInput): SpiritPalette {
  const {
    bg,
    bgSoft,
    panel,
    panelStrong,
    accent,
    accentStrong,
    secondary,
    glow,
    border,
    atmosphereBase,
    atmosphereA,
    atmosphereB,
    glassSurface,
    glassBorder,
    panelGlow,
    navGlow,
    progressTrack,
    chipBg,
    chipGlow,
    ...meta
  } = input;

  return {
    ...meta,
    cssVars: {
      "--spirit-bg": bg,
      "--spirit-bg-soft": bgSoft,
      "--spirit-panel": panel,
      "--spirit-panel-strong": panelStrong,
      "--spirit-accent": accent,
      "--spirit-accent-strong": accentStrong,
      "--spirit-glow": glow,
      "--spirit-border": border,
      "--spirit-secondary-mix": secondary,
      "--spirit-atmosphere-base": atmosphereBase,
      "--spirit-atmosphere-a": atmosphereA,
      "--spirit-atmosphere-b": atmosphereB,
      "--spirit-glass-surface": glassSurface,
      "--spirit-glass-border": glassBorder,
      "--spirit-panel-glow": panelGlow,
      "--spirit-nav-glow": navGlow,
      "--spirit-fairy-halo": glow,
      "--spirit-progress-track": progressTrack,
      "--spirit-theme-chip-active-bg": chipBg,
      "--spirit-theme-chip-active-glow": chipGlow,
    },
  };
}

function lightVars(surfaceA: string, surfaceB: string, accent: string, accentStrong: string, secondary: string) {
  return {
    bg: surfaceA,
    bgSoft: surfaceB,
    panel: "rgba(255,255,255,0.58)",
    panelStrong: "rgba(255,255,255,0.78)",
    accent,
    accentStrong,
    secondary,
    glow: `${accent}55`,
    border: "rgba(15,23,42,0.10)",
    atmosphereBase:
      "linear-gradient(145deg, rgba(255,255,255,0.56), rgba(186,210,238,0.24) 52%, rgba(255,255,255,0.42))",
    atmosphereA: accent,
    atmosphereB: secondary,
    glassSurface:
      "linear-gradient(135deg, rgba(255,255,255,0.46) 0%, rgba(255,255,255,0.18) 58%, rgba(210,226,242,0.14) 100%)",
    glassBorder: "rgba(255,255,255,0.66)",
    panelGlow:
      "0 30px 80px -34px rgba(15,23,42,0.22), 0 10px 26px -24px rgba(15,23,42,0.20), inset 0 1px 0 rgba(255,255,255,0.72)",
    navGlow: `0 0 42px -12px ${accent}66`,
    progressTrack: "rgba(15,23,42,0.10)",
    chipBg: `${accent}29`,
    chipGlow: `0 0 28px -6px ${accent}66`,
  };
}

function darkVars(bg: string, bgSoft: string, panel: string, panelStrong: string, accent: string, accentStrong: string, secondary: string) {
  return {
    bg,
    bgSoft,
    panel,
    panelStrong,
    accent,
    accentStrong,
    secondary,
    glow: `${accent}52`,
    border: `${accent}24`,
    atmosphereBase:
      "linear-gradient(155deg, rgba(255,255,255,0.06) 0%, transparent 46%, rgba(0,0,0,0.42) 100%)",
    atmosphereA: accent,
    atmosphereB: secondary,
    glassSurface:
      "linear-gradient(135deg, rgba(255,255,255,0.075) 0%, rgba(15,23,42,0.34) 52%, rgba(8,10,18,0.72) 100%)",
    glassBorder: "rgba(255,255,255,0.22)",
    panelGlow:
      "0 56px 130px -36px rgba(0,0,0,0.78), 0 18px 46px -34px rgba(255,255,255,0.12), inset 0 1px 0 rgba(255,255,255,0.12)",
    navGlow: `0 0 44px -10px ${accent}66`,
    progressTrack: "rgba(0,0,0,0.52)",
    chipBg: `${accent}33`,
    chipGlow: `0 0 30px -6px ${accent}66`,
  };
}

export const SPIRIT_PALETTES: readonly SpiritPalette[] = [
  palette({
    id: "frozen-water",
    label: "Smoked Pearl",
    shortLabel: "Pearl",
    family: "light",
    toneLabel: "PEARL / AIRY",
    description: "Frosted pearl glass with cool blue lift.",
    previewSurface: "linear-gradient(135deg,#f8fbff,#dbeaf7 55%,#eef7fb)",
    previewAccent: "#8FB8DE",
    previewPattern: "mesh",
    colors: [
      { name: "Pearl", hex: "#F8FBFF" },
      { name: "Baby Blue", hex: "#8FB8DE" },
      { name: "Lavender Grey", hex: "#9A94BC" },
    ],
    typography: "sans",
    ...lightVars("#eef6fb", "#dceaf4", "#8FB8DE", "#CDF7F6", "#9A94BC"),
  }),
  palette({
    id: "frost-linen",
    label: "Frost Linen",
    shortLabel: "Linen",
    family: "light",
    toneLabel: "LINEN / SOFT",
    description: "Warm white material with a quiet linen cast.",
    previewSurface: "linear-gradient(135deg,#fbfaf5,#ece7dc 58%,#f7f1e8)",
    previewAccent: "#B9A37D",
    previewPattern: "none",
    colors: [
      { name: "Frost", hex: "#FBFAF5" },
      { name: "Linen", hex: "#ECE7DC" },
      { name: "Wheat", hex: "#B9A37D" },
    ],
    typography: "sans",
    ...lightVars("#f4f0e8", "#e8e2d6", "#B9A37D", "#7D6B4F", "#A8B5B2"),
  }),
  palette({
    id: "ivory-mist",
    label: "Ivory Mist",
    shortLabel: "Ivory",
    family: "light",
    toneLabel: "IVORY / FOG",
    description: "Ivory haze with low-contrast cyan edges.",
    previewSurface: "linear-gradient(135deg,#fffdf7,#eef5f2 55%,#dbeef0)",
    previewAccent: "#79BFC8",
    previewPattern: "cyan",
    colors: [
      { name: "Ivory", hex: "#FFFDF7" },
      { name: "Mist", hex: "#DBEEF0" },
      { name: "Cyan", hex: "#79BFC8" },
    ],
    typography: "sans",
    ...lightVars("#f6f4ed", "#e4efef", "#79BFC8", "#327F8E", "#D7B98C"),
  }),
  palette({
    id: "lunar-chalk",
    label: "Lunar Chalk",
    shortLabel: "Chalk",
    family: "light",
    toneLabel: "CHALK / CLEAR",
    description: "Clean lunar white with violet-grey depth.",
    previewSurface: "linear-gradient(135deg,#fbfcff,#e9edf5 58%,#d8dce9)",
    previewAccent: "#9A94BC",
    previewPattern: "violet",
    colors: [
      { name: "Chalk", hex: "#FBFCFF" },
      { name: "Moon", hex: "#D8DCE9" },
      { name: "Violet Grey", hex: "#9A94BC" },
    ],
    typography: "sans",
    ...lightVars("#f1f4fa", "#e1e5ee", "#9A94BC", "#6F67A4", "#8FB8DE"),
  }),
  palette({
    id: "soft-ash",
    label: "Soft Ash",
    shortLabel: "Ash",
    family: "light",
    toneLabel: "ASH / MUTED",
    description: "Soft ash glass with graphite-readable contrast.",
    previewSurface: "linear-gradient(135deg,#f5f6f4,#dfe4e2 52%,#cbd3d2)",
    previewAccent: "#7D9298",
    previewPattern: "mesh",
    colors: [
      { name: "Ash", hex: "#DFE4E2" },
      { name: "Graphite", hex: "#516168" },
      { name: "Blue Grey", hex: "#7D9298" },
    ],
    typography: "sans",
    ...lightVars("#edf1ef", "#dfe5e3", "#7D9298", "#516168", "#A99D8E"),
  }),
  palette({
    id: "alice-seagrass",
    label: "Dark Node",
    shortLabel: "Node",
    family: "dark",
    toneLabel: "SMOKY / DEEP",
    description: "Premium node smoke with restrained seagrass signal.",
    previewSurface: "linear-gradient(135deg,#0f1018,#1c1e2e 58%,#25283D)",
    previewAccent: "#439A86",
    previewPattern: "mesh",
    colors: [
      { name: "Space", hex: "#0F1018" },
      { name: "Seagrass", hex: "#439A86" },
      { name: "Ocean", hex: "#228CDB" },
    ],
    typography: "mono",
    ...darkVars("#0f1018", "#161828", "#1c1e2e", "#25283D", "#439A86", "#E8F1F2", "#228CDB"),
  }),
  palette({
    id: "ember-circuit",
    label: "Ember Circuit",
    shortLabel: "Ember",
    family: "dark",
    toneLabel: "EMBER / SMOKE",
    description: "Graphite UI with a subtle orange circuit warmth.",
    previewSurface: "linear-gradient(135deg,#11100f,#211a16 55%,#362318)",
    previewAccent: "#F59E5B",
    previewPattern: "ember",
    colors: [
      { name: "Graphite", hex: "#11100F" },
      { name: "Circuit", hex: "#362318" },
      { name: "Ember", hex: "#F59E5B" },
    ],
    typography: "mono",
    ...darkVars("#11100f", "#171412", "#211a16", "#362318", "#F59E5B", "#FFD1A8", "#8C6AFA"),
  }),
  palette({
    id: "violet-twilight",
    label: "Violet Graphite",
    shortLabel: "Violet",
    family: "dark",
    toneLabel: "VIOLET / DEEP",
    description: "Violet graphite with a quiet orchid glow.",
    previewSurface: "linear-gradient(135deg,#0c0d14,#17172a 52%,#272044)",
    previewAccent: "#B14AED",
    previewPattern: "violet",
    colors: [
      { name: "Graphite", hex: "#0C0D14" },
      { name: "Violet", hex: "#454ADE" },
      { name: "Orchid", hex: "#B14AED" },
    ],
    typography: "sans",
    ...darkVars("#0c0d14", "#1B1F3B", "#141628", "#1a1e36", "#B14AED", "#C874D9", "#454ADE"),
  }),
  palette({
    id: "obsidian-plum",
    label: "Obsidian Plum",
    shortLabel: "Plum",
    family: "dark",
    toneLabel: "PLUM / OBSIDIAN",
    description: "Black glass with subdued plum undertones.",
    previewSurface: "linear-gradient(135deg,#09090d,#17111d 58%,#2d1b35)",
    previewAccent: "#A56ACB",
    previewPattern: "violet",
    colors: [
      { name: "Obsidian", hex: "#09090D" },
      { name: "Plum", hex: "#2D1B35" },
      { name: "Orchid", hex: "#A56ACB" },
    ],
    typography: "sans",
    ...darkVars("#09090d", "#121018", "#17111d", "#2d1b35", "#A56ACB", "#D8B4FE", "#6E5BC5"),
  }),
  palette({
    id: "night-signal",
    label: "Night Signal",
    shortLabel: "Signal",
    family: "dark",
    toneLabel: "NIGHT / CYAN",
    description: "Near-black dashboard glass with cyan signal lines.",
    previewSurface: "linear-gradient(135deg,#071018,#101a24 55%,#173145)",
    previewAccent: "#2EC0F9",
    previewPattern: "cyan",
    colors: [
      { name: "Night", hex: "#071018" },
      { name: "Signal", hex: "#2EC0F9" },
      { name: "Blue", hex: "#67AAF9" },
    ],
    typography: "mono",
    ...darkVars("#071018", "#0d1722", "#101a24", "#173145", "#2EC0F9", "#67AAF9", "#7B61FF"),
  }),
  palette({
    id: "deep-sky",
    label: "Neural Cyan",
    shortLabel: "Cyan",
    family: "hybrid",
    toneLabel: "CYAN / NEURAL",
    description: "Cool cyan interface with dark neural depth.",
    previewSurface: "linear-gradient(135deg,#0a1018,#123149 52%,#c4e0f9)",
    previewAccent: "#2EC0F9",
    previewPattern: "cyan",
    colors: [
      { name: "Deep Sky", hex: "#2EC0F9" },
      { name: "Cool Horizon", hex: "#67AAF9" },
      { name: "Pale Sky", hex: "#C4E0F9" },
    ],
    typography: "sans",
    ...darkVars("#0a1018", "#0e1520", "#121c28", "#152235", "#2EC0F9", "#67AAF9", "#B95F89"),
  }),
  palette({
    id: "solar-ember",
    label: "Solar Ember",
    shortLabel: "Solar",
    family: "hybrid",
    toneLabel: "SOLAR / WARM",
    description: "Pearl surface with a precise amber control glow.",
    previewSurface: "linear-gradient(135deg,#f8f2e6,#e7d6be 52%,#322118)",
    previewAccent: "#EFA552",
    previewPattern: "ember",
    colors: [
      { name: "Solar", hex: "#EFA552" },
      { name: "Cream", hex: "#F8F2E6" },
      { name: "Umber", hex: "#322118" },
    ],
    typography: "sans",
    ...lightVars("#f1e8dc", "#e4d5c4", "#EFA552", "#845321", "#7D6BBA"),
  }),
  palette({
    id: "orchid-smoke",
    label: "Orchid Smoke",
    shortLabel: "Orchid",
    family: "hybrid",
    toneLabel: "ORCHID / SMOKE",
    description: "Smoked glass with a restrained orchid accent path.",
    previewSurface: "linear-gradient(135deg,#17151f,#2a2436 58%,#c7b4d8)",
    previewAccent: "#C084FC",
    previewPattern: "violet",
    colors: [
      { name: "Smoke", hex: "#17151F" },
      { name: "Orchid", hex: "#C084FC" },
      { name: "Mist", hex: "#C7B4D8" },
    ],
    typography: "sans",
    ...darkVars("#17151f", "#211c2a", "#2a2436", "#3a2d4c", "#C084FC", "#E9D5FF", "#8FB8DE"),
  }),
  palette({
    id: "aurora-slate",
    label: "Aurora Slate",
    shortLabel: "Aurora",
    family: "hybrid",
    toneLabel: "SLATE / AURORA",
    description: "Slate glass with cyan, violet, and pearl highlights.",
    previewSurface: "linear-gradient(135deg,#111827,#334155 52%,#dbeafe)",
    previewAccent: "#93C5FD",
    previewPattern: "mesh",
    colors: [
      { name: "Slate", hex: "#111827" },
      { name: "Aurora", hex: "#93C5FD" },
      { name: "Violet", hex: "#A78BFA" },
    ],
    typography: "sans",
    ...darkVars("#111827", "#172033", "#1f2937", "#334155", "#93C5FD", "#DBEAFE", "#A78BFA"),
  }),
];

export const THEME_IDS = new Set<string>(SPIRIT_PALETTES.map((p) => p.id));

export function getPaletteById(id: ThemeId): SpiritPalette {
  const p = SPIRIT_PALETTES.find((x) => x.id === id);
  if (!p) throw new Error(`Unknown Spirit palette: ${id}`);
  return p;
}

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
