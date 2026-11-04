import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { api, type RecLesson, type Recommendations } from "../../api";
import { Button } from "../ui/Button";
import { Badge, Card, CardTitle, Kicker } from "../ui/Page";

// Thẻ gợi ý trên Dashboard (G-3 cách B): ba mục riêng, không tranh nhau top 5.
// Điểm và lý do đều do backend tính (04 mục 6.5); ở đây chỉ hiển thị. Dashboard hiện tối đa 3 bài mỗi mục
// (đề GĐ2 mục 8), nên gọi API với k = 3 để nhật ký gợi ý khớp đúng những gì người học thấy.
const SHOWN = 3;

const pct = (v: number | null) => (v === null ? "chưa có" : `${Math.round(v * 100)}%`);

function Why({ item }: { item: RecLesson }) {
  const c = item.components;
  return <details className="mt-2 text-sm text-muted">
    <summary className="cursor-pointer select-none">Vì sao gợi ý bài này?</summary>
    <ul className="mt-1 grid grid-cols-2 gap-x-4 gap-y-0.5">
      <li>Hợp mục tiêu: {pct(c.content)}</li>
      <li>Mức thành thạo: {pct(c.mastery)}</li>
      <li>Thẻ đến hạn: {c.due > 0 ? "có" : "không"}</li>
      <li>Người học tương tự: {pct(c.cf)}</li>
    </ul>
  </details>;
}

function LessonRow({ item, onOpen }: { item: RecLesson; onOpen: (item: RecLesson) => void }) {
  return <li className="rounded-lg border border-line p-3">
    <div className="flex flex-wrap items-center gap-2">
      <Badge tone={item.reason_code === "due" ? "warning" : "primary"}>{item.label ?? item.badge}</Badge>
      <span className="font-semibold">Bài {item.order}. {item.title}</span>
    </div>
    <p className="mt-1 text-sm">{item.reason}</p>
    <Why item={item} />
    <Button variant="secondary" className="mt-2" onClick={() => onOpen(item)}>
      {item.label ? "Ôn lại bài này" : "Mở bài"}
    </Button>
  </li>;
}

function GoalForm({ initial, onSaved }: { initial: string; onSaved: () => void }) {
  const [text, setText] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => setText(initial), [initial]);
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setSaving(true); setError(null);
    try { await api.setGoal(text); onSaved(); }
    catch { setError("Chưa lưu được mục tiêu, thử lại sau."); }
    finally { setSaving(false); }
  };
  return <form onSubmit={submit} className="mt-3">
    <label htmlFor="goal" className="text-sm font-semibold">Mục tiêu học của bạn</label>
    <div className="mt-1 flex flex-col gap-2 sm:flex-row">
      <input id="goal" value={text} maxLength={500} onChange={(e) => setText(e.target.value)}
        placeholder="Ví dụ: đệm hát nhạc pop bằng guitar"
        className="min-h-11 flex-1 rounded-lg border border-line bg-surface px-3" />
      <Button type="submit" variant="secondary" loading={saving}>Lưu mục tiêu</Button>
    </div>
    {error && <p className="mt-1 text-sm text-danger">{error}</p>}
  </form>;
}

export default function RecommendedLessons() {
  const navigate = useNavigate();
  const [data, setData] = useState<Recommendations | null>(null);
  const [goal, setGoal] = useState("");
  const [failed, setFailed] = useState(false);

  const load = () => {
    api.recommend(SHOWN).then((r) => { setData(r); setFailed(false); }).catch(() => setFailed(true));
    api.myGoal().then((g) => setGoal(g.goal_text ?? "")).catch(() => undefined);
  };
  useEffect(load, []);

  const open = (item: RecLesson | { lesson_id: string }) => {
    // Ghi lượt bấm để đo tỷ lệ bấm ở GĐ5; lỗi ghi nhật ký không được chặn việc mở bài.
    if (data && "reason" in item) api.clickRecommendation(data.log_id, item.lesson_id).catch(() => undefined);
    navigate(`/app/hoc?bai=${encodeURIComponent(item.lesson_id)}`);
  };

  return <Card className="mb-4 p-4" aria-labelledby="rec-title">
    <Kicker>Gợi ý cho bạn</Kicker>
    <CardTitle className="mt-1"><span id="rec-title">Học gì tiếp theo?</span></CardTitle>
    {failed && <div className="mt-2" role="alert">
      <p className="text-muted">Chưa tải được gợi ý. Bạn vẫn học theo lộ trình ở trên được.</p>
      <Button variant="ghost" className="-ml-4" onClick={load}>Thử lại</Button>
    </div>}

    {data?.continue.length ? <div className="mt-3">
      <h3 className="text-sm font-semibold">Tiếp tục bài đang học</h3>
      <ul className="mt-1 flex flex-wrap gap-2">
        {data.continue.map((l) => <li key={l.lesson_id}>
          <Button variant="ghost" onClick={() => open(l)}>Bài {l.order}. {l.title}</Button>
        </li>)}
      </ul>
    </div> : null}

    <div className="mt-3">
      <h3 className="text-sm font-semibold">Bài nên học tiếp</h3>
      {!data ? (failed ? null : <p className="mt-1 text-muted">Đang tính gợi ý…</p>)
        : data.next.length ? <ul className="mt-2 grid gap-2">{data.next.map((x) => <LessonRow key={x.lesson_id} item={x} onOpen={open} />)}</ul>
        : <p className="mt-1 text-muted">Chưa có bài mới đủ điều kiện. Hãy củng cố các kỹ năng tiên quyết (đạt 60%) để mở bài tiếp theo.</p>}
    </div>

    {data?.review.length ? <div className="mt-3">
      <h3 className="text-sm font-semibold">Bài nên ôn lại</h3>
      <ul className="mt-2 grid gap-2">{data.review.map((x) => <LessonRow key={x.lesson_id} item={x} onOpen={open} />)}</ul>
    </div> : null}

    <GoalForm initial={goal} onSaved={load} />
    {data && <p className="mt-2 text-xs text-muted">
      {data.mode !== "full" ? "Chưa đủ dữ liệu người học tương tự, gợi ý dựa trên mục tiêu, mức thành thạo và lịch ôn."
        : `So với ${data.neighbors_count} người học có trình độ gần bạn${data.cf_source === "synthetic" ? " (dữ liệu mô phỏng)" : ""}.`}
    </p>}
  </Card>;
}
