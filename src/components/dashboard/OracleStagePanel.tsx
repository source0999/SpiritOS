"use client";

// ── OracleStagePanel — hub “Oracle” tab CTA (not the full /oracle workspace) ─
import Link from "next/link";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { spiritPrimaryCtaClasses } from "@/components/ui/SpiritButton";
import { cn } from "@/lib/cn";

export function OracleStagePanel() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-8 p-6 text-center">
      <GlassPanel className="max-w-xl rounded-3xl px-10 py-12">
        <SectionLabel className="tracking-[0.3em]">Oracle</SectionLabel>
        <h2 className="mt-2 text-2xl font-semibold text-chalk">Signal router + orb lane</h2>
        <p className="mt-4 leading-relaxed text-chalk/55">
          Dedicated Oracle routes still live outside this hub shell. Ship there when you
          need STT streaming + longer sessions.
        </p>
        <Link href="/oracle" className={cn(spiritPrimaryCtaClasses, "mt-10 px-10")}>
          Open Oracle workspace →
        </Link>
      </GlassPanel>
    </div>
  );
}
