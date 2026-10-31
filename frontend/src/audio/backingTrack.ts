// Phát backing track của Harmony Lab (phuc-music Bước 4, FR-17) bằng Tone.js.
// Lịch phát tính theo phách rồi đổi sang thời gian nhạc của Transport (ô:phách:móc kép), nên đổi tempo
// khi đang phát không làm lệch các kênh (tài liệu 04 mục 6.8: giây = phách × 60 / BPM, chỉ tính lúc phát).
// Cao độ lấy từ API voicings (Music Engine); file này chỉ xếp lịch, không tự tính nốt.
import * as Tone from "tone";

import { BEATS_PER_BAR, beatToTransport, type Channel, type TrackEvent } from "./trackSchedule";


const toFreq = (midi: number) => Tone.Frequency(midi, "midi").toFrequency();

class BackingTrackPlayer {
  private nodes: { channels: Record<Channel, Tone.Volume>; chords: Tone.PolySynth; bass: Tone.MonoSynth; kick: Tone.MembraneSynth; snare: Tone.NoiseSynth; hat: Tone.MetalSynth } | null = null;
  private scheduled: number[] = [];
  private muted: Record<Channel, boolean> = { chords: false, bass: false, drums: false };

  private ensureNodes() {
    if (this.nodes) return this.nodes;
    const channels = {
      chords: new Tone.Volume(-10).toDestination(),
      bass: new Tone.Volume(-6).toDestination(),
      drums: new Tone.Volume(-4).toDestination(),
    };
    const chords = new Tone.PolySynth(Tone.Synth, { oscillator: { type: "triangle" }, envelope: { attack: 0.02, decay: 0.3, sustain: 0.4, release: 0.8 } }).connect(channels.chords);
    const bass = new Tone.MonoSynth({ oscillator: { type: "square" }, filter: { Q: 1, type: "lowpass" }, envelope: { attack: 0.01, decay: 0.2, sustain: 0.5, release: 0.2 }, filterEnvelope: { attack: 0.01, decay: 0.2, sustain: 0.3, baseFrequency: 120, octaves: 2 } }).connect(channels.bass);
    const kick = new Tone.MembraneSynth({ pitchDecay: 0.04, octaves: 6, envelope: { attack: 0.001, decay: 0.3, sustain: 0, release: 0.1 } }).connect(channels.drums);
    const snare = new Tone.NoiseSynth({ noise: { type: "white" }, envelope: { attack: 0.001, decay: 0.15, sustain: 0 } }).connect(channels.drums);
    const hat = new Tone.MetalSynth({ envelope: { attack: 0.001, decay: 0.05, release: 0.01 }, harmonicity: 5.1, modulationIndex: 32, resonance: 4000, octaves: 1.5 }).connect(channels.drums);
    hat.volume.value = -22;
    snare.volume.value = -8;
    for (const channel of Object.keys(channels) as Channel[]) channels[channel].mute = this.muted[channel];
    this.nodes = { channels, chords, bass, kick, snare, hat };
    return this.nodes;
  }

  setMuted(channel: Channel, muted: boolean) {
    this.muted[channel] = muted;
    if (this.nodes) this.nodes.channels[channel].mute = muted;
  }

  setBpm(bpm: number) {
    Tone.getTransport().bpm.value = bpm;
  }

  /** Phát từ đầu. `onBar` gọi khi sang ô mới (để tô ô đang phát), `onEnd` khi hết bài lúc không lặp. */
  async play(options: { events: TrackEvent[]; bars: number; bpm: number; swing: number; loop: boolean; onBar: (bar: number) => void; onEnd: () => void }) {
    await Tone.start();
    const nodes = this.ensureNodes();
    this.stop();
    const transport = Tone.getTransport();
    transport.bpm.value = options.bpm;
    transport.swing = options.swing;
    transport.swingSubdivision = "8n";
    transport.position = 0;
    const end = beatToTransport(options.bars * BEATS_PER_BAR);
    transport.loop = options.loop;
    transport.loopStart = 0;
    transport.loopEnd = end;

    for (const event of options.events) {
      this.scheduled.push(transport.schedule((time) => {
        if (event.channel === "drums") {
          const velocity = event.velocity / 127;
          if (event.drum === "kick") nodes.kick.triggerAttackRelease("C1", "8n", time, velocity);
          else if (event.drum === "snare") nodes.snare.triggerAttackRelease("16n", time, velocity);
          else nodes.hat.triggerAttackRelease("C6", "32n", time, velocity);
          return;
        }
        // Ngân 92% độ dài để hai lần đánh liền nhau vẫn tách tiếng.
        const seconds = Tone.Time(`${event.beats}*4n`).toSeconds() * 0.92;
        if (event.channel === "chords") nodes.chords.triggerAttackRelease(event.midi.map(toFreq), seconds, time, 0.7);
        else nodes.bass.triggerAttackRelease(toFreq(event.midi[0]), seconds, time, 0.9);
      }, beatToTransport(event.beat)));
    }
    for (let bar = 0; bar < options.bars; bar += 1) {
      this.scheduled.push(transport.schedule((time) => {
        Tone.getDraw().schedule(() => options.onBar(bar), time);
      }, `${bar}:0:0`));
    }
    if (!options.loop) {
      this.scheduled.push(transport.schedule((time) => {
        Tone.getDraw().schedule(() => { this.stop(); options.onEnd(); }, time);
      }, end));
    }
    transport.start("+0.05");
  }

  stop() {
    const transport = Tone.getTransport();
    for (const id of this.scheduled) transport.clear(id);
    this.scheduled = [];
    transport.stop();
    transport.loop = false;
    transport.swing = 0;
    this.nodes?.chords.releaseAll();
    this.nodes?.bass.triggerRelease();
  }
}

export const backingTrack = new BackingTrackPlayer();
