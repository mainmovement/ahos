/**
 * AHOS sound engine — generated WebAudio tones only (no audio files).
 * Muted by default; the AudioContext is created lazily on the first user
 * gesture to respect autoplay policies.
 */
export type SoundName = "tick" | "open" | "close" | "notify" | "alert" | "success" | "whoosh" | "send" | "receive";

type Ctx = AudioContext;

class SoundEngine {
  private ctx: Ctx | null = null;
  private master: GainNode | null = null;
  private ambientNodes: { stop: () => void } | null = null;
  private volume = 0.5;
  private muted = true;
  private noiseBuffer: AudioBuffer | null = null;

  private ensure(): Ctx | null {
    if (typeof window === "undefined") return null;
    if (!this.ctx) {
      const AC = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!AC) return null;
      this.ctx = new AC();
      this.master = this.ctx.createGain();
      this.master.gain.value = this.muted ? 0 : this.volume;
      // Gentle limiter so stacked tones never clip.
      const comp = this.ctx.createDynamicsCompressor();
      comp.threshold.value = -18;
      comp.ratio.value = 6;
      this.master.connect(comp).connect(this.ctx.destination);
    }
    if (this.ctx.state === "suspended") void this.ctx.resume();
    return this.ctx;
  }

  configure(opts: { muted: boolean; volume: number }) {
    this.muted = opts.muted;
    this.volume = opts.volume;
    if (this.ctx && this.master) {
      const now = this.ctx.currentTime;
      this.master.gain.cancelScheduledValues(now);
      this.master.gain.setTargetAtTime(this.muted ? 0 : this.volume * 0.9, now, 0.04);
    }
    if (this.muted) this.stopAmbient();
  }

  private tone(freq: number, start: number, dur: number, opts: { type?: OscillatorType; gain?: number; attack?: number; detune?: number; glideTo?: number } = {}) {
    const ctx = this.ctx!;
    const osc = ctx.createOscillator();
    const g = ctx.createGain();
    osc.type = opts.type ?? "sine";
    osc.frequency.setValueAtTime(freq, start);
    if (opts.glideTo) osc.frequency.exponentialRampToValueAtTime(opts.glideTo, start + dur);
    if (opts.detune) osc.detune.value = opts.detune;
    const peak = opts.gain ?? 0.2;
    const attack = opts.attack ?? 0.005;
    g.gain.setValueAtTime(0.0001, start);
    g.gain.exponentialRampToValueAtTime(peak, start + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, start + dur);
    osc.connect(g).connect(this.master!);
    osc.start(start);
    osc.stop(start + dur + 0.05);
  }

  private noise(start: number, dur: number, from: number, to: number, gain = 0.12) {
    const ctx = this.ctx!;
    if (!this.noiseBuffer) {
      const len = ctx.sampleRate * 1.5;
      this.noiseBuffer = ctx.createBuffer(1, len, ctx.sampleRate);
      const data = this.noiseBuffer.getChannelData(0);
      let seed = 1234567;
      for (let i = 0; i < len; i++) {
        seed = (seed * 16807) % 2147483647;
        data[i] = (seed / 2147483647) * 2 - 1;
      }
    }
    const src = ctx.createBufferSource();
    src.buffer = this.noiseBuffer;
    const filter = ctx.createBiquadFilter();
    filter.type = "bandpass";
    filter.Q.value = 1.2;
    filter.frequency.setValueAtTime(from, start);
    filter.frequency.exponentialRampToValueAtTime(to, start + dur);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, start);
    g.gain.exponentialRampToValueAtTime(gain, start + dur * 0.35);
    g.gain.exponentialRampToValueAtTime(0.0001, start + dur);
    src.connect(filter).connect(g).connect(this.master!);
    src.start(start);
    src.stop(start + dur + 0.05);
  }

  play(name: SoundName) {
    if (this.muted) return;
    const ctx = this.ensure();
    if (!ctx || !this.master) return;
    const t = ctx.currentTime + 0.01;
    switch (name) {
      case "tick":
        this.tone(2400, t, 0.045, { gain: 0.05, type: "sine" });
        break;
      case "open":
        this.tone(660, t, 0.16, { gain: 0.07, type: "sine" });
        this.tone(990, t + 0.05, 0.2, { gain: 0.05, type: "sine" });
        break;
      case "close":
        this.tone(880, t, 0.12, { gain: 0.06, type: "sine", glideTo: 620 });
        break;
      case "send":
        this.tone(1180, t, 0.08, { gain: 0.06, type: "triangle", glideTo: 1560 });
        break;
      case "receive":
        this.tone(784, t, 0.35, { gain: 0.06 });
        this.tone(1175, t + 0.07, 0.45, { gain: 0.045 });
        break;
      case "notify": // glassy chime: three partials
        [1046.5, 1568, 2093].forEach((f, i) => this.tone(f, t + i * 0.06, 1.1 - i * 0.2, { gain: 0.06 - i * 0.012 }));
        break;
      case "success":
        this.tone(523.25, t, 0.22, { gain: 0.07, type: "triangle" });
        this.tone(783.99, t + 0.09, 0.32, { gain: 0.06, type: "triangle" });
        break;
      case "alert": // descending minor third, soft triangle — attention, not alarm
        this.tone(880, t, 0.22, { gain: 0.08, type: "triangle" });
        this.tone(740, t + 0.18, 0.32, { gain: 0.08, type: "triangle" });
        break;
      case "whoosh":
        this.noise(t, 0.9, 300, 2600, 0.09);
        break;
    }
  }

  startAmbient() {
    if (this.muted || this.ambientNodes) return;
    const ctx = this.ensure();
    if (!ctx || !this.master) return;
    const out = ctx.createGain();
    out.gain.value = 0.0001;
    out.gain.setTargetAtTime(0.035, ctx.currentTime, 2.5);
    const filter = ctx.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.value = 520;
    filter.Q.value = 0.6;
    const lfo = ctx.createOscillator();
    const lfoGain = ctx.createGain();
    lfo.frequency.value = 0.05;
    lfoGain.gain.value = 180;
    lfo.connect(lfoGain).connect(filter.frequency);
    // A2 – E3 – B3 – F#4: an open, calm fifth stack
    const oscs = [110, 164.81, 246.94, 369.99].map((f, i) => {
      const o = ctx.createOscillator();
      o.type = i % 2 ? "triangle" : "sine";
      o.frequency.value = f;
      o.detune.value = (i - 1.5) * 4;
      const g = ctx.createGain();
      g.gain.value = 0.5 / (i + 1);
      o.connect(g).connect(filter);
      o.start();
      return o;
    });
    filter.connect(out).connect(this.master);
    lfo.start();
    this.ambientNodes = {
      stop: () => {
        const now = ctx.currentTime;
        out.gain.cancelScheduledValues(now);
        out.gain.setTargetAtTime(0.0001, now, 0.6);
        window.setTimeout(() => {
          oscs.forEach((o) => o.stop());
          lfo.stop();
          out.disconnect();
        }, 2500);
      },
    };
  }

  stopAmbient() {
    this.ambientNodes?.stop();
    this.ambientNodes = null;
  }
}

export const soundEngine = new SoundEngine();
