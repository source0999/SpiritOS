// ── cn() — Tailwind class merge without fighting yourself ─────────────────────
// > Extracted from: ad-hoc dashboard copy-paste (deleted with prejudice)
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
