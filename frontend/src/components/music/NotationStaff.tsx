import { useEffect, useId, useMemo, useState } from "react";
import { Accidental, Formatter, Renderer, Stave, StaveNote } from "vexflow";

type NotationGroup = { label?: string; notes: string[] };

type Props = {
  groups: NotationGroup[];
  clef?: "treble" | "bass";
  caption?: string;
};

type VexPitch = {
  key: string;
  accidental: string | null;
};

function toVexPitch(note: string): VexPitch | null {
  const match = note.match(/^([A-Ga-g])((?:#{1,2}|b{1,2}|x)?)(-?\d+)$/);
  if (!match) return null;
  return {
    key: `${match[1].toLowerCase()}/${match[3]}`,
    accidental: match[2] === "x" ? "##" : (match[2] || null),
  };
}

export default function NotationStaff({ groups, clef = "treble", caption }: Props) {
  const reactId = useId();
  const elementId = useMemo(() => `vf-${reactId.replace(/[^a-zA-Z0-9_-]/g, "")}`, [reactId]);
  const [renderErrors, setRenderErrors] = useState<Record<number, string>>({});

  useEffect(() => {
    const nextErrors: Record<number, string> = {};

    groups.forEach((group, groupIndex) => {
      const root = document.getElementById(`${elementId}-${groupIndex}`);
      if (!root) return;
      root.innerHTML = "";

      try {
        const parsed = group.notes.map(toVexPitch);
        if (!group.notes.length || parsed.some((item) => item === null)) {
          throw new Error("Dữ liệu nốt không hợp lệ.");
        }

        const valid = parsed as VexPitch[];
        const width = 220;
        const renderer = new Renderer(root, Renderer.Backends.SVG);
        renderer.resize(width, 135);
        const context = renderer.getContext();
        const stave = new Stave(8, 18, width - 16).addClef(clef);
        stave.setContext(context).draw();

        const staveNote = new StaveNote({
          clef,
          keys: valid.map((item) => item.key),
          duration: "q",
        });
        valid.forEach((item, noteIndex) => {
          if (item.accidental) staveNote.addModifier(new Accidental(item.accidental), noteIndex);
        });

        // Each lesson example is intentionally a short fragment rather than a complete measure.
        // FormatAndDraw uses a SOFT voice, so VexFlow does not reject an incomplete bar.
        Formatter.FormatAndDraw(context, stave, [staveNote]);
      } catch (error) {
        root.innerHTML = "";
        const message = error instanceof Error ? error.message : "Không thể render ký âm.";
        console.error("[NotationStaff] VexFlow render failed", { groupIndex, group, error });
        nextErrors[groupIndex] = message;
      }
    });

    setRenderErrors(nextErrors);
  }, [elementId, groups, clef]);

  if (!groups.length) {
    return <div className="notation-fallback" role="status">
      <b>Chưa có dữ liệu ký âm để hiển thị.</b>
    </div>;
  }

  return <div className="notation-shell">
    <div className="notation-examples">
      {groups.map((group, index) => <div className="notation-example" key={`${group.label ?? "example"}-${index}`}>
        <div id={`${elementId}-${index}`} className="notation-canvas" aria-label={group.label ?? `Ví dụ ký âm ${index + 1}`} />
        {renderErrors[index] && <div className="notation-fallback" role="status">
          <b>Ký âm tạm thời không hiển thị được.</b>
          <span>{renderErrors[index]}</span>
        </div>}
        <div className="notation-example-label">{group.label ?? group.notes.join("–")}</div>
      </div>)}
    </div>
    {caption && <p className="notation-caption">{caption}</p>}
  </div>;
}
