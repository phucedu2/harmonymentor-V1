import { useEffect, useRef, useState } from "react";
import { audioEngine } from "../../audio/AudioEngine";
import { pitchClassesToAscendingNotes } from "../../audio/musicUtils";
import { api, type ApiError, type ChordInspection } from "../../api";

type Props = {
  symbol: string;
  contextKey?: string;
  compact?: boolean;
  displayLabel?: string;
  eager?: boolean;
};

const QUALITY_LABELS: Record<string, string> = {
  maj: "hợp âm trưởng",
  min: "hợp âm thứ",
  dim: "hợp âm giảm",
  aug: "hợp âm tăng",
  "7": "dominant seventh",
  maj7: "major seventh",
  m7: "minor seventh",
  m7b5: "half-diminished seventh",
  dim7: "diminished seventh",
  sus2: "suspended 2",
  sus4: "suspended 4",
};

export default function ChordInspector({ symbol, contextKey, compact = false, displayLabel, eager = false }: Props) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<ChordInspection | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const fetchedFor = useRef("");
  const queryKey = `${symbol}|${contextKey ?? ""}`;

  const load = async () => {
    if (data && fetchedFor.current === queryKey) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.inspectChord(symbol, contextKey);
      setData(result);
      fetchedFor.current = queryKey;
    } catch (e) {
      const err = e as ApiError;
      setError(err.message ?? err.code);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setData(null);
    setError(null);
    fetchedFor.current = "";
    if (eager || open) void load();
    // queryKey is the semantic identity; load is intentionally not a dependency.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queryKey, eager]);

  const show = () => {
    setOpen(true);
    void load();
  };

  const play = async () => {
    if (!data) return;
    await audioEngine.playChord(pitchClassesToAscendingNotes(data.notes, 3), "2n");
  };

  return (
    <span className={`chord-inspector ${compact ? "compact" : ""}`} onMouseLeave={() => setOpen(false)}>
      <button
        type="button"
        className="chord-chip"
        aria-expanded={open}
        aria-label={`Xem cấu tạo hợp âm ${symbol}`}
        onMouseEnter={show}
        onFocus={show}
        onClick={() => {
          const next = !open;
          setOpen(next);
          if (next) void load();
        }}
      >
        {displayLabel ?? symbol}
      </button>
      {open && (
        <span className="chord-popover" role="dialog" aria-label={`Thông tin hợp âm ${symbol}`}>
          {loading && <span className="muted">Đang phân tích…</span>}
          {error && <span className="error-text">Không phân tích được {symbol}: {error}</span>}
          {data && !loading && (
            <>
              <span className="chord-popover-head"><b>{data.symbol}</b><small>{QUALITY_LABELS[data.quality] ?? data.quality}</small></span>
              <span className="chord-row"><em>Các nốt</em><strong>{data.notes.join(" – ")}</strong></span>
              <span className="chord-row"><em>Công thức</em><strong>{data.formula.join(" – ")}</strong></span>
              {data.bass && <span className="chord-row"><em>Nốt bass</em><strong>{data.bass}</strong></span>}
              {data.context?.roman && <span className="chord-row"><em>Số La Mã</em><strong>{data.context.roman}</strong></span>}
              {data.context?.function && <span className="chord-row"><em>Chức năng</em><strong>{data.context.function}</strong></span>}
              <button type="button" className="popover-audio" onClick={() => void play()}>▶ Nghe hợp âm</button>
              <span className="chord-popover-note">Cấu tạo hợp âm được tính bởi Music Theory Engine. Voicing thực tế có thể lược/đảo nốt tùy bài tập và phong cách.</span>
            </>
          )}
        </span>
      )}
    </span>
  );
}

export function ProgressionInspector({ text, contextKey }: { text: string; contextKey?: string }) {
  const harmonicPart = text.split("=")[0].trim();
  const pieces = harmonicPart.split(/\s*(?:→|->)\s*/).filter(Boolean);
  const chordLike = pieces.length > 1 && pieces.every((piece) => /^[A-G](?:#|b)?(?:maj|min|m|dim|aug|sus|add|M|ø|o)?[0-9#b()\/+\-]*$/i.test(piece));
  if (!chordLike) return <span className="progression-text">{text}</span>;
  return (
    <span className="progression-line">
      {pieces.map((piece, index) => (
        <span className="progression-part" key={`${piece}-${index}`}>
          <ChordInspector symbol={piece} contextKey={contextKey} />
          {index < pieces.length - 1 && <span className="progression-arrow">→</span>}
        </span>
      ))}
      {text.includes("=") && <span className="progression-analysis">= {text.split("=").slice(1).join("=").trim()}</span>}
    </span>
  );
}
