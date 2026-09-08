"use client";

// ---------------------------------------------------------------------------
// AHOS synthetic sound engine.
// All UI sounds are generated in real-time via the Web Audio API — no audio
// files are shipped, keeping the bundle tiny while still giving every
// interactive element a distinct sci-fi audio signature.
// ---------------------------------------------------------------------------

let ctx: AudioContext | null = null;
let masterGain: GainNode | null = null;
let muted = false;

function getCtx(): AudioContext | null {
  if (typeof window === "undefined") return null;
  if (!ctx) {
    const AC = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    if (!AC) return null;
    ctx = new AC();
    masterGain = ctx.createGain();
    masterGain.gain.value = 0.16;
    masterGain.connect(ctx.destination);
  }
  if (ctx.state === "suspended") {
    ctx.resume().catch(() => {});
  }
  return ctx;
}

export function setMuted(value: boolean) {
  muted = value;
  if (typeof window !== "undefined") {
    window.localStorage.setItem("ahos_muted", value ? "1" : "0");
  }
}

export function getMuted() {
  if (typeof window !== "undefined") {
    return window.localStorage.getItem("ahos_muted") === "1";
  }
  return muted;
}

type Tone = {
  freq: number;
  end?: number;
  duration?: number;
  type?: OscillatorType;
  gain?: number;
  delay?: number;
};

function playTones(tones: Tone[]) {
  if (getMuted()) return;
  const audioCtx = getCtx();
  if (!audioCtx || !masterGain) return;
  const now = audioCtx.currentTime;

  tones.forEach((t) => {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = t.type ?? "sine";
    const start = now + (t.delay ?? 0);
    const duration = t.duration ?? 0.12;
    osc.frequency.setValueAtTime(t.freq, start);
    if (t.end) {
      osc.frequency.exponentialRampToValueAtTime(Math.max(t.end, 1), start + duration);
    }
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(t.gain ?? 0.5, start + 0.012);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
    osc.connect(gain);
    gain.connect(masterGain!);
    osc.start(start);
    osc.stop(start + duration + 0.02);
  });
}

export const sfx = {
  hover: () => playTones([{ freq: 720, end: 980, duration: 0.06, type: "sine", gain: 0.22 }]),
  click: () =>
    playTones([
      { freq: 340, end: 180, duration: 0.09, type: "triangle", gain: 0.5 },
      { freq: 1200, end: 800, duration: 0.05, type: "sine", gain: 0.18, delay: 0.01 },
    ]),
  toggleOn: () =>
    playTones([
      { freq: 440, end: 660, duration: 0.08, type: "sine", gain: 0.4 },
      { freq: 880, end: 1100, duration: 0.08, type: "sine", gain: 0.25, delay: 0.05 },
    ]),
  toggleOff: () => playTones([{ freq: 500, end: 260, duration: 0.09, type: "sine", gain: 0.35 }]),
  success: () =>
    playTones([
      { freq: 523, duration: 0.09, type: "sine", gain: 0.35 },
      { freq: 659, duration: 0.09, type: "sine", gain: 0.35, delay: 0.09 },
      { freq: 784, duration: 0.16, type: "sine", gain: 0.4, delay: 0.18 },
    ]),
  alert: () =>
    playTones([
      { freq: 220, end: 180, duration: 0.14, type: "sawtooth", gain: 0.3 },
      { freq: 220, end: 180, duration: 0.14, type: "sawtooth", gain: 0.3, delay: 0.18 },
    ]),
  nav: () => playTones([{ freq: 300, end: 620, duration: 0.1, type: "sine", gain: 0.22 }]),
  open: () =>
    playTones([
      { freq: 200, end: 500, duration: 0.14, type: "sine", gain: 0.3 },
      { freq: 500, end: 900, duration: 0.1, type: "sine", gain: 0.15, delay: 0.06 },
    ]),
  close: () => playTones([{ freq: 500, end: 160, duration: 0.12, type: "sine", gain: 0.25 }]),
  type: () => playTones([{ freq: 900 + Math.random() * 300, duration: 0.02, type: "square", gain: 0.05 }]),
  whoosh: () =>
    playTones([
      { freq: 120, end: 40, duration: 0.4, type: "sawtooth", gain: 0.12 },
      { freq: 900, end: 60, duration: 0.35, type: "sine", gain: 0.08 },
    ]),
};

export function primeAudio() {
  getCtx();
}
