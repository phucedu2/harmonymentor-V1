// Harmony Lab tối thiểu (phuc-music Bước 4, FR-17/18): ghép vòng hợp âm 4–8 ô, chọn nhạc nền, nghe lặp,
// xin gợi ý "lạ tai" theo luật (độ lạ 0–3) và đọc phân tích vì sao vòng nghe lạ.
// Nốt, tên hợp âm, gợi ý và phân tích đều do backend + Music Engine trả về; trang chỉ hiển thị và phát.
// Gợi ý không tự sửa dự án (nguyên tắc 5): người học bấm "Dùng hợp âm này" rồi tự lưu.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  api, type ApiError, type ComposeAnalysis, type ComposeCandidate, type ComposeOptions, type ComposeProjectSummary,
  type ComposeVoicing,
} from "../../api";
import { audioEngine } from "../../audio/AudioEngine";
import { backingTrack } from "../../audio/backingTrack";
import { buildSchedule, type Channel } from "../../audio/trackSchedule";
import { midiToScientific } from "../../audio/musicUtils";
import { LEVEL_BADGE, chordsOfKey, remapToKey, resizeBars, starterProgression } from "../../components/compose/harmonyLab";
import NotationStaff from "../../components/music/NotationStaff";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Badge, Card, CardTitle, ChipButton, Kicker, PageHeading, ToggleGroup } from "../../components/ui/Page";
import { PageLoader } from "../../components/ui/PageLoader";

const CHANNEL_LABELS: Record<Channel, string> = { chords: "Hợp âm", bass: "Bass", drums: "Trống" };
const errorText = (e: unknown) => { const err = e as ApiError; return err.message ?? err.code ?? "Có lỗi, hãy thử lại."; };

type Draft = { id: string | null; name: string; key: string; tempo: number; bars: number; style: string; chords: (string | null)[] };

export default function CompositionLabPage() {
  const [options, setOptions] = useState<ComposeOptions | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [dirty, setDirty] = useState(false);
  const [selected, setSelected] = useState(0);
  const [voicings, setVoicings] = useState<Record<string, ComposeVoicing>>({});
  const [analysis, setAnalysis] = useState<ComposeAnalysis | null>(null);
  const [playing, setPlaying] = useState(false);
  const [currentBar, setCurrentBar] = useState<number | null>(null);
  const [loop, setLoop] = useState(true);
  const [muted, setMuted] = useState<Record<Channel, boolean>>({ chords: false, bass: false, drums: false });
  const [projects, setProjects] = useState<ComposeProjectSummary[]>([]);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState<{ tone: "success" | "danger" | "info"; text: string } | null>(null);

  useEffect(() => {
    Promise.all([api.composeOptions(), api.listProjects()])
      .then(([opts, list]) => {
        setOptions(opts);
        setProjects(list);
        const style = opts.styles[0];
        setDraft({ id: null, name: "Vòng hợp âm đầu tiên", key: "C", tempo: style.default_bpm, bars: 4, style: style.id,
          chords: starterProgression(opts, "C", 4) });
      })
      .catch((e) => setLoadError(errorText(e)));
    return () => backingTrack.stop();
  }, []);

  const update = (patch: Partial<Draft>) => { setDraft((d) => (d ? { ...d, ...patch } : d)); setDirty(true); };

  // Lấy cao độ (Music Engine) cho các hợp âm chưa có trong bộ nhớ tạm.
  const ensureVoicings = useCallback(async (symbols: string[]) => {
    const missing = [...new Set(symbols)].filter((s) => !voicings[s]);
    if (!missing.length) return voicings;
    const fetched = await api.composeVoicings(missing);
    const merged = { ...voicings, ...fetched };
    setVoicings(merged);
    return merged;
  }, [voicings]);

  const chordKey = draft ? `${draft.key}|${draft.chords.join(",")}` : "";
  useEffect(() => {
    if (!draft) return;
    const symbols = draft.chords.filter((c): c is string => Boolean(c));
    void ensureVoicings(symbols).catch((e) => setNotice({ tone: "danger", text: errorText(e) }));
    const timer = window.setTimeout(() => {
      api.composeAnalyze(draft.key, draft.chords).then(setAnalysis).catch(() => setAnalysis(null));
    }, 250);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chordKey]);

  const style = options?.styles.find((s) => s.id === draft?.style) ?? options?.styles[0];

  const startPlayback = useCallback(async () => {
    if (!draft || !style) return;
    try {
      audioEngine.stopAll();
      const map = await ensureVoicings(draft.chords.filter((c): c is string => Boolean(c)));
      const events = buildSchedule(draft.chords.map((c) => (c ? map[c] ?? null : null)), style);
      await backingTrack.play({
        events, bars: draft.bars, bpm: draft.tempo, swing: style.swing, loop,
        onBar: setCurrentBar, onEnd: () => { setPlaying(false); setCurrentBar(null); },
      });
      setPlaying(true);
    } catch (e) {
      setNotice({ tone: "danger", text: `Chưa phát được: ${errorText(e)}` });
    }
  }, [draft, style, loop, ensureVoicings]);

  const stopPlayback = () => { backingTrack.stop(); setPlaying(false); setCurrentBar(null); };

  // Đang phát mà đổi hợp âm, mẫu nền hoặc chế độ lặp thì phát lại từ đầu với lưới mới.
  const restartKey = draft ? `${draft.chords.join(",")}|${draft.style}|${draft.bars}|${loop}` : "";
  const playingRef = useRef(playing);
  playingRef.current = playing;
  useEffect(() => { if (playingRef.current) void startPlayback(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [restartKey]);
  useEffect(() => { if (draft) backingTrack.setBpm(draft.tempo); }, [draft?.tempo]);

  const toggleChannel = (channel: Channel) => {
    const next = { ...muted, [channel]: !muted[channel] };
    setMuted(next);
    backingTrack.setMuted(channel, next[channel]);
  };

  const save = async () => {
    if (!draft) return;
    setSaving(true);
    setNotice(null);
    const body = { name: draft.name.trim() || "Vòng chưa đặt tên", key: draft.key, tempo_bpm: draft.tempo, bars: draft.bars, style: draft.style, chords: draft.chords };
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
      setDraft({ id: p.id, name: p.name, key: p.key, tempo: p.tempo_bpm, bars: p.bars, style: p.style, chords: p.chords });
      setSelected(0);
      setDirty(false);
      setNotice({ tone: "info", text: `Đã mở "${p.name}".` });
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
      chords: starterProgression(options, draft?.key ?? "C", 4) });
    setSelected(0);
    setDirty(false);
  };

  if (loadError) return <section><PageHeading eyebrow="Sáng tác" title="Harmony Lab" /><Alert tone="danger">Chưa tải được xưởng sáng tác: {loadError}</Alert></section>;
  if (!options || !draft || !style) return <PageLoader />;

  const keyChords = chordsOfKey(options, draft.key);
  const selectedChord = draft.chords[selected] ?? null;
  const selectedVoicing = selectedChord ? voicings[selectedChord] : undefined;
  const barInfo = (i: number) => analysis?.bars[i];

  return <section className="pb-24 sm:pb-0">
    <PageHeading eyebrow="Sáng tác" title="Harmony Lab">
      Ghép một vòng hợp âm, chọn nhạc nền rồi bấm Phát. Muốn nghe lạ tai hơn, chọn một ô và xin gợi ý.
    </PageHeading>

    {notice && <div className="mb-4"><Alert tone={notice.tone}>{notice.text}</Alert></div>}

    {/* Thanh điều khiển: giọng, tốc độ, phát, lặp (tài liệu 04 Bảng 25). */}
    <Card className="mb-4 grid gap-4">
      <div className="grid gap-4 md:grid-cols-[1fr_auto_auto] md:items-end">
        <label className="grid gap-1.5 text-sm font-medium text-ink">Tên vòng hợp âm
          <input className="min-h-11 rounded-lg border border-line bg-surface px-3 text-base text-ink" value={draft.name} maxLength={80}
            onChange={(e) => update({ name: e.target.value })} />
        </label>
        <label className="grid gap-1.5 text-sm font-medium text-ink">Giọng (trưởng)
          <select className="min-h-11 rounded-lg border border-line bg-surface px-3 text-base text-ink" value={draft.key}
            onChange={(e) => update({ key: e.target.value, chords: remapToKey(draft.chords, options, draft.key, e.target.value) })}>
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
      <div className="grid gap-4 md:grid-cols-2">
        <div><p className="mb-1.5 text-sm font-medium text-ink">Số ô nhịp</p>
          <ToggleGroup label="Số ô nhịp" value={String(draft.bars)}
            options={[4, 5, 6, 7, 8].map((n) => ({ value: String(n), label: n }))}
            onChange={(v) => { const bars = Number(v); update({ bars, chords: resizeBars(draft.chords, bars) }); setSelected((s) => Math.min(s, bars - 1)); }} />
        </div>
        <div><p className="mb-1.5 text-sm font-medium text-ink">Kênh đang bật</p>
          <div role="group" aria-label="Bật hoặc tắt từng kênh" className="flex flex-wrap gap-2">
            {(Object.keys(CHANNEL_LABELS) as Channel[]).map((c) => <ChipButton key={c} pressed={!muted[c]} onClick={() => toggleChannel(c)}>
              <span aria-hidden="true">{muted[c] ? "🔇 " : "🔊 "}</span>{CHANNEL_LABELS[c]}</ChipButton>)}
            <ChipButton pressed={loop} onClick={() => setLoop((v) => !v)}><span aria-hidden="true">↻ </span>Lặp lại</ChipButton>
          </div>
        </div>
      </div>
      {/* Nút chính: dính đáy màn hình điện thoại để luôn thấy, nằm trong thẻ trên màn rộng. */}
      <div className="fixed inset-x-0 bottom-0 z-20 flex gap-3 border-t border-line bg-bg/95 p-3 backdrop-blur sm:static sm:border-0 sm:bg-transparent sm:p-0">
        {playing
          ? <Button size="lg" className="flex-1 sm:flex-none" onClick={stopPlayback}><span aria-hidden="true">■</span> Dừng</Button>
          : <Button size="lg" className="flex-1 sm:flex-none" onClick={() => void startPlayback()}><span aria-hidden="true">▶</span> Phát</Button>}
        <Button size="lg" variant="secondary" className="flex-1 sm:flex-none" loading={saving} onClick={() => void save()}>
          {draft.id ? "Lưu thay đổi" : "Lưu vòng này"}
        </Button>
        <span className="hidden self-center text-sm text-muted sm:inline" aria-live="polite">{dirty ? "Có thay đổi chưa lưu" : draft.id ? "Đã lưu" : ""}</span>
      </div>
    </Card>

    {/* Lưới hợp âm ở giữa. */}
    <Card className="mb-4">
      <div className="mb-3 flex items-end justify-between gap-3">
        <div><Kicker>Lưới hợp âm</Kicker><CardTitle className="mt-1">Chọn một ô để đổi hợp âm</CardTitle></div>
        {analysis && <Badge tone={LEVEL_BADGE[analysis.level]}>Độ lạ {analysis.level}/3 · {analysis.level_label}</Badge>}
      </div>
      <ol className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {draft.chords.map((chord, i) => {
          const info = barInfo(i);
          const isPlaying = currentBar === i;
          return <li key={i}>
            <button type="button" aria-pressed={selected === i} onClick={() => setSelected(i)}
              aria-label={`Ô ${i + 1}: ${chord ?? "trống"}${info?.label ? `, ${info.label}` : ""}${info?.level != null ? `, độ lạ ${info.level}` : ""}${isPlaying ? ", đang phát" : ""}`}
              className={`grid min-h-24 w-full content-between rounded-xl border-2 p-3 text-left transition-colors ${selected === i ? "border-primary bg-primary-soft" : "border-line bg-surface hover:border-primary"} ${isPlaying ? "shadow-[inset_0_-4px_0_var(--color-brass)]" : ""}`}>
              <span className="flex items-center justify-between text-xs font-semibold text-muted"><span>Ô {i + 1}</span>{isPlaying && <span className="text-ink">▶ đang phát</span>}</span>
              <span className="font-mono text-2xl font-semibold text-ink">{chord ?? "—"}</span>
              <span className="text-xs text-muted">{info?.label ?? (chord ? "…" : "chưa có hợp âm")}{info?.level ? ` · lạ ${info.level}` : ""}</span>
            </button>
          </li>;
        })}
      </ol>
    </Card>

    <div className="mb-4 grid gap-4 lg:grid-cols-[1.1fr_1fr]">
      <BarEditor index={selected} chord={selectedChord} voicing={selectedVoicing} keyName={draft.key} keyChords={keyChords}
        chords={draft.chords} levels={options.levels}
        onChange={(symbol) => { const chords = [...draft.chords]; chords[selected] = symbol; update({ chords }); }}
        ensureVoicings={ensureVoicings} />
      <AnalysisCard analysis={analysis} />
    </div>

    {/* Mẫu nền ở dưới (tài liệu 04 Bảng 25). */}
    <Card className="mb-4">
      <Kicker>Nhạc nền</Kicker><CardTitle className="mt-1">Chọn kiểu trống và bass</CardTitle>
      <div role="group" aria-label="Mẫu nhạc nền" className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {options.styles.map((s) => <button key={s.id} type="button" aria-pressed={draft.style === s.id}
          onClick={() => update({ style: s.id, tempo: s.default_bpm })}
          className={`grid min-h-11 gap-1 rounded-xl border-2 p-3 text-left ${draft.style === s.id ? "border-primary bg-primary-soft" : "border-line bg-surface hover:border-primary"}`}>
          <b className="text-ink">{s.label}</b><span className="text-sm text-muted">{s.description}</span>
          <span className="font-mono text-xs text-muted">{s.default_bpm} BPM{s.swing ? " · swing" : ""}</span>
        </button>)}
      </div>
    </Card>

    <Card>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div><Kicker>Đã lưu</Kicker><CardTitle className="mt-1">Vòng hợp âm của bạn</CardTitle></div>
        <Button variant="secondary" onClick={newProject}>+ Vòng mới</Button>
      </div>
      {projects.length === 0
        ? <p className="mt-2 text-muted">Chưa có vòng nào được lưu. Bấm "Lưu vòng này" để giữ lại.</p>
        : <ul className="mt-3 divide-y divide-line">{projects.map((p) => <li key={p.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
            <div><b className="text-ink">{p.name}</b><small className="block text-muted">{p.key} trưởng · {p.bars} ô · {options.styles.find((s) => s.id === p.style)?.label ?? p.style}</small></div>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => void openProject(p.id)} aria-label={`Mở ${p.name}`}>Mở</Button>
              <Button variant="ghost" onClick={() => void removeProject(p.id, p.name)} aria-label={`Xóa ${p.name}`}>Xóa</Button>
            </div>
          </li>)}</ul>}
    </Card>
  </section>;
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
