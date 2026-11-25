import { outcomes } from "./copy";

/** "Bạn sẽ học gì và làm được gì": 3 cột Hiểu / Nghe và chơi / Tạo ra. */
export function OutcomesSection() {
  return (
    <>
      <div className="grid gap-4 lg:grid-cols-3">
        {outcomes.columns.map((col, i) => (
          <article key={col.id} className="hm-outcome reveal">
            <p className="font-mono text-xs text-[var(--w-ink-soft)]">{String(i + 1).padStart(2, "0")}</p>
            <h3 className="display mt-2 text-2xl">{col.name}</h3>
            <p className="mt-3 text-sm text-[var(--w-ink-soft)]">{col.body}</p>
            <ul className="mt-5 space-y-2 text-sm text-ink">
              {col.items.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </article>
        ))}
      </div>
      <p className="reveal mt-5 text-sm text-[var(--w-ink-soft)]">{outcomes.note}</p>
    </>
  );
}
