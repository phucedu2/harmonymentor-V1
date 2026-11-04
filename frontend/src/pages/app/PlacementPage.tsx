import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { api, type Placement, type PlacementSubmitResult } from "../../api";
import { Alert } from "../../components/ui/Alert";
import { Button, ButtonLink } from "../../components/ui/Button";
import { Card, PageHeading } from "../../components/ui/Page";
import { PageLoader } from "../../components/ui/PageLoader";

// Bài kiểm tra đầu vào (UC-06). Máy chủ chấm bằng Music Engine; trang chỉ thu câu trả lời.
// Kỹ năng làm đúng được 0,65 (đủ học tiếp, chưa thành thạo), sai được 0, bỏ trống là "chưa đánh giá".
export default function PlacementPage() {
  const navigate = useNavigate();
  const [placement, setPlacement] = useState<Placement | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<PlacementSubmitResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmRetake, setConfirmRetake] = useState(false);

  useEffect(() => { api.placement().then(setPlacement).catch(() => setLoadError(true)); }, []);

  if (loadError) return <Alert tone="danger">Chưa tải được bài kiểm tra. Hãy thử tải lại trang.</Alert>;
  if (!placement) return <PageLoader />;

  const done = placement.status === "completed";
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const payload = placement.questions
        .filter((q) => (answers[q.exercise_version_id] ?? "").trim() !== "")
        .map((q) => ({ exercise_version_id: q.exercise_version_id, answer: answers[q.exercise_version_id].trim() }));
      setResult(await api.submitPlacement(payload, done && confirmRetake));
    } catch {
      setError(done ? "Bạn đã làm bài này. Đánh dấu ô xác nhận để làm lại." : "Chưa gửi được bài. Hãy thử lại.");
    } finally {
      setBusy(false);
    }
  };
  const skip = async () => {
    setBusy(true);
    try { await api.skipPlacement(); navigate("/app", { replace: true }); } catch { setError("Chưa bỏ qua được. Hãy thử lại."); setBusy(false); }
  };

  if (result) {
    const right = result.results.filter((r) => r.correct).length;
    return <section>
      <PageHeading eyebrow="Kiểm tra đầu vào" title="Đã ghi kết quả">
        Bạn làm đúng {right}/{placement.questions.length} câu. Kỹ năng làm đúng được tính là đủ để học tiếp (0,65).
      </PageHeading>
      <ButtonLink to="/app">Về trang Tổng quan</ButtonLink>
    </section>;
  }

  return <section>
    <PageHeading eyebrow="Kiểm tra đầu vào" title="12 câu ngắn để biết bạn bắt đầu từ đâu">
      Không tính điểm, không cần làm hết. Câu nào chưa biết thì để trống. Bạn có thể bỏ qua và học từ Bài 1.
    </PageHeading>
    {done && <Alert tone="info">Bạn đã làm bài này. Làm lại sẽ thay kết quả cũ ở những kỹ năng chưa học trong bài.</Alert>}
    {error && <div className="my-3"><Alert tone="danger">{error}</Alert></div>}
    <form onSubmit={submit} className="mt-4 space-y-4">
      {placement.questions.map((q, i) => {
        const id = `pl-${q.exercise_version_id}`;
        return <Card key={q.exercise_version_id} className="p-4">
          <p id={`${id}-label`} className="mb-2 font-medium">{i + 1}. {q.prompt}</p>
          {q.options && q.options.length > 0
            ? <div role="radiogroup" aria-labelledby={`${id}-label`} className="flex flex-wrap gap-2">
                {q.options.map((opt) => {
                  const chosen = answers[q.exercise_version_id] === opt;
                  return <button type="button" key={opt} role="radio" aria-checked={chosen}
                    onClick={() => setAnswers((a) => ({ ...a, [q.exercise_version_id]: opt }))}
                    className={`rounded-lg border px-3 py-2 text-sm ${chosen ? "border-primary bg-primary-soft" : "border-line bg-surface"}`}>
                    {opt}
                  </button>;
                })}
              </div>
            : <input aria-labelledby={`${id}-label`} className="w-full rounded-lg border border-line bg-surface px-3 py-2"
                value={answers[q.exercise_version_id] ?? ""} placeholder="Ví dụ: C E G"
                onChange={(e) => setAnswers((a) => ({ ...a, [q.exercise_version_id]: e.target.value }))} />}
        </Card>;
      })}
      {done && <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={confirmRetake} onChange={(e) => setConfirmRetake(e.target.checked)} />
        Tôi muốn làm lại và thay kết quả cũ
      </label>}
      <div className="flex flex-wrap gap-3">
        <Button type="submit" loading={busy} disabled={done && !confirmRetake}>Nộp bài</Button>
        {!done && <Button type="button" variant="secondary" onClick={skip} disabled={busy}>Bỏ qua, học từ Bài 1</Button>}
      </div>
    </form>
  </section>;
}
