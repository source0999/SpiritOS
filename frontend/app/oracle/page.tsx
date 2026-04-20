"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ArrowLeft, Mic, MicOff, Loader2 } from "lucide-react";
import Link from "next/link";

// ── Types ─────────────────────────────────────────────────────────────────────

type SarcasmId = "chill" | "peer" | "unhinged";
type OracleStatus = "idle" | "recording" | "processing" | "playing" | "error";

// ── Static config ─────────────────────────────────────────────────────────────

const SARCASM_LEVELS: {
  id: SarcasmId;
  label: string;
  desc: string;
  active: string;
}[] = [
  {
    id:     "chill",
    label:  "Chill",
    desc:   "Measured. Cooperative.",
    active: "border-emerald-500/40 bg-emerald-500/15 text-emerald-300",
  },
  {
    id:     "peer",
    label:  "Peer",
    desc:   "Direct. Unfiltered.",
    active: "border-violet-500/40 bg-violet-500/15 text-violet-300",
  },
  {
    id:     "unhinged",
    label:  "Unhinged",
    desc:   "Maximum exasperation.",
    active: "border-rose-500/40 bg-rose-500/15 text-rose-300",
  },
];

// XTTS v2 acoustic stage-direction markers
const MARKERS = [
  "[sigh]",
  "[scoffs]",
  "[groan]",
  "[exhale]",
  "[pause]",
  "[laughs]",
] as const;

// Pre-computed waveform bar shapes — envelope peaks at the centre so the
// visualiser looks like a real voice fundamental frequency plot.
const BARS = Array.from({ length: 44 }, (_, i) => {
  const envelope = Math.sin((i / 43) * Math.PI);            // 0 → 1 → 0
  const jitter   = ((i * 53 + 17) % 18);                    // 0–17 pseudo-random
  const maxH     = Math.round(10 + envelope * 50 + jitter); // 10–78 px
  const dur      = 0.48 + (i % 7) * 0.06;                   // 0.48–0.84 s
  const delay    = i * 0.022;                                // staggered
  const color =
    i % 9 === 4 ? "bg-rose-400/65"
    : i % 5 === 2 ? "bg-amber-400/55"
    : "bg-violet-500/60";
  return { maxH, dur, delay, color };
});

// Best available MIME type for MediaRecorder across browsers / mobile WebKit
function getBestMimeType(): string {
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
    "audio/mp4",
    "",
  ];
  for (const type of candidates) {
    if (!type || MediaRecorder.isTypeSupported(type)) return type;
  }
  return "";
}

// Status → badge text / colour helpers
const STATUS_BADGE: Record<OracleStatus, { text: string; className: string }> = {
  idle:       { text: "Listening · Idle",       className: "border-violet-500/20 bg-violet-500/[0.06] text-violet-300" },
  recording:  { text: "● Recording",            className: "border-rose-500/30 bg-rose-500/[0.10] text-rose-300 animate-pulse" },
  processing: { text: "Processing…",            className: "border-amber-500/30 bg-amber-500/[0.10] text-amber-300" },
  playing:    { text: "◆ Speaking",             className: "border-emerald-500/30 bg-emerald-500/[0.10] text-emerald-300" },
  error:      { text: "Error · Tap to retry",   className: "border-rose-500/40 bg-rose-500/15 text-rose-300" },
};

// ── Component ─────────────────────────────────────────────────────────────────

export default function OraclePage() {
  const [sarcasm,      setSarcasm]      = useState<SarcasmId>("peer");
  const [activeMarker, setActiveMarker] = useState<string | null>(null);
  const [status,       setStatus]       = useState<OracleStatus>("idle");
  const [transcript,   setTranscript]   = useState<string>("");
  const [reply,        setReply]        = useState<string>("");
  const [errorMsg,     setErrorMsg]     = useState<string>("");

  // Refs — all long-lived audio objects live outside React's render cycle
  const sarcasmRef       = useRef<SarcasmId>(sarcasm);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef   = useRef<Blob[]>([]);
  const audioCtxRef      = useRef<AudioContext | null>(null);
  const rafRef           = useRef<number>(0);
  // One ref slot per bar — lets us update heights directly without re-renders
  const barRefs          = useRef<(HTMLSpanElement | null)[]>([]);

  // Keep sarcasm ref in sync so the MediaRecorder.onstop closure sees latest value
  useEffect(() => { sarcasmRef.current = sarcasm; }, [sarcasm]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cancelAnimationFrame(rafRef.current);
      mediaRecorderRef.current?.stop();
      audioCtxRef.current?.close().catch(() => {});
    };
  }, []);

  // ── Waveform visualizer ───────────────────────────────────────────────────

  // Direct DOM mutations at 60 fps — bypassing React reconciler intentionally
  const startVisualizer = useCallback((analyser: AnalyserNode) => {
    const data   = new Uint8Array(analyser.frequencyBinCount);
    // Focus on the voice frequency range (roughly the lower 65 % of bins)
    const maxBin = Math.floor(analyser.frequencyBinCount * 0.65);

    function draw() {
      analyser.getByteFrequencyData(data);

      for (let i = 0; i < BARS.length; i++) {
        const el = barRefs.current[i];
        if (!el) continue;
        const binIdx    = Math.floor((i / BARS.length) * maxBin);
        const amplitude = data[binIdx] / 255;                    // 0 – 1
        const height    = 4 + amplitude * (BARS[i].maxH - 4);   // min 4 px
        el.style.height    = `${height}px`;
        el.style.animation = "none";                             // pause CSS anim
      }

      rafRef.current = requestAnimationFrame(draw);
    }

    cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(draw);
  }, []);

  const stopVisualizer = useCallback(() => {
    cancelAnimationFrame(rafRef.current);

    for (let i = 0; i < BARS.length; i++) {
      const el = barRefs.current[i];
      if (!el) continue;
      el.style.height    = `${BARS[i].maxH}px`;
      el.style.animation =
        `navi-bar ${BARS[i].dur}s ease-in-out ${BARS[i].delay}s infinite alternate`;
    }
  }, []);

  // ── Audio playback ────────────────────────────────────────────────────────

  const playAudio = useCallback(async (buffer: ArrayBuffer) => {
    setStatus("playing");

    const ctx      = new AudioContext();
    audioCtxRef.current = ctx;

    const analyser = ctx.createAnalyser();
    analyser.fftSize = 256;

    let decoded: AudioBuffer;
    try {
      decoded = await ctx.decodeAudioData(buffer.slice(0)); // slice prevents detachment
    } catch {
      await ctx.close();
      setErrorMsg("Could not decode audio from TTS service.");
      setStatus("error");
      stopVisualizer();
      return;
    }

    const source = ctx.createBufferSource();
    source.buffer = decoded;
    source.connect(analyser);
    analyser.connect(ctx.destination);

    startVisualizer(analyser);

    source.onended = () => {
      stopVisualizer();
      ctx.close().catch(() => {});
      setStatus("idle");
    };

    source.start();
  }, [startVisualizer, stopVisualizer]);

  // ── Pipeline: blob → STT → LLM → TTS → play ──────────────────────────────

  const processAudio = useCallback(async (blob: Blob, level: SarcasmId) => {
    setStatus("processing");

    try {
      const form = new FormData();
      form.append("audio", blob, "recording.webm");
      form.append("sarcasmLevel", level);

      const res = await fetch("/api/oracle", { method: "POST", body: form });

      if (!res.ok) {
        let msg = `HTTP ${res.status}`;
        try {
          const json = (await res.json()) as { error?: string };
          if (json.error) msg = json.error;
        } catch { /* ignore */ }
        throw new Error(msg);
      }

      const xTranscript = res.headers.get("X-Transcript");
      const xReply      = res.headers.get("X-Reply");
      if (xTranscript) setTranscript(decodeURIComponent(xTranscript));
      if (xReply)      setReply(decodeURIComponent(xReply));

      const audioBuffer = await res.arrayBuffer();
      await playAudio(audioBuffer);
    } catch (err) {
      setErrorMsg(String(err));
      setStatus("error");
      stopVisualizer();
    }
  }, [playAudio, stopVisualizer]);

  // ── Mic recording ─────────────────────────────────────────────────────────

  const startRecording = useCallback(async () => {
    setErrorMsg("");

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setErrorMsg("Microphone access denied. Allow it in your browser and try again.");
      setStatus("error");
      return;
    }

    // Tap the mic stream into an AnalyserNode for live input visualisation
    const ctx = new AudioContext();
    audioCtxRef.current = ctx;
    const micSource = ctx.createMediaStreamSource(stream);
    const analyser  = ctx.createAnalyser();
    analyser.fftSize = 256;
    micSource.connect(analyser);
    startVisualizer(analyser);

    const mimeType = getBestMimeType();
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
    audioChunksRef.current = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunksRef.current.push(e.data);
    };

    recorder.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      stopVisualizer();
      ctx.close().catch(() => {});

      const blob = new Blob(audioChunksRef.current, {
        type: mimeType || "audio/webm",
      });
      void processAudio(blob, sarcasmRef.current);
    };

    recorder.start();
    mediaRecorderRef.current = recorder;
    setStatus("recording");
  }, [startVisualizer, stopVisualizer, processAudio]);

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
    mediaRecorderRef.current = null;
    // status transitions to "processing" inside recorder.onstop → processAudio
  }, []);

  // ── Mic button handler ────────────────────────────────────────────────────

  function handleMicButton() {
    if (status === "idle" || status === "error") {
      void startRecording();
    } else if (status === "recording") {
      stopRecording();
    }
    // processing / playing: no-op — let the pipeline finish
  }

  // ── Derived UI values ─────────────────────────────────────────────────────

  const currentLevel = SARCASM_LEVELS.find((l) => l.id === sarcasm)!;
  const badge        = STATUS_BADGE[status];

  const micButtonLabel =
    status === "idle"       ? "TAP TO SPEAK"
    : status === "recording"  ? "TAP TO STOP"
    : status === "processing" ? "PROCESSING…"
    : status === "playing"    ? "SPEAKING"
    : status === "error"      ? "TAP TO RETRY"
    : "TAP TO SPEAK";

  const micButtonClass = (() => {
    const base = "flex items-center justify-center gap-2 rounded-2xl border px-6 py-3.5 font-mono text-xs font-semibold uppercase tracking-widest transition-all active:scale-[0.97] touch-manipulation";
    if (status === "recording")
      return `${base} border-rose-500/50 bg-rose-500/15 text-rose-300`;
    if (status === "processing" || status === "playing")
      return `${base} border-white/10 bg-white/[0.03] text-zinc-500 cursor-not-allowed`;
    if (status === "error")
      return `${base} border-rose-500/40 bg-rose-500/10 text-rose-400 hover:bg-rose-500/20`;
    // idle — tinted by sarcasm level
    return sarcasm === "chill"
      ? `${base} border-emerald-500/30 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20`
      : sarcasm === "unhinged"
      ? `${base} border-rose-500/25 bg-rose-500/[0.08] text-rose-300 hover:bg-rose-500/15`
      : `${base} border-violet-500/30 bg-violet-500/10 text-violet-300 hover:bg-violet-500/20`;
  })();

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="flex h-[calc(100dvh-60px)] flex-col overflow-hidden bg-zinc-950 text-zinc-100 md:h-[100dvh]">

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <header className="flex-shrink-0 flex items-center justify-between border-b border-white/[0.05] px-5 py-3">
        <Link
          href="/"
          className="flex items-center gap-2 text-sm text-zinc-400 transition-colors hover:text-zinc-100"
        >
          <ArrowLeft size={15} className="pointer-events-none" />
          Dashboard
        </Link>

        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-50" />
            <span className="relative h-2 w-2 rounded-full bg-emerald-400" />
          </span>
          <span className="font-mono text-xs text-zinc-400">XTTS v2 · Online</span>
        </div>

        <span className="font-mono text-xs text-zinc-600">Architecture 7</span>
      </header>

      {/* ── Main ────────────────────────────────────────────────────────── */}
      <main className="flex flex-1 flex-col items-center justify-center gap-6 overflow-hidden px-4 py-4">

        {/* Dynamic status badge */}
        <div className={`flex items-center gap-2 rounded-full border px-4 py-1.5 ${badge.className}`}>
          <Mic size={12} className="pointer-events-none shrink-0" />
          <span className="font-mono text-[11px] uppercase tracking-widest">
            {badge.text}
          </span>
        </div>

        {/* ── XL Navi Orb ─────────────────────────────────────────────── */}
        <div className="relative h-72 w-72 flex-shrink-0 pointer-events-none">
          <span className="navi-aura  pointer-events-none absolute inset-0 m-auto h-44 w-44 rounded-full bg-violet-500/15" />
          <span className="navi-halo  pointer-events-none absolute inset-0 m-auto h-32 w-32 rounded-full bg-violet-600/18" />

          <span className="navi-p1-xl pointer-events-none absolute inset-0 m-auto h-[11px] w-[11px] rounded-full bg-violet-300 opacity-70" />
          <span className="navi-p2-xl pointer-events-none absolute inset-0 m-auto h-[8px]  w-[8px]  rounded-full bg-violet-400 opacity-50" />
          <span className="navi-p3-xl pointer-events-none absolute inset-0 m-auto h-[6px]  w-[6px]  rounded-full bg-violet-400 opacity-30" />
          <span className="navi-p4-xl pointer-events-none absolute inset-0 m-auto h-[4px]  w-[4px]  rounded-full bg-violet-500 opacity-[0.18]" />
          <span className="navi-p5-xl pointer-events-none absolute inset-0 m-auto h-[3px]  w-[3px]  rounded-full bg-violet-500 opacity-10" />

          <div className="navi-float-xl absolute inset-0 m-auto flex h-20 w-20 items-center justify-center rounded-full">
            <span className="navi-wing-l-xl pointer-events-none absolute h-16 w-[14px] rounded-full bg-gradient-to-b from-violet-300/65 to-violet-700/10" />
            <span className="navi-wing-r-xl pointer-events-none absolute h-16 w-[14px] rounded-full bg-gradient-to-b from-violet-300/65 to-violet-700/10" />
            <span className="navi-halo-btn  pointer-events-none absolute h-20 w-20    rounded-full border border-violet-300/30" />
            <span
              className="navi-glow-pulse pointer-events-none absolute h-24 w-24 rounded-full"
              style={{ background: "radial-gradient(circle, rgba(139,92,246,0.70) 0%, rgba(139,92,246,0) 70%)" }}
            />
            <span className="navi-core-xl   pointer-events-none absolute h-10 w-10    rounded-full bg-white" />
          </div>
        </div>

        {/* ── Mic Button ──────────────────────────────────────────────── */}
        <button
          type="button"
          onClick={handleMicButton}
          disabled={status === "processing" || status === "playing"}
          aria-label={micButtonLabel}
          className={micButtonClass}
        >
          {status === "processing" ? (
            <Loader2 size={13} className="animate-spin pointer-events-none" />
          ) : status === "recording" ? (
            <MicOff size={13} className="pointer-events-none" />
          ) : (
            <Mic size={13} className="pointer-events-none" />
          )}
          {micButtonLabel}
        </button>

        {/* Error message */}
        {status === "error" && errorMsg && (
          <p className="max-w-xs text-center font-mono text-[11px] text-rose-400">
            {errorMsg}
          </p>
        )}

        {/* ── Waveform Visualiser ──────────────────────────────────────── */}
        <div className="flex w-full max-w-xl flex-col items-center gap-4">

          {/* Bar graph — bar heights driven by AnalyserNode during audio, CSS otherwise */}
          <div className="flex h-20 w-full items-end justify-center gap-[3px]">
            {BARS.map((bar, i) => (
              <span
                key={i}
                ref={(el) => { barRefs.current[i] = el; }}
                className={`${bar.color} w-[4px] origin-bottom rounded-full`}
                style={{
                  height: `${bar.maxH}px`,
                  animation: `navi-bar ${bar.dur}s ease-in-out ${bar.delay}s infinite alternate`,
                }}
              />
            ))}
          </div>

          {/* Legend */}
          <div className="flex items-center gap-4 text-[11px] font-mono text-zinc-600">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-violet-500/60" />
              Normal
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-amber-400/55" />
              Stress
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-rose-400/65" />
              Marker
            </span>
          </div>

          {/* Transcript / reply readout (collapses when empty) */}
          {(transcript || reply) && (
            <div className="w-full max-w-sm rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 space-y-2">
              {transcript && (
                <p className="font-mono text-[11px] text-zinc-500">
                  <span className="text-zinc-600 uppercase tracking-widest mr-1.5">You</span>
                  {transcript}
                </p>
              )}
              {reply && (
                <p className="font-mono text-[11px] text-violet-300">
                  <span className="text-violet-600 uppercase tracking-widest mr-1.5">Spirit</span>
                  {reply}
                </p>
              )}
            </div>
          )}

          {/* Acoustic marker chips */}
          <div className="flex flex-wrap items-center justify-center gap-2">
            {MARKERS.map((marker) => {
              const active = activeMarker === marker;
              return (
                <button
                  key={marker}
                  type="button"
                  onClick={() => setActiveMarker(active ? null : marker)}
                  onTouchEnd={(e) => {
                    e.preventDefault();
                    setActiveMarker(active ? null : marker);
                  }}
                  className={`rounded-full border px-3 py-1 font-mono text-[11px] transition-colors ${
                    active
                      ? "border-rose-500/50 bg-rose-500/15 text-rose-300"
                      : "border-white/[0.08] bg-white/[0.02] text-zinc-500 hover:border-white/20 hover:text-zinc-400"
                  }`}
                >
                  {marker}
                </button>
              );
            })}
          </div>

          {activeMarker && (
            <p className="font-mono text-[11px] italic text-zinc-500">
              XTTS v2 injects emotional inflection at{" "}
              <span className="text-rose-400">{activeMarker}</span> tokens
            </p>
          )}
        </div>
      </main>

      {/* ── Sarcasm Level ────────────────────────────────────────────────── */}
      <footer
        className="flex-shrink-0 border-t border-white/[0.05] bg-zinc-950 px-4 pt-4"
        style={{ paddingBottom: "max(20px, env(safe-area-inset-bottom))" }}
      >
        <div className="mx-auto flex max-w-sm flex-col gap-3">

          <div className="flex items-center justify-between">
            <span className="font-mono text-[11px] uppercase tracking-widest text-zinc-500">
              Sarcasm Level
            </span>
            <span className="font-mono text-[11px] text-zinc-600 transition-all">
              {currentLevel.desc}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-1 rounded-xl border border-white/[0.07] bg-white/[0.02] p-1">
            {SARCASM_LEVELS.map((level) => (
              <button
                key={level.id}
                type="button"
                onClick={() => setSarcasm(level.id)}
                onTouchEnd={(e) => { e.preventDefault(); setSarcasm(level.id); }}
                className={`rounded-lg border py-2.5 text-xs font-semibold transition-colors ${
                  sarcasm === level.id
                    ? level.active
                    : "border-transparent text-zinc-500 hover:text-zinc-300"
                }`}
              >
                {level.label}
              </button>
            ))}
          </div>

          <div className="flex gap-1">
            {SARCASM_LEVELS.map((level) => (
              <div
                key={level.id}
                className={`h-0.5 flex-1 rounded-full transition-all duration-300 ${
                  sarcasm === level.id
                    ? level.id === "chill"    ? "bg-emerald-400"
                      : level.id === "peer"   ? "bg-violet-400"
                      :                         "bg-rose-400"
                    : "bg-white/10"
                }`}
              />
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
