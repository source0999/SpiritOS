// ── spirit-capability-context — short pointer for /api/spirit (client + server safe) ─
// > Live capability answers for intent-matched questions are assembled server-side in /api/spirit.
// > GET /api/telemetry/capabilities returns the full JSON for dashboards and curl.

/** Appended to mode system prompt so Spirit knows what it can query vs pretend. */
export const SPIRIT_CAPABILITY_CONTEXT_HINT = `## SpiritOS live capability registry (read-only)
SpiritOS has live cluster telemetry and read-only capability data on the server. For questions like **what you can do**, **what your capabilities are**, **what tools exist**, or **what you cannot do yet**, /api/spirit answers from that live registry when intent matches — use those facts instead of generic “I don’t have access” boilerplate.
Do not imply you lack visibility into the homelab when telemetry is available; say clearly what is **wired vs not wired** (app-level file browse, SSH from chat, desktop control are not tools yet).
SPIRIT_PROJECT_PATH in env only means paths are configured, not that files were inspected.`;
