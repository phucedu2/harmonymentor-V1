// phuc-music Bước 3: chú giải thuật ngữ lần đầu xuất hiện trong bài.
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { TERMS, TermText, firstAppearances } from "../src/components/learning/TermText";

describe("chú giải thuật ngữ", () => {
  it("gán mỗi thuật ngữ cho khối đầu tiên nhắc tới nó", () => {
    const map = firstAppearances([
      { id: "B1", texts: ["Đếm nửa cung trên bàn phím."] },
      { id: "B2", texts: ["M3 rộng 4 nửa cung, P5 rộng 7 nửa cung."] },
      { id: "B3", texts: ["Lại nhắc M3 và m3."] },
    ]);
    expect([...map.get("B1")!]).toEqual(["half-step"]);
    expect([...map.get("B2")!].sort()).toEqual(["M3", "P5"]);
    expect([...map.get("B3")!]).toEqual(["m3"]);
  });

  it("phân biệt M3 và m3, không khớp giữa chữ", () => {
    const map = firstAppearances([{ id: "B", texts: ["Viết Am3 hoặc xm3 không phải ký hiệu quãng."] }]);
    expect(map.size).toBe(0);
  });

  it("chỉ chú giải lần đầu trong khối, lần sau để chữ thường", () => {
    const claimed = new Set<string>();
    const terms = new Set(["half-step"]);
    const first = renderToStaticMarkup(<TermText text="Một nửa cung rồi thêm nửa cung." terms={terms} claimed={claimed} />);
    const second = renderToStaticMarkup(<TermText text="Đoạn sau: nửa cung." terms={terms} claimed={claimed} />);
    expect(first.match(/<button/g)).toHaveLength(1);
    expect(first).toContain('aria-expanded="false"');
    expect(first).toContain("thêm nửa cung.");
    expect(second).not.toContain("<button");
  });

  it("thuật ngữ có âm thanh dùng mã quãng/ký hiệu để hỏi Music Engine, không chứa nốt viết cứng", () => {
    for (const term of TERMS) {
      if (!term.sound) continue;
      if (term.sound.kind === "interval") expect(term.sound.code).toMatch(/^[PMmAd]\d$/);
      else expect(term.sound.symbol).toMatch(/^C(m|dim|aug)?$/);
    }
  });
});
