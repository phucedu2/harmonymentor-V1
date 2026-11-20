// ADR-017 (góp ý thầy G1/G3): mỗi câu trả lời của AI Tutor hiện nhãn nguồn; câu "không biết" có nút mở bài gợi ý,
// câu hướng dẫn có nút mở đúng trang. Nhãn do máy chủ đặt, giao diện chỉ hiển thị.
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { ChatReply } from "../src/api";
import { AssistantBubble } from "../src/components/learning/FloatingTutorDrawer";

const base: ChatReply = {
  message_id: 1, session_id: "s", reply: "x", citations: [], engine_claims: [], verified: false, verified_label: null,
  intent: "concept", hint_level: 0, status: "ok", suggested_actions: [], fallback_reason: null, retrieval_method: null,
  quota_remaining_today: 10,
};
const html = (data: Partial<ChatReply>) =>
  renderToStaticMarkup(<AssistantBubble data={{ ...base, ...data }} onCite={() => {}} onOpen={() => {}} busy={false} />);

describe("nhãn nguồn AI Tutor", () => {
  it("luồng B không biết: nhãn + nút mở bài gợi ý", () => {
    const out = html({ flow: "B", source_label: "Không biết", suggested_lesson: { lesson_id: "L02", title: "Âm giai trưởng" } });
    expect(out).toContain("Không biết");
    expect(out).toContain("Mở bài L02: Âm giai trưởng");
  });

  it("luồng D: nút mở trang, không hiện mục hướng dẫn như trích dẫn bài học", () => {
    const out = html({
      flow: "D", source_label: "Hướng dẫn sử dụng", intent: "help", help_page: { path: "/app/tien-do", title: "Tiến độ" },
      citations: [{ lesson_id: "HELP", block_id: "H09", title: "Xem tiến độ", lesson_title: "Hướng dẫn · Tiến độ" }],
    });
    expect(out).toContain("Mở trang Tiến độ");
    expect(out).not.toContain("[HELP]");
  });

  it("luồng A: trích dẫn bài, không có nút mở bài gợi ý", () => {
    const out = html({
      flow: "A", source_label: "Từ bài học", suggested_lesson: { lesson_id: "L02", title: "t" },
      citations: [{ lesson_id: "L02", block_id: "L02-B05", title: "Giải mã maj7", lesson_title: "L02" }],
    });
    expect(out).toContain("Từ bài học");
    expect(out).toContain("[L02] Giải mã maj7");
    expect(out).not.toContain("Mở bài L02");
  });

  it("câu trả lời cũ không có trường flow vẫn hiển thị như trước", () => {
    expect(html({})).not.toContain("Mở bài");
  });
});
