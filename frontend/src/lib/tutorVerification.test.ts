import { describe, it, expect } from "vitest";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { AssistantBubble } from "../components/learning/FloatingTutorDrawer";
import type { ChatReply } from "../api";
const base = {message_id:1,session_id:"test",reply:"Trong giọng C trưởng, Am là vi.",citations:[],engine_claims:[{tool:"get_roman_numeral",args:{key:"C",chord:"Am"},claimed:"vi",engine:"vi",status:"verified",origin:"scanned"}],verified:true,verified_label:"Đã kiểm bằng Music Engine",intent:"concept",hint_level:0,status:"ok",suggested_actions:[],fallback_reason:null,retrieval_method:null,quota_remaining_today:30} as ChatReply;
const html = (data:ChatReply) => renderToStaticMarkup(createElement(AssistantBubble,{data,onCite:()=>{},onOpen:()=>{},busy:false}));
describe("scoped verification badge",()=>{
 it("renders scoped wording even with legacy label",()=>{const out=html(base); expect(out).toContain("Đã kiểm tra dữ kiện nhạc lý hiển thị"); expect(out).toContain("không xác minh toàn bộ"); expect(out).not.toContain("✓ Đã kiểm bằng Music Engine");});
 it("rejects label without server verification",()=>expect(html({...base,verified:false})).not.toContain("✓"));
 it("rejects no claims",()=>expect(html({...base,engine_claims:[]})).not.toContain("✓"));
 it.each(["contradicted","unsupported"] as const)("rejects %s",status=>expect(html({...base,engine_claims:[{...base.engine_claims[0],status}]})).not.toContain("✓"));
});
