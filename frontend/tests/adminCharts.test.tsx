// ADR-023: biểu đồ quản trị là SVG thuần, có nhãn đọc được và không vỡ khi thiếu dữ liệu.
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { BarList, LineChart } from "../src/components/admin/Charts";

describe("biểu đồ quản trị", () => {
  it("LineChart có aria-label tổng lượt và vẽ 3 đường", () => {
    const data = [{ date: "2026-11-01", attempts: 4, correct: 3, reviews: 1 }, { date: "2026-11-02", attempts: 0, correct: 0, reviews: 2 }];
    const out = renderToStaticMarkup(<LineChart data={data} />);
    expect(out).toContain("tổng 7 lượt");
    expect(out.match(/<path /g)).toHaveLength(3);
  });

  it("LineChart không lỗi khi toàn số 0", () => {
    const out = renderToStaticMarkup(<LineChart data={[{ date: "2026-11-01", attempts: 0, correct: 0, reviews: 0 }]} />);
    expect(out).not.toContain("NaN");
  });

  it("BarList giới hạn thanh trong 100% và báo khi rỗng", () => {
    expect(renderToStaticMarkup(<BarList label="x" rows={[]} />)).toContain("Chưa có dữ liệu");
    const out = renderToStaticMarkup(<BarList label="x" rows={[{ label: "A", value: 9, max: 3, note: "n" }]} />);
    expect(out).toContain('width="100"');
  });
});
