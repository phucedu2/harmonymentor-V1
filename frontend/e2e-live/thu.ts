import { expect } from "@playwright/test";

// Đọc thư thử từ Mailpit (ADR-040, A12) qua API HTTP của nó: http://127.0.0.1:8025/api/v1/...
export const MAILPIT = process.env.MAILPIT_URL || "http://127.0.0.1:8025";

type Summary = { ID: string; Subject: string; To: { Address: string }[] };

/** Chờ thư có tiêu đề `subject` gửi tới `to` (thư gửi trong BackgroundTasks nên tới sau vài trăm ms). */
export async function thuMoiNhat(to: string, subject: string, atLeast = 1): Promise<{ text: string; html: string; id: string }> {
  let found: Summary | undefined;
  await expect.poll(async () => {
    const res = await fetch(`${MAILPIT}/api/v1/search?query=${encodeURIComponent(`to:"${to}" subject:"${subject}"`)}`);
    const body = (await res.json()) as { messages: Summary[] };
    found = body.messages[0]; // Mailpit trả thư mới nhất trước
    return body.messages.length;
  }, { timeout: 15_000, message: `chờ thư "${subject}" tới ${to}` }).toBeGreaterThanOrEqual(atLeast);
  const res = await fetch(`${MAILPIT}/api/v1/message/${found!.ID}`);
  const msg = (await res.json()) as { Text: string; HTML: string };
  return { text: msg.Text, html: msg.HTML, id: found!.ID };
}

/** Lấy liên kết đặt lại / xác minh (token sau dấu #) trong bản chữ thuần của thư. */
export function lienKet(text: string, path: string): string {
  const match = text.match(new RegExp(`https?://\\S+${path}#token=[A-Za-z0-9_-]+`));
  if (!match) throw new Error(`Không thấy liên kết ${path} trong thư`);
  return match[0];
}
