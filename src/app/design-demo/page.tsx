import type { Metadata } from "next";

import "@/styles/spirit-demo.tokens.css";
import "@/styles/spirit-demo.layout.css";
import "@/styles/spirit-demo.effects.css";
import "@/styles/spirit-demo.components.css";
import "@/styles/spirit-demo.animations.css";

import { SpiritDesignDemo } from "@/components/design-demo/SpiritDesignDemo";

export const metadata: Metadata = {
  title: "Spirit OS · Design Demo",
  description:
    "Visual-only preview of the Spirit OS command center. Production routes (/chat, /oracle, /quarantine) remain untouched.",
};

export default function DesignDemoPage() {
  return <SpiritDesignDemo />;
}
