"use client";

// -- SpiritTrinityChatShell - dashboard v4 chrome around the real SpiritChat runtime --
import { useEffect, useState } from "react";

import { SpiritChat } from "@/components/chat/SpiritChat";
import type { SpiritChatProps } from "@/components/chat/SpiritChat";
import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";

function ClientOnlySpiritChat(props: SpiritChatProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const id = window.setTimeout(() => setMounted(true), 0);
    return () => window.clearTimeout(id);
  }, []);

  if (!mounted) return null;

  return <SpiritChat {...props} />;
}

export default function SpiritTrinityChatShell() {
  return (
    <div className="spirit-trinity-chat fixed inset-0 flex overflow-hidden text-[var(--spirit-text)]">
      <div className="spirit-trinity-atmosphere" aria-hidden>
        <div className="spirit-trinity-atmosphere__base" />
        <div className="spirit-trinity-atmosphere__grid" />
        <div className="spirit-trinity-atmosphere__wash" />
        <div className="spirit-trinity-atmosphere__veil" />
      </div>

      <main className="spirit-trinity-live-chat min-w-0 flex-1">
        <ClientOnlySpiritChat
          persistence
          variant="workspace"
          showThreadSidebar
          chromeVariant="trinity"
          title="Spirit"
          subtitle="Workspace 1.5"
          shellClassName="h-full min-h-0"
        />
      </main>

      <DashboardDemoV4FloatingNav desktopVariant="full-height" />
    </div>
  );
}
