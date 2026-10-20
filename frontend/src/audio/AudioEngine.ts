import * as Tone from "tone";

export type ProgressionEvent = {
  notes: string[];
  beats?: number;
};

class HarmonyAudioEngine {
  private piano: Tone.PolySynth | null = null;
  private click: Tone.Synth | null = null;
  private metronomeEvent: number | null = null;
  private progressionEvents: number[] = [];

  private getPiano() {
    if (!this.piano) {
      this.piano = new Tone.PolySynth().toDestination();
      this.piano.volume.value = -8;
      this.piano.set({
        envelope: { attack: 0.01, decay: 0.25, sustain: 0.25, release: 0.9 },
      });
    }
    return this.piano;
  }

  private getClick() {
    if (!this.click) {
      this.click = new Tone.Synth({
        envelope: { attack: 0.001, decay: 0.03, sustain: 0, release: 0.02 },
      }).toDestination();
      this.click.volume.value = -12;
    }
    return this.click;
  }

  async ensureStarted() {
    await Tone.start();
  }

  async playNote(note: string, duration: Tone.Unit.Time = "8n") {
    await this.ensureStarted();
    this.getPiano().triggerAttackRelease(note, duration);
  }

  async playChord(notes: string[], duration: Tone.Unit.Time = "2n") {
    if (!notes.length) return;
    await this.ensureStarted();
    const piano = this.getPiano();
    // Interactive root/quality changes can happen quickly; release the previous preview so
    // two different examples do not blur into one another.
    piano.releaseAll();
    piano.triggerAttackRelease(notes, duration);
  }

  async playProgression(events: ProgressionEvent[], bpm = 80) {
    if (!events.length) return;
    await this.ensureStarted();
    const transport = Tone.getTransport();

    // Progression and metronome share Tone's single Transport. Reset the timeline,
    // but keep a scheduled metronome event alive so it resumes with the progression.
    this.clearProgressionEvents();
    transport.stop();
    transport.position = 0;
    transport.bpm.value = bpm;

    let beatCursor = 0;
    const secondsPerBeat = 60 / bpm;
    for (const event of events) {
      const beats = event.beats ?? 4;
      const startSeconds = beatCursor * secondsPerBeat;
      const durationSeconds = Math.max(0.08, beats * secondsPerBeat * 0.92);
      const eventId = transport.scheduleOnce((time) => {
        this.getPiano().triggerAttackRelease(event.notes, durationSeconds, time);
      }, startSeconds);
      this.progressionEvents.push(eventId);
      beatCursor += beats;
    }

    const finishId = transport.scheduleOnce(() => {
      this.progressionEvents = [];
      if (this.metronomeEvent === null) transport.stop();
    }, beatCursor * secondsPerBeat);
    this.progressionEvents.push(finishId);
    transport.start();
  }

  private clearProgressionEvents() {
    const transport = Tone.getTransport();
    for (const eventId of this.progressionEvents) transport.clear(eventId);
    this.progressionEvents = [];
  }

  stopProgression() {
    const transport = Tone.getTransport();
    this.clearProgressionEvents();
    if (this.metronomeEvent === null) transport.stop();
  }

  async startMetronome(bpm = 80) {
    await this.ensureStarted();
    this.stopMetronome();
    const transport = Tone.getTransport();
    transport.bpm.value = bpm;
    let beat = 0;
    this.metronomeEvent = transport.scheduleRepeat((time) => {
      const note = beat % 4 === 0 ? "C7" : "C6";
      this.getClick().triggerAttackRelease(note, "32n", time);
      beat += 1;
    }, "4n");
    if (transport.state !== "started") transport.start();
  }

  stopMetronome() {
    const transport = Tone.getTransport();
    if (this.metronomeEvent !== null) {
      transport.clear(this.metronomeEvent);
      this.metronomeEvent = null;
    }
    if (!this.progressionEvents.length) transport.stop();
  }

  stopAll() {
    this.stopMetronome();
    this.clearProgressionEvents();
    Tone.getTransport().stop();
    this.piano?.releaseAll();
  }
}

export const audioEngine = new HarmonyAudioEngine();
