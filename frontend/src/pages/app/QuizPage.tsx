import { useEffect, useState, type FormEvent } from "react";
import { api, type AttemptResult, type Quiz, type SkillMastery } from "../../api";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Card, PageHeading, ProgressBar, ResultBox } from "../../components/ui/Page";
import { PageLoader } from "../../components/ui/PageLoader";

// Quiz 10 câu theo kỹ năng (FR-14 rút gọn, ADR-024): chọn kỹ năng, làm từng câu có sẵn trong ngân hàng,
// mỗi câu nộp qua /attempts nên mastery cập nhật như khi làm trong bài. Không sinh câu bằng AI.
export default function QuizPage() {
  const [skills, setSkills] = useState<SkillMastery[] | null>(null);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [score, setScore] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { api.myMastery().then((r) => setSkills(r.skills)).catch(() => setError("Chưa tải được danh sách kỹ năng.")); }, []);

  const start = async (skillId: string) => {
    setBusy(true); setError(null);
    try {
      const q = await api.quiz(skillId, 10);
      if (!q.questions.length) { setError("Kỹ năng này chưa có câu hỏi để làm quiz."); return; }
      setQuiz(q); setIndex(0); setScore(0); setAnswer(""); setResult(null);
    } catch { setError("Chưa tạo được quiz, thử lại sau."); }
    finally { setBusy(false); }
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!quiz || !answer.trim()) return;
    setBusy(true); setError(null);
    try {
      const q = quiz.questions[index];
      const r = await api.submitAttempt(q.exercise_version_id, answer.trim(), q.options?.length ? "choice" : "text");
      setResult(r); if (r.correct) setScore((s) => s + 1);
    } catch { setError("Chưa nộp được câu này, thử lại."); }
    finally { setBusy(false); }
  };
  const next = () => { setIndex((i) => i + 1); setAnswer(""); setResult(null); };

  if (!skills && !error) return <PageLoader />;

  if (quiz && index >= quiz.questions.length) {
    return <section>
      <PageHeading eyebrow="Quiz kỹ năng" title={`Bạn đúng ${score}/${quiz.questions.length} câu`}>
        Kết quả đã được ghi vào mức thành thạo của kỹ năng này.
      </PageHeading>
      <div className="mt-4 flex flex-wrap gap-3">
        <Button onClick={() => start(quiz.skill_id)} loading={busy}>Làm lại kỹ năng này</Button>
        <Button variant="secondary" onClick={() => setQuiz(null)}>Chọn kỹ năng khác</Button>
      </div>
    </section>;
  }

  if (quiz) {
    const q = quiz.questions[index];
    return <section>
      <PageHeading eyebrow="Quiz kỹ năng" title={`Câu ${index + 1}/${quiz.questions.length}`}>
        {quiz.available < quiz.requested ? `Kỹ năng này hiện có ${quiz.available} câu trong ngân hàng.` : "Mỗi câu chỉ nộp một lần."}
      </PageHeading>
      <ProgressBar value={index / quiz.questions.length} label="Tiến độ quiz" className="my-3" />
      {error && <div className="my-3"><Alert tone="danger">{error}</Alert></div>}
      <form onSubmit={submit}>
        <Card className="p-4">
          <p id="quiz-q" className="mb-2 font-medium">{q.prompt}</p>
          {q.options?.length
            ? <div role="radiogroup" aria-labelledby="quiz-q" className="flex flex-wrap gap-2">
                {q.options.map((opt) => <button type="button" key={opt} role="radio" aria-checked={answer === opt} disabled={!!result}
                  onClick={() => setAnswer(opt)} className={`rounded-lg border px-3 py-2 text-sm ${answer === opt ? "border-primary bg-primary-soft" : "border-line bg-surface"}`}>{opt}</button>)}
              </div>
            : <input aria-labelledby="quiz-q" value={answer} disabled={!!result} onChange={(e) => setAnswer(e.target.value)}
                className="w-full rounded-lg border border-line bg-surface px-3 py-2" placeholder="Gõ câu trả lời" />}
        </Card>
        {result
          ? <div className="mt-3 grid gap-3">
              <ResultBox correct={result.correct} title={result.correct ? "Đúng rồi" : "Chưa đúng"}>
                {result.feedback}{result.explanation ? <p className="mt-1">{result.explanation}</p> : null}
              </ResultBox>
              <Button type="button" onClick={next}>{index + 1 < quiz.questions.length ? "Câu tiếp theo" : "Xem kết quả"}</Button>
            </div>
          : <Button type="submit" className="mt-3" loading={busy} disabled={!answer.trim()}>Nộp câu này</Button>}
      </form>
    </section>;
  }

  return <section>
    <PageHeading eyebrow="Quiz kỹ năng" title="Chọn một kỹ năng để làm quiz 10 câu">
      Câu hỏi lấy từ ngân hàng đã được Music Engine kiểm đáp án; ưu tiên câu bạn chưa làm hoặc từng sai.
    </PageHeading>
    {error && <div className="my-3"><Alert tone="danger">{error}</Alert></div>}
    <ul className="mt-4 grid gap-2 sm:grid-cols-2">
      {skills?.map((s) => <li key={s.skill_id}><Card className="flex items-center justify-between gap-2 p-3">
        <div><p className="font-semibold">{s.name}</p>
          <p className="text-xs text-muted">{s.assessed && s.score !== null ? `Thành thạo ${Math.round(s.score * 100)}%` : "Chưa đánh giá"}</p></div>
        <Button variant="secondary" loading={busy} onClick={() => start(s.skill_id)}>Làm quiz</Button>
      </Card></li>)}
    </ul>
  </section>;
}
