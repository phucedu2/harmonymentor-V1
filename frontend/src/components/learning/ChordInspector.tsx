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
    <span className="relative inline-flex" onMouseLeave={() => setOpen(false)} onKeyDown={(event) => { if (event.key === "Escape") setOpen(false); }}>
      <button
        type="button"
        className={`min-h-11 rounded-lg border border-primary/40 bg-primary-soft px-3 font-mono font-semibold text-primary-strong hover:bg-primary-soft/60 ${compact ? "text-sm" : ""}`}
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
        <span className="absolute top-[calc(100%+8px)] right-0 z-30 grid w-[min(17rem,85vw)] gap-2 rounded-xl border border-shell-line bg-shell p-3 text-left text-shell-ink shadow-xl sm:right-auto sm:left-0" role="dialog" aria-label={`Thông tin hợp âm ${symbol}`}>
          {loading && <span className="text-shell-muted">Đang phân tích…</span>}
          {error && <span className="text-[#ffb4b0]">Không phân tích được {symbol}: {error}</span>}
          {data && !loading && (
            <>
              <span className="flex items-baseline justify-between border-b border-shell-line pb-2"><b className="font-mono text-lg">{data.symbol}</b><small className="text-shell-muted">{QUALITY_LABELS[data.quality] ?? data.quality}</small></span>
              <span className="grid grid-cols-[4.5rem_1fr] gap-2"><em className="text-[11px] text-shell-muted uppercase not-italic">Các nốt</em><strong>{data.notes.join(" – ")}</strong></span>
              <span className="grid grid-cols-[4.5rem_1fr] gap-2"><em className="text-[11px] text-shell-muted uppercase not-italic">Công thức</em><strong>{data.formula.join(" – ")}</strong></span>
              {data.bass && <span className="grid grid-cols-[4.5rem_1fr] gap-2"><em className="text-[11px] text-shell-muted uppercase not-italic">Nốt bass</em><strong>{data.bass}</strong></span>}
              {data.context?.roman && <span className="grid grid-cols-[4.5rem_1fr] gap-2"><em className="text-[11px] text-shell-muted uppercase not-italic">Số La Mã</em><strong>{data.context.roman}</strong></span>}
              {data.context?.function && <span className="grid grid-cols-[4.5rem_1fr] gap-2"><em className="text-[11px] text-shell-muted uppercase not-italic">Chức năng</em><strong>{data.context.function}</strong></span>}
              <button type="button" className="mt-1 min-h-11 w-full rounded-lg bg-primary px-3 text-sm font-semibold text-white hover:bg-primary-strong" onClick={() => void play()}>▶ Nghe hợp âm</button>
              <span className="mt-0.5 border-t border-shell-line pt-2 text-[11px] text-shell-muted">Cấu tạo hợp âm được tính bởi Music Theory Engine. Voicing thực tế có thể lược/đảo nốt tùy bài tập và phong cách.</span>
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
  if (!chordLike) return <span className="font-semibold">{text}</span>;
  return (
    <span className="mt-3 flex flex-wrap items-center gap-2 text-lg">
      {pieces.map((piece, index) => (
        <span className="inline-flex items-center gap-2" key={`${piece}-${index}`}>
          <ChordInspector symbol={piece} contextKey={contextKey} />
          {index < pieces.length - 1 && <span className="text-muted" aria-hidden="true">→</span>}
        </span>
      ))}
      {text.includes("=") && <span className="ml-1 text-sm text-muted">= {text.split("=").slice(1).join("=").trim()}</span>}
    </span>
  );
}
