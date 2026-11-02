// Dòng thời gian "Cấu trúc bài" (QĐ 2A): khối đoạn màu theo loại, rộng theo số ô, kéo thả đổi thứ tự (chuột) hoặc
// nút ◀ ▶ (bàn phím, điện thoại); đường cong năng lượng thiết kế vẽ bên dưới, có dấu ▲ ở điểm bất ngờ; con trỏ phát chạy qua.
import { useState, type DragEvent, type KeyboardEvent } from "react";

import { beatToSeconds, mmss } from "../../audio/band/songSchedule";
import type { Arrangement, FormSection, ProgressionSlot, SectionType } from "../../audio/band/types";
import { Button } from "../ui/Button";
import { ChipButton, ToggleGroup } from "../ui/Page";
import {
  FEEL_VI, MAX_SONG_BARS, SECTION_COLOR, SECTION_VI, TRANSITION_VI, addSection, barOptions, moveSection, patchSection,
  removeSection, totalBars,
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

  // Đường cong năng lượng: bậc thang theo ô nhịp (năng lượng thật đã cộng "Năng lượng tổng").
  const energyPoints = sections.flatMap((s, i) => {
    const e = resolved?.[i]?.energy ?? s.energy;
    const y = 52 - e * 10;
    return [`${(starts[i] / total) * 1000},${y}`, `${((starts[i] + s.bars) / total) * 1000},${y}`];
  }).join(" ");
  const surprises = arrangement?.surprises ?? [];

  return <div className="grid gap-3">
    <div className="flex flex-wrap items-baseline justify-between gap-2 text-sm text-muted">
      <span><b className="text-ink">{sections.length}</b> đoạn · <b className="text-ink">{total}</b>/{MAX_SONG_BARS} ô</span>
      <span>Thời lượng thật ở {bpm} BPM: <b className="font-mono text-ink">{mmss(durationSec)}</b></span>
    </div>

    {/* Khối đoạn: rộng theo số ô. Cuộn ngang trong khung trên điện thoại, không làm cả trang cuộn ngang. */}
    <div className="overflow-x-auto pb-1">
      <ol aria-label="Các đoạn của bài, theo thứ tự phát" className="relative flex min-w-[36rem] gap-1">
        {sections.map((s, i) => {
          const active = currentBar !== null && currentBar >= starts[i] && currentBar < starts[i] + s.bars;
          const label = resolved?.[i]?.label ?? s.label ?? SECTION_VI[s.type];
          return <li key={s.id} style={{ flexGrow: s.bars, flexBasis: 0, minWidth: "2.75rem" }}
            onDragOver={(e) => e.preventDefault()} onDrop={(e) => onDrop(e, i)}>
            <button type="button" draggable onDragStart={() => setDragFrom(i)} onKeyDown={(e) => onKey(e, i)}
              onClick={() => onSelect(i)} aria-pressed={selected === i}
              aria-label={`${label}, ${s.bars} ô, vòng ${resolved?.[i]?.progression ?? s.progression}, năng lượng ${resolved?.[i]?.energy ?? s.energy}, bắt đầu ${mmss(secondsAt(starts[i]))}${active ? ", đang phát" : ""}. Alt + mũi tên để dời.`}
              style={{ background: SECTION_COLOR[s.type] }}
              className={`grid h-full min-h-16 w-full content-between overflow-hidden rounded-lg border-2 px-1.5 py-1 text-left text-ink ${selected === i ? "border-ink" : "border-transparent hover:border-ink/40"} ${active ? "shadow-[inset_0_-4px_0_var(--color-ink)]" : ""}`}>
              <span className="truncate text-xs font-semibold">{label}</span>
              <span className="truncate font-mono text-[11px]">{s.bars} ô · {resolved?.[i]?.progression ?? s.progression}{emptySlots.includes(s.progression) && s.progression !== "A" ? "*" : ""}</span>
            </button>
          </li>;
        })}
      </ol>
      {/* Đường cong năng lượng + con trỏ phát */}
      <svg viewBox="0 0 1000 56" preserveAspectRatio="none" role="img" className="mt-1 h-14 w-full min-w-[36rem]"
        aria-label={`Đường cong năng lượng: ${sections.map((s, i) => `${resolved?.[i]?.label ?? SECTION_VI[s.type]} ${resolved?.[i]?.energy ?? s.energy}`).join(", ")}`}>
        {[1, 2, 3, 4, 5].map((e) => <line key={e} x1={0} x2={1000} y1={52 - e * 10} y2={52 - e * 10} stroke="var(--color-line)" strokeWidth={1} vectorEffect="non-scaling-stroke" />)}
        <polyline points={energyPoints} fill="none" stroke="var(--color-primary)" strokeWidth={2.5} vectorEffect="non-scaling-stroke" />
        {surprises.map((sp, k) => <text key={k} x={(sp.beat / 4 / total) * 1000} y={10} fontSize={11} textAnchor="middle" fill="var(--color-danger)">▲</text>)}
        {currentBar !== null && <line x1={(currentBar / total) * 1000} x2={(currentBar / total) * 1000} y1={0} y2={56} stroke="var(--color-ink)" strokeWidth={2} vectorEffect="non-scaling-stroke" />}
      </svg>
    </div>
    <p className="text-xs text-muted">Đường xanh: năng lượng từng đoạn (1 mộc → 5 đỉnh). ▲ đỏ: điểm bất ngờ có chủ đích.{emptySlots.length > 0 && " *: vòng này còn trống, đang tạm dùng vòng A."}</p>
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
