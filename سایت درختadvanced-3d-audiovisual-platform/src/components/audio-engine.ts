type Kind = "hover" | "click" | "enter" | "warn" | "success" | "whoosh";

let ctx: AudioContext | null = null;
let master: GainNode | null = null;
let ambient: { stop: () => void } | null = null;
let enabled = true;

function ac() {
  if (typeof window === "undefined") return null;
  if (!ctx) {
    const C = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    ctx = new C();
    master = ctx.createGain();
    master.gain.value = 0.22;
    master.connect(ctx.destination);
  }
  return ctx;
}

export function setAudioEnabled(v: boolean) {
  enabled = v;
  if (!v) stopAmbient();
  if (master && ctx) {
    master.gain.setTargetAtTime(v ? 0.22 : 0, ctx.currentTime, 0.05);
  }
}

export function isAudioEnabled() {
  return enabled;
}

export async function unlockAudio() {
  const c = ac();
  if (!c) return;
  if (c.state === "suspended") await c.resume();
}

export function play(kind: Kind) {
  if (!enabled) return;
  const c = ac();
  if (!c || !master) return;
  const now = c.currentTime;
  const osc = c.createOscillator();
  const g = c.createGain();
  const f = c.createBiquadFilter();
  osc.connect(f);
  f.connect(g);
  g.connect(master);

  if (kind === "hover") {
    osc.type = "triangle";
    osc.frequency.setValueAtTime(1640, now);
    osc.frequency.exponentialRampToValueAtTime(1880, now + 0.04);
    g.gain.setValueAtTime(0.0001, now);
    g.gain.exponentialRampToValueAtTime(0.05, now + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, now + 0.07);
    f.frequency.value = 2400;
  } else if (kind === "click") {
    osc.type = "sine";
    osc.frequency.setValueAtTime(220, now);
    osc.frequency.exponentialRampToValueAtTime(90, now + 0.12);
    g.gain.setValueAtTime(0.0001, now);
    g.gain.exponentialRampToValueAtTime(0.18, now + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, now + 0.18);
    f.frequency.value = 900;
    const noise = c.createOscillator();
    const ng = c.createGain();
    noise.type = "square";
    noise.frequency.value = 42;
    ng.gain.setValueAtTime(0.04, now);
    ng.gain.exponentialRampToValueAtTime(0.0001, now + 0.08);
    noise.connect(ng);
    ng.connect(master);
    noise.start(now);
    noise.stop(now + 0.09);
  } else if (kind === "enter") {
    osc.type = "sine";
    osc.frequency.setValueAtTime(110, now);
    osc.frequency.exponentialRampToValueAtTime(330, now + 0.35);
    g.gain.setValueAtTime(0.0001, now);
    g.gain.exponentialRampToValueAtTime(0.14, now + 0.05);
    g.gain.exponentialRampToValueAtTime(0.0001, now + 0.5);
  } else if (kind === "warn") {
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(180, now);
    osc.frequency.exponentialRampToValueAtTime(70, now + 0.25);
    g.gain.setValueAtTime(0.0001, now);
    g.gain.exponentialRampToValueAtTime(0.1, now + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, now + 0.3);
    f.frequency.value = 400;
  } else if (kind === "success") {
    osc.type = "triangle";
    osc.frequency.setValueAtTime(440, now);
    osc.frequency.exponentialRampToValueAtTime(880, now + 0.18);
    g.gain.setValueAtTime(0.0001, now);
    g.gain.exponentialRampToValueAtTime(0.1, now + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, now + 0.32);
  } else {
    osc.type = "sine";
    osc.frequency.setValueAtTime(80, now);
    osc.frequency.exponentialRampToValueAtTime(40, now + 0.4);
    g.gain.setValueAtTime(0.0001, now);
    g.gain.exponentialRampToValueAtTime(0.12, now + 0.04);
    g.gain.exponentialRampToValueAtTime(0.0001, now + 0.5);
  }

  osc.start(now);
  osc.stop(now + 0.55);
}

export function startAmbient() {
  if (!enabled || ambient) return;
  const c = ac();
  if (!c || !master) return;
  const o1 = c.createOscillator();
  const o2 = c.createOscillator();
  const g = c.createGain();
  const f = c.createBiquadFilter();
  o1.type = "sine";
  o2.type = "sine";
  o1.frequency.value = 55;
  o2.frequency.value = 82.5;
  f.type = "lowpass";
  f.frequency.value = 220;
  g.gain.value = 0.0001;
  o1.connect(f);
  o2.connect(f);
  f.connect(g);
  g.connect(master);
  o1.start();
  o2.start();
  g.gain.linearRampToValueAtTime(0.035, c.currentTime + 1.4);
  ambient = {
    stop: () => {
      g.gain.linearRampToValueAtTime(0.0001, c.currentTime + 0.4);
      setTimeout(() => {
        o1.stop();
        o2.stop();
      }, 500);
    },
  };
}

export function stopAmbient() {
  ambient?.stop();
  ambient = null;
}
