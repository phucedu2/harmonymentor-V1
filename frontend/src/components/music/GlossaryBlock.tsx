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
  return <article className="lesson-content-block glossary-block">
    <span className="section-kicker">{kicker}</span>
    <h3>{title}</h3>
    {intro && <p>{intro}</p>}
    {spectrums.length > 0 && <div className="interval-spectrum" aria-label="Sơ đồ chất lượng quãng">
      {spectrums.map((item) => <div className="interval-spectrum-row" key={item.label}>
        <b>{item.label}</b><span>{item.text}</span>
      </div>)}
    </div>}
    <div className="glossary-grid">
      {terms.map((item) => <div className="glossary-term" key={`${item.symbol ?? ""}-${item.term}`}>
        <div className="glossary-term-head">{item.symbol && <code>{item.symbol}</code>}<b>{item.term}</b></div>
        <p>{item.definition}</p>
        {item.example && <small>Ví dụ: {item.example}</small>}
      </div>)}
    </div>
  </article>;
}
