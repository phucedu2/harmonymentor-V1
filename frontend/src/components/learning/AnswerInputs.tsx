import { useState } from "react";
import { api, type OpenFeedback } from "../../api";
import { Button } from "../ui/Button";
import { choice } from "./lessonStyles";

// ADR-028: các ô trả lời dùng chung cho bài học, Quiz kỹ năng và Luyện tập "Từ tài liệu".
// Chỉ hiển thị và gom lựa chọn; chấm luôn ở máy chủ (Music Engine hoặc đáp án đã duyệt).

/** Một hoặc nhiều lựa chọn. Chọn nhiều thì bấm lại để bỏ chọn. */
export function ChoiceList({ options, multi = false, value, onChange, disabled = false, label }: {
  options: string[]; multi?: boolean; value: string[]; onChange: (next: string[]) => void; disabled?: boolean; label: string;
}) {
  const toggle = (opt: string) => {
    if (!multi) return onChange([opt]);
    onChange(value.includes(opt) ? value.filter((v) => v !== opt) : [...value, opt]);
  };
  return <div className="grid gap-1.5">
    {multi && <p className="text-xs text-muted">Chọn TẤT CẢ phương án đúng (có thể nhiều hơn một).</p>}
    <div className="flex flex-wrap gap-2" role={multi ? "group" : "radiogroup"} aria-label={label}>
      {options.map((opt) => {
        const on = value.includes(opt);
        return <button type="button" key={opt} disabled={disabled} onClick={() => toggle(opt)}
          {...(multi ? { "aria-pressed": on } : { role: "radio", "aria-checked": on })} className={choice(on)}>
          {multi && <span aria-hidden="true" className="mr-1">{on ? "☑" : "☐"}</span>}{opt}</button>;
      })}
    </div>
  </div>;
}

const MET: Record<"yes" | "partial" | "no", { icon: string; label: string; tone: string }> = {
  yes: { icon: "✓", label: "Đã nêu", tone: "text-success" },
  partial: { icon: "◐", label: "Nêu chưa đủ", tone: "text-warning" },
  no: { icon: "✗", label: "Chưa nêu", tone: "text-danger" },
};
const AI_NOTE: Record<OpenFeedback["ai_status"], string | null> = {
  ok: null,
  off: "AI đang tắt, bạn tự đối chiếu bài làm với từng ý chấm bên dưới nhé.",
  quota: "Hôm nay bạn đã dùng hết lượt AI nhận xét. Hãy tự đối chiếu với từng ý chấm.",
  unavailable: "AI chưa trả lời được lúc này. Hãy tự đối chiếu với từng ý chấm.",
  flagged: "Nhận xét của AI có chỗ Music Engine thấy chưa đúng nên đã ẩn đi. Hãy tự đối chiếu với từng ý chấm.",
};

/** Câu tự luận mở: viết bài, xem đáp án mẫu + ý chấm, kèm nhận xét AI nếu có. Không tính điểm thành thạo. */
export function OpenAnswer({ versionId, label }: { versionId: string; label: string }) {
  const [text, setText] = useState("");
  const [fb, setFb] = useState<OpenFeedback | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const send = async () => {
    setBusy(true); setError(null);
    try { setFb(await api.openFeedback(versionId, text.trim())); }
    catch (e) { setError((e as { message?: string }).message ?? "Chưa gửi được, thử lại sau."); }
    finally { setBusy(false); }
  };
  return <div className="grid gap-2">
    <textarea rows={4} value={text} onChange={(e) => setText(e.target.value)} aria-label={label} maxLength={3000}
      placeholder="Viết câu trả lời của bạn bằng lời của mình…" className="w-full rounded-lg border border-line bg-surface p-2 text-ink" />
    <p className="text-xs text-muted">Câu tự luận mở không chấm đúng/sai và không tính vào mức thành thạo; dùng để tự luyện diễn đạt.</p>
    <div><Button disabled={busy || !text.trim()} loading={busy} onClick={send}>{fb ? "Gửi lại để nhận xét" : "Xem đáp án mẫu và nhận xét"}</Button></div>
    {error && <p role="alert" className="text-sm text-danger">{error}</p>}
    {fb && <div className="grid gap-2 rounded-lg border border-line bg-bg p-3 text-sm" role="status">
      {AI_NOTE[fb.ai_status] && <p className="text-muted">{AI_NOTE[fb.ai_status]}</p>}
      {fb.ai && <p className="font-semibold text-ink">{fb.ai.summary}</p>}
      <div><p className="font-semibold">Các ý cần có</p>
        <ul className="mt-1 grid gap-1">{fb.rubric.map((point, i) => {
          const got = fb.ai?.points[i];
          const met = got ? MET[got.met] : null;
          return <li key={i} className="flex gap-2">
            <span aria-hidden="true" className={met?.tone ?? "text-muted"}>{met?.icon ?? "•"}</span>
            <span>{point}{met && <span className="sr-only"> ({met.label})</span>}{got?.comment && <span className="block text-muted">{got.comment}</span>}</span>
          </li>;
        })}</ul></div>
      <div><p className="font-semibold">Đáp án mẫu</p><p className="mt-1">{fb.model_answer}</p></div>
      {fb.explanation && <p className="text-muted">{fb.explanation}</p>}
    </div>}
  </div>;
}
