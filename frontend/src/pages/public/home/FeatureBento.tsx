import { useEffect, useState } from "react";
import { readTheme, type Theme } from "../../../theme/theme";
import { features } from "./copy";

/** Kích thước thật của ảnh chụp trong frontend/public/home (scripts/chup-anh-trang-chu.cjs). */
const SHOT_W = 1200;
const SHOT_H = 780;

function useThemeName(): Theme {
  const [theme, setTheme] = useState<Theme>(readTheme);
  useEffect(() => {
    const sync = (e: Event) => setTheme((e as CustomEvent<Theme>).detail);
    window.addEventListener("hm-theme", sync);
    return () => window.removeEventListener("hm-theme", sync);
  }, []);
  return theme;
}

function Shot({ id, alt }: { id: string; alt: string }) {
  const theme = useThemeName();
  const [missing, setMissing] = useState(false);
  if (missing) return null;
  return (
    <img
      className="hm-shot mt-5"
      src={`/home/${id}-${theme}.webp`}
      alt={alt}
      width={SHOT_W}
      height={SHOT_H}
      loading="lazy"
      decoding="async"
      onError={() => setMissing(true)}
    />
  );
}

type TileProps = { id: string; name: string; tagline?: string; body: string; alt: string; big?: boolean };

function Tile({ id, name, tagline, body, alt, big }: TileProps) {
  return (
    <article id={id} className={`hm-tile reveal scroll-mt-20 ${big ? "span-2" : ""}`}>
      {tagline && <p className="wow-kicker">{tagline}</p>}
      <h3 className={`display ${big ? "mt-2 text-3xl" : "text-xl"}`}>{name}</h3>
      <p className="mt-2 text-sm text-[var(--w-ink-soft)]">{body}</p>
      <Shot id={id} alt={alt} />
    </article>
  );
}

export function FeatureBento() {
  const c = features.cards;
  return (
    <div className="hm-bento">
      <Tile {...c.lab} big />
      <Tile {...c.tutor} big />
      <Tile {...c.lesson} big />
      <Tile {...c.build} big />
      <Tile {...c.review} />
      <Tile {...c.placement} />
      <Tile {...c.progress} />
      <Tile {...c.explain} />
    </div>
  );
}
