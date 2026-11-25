import type { ChatContext } from "../api";

const EMPTY: ChatContext = Object.freeze({});
let scope = "";
let snapshot: ChatContext = EMPTY;
let owner: symbol | undefined;
const listeners = new Set<() => void>();
export const browserTutorScope = () => window.location.pathname + window.location.search;
export function subscribeTutorContext(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener); }; }
export function readTutorContext(route: string): ChatContext { return route === scope ? snapshot : EMPTY; }
function notify() { listeners.forEach((fn) => fn()); }
export function activateTutorScope(route: string) {
  if (scope !== route) { scope = route; snapshot = EMPTY; owner = undefined; notify(); }
}
export function patchTutorContext(route: string, patch: ChatContext) {
  activateTutorScope(route); snapshot = { ...snapshot, ...patch }; notify();
}
export function selectTutorMusic(route: string, token: symbol, selection: ChatContext) {
  activateTutorScope(route); owner = token;
  snapshot = { ...snapshot, selected_root: undefined, selected_chord: undefined, ...selection }; notify();
}
export function updateTutorMusic(route: string, token: symbol, selection: ChatContext) {
  if (scope === route && owner === token) selectTutorMusic(route, token, selection);
}
export function releaseTutorMusic(route: string, token: symbol) {
  if (scope === route && owner === token) {
    owner = undefined; snapshot = { ...snapshot, selected_root: undefined, selected_chord: undefined }; notify();
  }
}
export function resetTutorLesson(route: string, lesson?: string) {
  scope = route; owner = undefined; snapshot = lesson ? { lesson_id: lesson } : EMPTY; notify();
}

export function clearTutorLesson(route: string) {
  if (route === scope) resetTutorLesson(route);
}
