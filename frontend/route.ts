import { NextRequest, NextResponse } from "next/server";

// ─── Intent matcher ───────────────────────────────────────────────────────────
// Simple keyword-based router. Replace the return values with real Ollama
// fetch calls once the backend is wired:
//
//   const ollamaRes = await fetch("http://spirit:11434/api/generate", {
//     method: "POST",
//     body: JSON.stringify({ model: "llama3-abliterated", prompt }),
//   });
//
function getReply(prompt: string): string {
  const q = prompt.toLowerCase();

  if (q.includes("energy") || q.includes("power") || q.includes("watt"))
    return "Current draw: 350W. spiritdesktop at 148W, spirit Dell at 198W, Pi holding steady at 4W. Super off-peak until 2 PM. You are not burning money yet. Give it time.";

  if (q.includes("grade") || q.includes("roast") || q.includes("grader"))
    return "Grader Agent is primed and waiting. Click [GRADE ME] on the widget when your self-esteem has recovered from the last session. Take your time. I will be here.";

  if (q.includes("p40") || q.includes("tesla") || q.includes("gpu"))
    return "P40 is still a very expensive paperweight. The 24-pin to 8-pin ATX adapter is the blocker. Order it. 24GB of passive-cooled VRAM changes every inference calculation you have.";

  if (q.includes("briefing") || q.includes("report") || q.includes("brief"))
    return "Last briefing synthesized at 06:00 AM. Four topics: local LLM benchmarks, PCIe riser bandwidth, CCPA enforcement, ToU rate shift. Next GPT-Researcher run queued for 03:00 AM. Go to sleep at a reasonable hour.";

  if (q.includes("drive") || q.includes("disk") || q.includes("storage"))
    return "spiritdesktop: 250GB SSD boot at 59% capacity, 1TB HDD at 41%, 2TB HDD at 44%. spirit Dell: 512GB SSD at 39%. All four SMART statuses: Healthy. Wire smartctl for live temp readings.";

  if (q.includes("pi") || q.includes("ghost") || q.includes("dns") || q.includes("pihole"))
    return "Ghost Node is up. Pi-hole running. DNS resolving. FLIRC aluminum case is still in transit — that ARM Cortex will thermal throttle under sustained Cloudflare tunnel load without it. Watch the temp.";

  if (q.includes("backup") || q.includes("borg"))
    return "No Vault yet — that 20TB NAS is future infrastructure. BorgBackup config is ready to deploy the moment the hardware lands. Borg + deduplication will keep that delta small.";

  if (q.includes("cinema") || q.includes("jellyfin") || q.includes("movie"))
    return "Cinema Engine config repo is at 82% completion. Jellyfin container is ready. Cloudflare tunnel for video is a ToS violation on the free tier — use Tailscale for your inner circle or rent a $5 VPS for WireGuard routing.";

  if (q.includes("hello") || q.includes("hey") || q.includes("hi") || q.includes("sup"))
    return "Source. I am here. What do you need? Do not waste both our time with pleasantries.";

  if (q.includes("help") || q.includes("what can you"))
    return "Energy stats, node vitals, P40 status, briefing summaries, drive health, Ghost Node, Borg backups, Cinema Engine. Wire me to the Ollama backend on spirit and I stop being a lookup table.";

  return "Command received. I do not have a hardcoded response for that one. Wire me to the Ollama backend on Node 2 and I will answer anything you throw at me. That is the whole point of this infrastructure.";
}

// ─── POST /api/spirit ─────────────────────────────────────────────────────────
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const prompt: string = body?.prompt ?? "";

    if (!prompt.trim()) {
      return NextResponse.json(
        { error: "prompt is required" },
        { status: 400 }
      );
    }

    // Simulate processing latency so the frontend thinking indicator
    // has time to render. Remove this once Ollama is wired.
    await new Promise((resolve) => setTimeout(resolve, 600 + Math.random() * 400));

    const reply = getReply(prompt);
    return NextResponse.json({ reply }, { status: 200 });

  } catch {
    return NextResponse.json(
      { error: "Failed to process request" },
      { status: 500 }
    );
  }
}
