// Harmony Lab tối thiểu (phuc-music Bước 4, FR-17/18): ghép vòng hợp âm 4–8 ô, chọn nhạc nền, nghe lặp,
// xin gợi ý "lạ tai" theo luật (độ lạ 0–3) và đọc phân tích vì sao vòng nghe lạ.
// Nốt, tên hợp âm, gợi ý và phân tích đều do backend + Music Engine trả về; trang chỉ hiển thị và phát.
// Gợi ý không tự sửa dự án (nguyên tắc 5): người học bấm "Dùng hợp âm này" rồi tự lưu.
// Nhạc nền (02/11, ADR-012 đề xuất): backend phối khí theo phong cách + seed + năng lượng; trang phát bằng mẫu thu thật.
// Chế độ Bài hát (02/11 chiều, ADR-013 đề xuất): vòng A/B/C → Intro/Verse/Chorus... trên dòng thời gian kéo thả.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  api, type ApiError, type ComposeAnalysis, type ComposeCandidate, type ComposeOptions, type ComposeProjectSummary,
  type ComposeVoicing,
} from "../../api";
import { audioEngine } from "../../audio/AudioEngine";
import { bandPlayer } from "../../audio/band/player";
import {
  DEFAULT_MIX, GUITAR_TONE_LABELS, type Arrangement, type BandChannel, type BandMix, type FormSection, type GuitarTone, type ProgressionSlot, type SongForm,
  type SongLength,
} from "../../audio/band/types";
import { midiToScientific } from "../../audio/musicUtils";
import { LEVEL_BADGE, chordsOfKey, remapToKey, resizeBars, starterProgression } from "../../components/compose/harmonyLab";
import { SongTimeline } from "../../components/compose/SongTimeline";
import { ENDING_VI, LENGTH_VI, emptyForm, formForSave } from "../../components/compose/songForm";
import NotationStaff from "../../components/music/NotationStaff";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Badge, Card, CardTitle, ChipButton, Kicker, PageHeading, ToggleGroup } from "../../components/ui/Page";
import { PageLoader } from "../../components/ui/PageLoader";

const CHANNEL_LABELS: Record<BandChannel, string> = { chords: "Hợp âm", bass: "Bass", guitar: "Guitar", drums: "Trống", hook: "Hook", strings: "Dây (cello)" };
const ENERGY_LABELS: Record<number, string> = { 1: "Mộc", 2: "Vừa", 3: "Đầy" };
// Chế độ Bài hát: thanh năng lượng cũ thành "Năng lượng tổng", dời cả đường cong −1/0/+1 mức (ADR-013 đề xuất).
const TOTAL_ENERGY_LABELS: Record<number, string> = { 1: "Nhẹ hơn 1 mức", 2: "Theo khuôn", 3: "Mạnh hơn 1 mức" };
// Hạt giống mới cho "Tạo bản khác": số nguyên dương 31 bit (khớp kiểu cột seed ở backend).
const newSeed = () => 1 + Math.floor(Math.random() * 2_147_483_646);
const errorText = (e: unknown) => { const err = e as ApiError; return err.message ?? err.code ?? "Có lỗi, hãy thử lại."; };

type FullForm = SongForm & { sections: FormSection[] };
type Draft = {
  id: string | null; name: string; key: string; tempo: number; bars: number; style: string; chords: (string | null)[];
  seed: number; energy: number; mix: BandMix;
  /** "loop" = Vòng lặp như cũ (mặc định, QĐ 6A); "song" = dựng thành bài hát có cấu trúc. */
  mode: "loop" | "song";
  form: FullForm | null;
};

export default function CompositionLabPage() {
  const [options, setOptions] = useState<ComposeOptions | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [dirty, setDirty] = useState(false);
  const [selected, setSelected] = useState(0);
  const [slot, setSlot] = useState<ProgressionSlot>("A");
  const [voicings, setVoicings] = useState<Record<string, ComposeVoicing>>({});
  const [analysis, setAnalysis] = useState<ComposeAnalysis | null>(null);
  const [playing, setPlaying] = useState(false);
  const [currentBar, setCurrentBar] = useState<number | null>(null);
  const [loop, setLoop] = useState(true);
  const [loading, setLoading] = useState<number | null>(null);
  const [colors, setColors] = useState<(string | null)[]>([]);
  const [fallback, setFallback] = useState(false);
  const [vinyl, setVinyl] = useState(true);
  const [guitarTone, setGuitarTone] = useState<GuitarTone>("auto");
  const [projects, setProjects] = useState<ComposeProjectSummary[]>([]);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState<{ tone: "success" | "danger" | "info"; text: string } | null>(null);
  // Chế độ Bài hát
  const [song, setSong] = useState<Arrangement | null>(null);
  const [songError, setSongError] = useState<string | null>(null);
  const [section, setSection] = useState(0);
  const [loopSection, setLoopSection] = useState(false);
  const [showNotes, setShowNotes] = useState(true);

  useEffect(() => {
    Promise.all([api.composeOptions(), api.listProjects()])
      .then(([opts, list]) => {
        setOptions(opts);
        setProjects(list);
        const style = opts.styles[0];
        setDraft({ id: null, name: "Vòng hợp âm đầu tiên", key: "C", tempo: style.default_bpm, bars: 4, style: style.id,
          chords: starterProgression(opts, "C", 4), seed: 1, energy: 2, mix: DEFAULT_MIX, mode: "loop", form: null });
      })
      .catch((e) => setLoadError(errorText(e)));
    return () => bandPlayer.stop();
  }, []);

  const update = (patch: Partial<Draft>) => { setDraft((d) => (d ? { ...d, ...patch } : d)); setDirty(true); };

  // Vòng đang sửa trên lưới: A là lưới của dự án (chord_events); B/C nằm trong form (QĐ 1A).
  const gridChords: (string | null)[] | null = draft
    ? slot === "A" || draft.mode === "loop" ? draft.chords : draft.form?.progressions[slot] ?? null
    : null;
  const setGridChords = (chords: (string | null)[]) => {
    if (!draft) return;
    if (slot === "A" || draft.mode === "loop" || !draft.form) { update({ chords, bars: chords.length }); return; }
    update({ form: { ...draft.form, progressions: { ...draft.form.progressions, [slot]: chords } } });
  };

  // Lấy cao độ (Music Engine) cho các hợp âm chưa có trong bộ nhớ tạm.
  const ensureVoicings = useCallback(async (symbols: string[]) => {
    const missing = [...new Set(symbols)].filter((s) => !voicings[s]);
    if (!missing.length) return voicings;
    const fetched = await api.composeVoicings(missing);
    const merged = { ...voicings, ...fetched };
    setVoicings(merged);
    return merged;
  }, [voicings]);

  const chordKey = draft && gridChords ? `${draft.key}|${gridChords.join(",")}` : "";
  useEffect(() => {
    if (!draft || !gridChords) return;
    const symbols = gridChords.filter((c): c is string => Boolean(c));
    void ensureVoicings(symbols).catch((e) => setNotice({ tone: "danger", text: errorText(e) }));
    const timer = window.setTimeout(() => {
      api.composeAnalyze(draft.key, gridChords).then(setAnalysis).catch(() => setAnalysis(null));
    }, 250);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chordKey]);

  const style = options?.styles.find((s) => s.id === draft?.style) ?? options?.styles[0];

  // Bản bài hát dựng ở backend mỗi khi form/vòng/phong cách đổi, để dòng thời gian, ghi chú và thời lượng luôn đúng.
  const songBody = draft?.mode === "song" && draft.form
    ? { key: draft.key, style: draft.style, seed: draft.seed, energy: draft.energy, bpm: draft.tempo,
        form: formForSave(draft.form, draft.chords) as FullForm }
    : null;
  const songKey = songBody ? JSON.stringify({ ...songBody, bpm: 0 }) : "";
  useEffect(() => {
    if (!songBody) { setSong(null); return; }
    const timer = window.setTimeout(() => {
      api.composeSong(songBody).then((s) => { setSong(s); setSongError(null); })
        .catch((e) => setSongError(errorText(e)));
    }, 200);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [songKey]);

  /** Dựng form mặc định của phong cách ở độ dài đã chọn; vòng A/B/C, hook, lên giọng giữ nguyên (mục F). */
  const buildForm = async (length: SongLength, base?: SongForm | null) => {
    if (!draft) return;
    const form: SongForm = { ...(base ?? emptyForm(draft.chords)), length };
    delete form.sections;
    try {
      const res = await api.composeSong({ key: draft.key, style: draft.style, seed: draft.seed, energy: draft.energy,
        bpm: draft.tempo, form: formForSave(form, draft.chords) });
      // Backend cũ (trước chế độ Bài hát) trả về bản phối không có `form`: báo rõ thay vì lặng lẽ ở lại Vòng lặp.
      if (!res.form) {
        setNotice({ tone: "danger", text: "Máy chủ đang chạy bản cũ, chưa có chế độ Bài hát. Hãy tắt rồi chạy lại backend (uvicorn) từ nhánh mới nhất." });
        return;
      }
      update({ mode: "song", form: res.form });
      setSong(res);
      setSection(0);
    } catch (e) { setNotice({ tone: "danger", text: `Chưa dựng được bài: ${errorText(e)}` }); }
  };

  const startPlayback = useCallback(async (fromSection?: number) => {
    if (!draft || !style) return;
    try {
      audioEngine.stopAll();
      // Bản phối (nốt, nhịp, lực) do backend + Music Engine dựng; trang chỉ lệch phách người, phát và trộn.
      if (draft.mode === "song" && draft.form) {
        const arrangement = await api.composeSong({ key: draft.key, style: draft.style, seed: draft.seed, energy: draft.energy,
          bpm: draft.tempo, form: formForSave(draft.form, draft.chords) });
        setSong(arrangement);
        const idx = fromSection ?? (loopSection ? section : 0);
        const sec = arrangement.sections?.[idx];
        setLoading(0);
        await bandPlayer.play({
          arrangement, bpm: draft.tempo, seed: draft.seed, loop: false, mix: draft.mix, guitarTone, vinyl,
          startBeat: sec?.start_beat ?? 0, loopRange: loopSection && sec ? { start: sec.start_beat, end: sec.end_beat } : null,
          onProgress: ({ loaded, total }) => setLoading(total ? Math.round((100 * loaded) / total) : 100),
          onBar: setCurrentBar, onEnd: () => { setPlaying(false); setCurrentBar(null); },
        });
      } else {
        const arrangement = await api.composeArrangement({ key: draft.key, style: draft.style, chords: draft.chords,
          seed: draft.seed, energy: draft.energy, bpm: draft.tempo });
        setColors(arrangement.colors.map((c) => c.played));
        setLoading(0);
        await bandPlayer.play({
          arrangement, bpm: draft.tempo, seed: draft.seed, loop, mix: draft.mix, guitarTone, vinyl,
          onProgress: ({ loaded, total }) => setLoading(total ? Math.round((100 * loaded) / total) : 100),
          onBar: setCurrentBar, onEnd: () => { setPlaying(false); setCurrentBar(null); },
        });
      }
      setFallback(bandPlayer.mode === "synth");
      setPlaying(true);
    } catch (e) {
      setNotice({ tone: "danger", text: `Chưa phát được: ${errorText(e)}` });
    } finally { setLoading(null); }
  }, [draft, style, loop, vinyl, loopSection, section, guitarTone]);

  const stopPlayback = () => { bandPlayer.stop(); setPlaying(false); setCurrentBar(null); };

  // Đang phát mà đổi hợp âm, phong cách, bản phối (seed), năng lượng, form hoặc chế độ lặp thì phát lại với bản mới.
  const restartKey = draft ? `${draft.key}|${draft.chords.join(",")}|${draft.style}|${draft.bars}|${draft.seed}|${draft.energy}|${loop}|${draft.mode}|${songKey}|${loopSection ? section : -1}|${draft.mix.strings?.muted ?? true}` : "";
  const playingRef = useRef(playing);
  playingRef.current = playing;
  useEffect(() => { if (playingRef.current) void startPlayback(loopSection ? section : undefined); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [restartKey]);
  useEffect(() => { if (draft) bandPlayer.setBpm(draft.tempo); }, [draft?.tempo]);
  useEffect(() => { if (draft) bandPlayer.setMix(draft.mix); }, [draft?.mix]);
  useEffect(() => { bandPlayer.setVinyl(vinyl && playingRef.current); }, [vinyl]);
  // Đổi âm sắc guitar khi đang nghe: chỉ đổi tham số méo/lọc, không phát lại.
  useEffect(() => { bandPlayer.setGuitarTone(guitarTone); }, [guitarTone]);

  const setChannel = (channel: BandChannel, patch: Partial<BandMix[BandChannel]>) => {
    if (!draft) return;
    update({ mix: { ...draft.mix, [channel]: { ...draft.mix[channel], ...patch } } });
  };

  const save = async () => {
    if (!draft) return;
    setSaving(true);
    setNotice(null);
    const body = { name: draft.name.trim() || "Vòng chưa đặt tên", key: draft.key, tempo_bpm: draft.tempo, bars: draft.chords.length,
      style: draft.style, chords: draft.chords, seed: draft.seed, energy: draft.energy, mix: draft.mix,
      form: draft.mode === "song" && draft.form ? formForSave(draft.form, draft.chords) : null };
    try {
      const saved = draft.id ? await api.updateProject(draft.id, body) : await api.createProject(body);
      setDraft((d) => (d ? { ...d, id: saved.id, name: saved.name } : d));
      setDirty(false);
      setProjects(await api.listProjects());
      setNotice({ tone: "success", text: `Đã lưu "${saved.name}".` });
    } catch (e) {
      setNotice({ tone: "danger", text: `Chưa lưu được: ${errorText(e)}` });
    } finally { setSaving(false); }
  };

  const openProject = async (id: string) => {
    try {
      stopPlayback();
      const p = await api.getProject(id);
      // Dự án cũ (trước 02/11) chưa có seed/mix: dùng seed 1, năng lượng 2, mix mặc định (QĐ 13A).
      // Dự án không có form (mọi dự án trước chế độ Bài hát) mở ở chế độ Vòng lặp như cũ.
      const form = (p.form ?? null) as FullForm | null;
      setDraft({ id: p.id, name: p.name, key: p.key, tempo: p.tempo_bpm, bars: p.bars, style: p.style, chords: p.chords,
        seed: p.seed ?? 1, energy: p.energy ?? 2, mix: { ...DEFAULT_MIX, ...(p.mix ?? {}) },
        mode: form ? "song" : "loop", form });
      setSelected(0);
      setSlot("A");
      setSection(0);
      setDirty(false);
      setNotice({ tone: "info", text: p.arrangement_outdated
        ? `Đã mở "${p.name}". Bộ phối khí đã được nâng cấp nên nhạc nền có thể nghe khác lúc bạn lưu.`
        : `Đã mở "${p.name}".` });
    } catch (e) { setNotice({ tone: "danger", text: errorText(e) }); }
  };

  const removeProject = async (id: string, name: string) => {
    try {
      await api.deleteProject(id);
      setProjects(await api.listProjects());
      if (draft?.id === id) setDraft((d) => (d ? { ...d, id: null } : d));
      setNotice({ tone: "info", text: `Đã xóa "${name}".` });
    } catch (e) { setNotice({ tone: "danger", text: errorText(e) }); }
  };

  const newProject = () => {
    if (!options || !style) return;
    stopPlayback();
    setDraft({ id: null, name: "Vòng hợp âm mới", key: draft?.key ?? "C", tempo: style.default_bpm, bars: 4, style: style.id,
      chords: starterProgression(options, draft?.key ?? "C", 4), seed: 1, energy: 2, mix: DEFAULT_MIX, mode: "loop", form: null });
    setSelected(0);
    setSlot("A");
    setDirty(false);
  };

  if (loadError) return <section><PageHeading eyebrow="Sáng tác" title="Harmony Lab" /><Alert tone="danger">Chưa tải được xưởng sáng tác: {loadError}</Alert></section>;
  if (!options || !draft || !style || !gridChords && slot === "A") return <PageLoader />;

  const isSongMode = draft.mode === "song" && draft.form !== null;
  const form = draft.form;
  const keyChords = chordsOfKey(options, draft.key);
  const grid = gridChords ?? [];
  const selectedChord = grid[selected] ?? null;
  const selectedVoicing = selectedChord ? voicings[selectedChord] : undefined;
  const barInfo = (i: number) => analysis?.bars[i];
  const songSections = song?.sections ?? [];
  const playingSection = isSongMode && currentBar !== null ? songSections.find((s) => currentBar * 4 >= s.start_beat && currentBar * 4 < s.end_beat) ?? null : null;
  // Ô đang phát trên lưới: ở chế độ Bài hát chỉ sáng khi đoạn đang phát dùng đúng vòng đang sửa.
  const gridPlayingBar = currentBar === null ? null : !isSongMode ? currentBar
    : playingSection && playingSection.progression === slot ? (currentBar - playingSection.start_beat / 4) % Math.max(1, grid.length) : null;
  const emptySlots = form ? (["B", "C"] as ProgressionSlot[]).filter((p) => !form.progressions[p]?.some(Boolean)) : [];
  const cycles: Record<ProgressionSlot, number> = { A: draft.chords.length, B: form?.progressions.B?.length ?? 0, C: form?.progressions.C?.length ?? 0 };
  const songColors = isSongMode && song?.bars ? (() => {
    const s = songSections.find((x) => x.progression === slot);
    return s ? song.bars!.slice(s.start_beat / 4, s.start_beat / 4 + grid.length).map((b) => b.played) : [];
  })() : colors;
  const channels = (Object.keys(CHANNEL_LABELS) as BandChannel[]).filter((c) => c !== "hook" || isSongMode);

  return <section className="pb-24 sm:pb-0">
    <PageHeading eyebrow="Sáng tác" title="Harmony Lab">
      Ghép một vòng hợp âm, chọn nhạc nền rồi bấm Phát. Muốn nghe như một bài hát có Intro, Verse, Chorus, bấm "Dựng thành bài hát".
    </PageHeading>

    {notice && <div className="mb-4"><Alert tone={notice.tone}>{notice.text}</Alert></div>}

    {/* Thanh điều khiển: giọng, tốc độ, phát, lặp (tài liệu 04 Bảng 25). */}
    <Card className="mb-4 grid gap-4">
      <div className="grid gap-4 md:grid-cols-[1fr_auto_auto] md:items-end">
        <label className="grid gap-1.5 text-sm font-medium text-ink">Tên {isSongMode ? "bài" : "vòng hợp âm"}
          <input className="min-h-11 rounded-lg border border-line bg-surface px-3 text-base text-ink" value={draft.name} maxLength={80}
            onChange={(e) => update({ name: e.target.value })} />
        </label>
        <label className="grid gap-1.5 text-sm font-medium text-ink">Giọng (trưởng)
          <select className="min-h-11 rounded-lg border border-line bg-surface px-3 text-base text-ink" value={draft.key}
            onChange={(e) => {
              const to = e.target.value;
              const remap = (p: (string | null)[] | null) => (p ? remapToKey(p, options, draft.key, to) : p);
              update({ key: to, chords: remapToKey(draft.chords, options, draft.key, to),
                form: draft.form ? { ...draft.form, progressions: { A: draft.form.progressions.A, B: remap(draft.form.progressions.B), C: remap(draft.form.progressions.C) } } : null });
            }}>
            {options.keys.map((k) => <option key={k.key} value={k.key}>{k.key} trưởng</option>)}
          </select>
        </label>
        <label className="grid gap-1.5 text-sm font-medium text-ink">
          <span>Tốc độ: <b className="font-mono">{draft.tempo}</b> BPM</span>
          <input type="range" min={options.tempo.min} max={options.tempo.max} step={1} value={draft.tempo}
            aria-valuetext={`${draft.tempo} phách mỗi phút`} className="min-h-11 w-full accent-primary md:w-52"
            onChange={(e) => update({ tempo: Number(e.target.value) })} />
        </label>
      </div>
      <div><p className="mb-1.5 text-sm font-medium text-ink">Chế độ</p>
        <ToggleGroup label="Chế độ nhạc nền" value={isSongMode ? "song" : "loop"}
          options={[{ value: "loop", label: "↻ Vòng lặp" }, { value: "song", label: "♫ Bài hát" }]}
          onChange={(v) => {
            stopPlayback();
            if (v === "loop") { update({ mode: "loop" }); setSlot("A"); return; }
            if (draft.form) update({ mode: "song" }); else void buildForm("medium");
          }} />
        <p className="mt-1 text-xs text-muted">{isSongMode
          ? "Bài hát: vòng hợp âm được dựng thành Intro, Verse, Chorus... có cao trào và chuyển đoạn, mỗi đoạn có ghi chú vì sao."
          : "Vòng lặp: nghe nhanh 4 vòng của lưới hợp âm, hợp để thử từng hợp âm."}</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div><p className="mb-1.5 text-sm font-medium text-ink">Số ô của vòng {isSongMode ? slot : ""}</p>
          <ToggleGroup label="Số ô nhịp" value={String(grid.length || 4)}
            options={[4, 5, 6, 7, 8].map((n) => ({ value: String(n), label: n }))}
            onChange={(v) => { const bars = Number(v); setGridChords(resizeBars(grid, bars)); setSelected((s) => Math.min(s, bars - 1)); }} />
        </div>
        <div><p className="mb-1.5 text-sm font-medium text-ink">{isSongMode ? "Năng lượng tổng" : "Năng lượng"}</p>
          <ToggleGroup label={isSongMode ? "Năng lượng tổng của bài" : "Năng lượng bản phối"} value={String(draft.energy)}
            options={[1, 2, 3].map((n) => ({ value: String(n), label: isSongMode ? TOTAL_ENERGY_LABELS[n] : `${n} · ${ENERGY_LABELS[n]}` }))}
            onChange={(v) => update({ energy: Number(v) })} />
          <p className="mt-1 text-xs text-muted">{isSongMode ? "Dời cả đường cong năng lượng của bài lên hoặc xuống một mức (giữ trong 1–5)."
            : "1 mộc: ít nhạc cụ, nốt dài · 3 đầy: thêm guitar, hat mở, crash."}</p>
        </div>
      </div>
      <div><p className="mb-1.5 text-sm font-medium text-ink">Kênh và âm lượng</p>
        <div role="group" aria-label="Bật, tắt và chỉnh âm lượng từng kênh" className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          {channels.map((c) => {
            const ch = draft.mix[c] ?? DEFAULT_MIX[c];
            return <div key={c} className="flex items-center gap-2 rounded-xl border border-line bg-surface p-1.5 pr-3">
              <ChipButton pressed={!ch.muted} onClick={() => setChannel(c, { muted: !ch.muted })}>
                <span aria-hidden="true">{ch.muted ? "🔇 " : "🔊 "}</span>{CHANNEL_LABELS[c]}</ChipButton>
              <input type="range" min={0} max={1} step={0.05} value={ch.volume} disabled={ch.muted}
                aria-label={`Âm lượng ${CHANNEL_LABELS[c]}`} aria-valuetext={`${Math.round(ch.volume * 100)}%`}
                className="min-h-11 w-full min-w-16 accent-primary" onChange={(e) => setChannel(c, { volume: Number(e.target.value) })} />
            </div>;
          })}
          <div className="flex flex-wrap items-center gap-2 sm:col-span-2 lg:col-span-3 xl:col-span-6" role="group" aria-label="Âm sắc guitar">
            <span className="text-sm text-muted">Âm sắc guitar:</span>
            {(Object.keys(GUITAR_TONE_LABELS) as GuitarTone[]).map((t) => (
              <ChipButton key={t} pressed={guitarTone === t} onClick={() => setGuitarTone(t)}>{GUITAR_TONE_LABELS[t]}</ChipButton>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {!isSongMode && <ChipButton pressed={loop} onClick={() => setLoop((v) => !v)}><span aria-hidden="true">↻ </span>Lặp lại</ChipButton>}
            {style.id === "lofi" && <ChipButton pressed={vinyl} onClick={() => setVinyl((v) => !v)}>Tiếng đĩa than</ChipButton>}
          </div>
        </div>
      </div>
      {/* Nút chính: dính đáy màn hình điện thoại để luôn thấy, nằm trong thẻ trên màn rộng. */}
      <div className="fixed inset-x-0 bottom-0 z-20 flex gap-3 border-t border-line bg-bg/95 p-3 backdrop-blur sm:static sm:border-0 sm:bg-transparent sm:p-0">
        {playing
          ? <Button size="lg" className="flex-1 sm:flex-none" onClick={stopPlayback}><span aria-hidden="true">■</span> Dừng</Button>
          : <Button size="lg" className="flex-1 sm:flex-none" onClick={() => void startPlayback()}><span aria-hidden="true">▶</span> {isSongMode ? (loopSection ? "Lặp đoạn" : "Phát cả bài") : "Phát"}</Button>}
        <Button size="lg" variant="secondary" className="flex-1 sm:flex-none" onClick={() => update({ seed: newSeed() })}
          aria-label={isSongMode ? "Tạo bản phối khác cho cả bài" : "Tạo bản phối khác cho cùng vòng hợp âm"}>
          <span aria-hidden="true">🎲</span> Tạo bản khác
        </Button>
        <Button size="lg" variant="secondary" className="flex-1 sm:flex-none" loading={saving} onClick={() => void save()}>
          {draft.id ? "Lưu thay đổi" : isSongMode ? "Lưu bài này" : "Lưu vòng này"}
        </Button>
        <span className="hidden self-center text-sm text-muted sm:inline" aria-live="polite">{dirty ? "Có thay đổi chưa lưu" : draft.id ? "Đã lưu" : ""}</span>
      </div>
      {loading !== null && <div role="status" aria-live="polite" className="grid gap-1">
        <span className="text-sm text-ink">Đang tải nhạc cụ… {loading}%</span>
        <progress className="h-2 w-full accent-primary" max={100} value={loading} />
      </div>}
      {fallback && <Alert tone="info">Chưa tải được mẫu âm thanh thật (mạng hoặc trình duyệt), đang phát bằng âm tổng hợp.</Alert>}
    </Card>

    {isSongMode && form && <Card className="mb-4 grid gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div><Kicker>Cấu trúc bài</Kicker><CardTitle className="mt-1">Dòng thời gian các đoạn</CardTitle></div>
        <ToggleGroup label="Độ dài bài" value={form.length}
          options={(["short", "medium", "full"] as SongLength[]).map((l) => ({ value: l, label: LENGTH_VI[l] }))}
          onChange={(l) => void buildForm(l, form)} />
      </div>
      {songError && <Alert tone="danger">Chưa dựng được bài: {songError}</Alert>}
      <SongTimeline arrangement={song} sections={form.sections} bpm={draft.tempo} currentBar={currentBar}
        selected={Math.min(section, form.sections.length - 1)} onSelect={(i) => { setSection(i); const p = form.sections[i]?.progression; if (p) setSlot(p); }}
        onChange={(sections) => update({ form: { ...form, sections } })} cycles={cycles} emptySlots={emptySlots}
        onPlaySection={(i) => { setSection(i); void startPlayback(i); }} loopSection={loopSection}
        onToggleLoopSection={() => setLoopSection((v) => !v)} playing={playing} />
      <div className="flex flex-wrap items-center gap-2">
        <ChipButton pressed={form.hook} onClick={() => update({ form: { ...form, hook: !form.hook } })}>Hook nhạc cụ</ChipButton>
        <ChipButton pressed={form.modulate.enabled} onClick={() => update({ form: { ...form, modulate: { ...form.modulate, enabled: !form.modulate.enabled } } })}>
          Lên giọng ở Chorus cuối</ChipButton>
        {form.modulate.enabled && <ToggleGroup label="Lên bao nhiêu" value={String(form.modulate.semitones)}
          options={[{ value: "1", label: "Nửa cung" }, { value: "2", label: "Một cung" }]}
          onChange={(v) => update({ form: { ...form, modulate: { ...form.modulate, semitones: Number(v) as 1 | 2 } } })} />}
        <label className="flex items-center gap-2 text-sm font-medium text-ink">Kết bài
          <select className="min-h-11 rounded-lg border border-line bg-surface px-3 text-base text-ink" value={form.ending}
            onChange={(e) => update({ form: { ...form, ending: e.target.value as SongForm["ending"] } })}>
            {Object.entries(ENDING_VI).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </label>
      </div>
      {playingSection && <div className="flex items-start justify-between gap-3 rounded-xl border border-line bg-primary-soft p-3" aria-live="polite">
        {showNotes ? <p className="text-sm text-ink"><b>Đang phát: {playingSection.label}.</b> {playingSection.note_vi}</p>
          : <p className="text-sm text-ink"><b>Đang phát: {playingSection.label}</b></p>}
        <Button variant="ghost" onClick={() => setShowNotes((v) => !v)}>{showNotes ? "Ẩn ghi chú" : "Hiện ghi chú"}</Button>
      </div>}
    </Card>}

    {/* Lưới hợp âm ở giữa. Ở chế độ Bài hát, lưới là vòng A/B/C đang chọn. */}
    <Card className="mb-4">
      <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
        <div><Kicker>Lưới hợp âm{isSongMode ? ` · vòng ${slot}` : ""}</Kicker><CardTitle className="mt-1">Chọn một ô để đổi hợp âm</CardTitle></div>
        <div className="flex flex-wrap items-center gap-2">
          {isSongMode && <ToggleGroup label="Vòng hợp âm đang sửa" value={slot}
            options={(["A", "B", "C"] as ProgressionSlot[]).map((p) => ({ value: p, label: `Vòng ${p}${p === "A" ? " · Verse" : p === "B" ? " · Chorus" : " · Bridge"}` }))}
            onChange={(p) => { setSlot(p); setSelected(0); }} />}
          {analysis && gridChords && <Badge tone={LEVEL_BADGE[analysis.level]}>Độ lạ {analysis.level}/3 · {analysis.level_label}</Badge>}
        </div>
      </div>
      {isSongMode && !gridChords && form && <EmptySlot slot={slot} suggestion={song?.suggestions?.[slot]}
        onUse={(chords) => update({ form: { ...form, progressions: { ...form.progressions, [slot]: chords } } })}
        onBlank={() => update({ form: { ...form, progressions: { ...form.progressions, [slot]: [null, null, null, null] } } })}
        ensureVoicings={ensureVoicings} />}
      {gridChords && <ol className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {grid.map((chord, i) => {
          const info = barInfo(i);
          const isPlaying = gridPlayingBar === i;
          return <li key={i}>
            <button type="button" aria-pressed={selected === i} onClick={() => setSelected(i)}
              aria-label={`Ô ${i + 1}: ${chord ?? "trống"}${info?.label ? `, ${info.label}` : ""}${info?.level != null ? `, độ lạ ${info.level}` : ""}${isPlaying ? ", đang phát" : ""}`}
              className={`grid min-h-24 w-full content-between rounded-xl border-2 p-3 text-left transition-colors ${selected === i ? "border-primary bg-primary-soft" : "border-line bg-surface hover:border-primary"} ${isPlaying ? "shadow-[inset_0_-4px_0_var(--color-brass)]" : ""}`}>
              <span className="flex items-center justify-between text-xs font-semibold text-muted"><span>Ô {i + 1}</span>{isPlaying && <span className="text-ink">▶ đang phát</span>}</span>
              <span className="font-mono text-2xl font-semibold text-ink">{chord ?? "—"}</span>
              <span className="text-xs text-muted">{info?.label ?? (chord ? "…" : "chưa có hợp âm")}{info?.level ? ` · lạ ${info.level}` : ""}</span>
              {chord && songColors[i] && <span className="text-xs text-muted">Bản phối tô thêm màu: <b className="font-mono text-ink">{songColors[i]}</b></span>}
            </button>
          </li>;
        })}
      </ol>}
      {isSongMode && slot !== "A" && gridChords && <Button variant="ghost" className="mt-3"
        onClick={() => form && update({ form: { ...form, progressions: { ...form.progressions, [slot]: null } } })}>
        Xóa vòng {slot} (các đoạn dùng vòng {slot} sẽ tạm dùng vòng A)</Button>}
    </Card>

    {gridChords && <div className="mb-4 grid gap-4 lg:grid-cols-[1.1fr_1fr]">
      <BarEditor index={selected} chord={selectedChord} voicing={selectedVoicing} keyName={draft.key} keyChords={keyChords}
        chords={grid} levels={options.levels}
        onChange={(symbol) => { const chords = [...grid]; chords[selected] = symbol; setGridChords(chords); }}
        ensureVoicings={ensureVoicings} />
      <AnalysisCard analysis={analysis} />
    </div>}

    {/* Mẫu nền ở dưới (tài liệu 04 Bảng 25). */}
    <Card className="mb-4">
      <Kicker>Nhạc nền</Kicker><CardTitle className="mt-1">Chọn phong cách ban nhạc</CardTitle>
      <p className="mt-1 text-sm text-muted">Piano, bass, guitar và trống thu thật (mẫu CC0/CC BY, xem ghi công). Mỗi lần bấm "Tạo bản khác" ra một cách chơi mới trong cùng phong cách.</p>
      <div role="group" aria-label="Phong cách nhạc nền" className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {options.styles.map((s) => <button key={s.id} type="button" aria-pressed={draft.style === s.id}
          onClick={() => {
            update({ style: s.id, tempo: s.default_bpm }); setColors([]);
            // Bài hát: đổi phong cách thì lấy khuôn của phong cách mới ở cùng độ dài (vòng A/B/C giữ nguyên).
            if (isSongMode && form) void (async () => {
              try {
                const res = await api.composeSong({ key: draft.key, style: s.id, seed: draft.seed, energy: draft.energy, bpm: s.default_bpm,
                  form: formForSave({ ...form, sections: undefined }, draft.chords) });
                update({ style: s.id, tempo: s.default_bpm, form: res.form! }); setSection(0);
              } catch (e) { setNotice({ tone: "danger", text: errorText(e) }); }
            })();
          }}
          className={`grid min-h-11 gap-1 rounded-xl border-2 p-3 text-left ${draft.style === s.id ? "border-primary bg-primary-soft" : "border-line bg-surface hover:border-primary"}`}>
          <b className="text-ink">{s.label}</b><span className="text-sm text-muted">{s.description}</span>
          <span className="font-mono text-xs text-muted">{s.default_bpm} BPM{s.swing ? " · swing" : ""}</span>
        </button>)}
      </div>
    </Card>

    <Card>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div><Kicker>Đã lưu</Kicker><CardTitle className="mt-1">Vòng hợp âm và bài của bạn</CardTitle></div>
        <Button variant="secondary" onClick={newProject}>+ Vòng mới</Button>
      </div>
      {projects.length === 0
        ? <p className="mt-2 text-muted">Chưa có vòng nào được lưu. Bấm "Lưu vòng này" để giữ lại.</p>
        : <ul className="mt-3 divide-y divide-line">{projects.map((p) => <li key={p.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
            <div><b className="text-ink">{p.name}</b><small className="block text-muted">{p.mode === "song" ? "Bài hát · " : ""}{p.key} trưởng · {p.bars} ô · {options.styles.find((s) => s.id === p.style)?.label ?? p.style}</small></div>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => void openProject(p.id)} aria-label={`Mở ${p.name}`}>Mở</Button>
              <Button variant="ghost" onClick={() => void removeProject(p.id, p.name)} aria-label={`Xóa ${p.name}`}>Xóa</Button>
            </div>
          </li>)}</ul>}
    </Card>
  </section>;
}

/** Vòng B/C còn trống (QĐ 3A): đoạn tạm dùng vòng A; gợi ý theo luật chỉ được dùng khi người học bấm chấp nhận. */
function EmptySlot({ slot, suggestion, onUse, onBlank, ensureVoicings }: {
  slot: ProgressionSlot; suggestion?: { chords: string[]; numerals: string[]; reason_vi: string };
  onUse: (chords: string[]) => void; onBlank: () => void;
  ensureVoicings: (symbols: string[]) => Promise<Record<string, ComposeVoicing>>;
}) {
  const listen = async () => {
    if (!suggestion) return;
    const map = await ensureVoicings(suggestion.chords);
    suggestion.chords.forEach((c, i) => window.setTimeout(() => playVoicing(map[c]), i * 900));
  };
  return <div className="grid gap-3 rounded-xl border border-dashed border-line bg-bg p-4">
    <p className="text-ink">Vòng {slot} đang trống, nên các đoạn dùng vòng {slot} tạm chơi vòng A. Nhiều bài pop dùng một vòng cho cả bài; tương phản lúc đó đến từ phối khí.</p>
    {suggestion && <div className="grid gap-2">
      <p className="text-sm text-ink">Gợi ý theo luật: <b className="font-mono">{suggestion.chords.join(" – ")}</b> <span className="text-muted">({suggestion.numerals.join(" – ")})</span></p>
      <p className="text-sm text-muted">{suggestion.reason_vi} Chưa dùng AI.</p>
    </div>}
    <div className="flex flex-wrap gap-2">
      {suggestion && <Button variant="secondary" onClick={() => void listen()}><span aria-hidden="true">▶</span> Nghe thử</Button>}
      {suggestion && <Button onClick={() => onUse(suggestion.chords)}>Dùng vòng này</Button>}
      <Button variant="ghost" onClick={onBlank}>Tự nhập vòng {slot}</Button>
    </div>
  </div>;
}

function playVoicing(voicing: ComposeVoicing) {
  // Phát theo số MIDI do Engine trả về (Bbb4 phát đúng cao độ A4), tên trên khuông vẫn giữ Bbb.
  void audioEngine.playChord(voicing.pitches.map((p) => midiToScientific(p.midi)), "2n");
}

function BarEditor({ index, chord, voicing, keyName, keyChords, chords, levels, onChange, ensureVoicings }: {
  index: number; chord: string | null; voicing?: ComposeVoicing; keyName: string;
  keyChords: { symbol: string; numeral: string }[]; chords: (string | null)[]; levels: { level: number; label: string }[];
  onChange: (symbol: string | null) => void; ensureVoicings: (symbols: string[]) => Promise<Record<string, ComposeVoicing>>;
}) {
  const [maxLevel, setMaxLevel] = useState("3");
  const [candidates, setCandidates] = useState<ComposeCandidate[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const contextKey = `${index}|${keyName}|${chords.join(",")}`;
  useEffect(() => { setCandidates(null); setError(null); }, [contextKey]);

  const ask = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.composeSuggest(keyName, chords, index, Number(maxLevel));
      setCandidates(res.candidates);
    } catch (e) { setError(errorText(e)); } finally { setLoading(false); }
  };
  const listen = async (symbol: string) => {
    try { const map = await ensureVoicings([symbol]); playVoicing(map[symbol]); } catch (e) { setError(errorText(e)); }
  };
  const groups = useMemo(() => {
    const byLevel = new Map<number, ComposeCandidate[]>();
    for (const c of candidates ?? []) byLevel.set(c.level, [...(byLevel.get(c.level) ?? []), c]);
    return [...byLevel.entries()].sort((a, b) => a[0] - b[0]);
  }, [candidates]);

  return <Card className="grid content-start gap-4">
    <div><Kicker>Ô {index + 1}</Kicker><CardTitle className="mt-1">{chord ? `Đang chọn ${chord}` : "Ô trống"}</CardTitle></div>

    <div>
      <p className="mb-1.5 text-sm font-medium text-ink">Hợp âm trong giọng {keyName} trưởng</p>
      <div role="group" aria-label={`Hợp âm trong giọng ${keyName} trưởng`} className="flex flex-wrap gap-2">
        {keyChords.map((c) => <ChipButton key={c.symbol} pressed={chord === c.symbol} onClick={() => onChange(c.symbol)}
          aria-label={`${c.symbol}, bậc ${c.numeral}`}><span className="font-mono">{c.symbol}</span> <span className="text-xs opacity-80">{c.numeral}</span></ChipButton>)}
        <ChipButton pressed={false} onClick={() => onChange(null)}>Xóa ô</ChipButton>
      </div>
    </div>

    {voicing && chord && <div>
      <NotationStaff groups={[{ label: `${chord}: ${voicing.notes.join(" – ")}`, notes: voicing.pitches.map((p) => p.name) }]} />
      <Button variant="secondary" className="mt-2" onClick={() => playVoicing(voicing)}><span aria-hidden="true">▶</span> Nghe {chord}</Button>
    </div>}

    {chord && <div className="grid gap-3 border-t border-line pt-4">
      <div><p className="mb-1.5 text-sm font-medium text-ink">Muốn lạ tai tới mức nào?</p>
        <ToggleGroup label="Độ lạ tối đa" value={maxLevel} onChange={setMaxLevel}
          options={levels.map((lv) => ({ value: String(lv.level), label: `${lv.level} · ${lv.label}` }))} />
      </div>
      <Button className="justify-self-start" loading={loading} onClick={() => void ask()}>Gợi ý hợp âm thay cho ô {index + 1}</Button>
      {error && <Alert tone="danger">{error}</Alert>}
      {candidates && candidates.length === 0 && <p className="text-muted">Chưa có gợi ý cho hợp âm này ở mức độ lạ đã chọn.</p>}
      {candidates && candidates.length > 0 && <p className="text-xs text-muted">Gợi ý sinh theo luật nhạc lý, xếp từ quen tai tới lạ tai. Chưa dùng AI.</p>}
      {groups.map(([level, items]) => <div key={level} className="grid gap-2">
        <h3 className="text-sm font-semibold text-ink">Độ lạ {level}: {items[0].level_label}</h3>
        <ul className="grid gap-2">{items.map((c) => <li key={c.symbol} className="grid gap-2 rounded-xl border border-line bg-bg p-3">
          <div className="flex flex-wrap items-center gap-2">
            <b className="font-mono text-lg text-ink">{c.symbol}</b><Badge tone={LEVEL_BADGE[c.level]}>{c.label}</Badge>
            <span className="text-xs text-muted">{c.rule_label}</span>
          </div>
          <p className="text-sm leading-relaxed text-ink">{c.reason_vi}</p>
          <p className="font-mono text-xs text-muted">Nốt: {c.notes.join(" – ")}</p>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => void listen(c.symbol)} aria-label={`Nghe ${c.symbol}`}><span aria-hidden="true">▶</span> Nghe</Button>
            <Button onClick={() => onChange(c.symbol)} aria-label={`Dùng ${c.symbol} cho ô ${index + 1}`}>Dùng hợp âm này</Button>
            <Button variant="ghost" onClick={() => setCandidates((list) => list?.filter((x) => x.symbol !== c.symbol) ?? null)} aria-label={`Bỏ qua ${c.symbol}`}>Bỏ qua</Button>
          </div>
        </li>)}</ul>
      </div>)}
    </div>}
  </Card>;
}

function AnalysisCard({ analysis }: { analysis: ComposeAnalysis | null }) {
  return <Card className="grid content-start gap-3">
    <div><Kicker>Phân tích</Kicker><CardTitle className="mt-1">Vì sao vòng này nghe như vậy</CardTitle></div>
    {!analysis ? <p className="text-muted">Đang phân tích…</p> : <>
      <p className="text-ink" aria-live="polite">{analysis.summary_vi}</p>
      {analysis.warnings.length > 0 && <div className="grid gap-2">{analysis.warnings.map((w) => <Alert key={`${w.code}-${w.bar}`} tone="info">{w.message_vi}</Alert>)}</div>}
      <ol className="grid gap-2">{analysis.bars.filter((b) => b.symbol).map((b) => <li key={b.bar} className="grid grid-cols-[auto_1fr] items-start gap-3 rounded-lg bg-bg p-2.5">
        <span className="grid min-w-14 place-items-center rounded-md bg-surface px-2 py-1 text-center font-mono text-sm font-semibold text-ink">{b.symbol}</span>
        <span className="text-sm text-ink"><b>Ô {b.bar} · {b.label}</b>{b.level ? ` · lạ ${b.level}` : ""}<br /><span className="text-muted">{b.reason_vi}</span></span>
      </li>)}</ol>
      <p className="text-xs text-muted">Cảnh báo chỉ để tham khảo, không cấm lựa chọn sáng tạo của bạn.</p>
    </>}
  </Card>;
}
