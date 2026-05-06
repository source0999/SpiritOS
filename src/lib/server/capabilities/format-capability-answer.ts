import "server-only";

import type { NodeDrive } from "@/lib/server/telemetry/types";
import {
  normalizeForCapabilityIntent,
  type CapabilityIntentKind,
} from "@/lib/spirit/capability-intent";
import type { SpiritDiagnosticsPayload } from "@/lib/server/spirit-diagnostics";
import type { CapabilityRegistryResponse } from "@/lib/server/capabilities/types";
import type { SpiritRuntimeSurface } from "@/lib/spirit/spirit-runtime-surface";

export type FormatCapabilityAnswerInput = {
  registry: CapabilityRegistryResponse;
  diagnostics: SpiritDiagnosticsPayload;
  webSearchEnabled: boolean;
  runtimeSurface: SpiritRuntimeSurface;
  activeResolvedModelId: string;
  intentKind: CapabilityIntentKind;
  userMessage?: string;
  /** From probeOllamaOpenAICompat when intent is ai_runtime */
  ollamaReachable?: boolean | null;
};

function fmtBytes(n: number | null | undefined): string {
  if (n == null || !Number.isFinite(n)) return "unknown";
  if (n >= 1e12) return `${(n / 1e12).toFixed(1)} TB`;
  if (n >= 1e9) return `${(n / 1e9).toFixed(1)} GB`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(0)} MB`;
  return `${Math.round(n)} B`;
}

/** Voice-friendly cap - Oracle should not read a telemetry novel */
function oracleClamp(surface: SpiritRuntimeSurface, text: string): string {
  if (surface !== "oracle") return text;
  const parts = text
    .replace(/^#{1,4}\s+/gm, "")
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter(Boolean);
  return parts.slice(0, 3).join(" ");
}

function modelMentionsHermes(id: string): boolean {
  return /hermes/i.test(id);
}

export function formatCapabilityAnswer(input: FormatCapabilityAnswerInput): string {
  const {
    registry,
    diagnostics,
    webSearchEnabled,
    runtimeSurface,
    activeResolvedModelId,
    intentKind,
    ollamaReachable,
  } = input;

  let body: string;
  switch (intentKind) {
    case "file_access":
      body = formatFileAccess(input);
      break;
    case "desktop_control":
      body = formatDesktopControl(input);
      break;
    case "ai_runtime":
      body = formatAiRuntime({
        diagnostics,
        runtimeSurface,
        activeResolvedModelId,
        ollamaReachable: ollamaReachable ?? null,
      });
      break;
    case "tool_inventory":
    case "general_capabilities":
      body = formatSpiritOsOverview({
        registry,
        diagnostics,
        webSearchEnabled,
        runtimeSurface,
        activeResolvedModelId,
      });
      break;
    case "node_status":
      body = formatNodeStatus(registry);
      break;
    case "storage_status":
      body = formatStorageStatus(input);
      break;
    case "hardware_summary":
      body = formatHardwareSummary(registry);
      break;
    default:
      body = formatSpiritOsOverview({
        registry,
        diagnostics,
        webSearchEnabled,
        runtimeSurface,
        activeResolvedModelId,
      });
  }

  return oracleClamp(runtimeSurface, body);
}

function formatFileAccess(input: FormatCapabilityAnswerInput): string {
  const { registry, runtimeSurface: surface } = input;
  if (surface === "oracle") {
    return [
      "No, not yet - folder browsing and file listing aren’t wired as app tools.",
      "I can still see drive-level storage telemetry (used/total per volume) where agents report it.",
    ].join(" ");
  }

  const lines: string[] = [];
  lines.push(
    "No, not yet. I can see **drive-level** telemetry for volumes like **C:** (used/total from agents), but **folder browsing and file listing** are not wired as app tools yet.",
  );
  lines.push(
    "That’s aggregate storage rows in telemetry - not walking `C:\\Users\\...` or enumerating directories from chat.",
  );

  const withStorage = registry.nodes.filter(
    (n) =>
      n.capabilities.storageTelemetry.enabled ||
      (n.telemetrySnapshot.storage?.drives?.length ?? 0) > 0,
  );
  if (withStorage.length > 0) {
    const names = withStorage.map((n) => n.label).join(", ");
    lines.push(`Nodes with storage rows in this poll include **${names}**.`);
  }

  return lines.join("\n\n");
}

function formatDesktopControl(input: FormatCapabilityAnswerInput): string {
  const { registry, runtimeSurface: surface } = input;
  const labels = registry.nodes.map((n) => n.label).join(", ");

  if (surface === "oracle") {
    return [
      "Not from the app yet - chat and Oracle don’t have an SSH command tool wired.",
      "You can still SSH manually on the machine side (e.g. your Dell) outside SpiritOS.",
    ].join(" ");
  }

  const lines: string[] = [];
  lines.push(
    "Not from the SpiritOS app yet - there’s no remote-desktop or app-level SSH command tool in this chat path.",
  );
  lines.push(
    `I **do** see nodes in telemetry (${labels || "none listed"}). You can still use **manual SSH** on the machine side if that’s how you work today.`,
  );
  lines.push(
    "In-app SSH / WinRM would be a future, approval-gated tool - it’s **not** hooked up here yet.",
  );
  return lines.join("\n\n");
}

function formatAiRuntime(opts: {
  diagnostics: SpiritDiagnosticsPayload;
  runtimeSurface: SpiritRuntimeSurface;
  activeResolvedModelId: string;
  ollamaReachable: boolean | null;
}): string {
  const { diagnostics, runtimeSurface, activeResolvedModelId, ollamaReachable } = opts;
  const chat = diagnostics.chatModel;
  const oracle = diagnostics.oracleLaneModel;

  if (runtimeSurface === "oracle") {
    const probe =
      ollamaReachable === true
        ? "Quick probe: Ollama reachable."
        : ollamaReachable === false
          ? "Quick probe: Ollama did not answer."
          : "";
    const hm =
      modelMentionsHermes(chat) ||
      modelMentionsHermes(oracle) ||
      modelMentionsHermes(activeResolvedModelId)
        ? "Hermes-class tag."
        : "";
    return [
      `Models: chat \`${chat}\`, this lane \`${activeResolvedModelId}\` (Oracle default \`${oracle}\`).`,
      hm,
      probe,
    ]
      .filter(Boolean)
      .join(" ");
  }

  const lines: string[] = [];

  lines.push(
    `Chat is configured for **${chat}**; Oracle lane defaults to **${oracle}** (unless env overrides).`,
  );
  lines.push(
    `This ${runtimeSurface} request is using Ollama tag **${activeResolvedModelId}**.`,
  );

  const hermesNote =
    modelMentionsHermes(chat) ||
    modelMentionsHermes(oracle) ||
    modelMentionsHermes(activeResolvedModelId);
  if (hermesNote) {
    lines.push("Yes - that tag reads as a Hermes-class model from routing config.");
  }

  if (ollamaReachable === true) {
    lines.push("Ollama OpenAI-compat endpoint responded **reachable** on the last probe.");
  } else if (ollamaReachable === false) {
    lines.push(
      "Ollama did **not** answer the quick compat probe - the tag is still what’s configured, but the host may be down.",
    );
  }

  lines.push(`Engine: ${diagnostics.engine}. Context window label: ${diagnostics.context.label}.`);
  return lines.join("\n\n");
}

/** Live overview for “what can you do / capabilities / tools” - no CPU/RAM dump */
function formatSpiritOsOverview(opts: {
  registry: CapabilityRegistryResponse;
  diagnostics: SpiritDiagnosticsPayload;
  webSearchEnabled: boolean;
  runtimeSurface: SpiritRuntimeSurface;
  activeResolvedModelId: string;
}): string {
  const { registry, diagnostics, webSearchEnabled, runtimeSurface, activeResolvedModelId } = opts;
  const nodeNames = registry.nodes.map((n) => n.label).join(" and ");
  const toolNames = registry.tools.map((t) => `\`${t.name}\``).join(", ");

  if (runtimeSurface === "oracle") {
    return [
      `I have live read-only cluster awareness right now - nodes: ${nodeNames || "none registered"}.`,
      `Chat model \`${diagnostics.chatModel}\`, this voice lane resolves to \`${activeResolvedModelId}\`. Registry tools: ${toolNames}.`,
      "App-level folder browsing, file tools, SSH shell from chat, and desktop control are **not wired yet** - only telemetry plus normal repo chat.",
    ].join(" ");
  }

  const lines: string[] = [];
  lines.push(
    "I have **live, read-only** awareness of the SpiritOS cluster from this server right now.",
  );
  lines.push("");
  lines.push("**What I can do now:**");
  lines.push(
    `- See cluster nodes through telemetry: ${nodeNames || "none in this poll"}.`,
  );
  lines.push(
    "- Report CPU, RAM, uptime, and aggregate storage telemetry when agents expose it - I won’t paste full hardware numbers here unless you ask for a hardware summary.",
  );
  lines.push(
    `- Report AI runtime and routing: chat \`${diagnostics.chatModel}\`, Oracle lane \`${diagnostics.oracleLaneModel}\`, this request \`${activeResolvedModelId}\` on **${runtimeSurface}**.`,
  );
  lines.push(
    `- Answer SpiritOS capability questions from the live registry; registered read-only tools: ${toolNames}.`,
  );
  lines.push("- Help plan, code, and debug this repo through normal chat.");
  lines.push(
    `- Researcher/Teacher OpenAI web prefetch is **${webSearchEnabled ? "enabled" : "disabled"}** via env (WEB_SEARCH_ENABLED).`,
  );
  lines.push("");
  lines.push("**What I cannot do from the app yet:**");
  lines.push(
    "- Browse or list arbitrary folders (like `C:\\`) or read/write/move/delete files through dedicated tools - those aren’t wired yet.",
  );
  lines.push(
    "- Run SSH/WinRM commands, open arbitrary desktop apps, or drive the GUI from chat.",
  );
  lines.push("");
  lines.push(
    "Those capabilities are on the roadmap as explicit tools; today it’s telemetry + chat only.",
  );

  return lines.join("\n");
}

function formatNodeStatus(registry: CapabilityRegistryResponse): string {
  const online = registry.nodes.filter((n) => n.status === "online" || n.status === "degraded");
  const offline = registry.nodes.filter((n) => n.status === "offline");
  const deg = registry.nodes.filter((n) => n.status === "unknown");

  const parts: string[] = [];
  if (online.length > 0) {
    parts.push(
      `Online: ${online.map((n) => `**${n.label}**`).join(", ")}.`,
    );
  }
  if (offline.length > 0) {
    parts.push(`Offline / unreachable: ${offline.map((n) => n.label).join(", ")}.`);
  }
  if (deg.length > 0) {
    parts.push(`Unknown state: ${deg.map((n) => n.label).join(", ")}.`);
  }
  if (parts.length === 0) {
    parts.push("No nodes reported in the registry snapshot.");
  }
  return parts.join(" ");
}

/** Hide tiny OEM partitions unless user asks for all/debug */
const SMALL_VOLUME_BYTES = 100 * 1024 * 1024;

function isSmallSystemVolume(d: NodeDrive, forceInclude: boolean): boolean {
  if (forceInclude) return false;
  if (d.totalBytes != null && d.totalBytes <= SMALL_VOLUME_BYTES) return true;
  if (/driver|efi|system reserved|recovery/i.test(d.name)) return true;
  return false;
}

function driveLettersFromVisibilityQuery(t: string): Array<"c" | "d" | "e"> {
  const out: Array<"c" | "d" | "e"> = [];
  if (/\bc:\b|c\s*drive/i.test(t)) out.push("c");
  if (/\bd\s*drive/i.test(t)) out.push("d");
  if (/\be\s*drive/i.test(t)) out.push("e");
  return out;
}

function findDriveSnapshot(
  registry: CapabilityRegistryResponse,
  letter: "c" | "d" | "e",
): { nodeLabel: string; drive: NodeDrive } | null {
  const sym = `${letter.toUpperCase()}:`;
  for (const n of registry.nodes) {
    if (!n.capabilities.telemetry.enabled) continue;
    for (const d of n.telemetrySnapshot.storage?.drives ?? []) {
      const mount = (d.mount ?? "").toUpperCase();
      const name = d.name.toUpperCase();
      if (mount.startsWith(sym) || name.includes(sym) || new RegExp(`${letter}:\\\\`, "i").test(d.name)) {
        return { nodeLabel: n.label, drive: d };
      }
    }
  }
  return null;
}

function formatSeeDriveTelemetry(
  registry: CapabilityRegistryResponse,
  t: string,
  surface: SpiritRuntimeSurface,
): string {
  const letters = driveLettersFromVisibilityQuery(t);
  const letterList = letters.length > 0 ? letters : (["c"] as const);

  const hits = letterList
    .map((L) => ({ L, hit: findDriveSnapshot(registry, L) }))
    .filter((x) => x.hit != null) as {
    L: "c" | "d" | "e";
    hit: { nodeLabel: string; drive: NodeDrive };
  }[];

  if (hits.length === 0) {
    const tailChat =
      "I don’t see that volume in the current storage telemetry. I can only report drives exposed by the active agents.";
    return surface === "oracle"
      ? `I don’t see **${letterList.map((l) => `${l.toUpperCase()}:`).join("/")}** in this poll’s storage telemetry - only drives active agents expose.`
      : `${tailChat}\n\nIf the host is online but the drive is missing, the collector may not have shipped storage rows yet for that node.`;
  }

  const order = { c: 0, d: 1, e: 2 } as const;
  const chunks = hits
    .map(({ L, hit }) => {
      const d = hit.drive;
      const used =
        d.usedBytes != null && d.totalBytes != null
          ? `${fmtBytes(d.usedBytes)} used of ${fmtBytes(d.totalBytes)}`
          : d.usedPct != null
            ? `${d.usedPct.toFixed(0)}% used`
            : "usage n/a";
      return {
        letter: L.toUpperCase(),
        node: hit.nodeLabel,
        used,
        name: d.name,
        sort: order[L],
      };
    })
    .sort((a, b) => a.sort - b.sort);

  if (surface === "oracle") {
    const first = chunks[0]!;
    const also =
      chunks.length > 1
        ? ` I also see ${chunks
            .slice(1)
            .map((c) => `**${c.letter}:**`)
            .join(", ")}.`
        : "";
    return `Yes - **${first.letter}:** shows on **${first.node}** in storage telemetry (${first.used}).${also} I can’t browse folders or list files inside those volumes from the app yet.`;
  }

  const primary = chunks[0]!;
  const alsoLine =
    chunks.length > 1
      ? `\n\nI also see ${chunks
          .slice(1)
          .map((c) => `**${c.letter}:** on **${c.node}**`)
          .join(" and ")}.`
      : "";

  return [
    `Yes. I can see **${primary.letter}:** through storage telemetry on **${primary.node}**, including total size and used space (${primary.used}).${alsoLine}`,
    "",
    "I **cannot** browse folders or list files inside those paths from the app yet - telemetry is drive-level totals only.",
  ].join("\n");
}

function formatStorageTelemetryInventory(
  registry: CapabilityRegistryResponse,
  surface: SpiritRuntimeSurface,
  includeSmallVolumes: boolean,
): string {
  const rows: string[] = [];

  if (surface === "oracle") {
    const summaryBits: string[] = [];
    for (const n of registry.nodes) {
      if (!n.capabilities.telemetry.enabled) continue;
      const drives = (n.telemetrySnapshot.storage?.drives ?? []).filter(
        (d) => !isSmallSystemVolume(d, includeSmallVolumes),
      );
      if (drives.length === 0) continue;
      const short = drives
        .map((d) => {
          const label = d.mount ?? d.name;
          const u =
            d.usedBytes != null && d.totalBytes != null
              ? `${fmtBytes(d.usedBytes)}/${fmtBytes(d.totalBytes)}`
              : d.usedPct != null
                ? `${d.usedPct.toFixed(0)}%`
                : "?";
          return `${label} ~${u}`;
        })
        .join("; ");
      summaryBits.push(`${n.label}: ${short}`);
    }
    const body =
      summaryBits.length > 0
        ? summaryBits.join(" · ")
        : "No drive rows in this telemetry poll.";
    return `Storage snapshot: ${body} - tiny OEM partitions omitted unless you ask for all/system volumes. I can’t browse folders from chat yet.`;
  }

  for (const n of registry.nodes) {
    const snap = n.telemetrySnapshot;
    const live = n.capabilities.telemetry.enabled;
    if (!live) {
      rows.push(`**${n.label}** - offline; no live storage snapshot.`);
      continue;
    }
    const drives = snap.storage?.drives ?? [];
    const filtered = drives.filter((d) => !isSmallSystemVolume(d, includeSmallVolumes));
    const skipped = drives.length - filtered.length;
    if (filtered.length === 0) {
      rows.push(
        `**${n.label}** - ${drives.length ? `${skipped} volume(s) hidden as small/system (ask for “all” or “debug” to include).` : "no drives listed in this poll."}`,
      );
      continue;
    }
    if (skipped > 0) {
      rows.push(`**${n.label}** - (${skipped} tiny/system volume(s) hidden)`);
    }
    for (const d of filtered) {
      const used =
        d.usedBytes != null && d.totalBytes != null
          ? `${fmtBytes(d.usedBytes)} / ${fmtBytes(d.totalBytes)}`
          : d.usedPct != null
            ? `${d.usedPct.toFixed(0)}% used`
            : "usage n/a";
      rows.push(
        `**${n.label}** - ${d.name} (${d.mount ?? "unmounted"}): ~${used}, type ${d.type}.`,
      );
    }
  }

  return rows.length > 0 ? rows.join("\n") : "No storage telemetry in this snapshot.";
}

function formatStorageStatus(input: FormatCapabilityAnswerInput): string {
  const t = normalizeForCapabilityIntent(input.userMessage ?? "");
  const { registry, runtimeSurface: surface } = input;

  const wantsAllDebug =
    /\b(all|every|full|complete|debug|removable)\b/i.test(t) ||
    /\bshow\s+all\b/i.test(t) ||
    /\b(system|small)\s+volumes?\b/i.test(t);

  const broadDriveInventory =
    /\bwhat\s+drives\b/i.test(t) ||
    /\bwhat\s+storage\b/i.test(t) ||
    /\b(can\s+you\s+|do\s+you\s+)?see\b.*\bmy\s+drives?\b/i.test(t);

  const singleDriveSee =
    !broadDriveInventory &&
    (/\b(can\s+you\s+|do\s+you\s+)?see\b.*\b(c:|c\s*drive|d\s*drive|e\s*drive)\b/i.test(t) ||
      /\bdo\s+you\s+see\b.*\bc:/i.test(t));

  if (singleDriveSee) {
    return formatSeeDriveTelemetry(registry, t, surface);
  }

  return formatStorageTelemetryInventory(registry, surface, wantsAllDebug);
}

function formatHardwareSummary(registry: CapabilityRegistryResponse): string {
  const lines: string[] = [];
  const names = registry.nodes.map((n) => n.label);
  lines.push(
    `I can see **${registry.nodes.length}** node(s) in cluster telemetry: ${names.join(", ")}.`,
  );
  lines.push("");

  for (const n of registry.nodes) {
    const snap = n.telemetrySnapshot;
    const live = n.capabilities.telemetry.enabled;
    lines.push(`**${n.label}** (\`${n.id}\`) - ${n.status}, ${n.source}${n.platform ? `, ${n.platform}` : ""}`);
    if (!live) {
      lines.push(`  - Live CPU/RAM not available${snap.error ? ` (${snap.error})` : ""}.`);
      continue;
    }
    const cpu = snap.cpu?.model ?? "unknown CPU";
    const cores = snap.cpu?.cores != null ? `${snap.cpu.cores}c` : "? cores";
    const cpuU = snap.cpu?.usagePct != null ? `${snap.cpu.usagePct.toFixed(0)}% busy` : "CPU load n/a";
    lines.push(`  - ${cpu} (${cores}), ${cpuU}`);
    if (snap.memory?.totalBytes != null) {
      const u =
        snap.memory.usedBytes != null
          ? fmtBytes(snap.memory.usedBytes)
          : snap.memory.usedPct != null
            ? `${snap.memory.usedPct.toFixed(0)}%`
            : "?";
      lines.push(`  - RAM: ~${u} of ${fmtBytes(snap.memory.totalBytes)}`);
    }
    const dr = snap.storage?.drives?.length ?? 0;
    lines.push(`  - Storage rows: ${dr} drive(s) in telemetry${dr ? "" : " (none this poll)"}.`);
  }

  return lines.join("\n");
}

