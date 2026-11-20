// Dòng thời gian "Cấu trúc bài" (QĐ 2A): dải đoạn màu theo loại, rộng theo thời lượng, kéo thả đổi thứ tự (chuột) hoặc
// nút ◀ ▶ (bàn phím, điện thoại); đường cong năng lượng thiết kế vẽ bên dưới, có dấu ▲ ở điểm bất ngờ; con trỏ phát chạy qua.
import { useState, type DragEvent, type KeyboardEvent } from "react";

import { beatToSeconds, mmss } from "../../audio/band/songSchedule";
import type { Arrangement, FormSection, ProgressionSlot, SectionType } from "../../audio/band/types";
import { Button } from "../ui/Button";
import { ChipButton, ToggleGroup } from "../ui/Page";
import {
  FEEL_VI, MAX_SONG_BARS, SECTION_COLOR, SECTION_VI, TRANSITION_VI, addSection, barOptions, moveSection, patchSection,
  removeSection, shortLabel, totalBars,
} from "./songForm";

const newSeed = () => 1 + Math.floor(Math.random() * 2_147_483_646);
const selectCls = "min-h-11 rounded-lg border border-line bg-surface px-3 text-base text-ink";

export function SongTimeline({ arrangement, sections, bpm, currentBar, selected, onSelect, onChange, cycles, emptySlots,
  onPlaySection, loopSection, onToggleLoopSection, playing }: {
  arrangement: Arrangement | null;
  sections: FormSection[];
  bpm: number;
  currentBar: number | null;
  selected: number;
  onSelect: (index: number) => void;
  onChange: (sections: FormSection[]) => void;
  cycles: Record<ProgressionSlot, number>;
  emptySlots: ProgressionSlot[];
  onPlaySection: (index: number) => void;
  loopSection: boolean;
  onToggleLoopSection: () => void;
  playing: boolean;
}) {
  const [dragFrom, setDragFrom] = useState<number | null>(null);
  const [addType, setAddType] = useState<SectionType>("chorus");
  const total = Math.max(1, totalBars(sections));
  const resolved = arrangement?.sections && arrangement.sections.length === sections.length ? arrangement.sections : null;
  const scale = arrangement ? arrangement.bpm / bpm : 1;
  const tempo = (arrangement?.tempo_map ?? []).map((p) => ({ ...p, bpm: p.bpm / scale }));
  const secondsAt = (bar: number) => beatToSeconds(bar * 4, bpm, tempo);
  const durationSec = secondsAt(total) + (arrangement?.tail_beats ?? 0) * 60 / bpm;
  const starts: number[] = [];
  sections.reduce((acc, s) => { starts.push(acc); return acc + s.bars; }, 0);
  const sel = sections[selected];
  const info = resolved?.[selected];

  const onDrop = (e: DragEvent, to: number) => {
    e.preventDefault();
    if (dragFrom !== null) onChange(moveSection(sections, dragFrom, to));
    setDragFrom(null);
  };
  const onKey = (e: KeyboardEvent, i: number) => {
    // Alt + ←/→: dời đoạn sang trái/phải mà không cần chuột.
    if (e.altKey && (e.key === "ArrowLeft" || e.key === "ArrowRight")) {
      e.preventDefault();
      const to = e.key === "ArrowLeft" ? i - 1 : i + 1;
      onChange(moveSection(sections, i, to));
      onSelect(Math.max(0, Math.min(sections.length - 1, to)));
    }
  };

  // Trục x theo GIÂY thật (không theo ô): đoạn ritardando dài ra đúng như tai nghe, khớp dải màu ở trang nghe thử.
  const songSec = Math.max(0.001, secondsAt(total));
  const xAt = (bar: number) => (secondsAt(bar) / songSec) * 1000;
  const pct = (bar: number) => `${(secondsAt(bar) / songSec) * 100}%`;
  const surprises = arrangement?.surprises ?? [];
  const labelOf = (i: number) => resolved?.[i]?.label ?? sections[i].label ?? SECTION_VI[sections[i].type];
  const energyOf = (i: number) => resolved?.[i]?.energy ?? sections[i].energy;
  const playing_i = currentBar === null ? -1 : sections.findIndex((s, i) => currentBar >= starts[i] && currentBar < starts[i] + s.bars);
  // Chữ tối cố định trên nền màu nhạt (giống hình mẫu), đủ tương phản cả giao diện sáng lẫn tối.
  const onPastel = "#13201d";

  return <div className="grid gap-3">
    <div className="flex flex-wrap items-baseline justify-between gap-2 text-sm text-muted">
      <span><b className="text-ink">{sections.length}</b> đoạn · <b className="text-ink">{total}</b>/{MAX_SONG_BARS} ô</span>
      <span>Thời lượng thật ở {bpm} BPM: <b className="font-mono text-ink">{mmss(durationSec)}</b></span>
    </div>

    {/* Dải đoạn mảnh (QĐ 1A): chỉ tên đoạn, rộng theo thời lượng; co vừa màn hình, đoạn hẹp thì viết tắt (QĐ 7A). */}
    <div className="relative">
      <ol aria-label="Các đoạn của bài, theo thứ tự phát" className="flex h-10 overflow-hidden rounded-lg border border-line">
        {sections.map((s, i) => {
          const label = labelOf(i);
          const t0 = secondsAt(starts[i]), t1 = secondsAt(starts[i] + s.bars);
          const prog = resolved?.[i]?.progression ?? s.progression;
          const tip = `${label} · ${mmss(t0)}–${mmss(t1)} · ${s.bars} ô · vòng ${prog} · năng lượng ${energyOf(i)}`;
          return <li key={s.id} className="@container min-w-0" style={{ flexGrow: Math.max(0.001, t1 - t0), flexBasis: 0 }}
            onDragOver={(e) => e.preventDefault()} onDrop={(e) => onDrop(e, i)}>
            <button type="button" draggable onDragStart={() => setDragFrom(i)} onKeyDown={(e) => onKey(e, i)}
              // QĐ 6A: bấm = chọn đoạn để sửa; nếu đang phát thì nhảy tới đoạn đó luôn.
              onClick={() => { onSelect(i); if (playing) onPlaySection(i); }} aria-pressed={selected === i} title={tip}
              aria-label={`${tip}${i === playing_i ? ", đang phát" : ""}. ${playing ? "Bấm để nhảy tới. " : ""}Alt + mũi tên để dời.`}
              style={{ background: SECTION_COLOR[s.type], color: onPastel }}
              className={`flex h-full w-full items-center border-r border-black/15 px-1.5 text-left text-xs font-semibold transition-[filter] ${selected === i ? "outline outline-2 -outline-offset-2 outline-[#13201d]" : ""} ${playing_i >= 0 && i !== playing_i ? "brightness-[0.82] saturate-[0.8]" : ""}`}>
              {/* Ô rộng: tên đủ ("Pre-Chorus 1"); ô hẹp: tên viết tắt vẫn nhận ra được ("Pre 1") thay vì "Pre-…". */}
              <span className="truncate @max-[6.5rem]:hidden">{label}</span>
              <span className="hidden truncate @max-[6.5rem]:inline" aria-hidden="true">{shortLabel(s.type, label)}</span>
            </button>
          </li>;
        })}
      </ol>
      {/* Con trỏ phát chạy dọc qua cả dải đoạn lẫn biểu đồ năng lượng (QĐ 5A). */}
      {currentBar !== null && <div aria-hidden="true" className="pointer-events-none absolute -bottom-1 top-0 z-10 w-0.5 bg-ink"
        style={{ left: pct(currentBar) }} />}
      {/* Cột năng lượng tô màu theo đoạn (QĐ 4A), ▲ là điểm bất ngờ. */}
      <svg viewBox="0 0 1000 64" preserveAspectRatio="none" role="img" className="mt-1 block h-16 w-full"
        aria-label={`Năng lượng từng đoạn: ${sections.map((_, i) => `${labelOf(i)} ${energyOf(i)}`).join(", ")}`}>
        {[1, 3, 5].map((e) => <line key={e} x1={0} x2={1000} y1={62 - e * 11} y2={62 - e * 11} stroke="var(--color-line)" strokeWidth={1} vectorEffect="non-scaling-stroke" />)}
        {sections.map((s, i) => {
          const x0 = xAt(starts[i]), x1 = xAt(starts[i] + s.bars), h = energyOf(i) * 11;
          return <rect key={s.id} x={x0} width={Math.max(0, x1 - x0 - 1.5)} y={62 - h} height={h} fill={SECTION_COLOR[s.type]}
            opacity={playing_i >= 0 && i !== playing_i ? 0.6 : 1} />;
        })}
        {surprises.map((sp, k) => <text key={k} x={xAt(sp.beat / 4)} y={9} fontSize={10} textAnchor="middle" fill="var(--color-danger)">▲</text>)}
        {currentBar !== null && <line x1={xAt(currentBar)} x2={xAt(currentBar)} y1={0} y2={64} stroke="var(--color-ink)" strokeWidth={2} vectorEffect="non-scaling-stroke" />}
      </svg>
      <div aria-hidden="true" className="mt-0.5 flex justify-between font-mono text-[11px] text-muted"><span>0:00</span><span>{mmss(songSec)}</span></div>
    </div>
    {/* Tên đầy đủ của đoạn đang chọn: trên điện thoại đoạn hẹp bị viết tắt, chạm vào là đọc được ở đây (QĐ 7A). */}
    {sel && <p className="text-sm text-ink" aria-live="polite">
      <span className="mr-1.5 inline-block size-3 rounded-sm align-middle" style={{ background: SECTION_COLOR[sel.type] }} aria-hidden="true" />
      <b>{labelOf(selected)}</b> <span className="font-mono text-muted">{mmss(secondsAt(starts[selected]))}–{mmss(secondsAt(starts[selected] + sel.bars))} · {sel.bars} ô · vòng {resolved?.[selected]?.progression ?? sel.progression}{emptySlots.includes(sel.progression) && sel.progression !== "A" ? " (còn trống, tạm dùng vòng A)" : ""} · năng lượng {energyOf(selected)}</span>
    </p>}
    <p className="text-xs text-muted">Cột màu: năng lượng từng đoạn (1 mộc → 5 đỉnh). ▲ đỏ: điểm bất ngờ có chủ đích. {playing ? "Bấm một đoạn để nhảy tới." : "Bấm một đoạn để sửa, kéo thả để đổi thứ tự."}</p>
    {surprises.length > 0 && <ul className="flex flex-wrap gap-2 text-xs">
      {surprises.map((sp, k) => <li key={k} className="rounded-full border border-line bg-bg px-2.5 py-1 text-ink">▲ {sp.label_vi}</li>)}
    </ul>}

    {sel && <div className="grid gap-3 rounded-xl border border-line bg-bg p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <b className="text-ink">{info?.label ?? SECTION_VI[sel.type]}</b>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={() => { onChange(moveSection(sections, selected, selected - 1)); onSelect(Math.max(0, selected - 1)); }}
            disabled={selected === 0} aria-label="Dời đoạn sang trái">◀</Button>
          <Button variant="secondary" onClick={() => { onChange(moveSection(sections, selected, selected + 1)); onSelect(Math.min(sections.length - 1, selected + 1)); }}
            disabled={selected === sections.length - 1} aria-label="Dời đoạn sang phải">▶</Button>
          <Button variant="secondary" onClick={() => onPlaySection(selected)}><span aria-hidden="true">▶</span> {playing ? "Nhảy tới đây" : "Phát từ đây"}</Button>
          <ChipButton pressed={loopSection} onClick={onToggleLoopSection}><span aria-hidden="true">↻ </span>Lặp đoạn này</ChipButton>
        </div>
      </div>
      {info?.note_vi && <p className="text-sm leading-relaxed text-ink"><span aria-hidden="true">🎛 </span>{info.note_vi}</p>}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <label className="grid gap-1 text-sm font-medium text-ink">Loại đoạn
          <select className={selectCls} value={sel.type} onChange={(e) => onChange(patchSection(sections, selected, { type: e.target.value as SectionType, label: null }))}>
            {(Object.keys(SECTION_VI) as SectionType[]).map((t) => <option key={t} value={t}>{SECTION_VI[t]}</option>)}
          </select>
        </label>
        <label className="grid gap-1 text-sm font-medium text-ink">Số ô
          <select className={selectCls} value={sel.bars} onChange={(e) => onChange(patchSection(sections, selected, { bars: Number(e.target.value) }))}>
            {[...new Set([...barOptions(cycles[sel.progression] || cycles.A), sel.bars])].sort((a, b) => a - b).map((n) => <option key={n} value={n}>{n} ô</option>)}
          </select>
        </label>
        <label className="grid gap-1 text-sm font-medium text-ink">Kiểu chuyển sang đoạn sau
          <select className={selectCls} value={sel.transition} onChange={(e) => onChange(patchSection(sections, selected, { transition: e.target.value as FormSection["transition"] }))}>
            {Object.entries(TRANSITION_VI).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </label>
        <label className="grid gap-1 text-sm font-medium text-ink">Cảm giác trống
          <select className={selectCls} value={sel.feel} onChange={(e) => onChange(patchSection(sections, selected, { feel: e.target.value as FormSection["feel"] }))}>
            {Object.entries(FEEL_VI).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </label>
      </div>
      <div className="grid gap-3 md:grid-cols-[auto_1fr] md:items-end">
        <div><p className="mb-1 text-sm font-medium text-ink">Vòng hợp âm</p>
          <ToggleGroup label="Vòng hợp âm của đoạn" value={sel.progression}
            options={(["A", "B", "C"] as ProgressionSlot[]).map((p) => ({ value: p, label: `${p}${emptySlots.includes(p) && p !== "A" ? " (trống)" : ""}` }))}
            onChange={(v) => onChange(patchSection(sections, selected, { progression: v }))} />
        </div>
        <div><p className="mb-1 text-sm font-medium text-ink">Năng lượng</p>
          <ToggleGroup label="Năng lượng của đoạn" value={String(sel.energy)}
            options={[1, 2, 3, 4, 5].map((n) => ({ value: String(n), label: n }))}
            onChange={(v) => onChange(patchSection(sections, selected, { energy: Number(v) }))} />
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <ChipButton pressed={sel.hook} onClick={() => onChange(patchSection(sections, selected, { hook: !sel.hook }))}>Hook ở đoạn này</ChipButton>
        <Button variant="secondary" onClick={() => onChange(patchSection(sections, selected, { seed: newSeed() }))}
          aria-label="Tạo bản phối khác chỉ cho đoạn này"><span aria-hidden="true">🎲</span> Bản khác cho đoạn này</Button>
        <Button variant="ghost" onClick={() => { onChange(removeSection(sections, selected)); onSelect(Math.max(0, selected - 1)); }}
          disabled={sections.length <= 1}>Xóa đoạn</Button>
        <span className="ml-auto flex items-center gap-2">
          <select aria-label="Loại đoạn sẽ thêm" className={selectCls} value={addType} onChange={(e) => setAddType(e.target.value as SectionType)}>
            {(Object.keys(SECTION_VI) as SectionType[]).map((t) => <option key={t} value={t}>{SECTION_VI[t]}</option>)}
          </select>
          <Button variant="secondary" onClick={() => { onChange(addSection(sections, addType, selected)); onSelect(selected + 1); }}
            disabled={total + 4 > MAX_SONG_BARS}>+ Thêm sau đoạn này</Button>
        </span>
      </div>
    </div>}
  </div>;
}
