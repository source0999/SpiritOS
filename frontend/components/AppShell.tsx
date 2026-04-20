"use client";

import type { ReactNode } from "react";
import { MobileNav, DesktopSidebar } from "@/components/Navigation";
import { OverlayLockProvider, useOverlayLock } from "@/components/OverlayLockContext";
import { WhiteScreenDebugProbe } from "@/components/WhiteScreenDebugProbe";

function MainChrome({ children }: { children: ReactNode }) {
  const { mainLocked } = useOverlayLock();

  return (
    // z-0 REMOVED — "relative z-0" creates a stacking context that can cause
    // WebKit to evaluate fixed children's z-index within it rather than the
    // root stacking context, silently clipping overlays on iOS.
    <main
      tabIndex={mainLocked ? -1 : undefined}
      className="relative min-w-0 flex-1 pt-[60px] md:pt-0"
    >
      {children}
    </main>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <body
      className="bg-zinc-950 text-zinc-100 antialiased"
      /* Inline fallbacks match app/globals.css :root — if CSS chunks fail to load,
         Tailwind text colors can still apply while body background stays browser-white (white-on-white). */
      style={{ backgroundColor: "#09090b", color: "#fafafa" }}
    >
      <WhiteScreenDebugProbe />
      <OverlayLockProvider>
        {/*
          MobileNav is rendered HERE — before the flex layout container — so its
          fixed header, backdrop, and drawer are direct siblings of the layout
          div inside <body>. This fully escapes the flex/stacking-context tree
          and eliminates any risk of a parent transform or overflow rule
          clipping the position:fixed overlays on iOS Safari.
        */}
        <MobileNav />

        <div className="flex min-h-[100dvh] w-full flex-row pointer-events-auto">
          <DesktopSidebar />
          <MainChrome>{children}</MainChrome>
        </div>
      </OverlayLockProvider>
    </body>
  );
}
