import VirtualPiano from "./components/music/VirtualPiano";

// Compatibility wrapper for the legacy Practice page.
// Phase 2 now uses the same interactive piano component as Learn.
export default function Piano({ good = [], bad = [] }: { good?: string[]; bad?: string[] }) {
  return <VirtualPiano
    highlightedPitchClasses={good}
    incorrectPitchClasses={bad}
    showLabels={false}
    startMidi={48}
    endMidi={72}
  />;
}
