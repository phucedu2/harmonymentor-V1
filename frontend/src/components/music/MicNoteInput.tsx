// ADR-032: trả lời bằng cách đàn/hát từng nốt vào micro. Trình duyệt đo tần số (YIN), Music Engine đặt tên nốt.
// Nốt nghe được hiện trên piano ảo; bấm phím để bỏ nốt nghe nhầm, nên người học luôn sửa được trước khi nộp.
import { useEffect, useRef, useState } from "react";
import { api } from "../../api";
import { loadPitchModel } from "../../audio/pitch/features";
import { classifyMicError, DETECTOR_LABEL, makeDetector, micSupported, startMic, type DetectorKind, type MicError, type MicSession } from "../../audio/pitch/micListener";
import { Alert } from "../ui/Alert";
import { Button } from "../ui/Button";
import VirtualPiano from "./VirtualPiano";

type Heard = { note: string; cents: number };

const ERROR_TEXT: Record<MicError, string> = {
  unsupported: "Trình duyệt này không cho dùng micro. Hãy mở bằng Chrome, Edge hoặc Firefox bản mới, qua https hoặc localhost.",
  denied: "Trình duyệt đang chặn micro. Bấm biểu tượng ổ khóa cạnh thanh địa chỉ, cho phép Micro rồi bấm Bật micro lại.",
  "no-device": "Không tìm thấy micro. Hãy cắm tai nghe có micro hoặc kiểm tra cài đặt âm thanh của máy.",
  failed: "Chưa mở được micro. Hãy đóng ứng dụng khác đang dùng micro rồi thử lại.",
};

export default function MicNoteInput(props: {
  notes: string[]; onChange: (notes: string[]) => void; disabled?: boolean;
  highlighted?: string[]; incorrect?: string[];
}) {
  const [kind, setKind] = useState<DetectorKind>("hybrid");
  const [modelMissing, setModelMissing] = useState(false);
  const [listening, setListening] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<MicError | null>(null);
  const [level, setLevel] = useState(0);
  const [liveHz, setLiveHz] = useState<number | null>(null);
  const [last, setLast] = useState<Heard | null>(null);
  const [engineDown, setEngineDown] = useState(false);
  const session = useRef<MicSession | null>(null);
  // Nốt mới đến từ callback của micro; giữ bản mới nhất trong ref để không cộng vào danh sách cũ.
  const notesRef = useRef(props.notes);
  notesRef.current = props.notes;
  const onChange = useRef(props.onChange);
  onChange.current = props.onChange;

  const stop = () => { session.current?.stop(); session.current = null; setListening(false); setLevel(0); setLiveHz(null); };
  useEffect(() => stop, []);
  useEffect(() => { if (props.disabled) stop(); }, [props.disabled]);

  const start = async () => {
    setError(null); setStarting(true); setModelMissing(false);
    // Model nạp lười; nạp lỗi thì vẫn chạy bằng YIN và báo cho người học biết.
    const model = kind === "yin" ? null : await loadPitchModel().catch(() => { setModelMissing(true); return null; });
    try {
      session.current = await startMic({
        detector: makeDetector(kind, model),
        onFrame: ({ level: l, hz }) => { setLevel(l); setLiveHz(hz); },
        onNote: ({ hz }) => {
          api.noteFromFrequency(hz).then((r) => {
            setEngineDown(false);
            setLast({ note: r.note, cents: r.cents });
            const cur = notesRef.current;
            if (!cur.includes(r.note)) onChange.current([...cur, r.note]);
          }).catch(() => setEngineDown(true));
        },
      });
      setListening(true);
    } catch (e) {
      setError(micSupported() ? classifyMicError(e) : "unsupported");
    } finally { setStarting(false); }
  };

  // Thanh âm lượng: RMS 0,1 (đàn to gần micro) ≈ đầy thanh.
  const pct = Math.min(100, Math.round((level / 0.1) * 100));
  return <div className="mt-4 grid gap-3">
    <div className="flex flex-wrap items-center gap-3">
      {listening
        ? <Button type="button" variant="secondary" onClick={stop}><span aria-hidden="true">■</span> Tắt micro</Button>
        : <Button type="button" onClick={() => void start()} loading={starting} disabled={props.disabled}><span aria-hidden="true">🎤</span> Bật micro</Button>}
      <div className="flex min-w-40 flex-1 items-center gap-2 text-sm text-muted">
        <span>Âm lượng</span>
        <div className="h-2 flex-1 overflow-hidden rounded-full bg-line" role="meter" aria-label="Âm lượng micro" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct}>
          <div className="h-full rounded-full bg-primary transition-[width] duration-75" style={{ width: `${listening ? pct : 0}%` }} />
        </div>
      </div>
    </div>
    <p className="text-sm text-muted" aria-live="polite">
      {listening
        ? liveHz ? `Đang nghe một nốt khoảng ${Math.round(liveHz)} Hz…` : "Đang nghe. Đàn hoặc hát từng nốt một, giữ khoảng nửa giây."
        : "Micro chỉ dùng trong máy bạn: không ghi âm, không gửi âm thanh đi, chỉ gửi tần số của từng nốt để máy chủ đặt tên."}
    </p>
    <label className="flex flex-wrap items-center gap-2 text-sm text-ink">Bộ nhận diện
      <select value={kind} disabled={listening} onChange={(e) => setKind(e.target.value as DetectorKind)}
        className="min-h-10 rounded-lg border border-line bg-surface px-2 font-normal">
        {(Object.keys(DETECTOR_LABEL) as DetectorKind[]).map((k) => <option key={k} value={k}>{DETECTOR_LABEL[k]}</option>)}
      </select></label>
    {modelMissing && <Alert tone="info">Chưa tải được model AI, đang dùng thuật toán YIN.</Alert>}
    {last && <p className="text-sm text-ink" aria-live="polite">Vừa nghe: <b className="font-mono">{last.note}</b>
      {" "}<span className="text-muted">{Math.abs(last.cents) >= 45
        // Model chỉ chọn nốt; khi đáy YIN bị nhiễu đẩy ra mép nốt thì độ lệch không đáng tin, không hiện.
        ? "(chưa đo được độ lệch vì nhiều tiếng ồn)"
        : `(${last.cents > 0 ? "+" : ""}${last.cents} cent${Math.abs(last.cents) > 25 ? ", hơi lệch, nên chỉnh dây đàn" : ""})`}</span></p>}
    {error && <Alert tone="danger">{ERROR_TEXT[error]}</Alert>}
    {engineDown && <Alert tone="danger">Không kết nối được máy chủ để đặt tên nốt. Hãy kiểm tra mạng rồi đàn lại.</Alert>}
    <VirtualPiano selectionMode selectedNotes={props.notes} onSelectionChange={props.onChange} showLabels={false} startMidi={48} endMidi={84}
      highlightedPitchClasses={props.highlighted ?? []} incorrectPitchClasses={props.incorrect ?? []} />
  </div>;
}
