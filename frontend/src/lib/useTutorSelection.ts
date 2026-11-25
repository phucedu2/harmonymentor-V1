import { useEffect, useRef } from "react";
import { browserTutorScope, selectTutorMusic, updateTutorMusic, releaseTutorMusic } from "./tutorContext";

// Only the last interacted explorer owns the chord hint. Rendering a whole
// lesson must not make the last mounted widget silently win.
export function useTutorSelection(root: string, chord?: string) {
  const token = useRef(Symbol("explorer"));
  const route = browserTutorScope();
  const selection = { selected_root: root, selected_chord: chord };
  useEffect(() => { updateTutorMusic(route, token.current, selection); }, [route, root, chord]);
  useEffect(() => { const id = token.current; return () => releaseTutorMusic(route, id); }, [route]);
  const activate = () => selectTutorMusic(route, token.current, selection);
  return { onPointerDownCapture: activate, onFocusCapture: activate };
}
