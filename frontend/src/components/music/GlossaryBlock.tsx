import * as ui from "../learning/lessonStyles";
type Term = {
  symbol?: string;
  term: string;
  definition: string;
  example?: string;
};

type Spectrum = {
  label: string;
  text: string;
};

export default function GlossaryBlock({
  title,
  intro,
  terms,
  spectrums = [],
  kicker = "Giải mã ký hiệu",
}: {
  title: string;
  intro?: string;
  terms: Term[];
  spectrums?: Spectrum[];
  kicker?: string;
}) {
  return <article className={`${ui.block} ${ui.blockTone.explorer}`}>
    <span className={ui.kicker}>{kicker}</span>
    <h3>{title}</h3>
    {intro && <p>{intro}</p>}
    {spectrums.length > 0 && <div className="my-3 grid gap-2" aria-label="Sơ đồ chất lượng quãng">
      {spectrums.map((item) => <div className="grid items-center gap-1 rounded-lg border border-line bg-bg px-3 py-2 sm:grid-cols-[minmax(9rem,0.8fr)_2fr] sm:gap-3" key={item.label}>
        <b className="text-primary-strong">{item.label}</b><span className="font-mono text-xs">{item.text}</span>
      </div>)}
    </div>}
    <div className="mt-3 grid gap-3 sm:grid-cols-2">
      {terms.map((item) => <div className="rounded-xl border border-line bg-surface p-3 [&_p]:my-1.5" key={`${item.symbol ?? ""}-${item.term}`}>
        <div className="flex items-center gap-2">{item.symbol && <code className="min-w-10 rounded-md bg-primary-soft px-1.5 py-0.5 text-center font-mono font-semibold text-primary-strong">{item.symbol}</code>}<b>{item.term}</b></div>
        <p>{item.definition}</p>
        {item.example && <small className="text-muted">Ví dụ: {item.example}</small>}
      </div>)}
    </div>
  </article>;
}
