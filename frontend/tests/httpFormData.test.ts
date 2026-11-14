// ADR-025: tải tệp lên dùng FormData; http() không được ép Content-Type JSON, nếu không boundary bị mất và máy chủ không đọc được tệp.
import { afterEach, describe, expect, it, vi } from "vitest";
import { http } from "../src/lib/http";

afterEach(() => vi.unstubAllGlobals());

describe("http() với FormData", () => {
  it("không đặt Content-Type cho FormData, vẫn đặt JSON cho body chuỗi", async () => {
    const seen: Headers[] = [];
    vi.stubGlobal("fetch", vi.fn(async (_url: string, init: RequestInit) => {
      seen.push(new Headers(init.headers));
      return new Response("{}", { status: 200, headers: { "Content-Type": "application/json" } });
    }));
    const form = new FormData();
    form.append("a", "b");
    await http("/x", { method: "POST", body: form });
    await http("/x", { method: "POST", body: "{}" });
    expect(seen[0].has("Content-Type")).toBe(false);
    expect(seen[1].get("Content-Type")).toBe("application/json");
  });
});
