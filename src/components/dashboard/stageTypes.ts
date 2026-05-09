// ── Dashboard stage IDs + taskbar metadata (DEPRECATED for root UX) ───────────
// > Root "/" no longer renders StageId; DashboardClient archived for reference.
// > Blueprint fossils live on until oracle/quarantine extracts finish migrating.
import type { LucideIcon } from "lucide-react";
import {
  Brain,
  LayoutDashboard,
  ShieldAlert,
  Sparkles,
} from "lucide-react";

export type StageId = "hub" | "neural" | "oracle" | "quarantine";

export const TASKBAR: { id: StageId; label: string; icon: LucideIcon }[] = [
  { id: "hub", icon: LayoutDashboard, label: "Hub" },
  { id: "neural", icon: Brain, label: "Neural" },
  { id: "oracle", icon: Sparkles, label: "Oracle" },
  { id: "quarantine", icon: ShieldAlert, label: "Quarantine" },
];
