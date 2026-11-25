import { beforeEach, describe, expect, it } from "vitest";
import { activateTutorScope, clearTutorLesson, patchTutorContext, readTutorContext, releaseTutorMusic, resetTutorLesson, selectTutorMusic, updateTutorMusic } from "./tutorContext";
const route = "/app/hoc?bai=L01";
beforeEach(() => resetTutorLesson(route, "L01"));
describe("tutor music context", () => {
 it("does not infer a key from a chord root", () => {
   selectTutorMusic(route, Symbol(), {selected_root:"A", selected_chord:"Am"});
   expect(readTutorContext(route).selected_key).toBeUndefined();
 });
 it("keeps explicit key separate when chord changes", () => {
   patchTutorContext(route, {selected_key:"A", mode:"natural_minor"});
   selectTutorMusic(route, Symbol(), {selected_root:"D", selected_chord:"Dm"});
   expect(readTutorContext(route)).toMatchObject({selected_key:"A", mode:"natural_minor", selected_chord:"Dm"});
 });
 it("only updates the last interacted explorer", () => {
   const a=Symbol(), b=Symbol();
   selectTutorMusic(route,a,{selected_chord:"Am"}); selectTutorMusic(route,b,{selected_chord:"Dm"});
   updateTutorMusic(route,a,{selected_chord:"C"});
   expect(readTutorContext(route).selected_chord).toBe("Dm");
   releaseTutorMusic(route,a); expect(readTutorContext(route).selected_chord).toBe("Dm");
 });
 it("clears stale chord while new root data loads", () => {
   const a=Symbol(); selectTutorMusic(route,a,{selected_root:"A",selected_chord:"Am"});
   updateTutorMusic(route,a,{selected_root:"D"});
   expect(readTutorContext(route).selected_chord).toBeUndefined();
 });
 it("never returns a previous page context", () => {
   patchTutorContext(route,{selected_key:"A",mode:"natural_minor"});
   expect(readTutorContext("/app/hoc?bai=L02")).toEqual({});
   activateTutorScope("/app/practice"); activateTutorScope(route);
   expect(readTutorContext(route)).toEqual({});
 });
 it("resets lesson and step context", () => {
   patchTutorContext(route,{selected_key:"A",mode:"natural_minor"}); resetTutorLesson(route,"L01");
   expect(readTutorContext(route)).toEqual({lesson_id:"L01"});
 });
 it("old cleanup cannot clear a newly mounted route", () => {
   resetTutorLesson("/app/hoc?bai=L02","L02"); clearTutorLesson(route);
   expect(readTutorContext("/app/hoc?bai=L02")).toEqual({lesson_id:"L02"});
 });
 it("an already captured request stays unchanged after selection changes", () => {
   selectTutorMusic(route,Symbol(),{selected_chord:"Am"}); const captured={...readTutorContext(route)};
   selectTutorMusic(route,Symbol(),{selected_chord:"Dm"}); expect(captured.selected_chord).toBe("Am");
 });
});
