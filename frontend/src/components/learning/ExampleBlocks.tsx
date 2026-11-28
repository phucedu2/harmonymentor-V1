import { useState } from "react";
import { audioEngine } from "../../audio/AudioEngine";
import { pitchClassesToAscendingNotes } from "../../audio/musicUtils";
import { buttonClass } from "../ui/Button";
import { NoteAudioButton } from "../music/AudioControls";
import * as ui from "./lessonStyles";

// FR-ADM-35..37: khối ví dụ do Quản trị viên thêm. Các nốt do Music Engine tính ở máy chủ lúc lưu; giao diện chỉ hiển thị và phát.
type P = Record<string, unknown>;
const str = (v: unknown) => (typeof v === "string" ? v : "");
const list = (v: unknown) => (Array.isArray(v) ? v.filter((x): x is string => typeof x === "string") : []);

function NoteChips({ notes }: { notes: string[] }) {
  return <p className="my-2 flex flex-wrap gap-2" aria-label={`Các nốt: ${notes.join(" ")}`}>
    {notes.map((n, i) => <span key={`${n}${i}`} className="rounded-full border border-line px-3 py-1 font-semibold">{n}</span>)}</p>;
}

export function ChordExampleBlock({ payload }: { payload: P }) {
  const notes = list(payload.notes);
  return <article className={`${ui.block} ${ui.blockTone.audio}`}>
    <span className={ui.kicker}>Ví dụ hợp âm</span><h3>{str(payload.title)}</h3>
    <NoteChips notes={notes} />
    <NoteAudioButton notes={notes} label={`Nghe ${str(payload.symbol)}`} />
    {str(payload.note) && <p>{str(payload.note)}</p>}
  </article>;
}

export function ScaleExampleBlock({ payload }: { payload: P }) {
  const notes = list(payload.notes);
  const [busy, setBusy] = useState(false);
  const play = async () => {
    setBusy(true);
    try {
      for (const n of pitchClassesToAscendingNotes(notes, 4)) {
        await audioEngine.playNote(n, "8n");
        await new Promise((r) => setTimeout(r, 420));
      }
    } finally { setBusy(false); }
  };
  return <article className={`${ui.block} ${ui.blockTone.audio}`}>
    <span className={ui.kicker}>Ví dụ âm giai</span><h3>{str(payload.title)}</h3>
    <NoteChips notes={notes} />
    <button type="button" className={buttonClass("secondary")} disabled={busy} onClick={() => void play()}><span aria-hidden="true">▶</span> Nghe âm giai</button>
    {str(payload.note) && <p>{str(payload.note)}</p>}
  </article>;
}

export function AudioExampleBlock({ payload }: { payload: P }) {
  return <article className={`${ui.block} ${ui.blockTone.audio}`}>
    <span className={ui.kicker}>Nghe ví dụ</span><h3>{str(payload.title)}</h3>
    <audio controls preload="none" src={str(payload.src)} className="my-2 w-full" aria-label={str(payload.title)} />
    {str(payload.note) && <p>{str(payload.note)}</p>}
    <p className="text-xs text-muted">Nguồn: {str(payload.source)} · Giấy phép: {str(payload.license)}</p>
  </article>;
}
