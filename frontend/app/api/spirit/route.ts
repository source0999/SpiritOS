import { NextResponse } from "next/server";

/** Simulated latency so the Command Bar thinking dots render; remove when Ollama is wired. */
const SIMULATED_DELAY_MS = 650;

/** Replace this with `fetch("http://spirit:11434/api/generate", …)` using your Tailscale hostname when ready. */
function getReply(prompt: string): string {
  const q = prompt.toLowerCase();
  if (q.includes("energy") || q.includes("power") || q.includes("watt"))
    return "Current draw: 350W. spiritdesktop, spirit, Pi. Super off-peak until 2 PM. Not burning money yet.";
  if (q.includes("grade") || q.includes("roast"))
    return "Grader Agent primed. Click [GRADE ME] on the widget when your self-esteem can take it.";
  if (q.includes("p40") || q.includes("tesla"))
    return "P40 still offline. Waiting on the 24-pin to 8-pin ATX adapter. It will be worth it.";
  if (q.includes("briefing") || q.includes("report"))
    return "Last briefing: 06:00 AM. Four topics covered. Next GPT-Researcher run: 03:00 AM.";
  if (q.includes("drive") || q.includes("disk") || q.includes("storage"))
    return "spiritdesktop: 250GB SSD boot, 1TB + 2TB HDDs. spirit Dell: 512GB SSD. All SMART statuses healthy.";
  if (q.includes("pi") || q.includes("ghost") || q.includes("dns"))
    return "Ghost Node up. Pi-hole running. FLIRC case in transit — watch thermal throttle under DNS load.";
  return "Command noted. Wire me to the Ollama backend for real answers.";
}

export async function POST(req: Request) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const prompt =
    typeof body === "object" &&
    body !== null &&
    "prompt" in body &&
    typeof (body as { prompt: unknown }).prompt === "string"
      ? (body as { prompt: string }).prompt.trim()
      : "";

  if (!prompt) {
    return NextResponse.json({ error: "Missing prompt" }, { status: 400 });
  }

  await new Promise((r) => setTimeout(r, SIMULATED_DELAY_MS));

  const reply = getReply(prompt);
  return NextResponse.json({ reply });
}
