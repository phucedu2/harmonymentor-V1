import { useEffect, useRef, useState } from "react";
import { api, type ApiError, type ChordInspection } from "../../api";

type Props = {
  symbol: string;
  contextKey?: string;
  compact?: boolean;
};

export default function ChordInspector({ symbol, contextKey, compact = false }: Props) {
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
    fetchedFor.current = "";
  }, [queryKey]);

  const show = () => {
    setOpen(true);
    void load();
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
        {symbol}
      </button>
      {open && (
        <span className="chord-popover" role="dialog" aria-label={`Thông tin hợp âm ${symbol}`}>
          {loading && <span className="muted">Đang phân tích…</span>}
          {error && <span className="error-text">{error}</span>}
          {data && !loading && (
            <>
              <span className="chord-popover-head"><b>{data.symbol}</b><small>{data.quality}</small></span>
              <span className="chord-row"><em>Notes</em><strong>{data.notes.join(" – ")}</strong></span>
              <span className="chord-row"><em>Formula</em><strong>{data.formula.join(" – ")}</strong></span>
              {data.bass && <span className="chord-row"><em>Bass</em><strong>{data.bass}</strong></span>}
              {data.context?.roman && <span className="chord-row"><em>Roman</em><strong>{data.context.roman}</strong></span>}
              {data.context?.function && <span className="chord-row"><em>Function</em><strong>{data.context.function}</strong></span>}
              <span className="chord-popover-note">Dữ liệu cấu tạo lấy từ Music Theory Engine, không từ LLM.</span>
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
  const chordLike = pieces.length > 1 && pieces.every((piece) => /^[A-G](?:#|b)?(?:maj|min|m|dim|aug|sus|add|M|ø|o)?[0-9#b()\/+-]*$/i.test(piece));
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
