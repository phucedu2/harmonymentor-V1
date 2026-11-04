import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";
// Tone.js nặng (~235 kB) nên chỉ tải khi người dùng bật âm thanh, để trang chủ mở nhanh.
const loadEngine = () => import("../../../audio/AudioEngine").then((m) => m.audioEngine);

// Âm thanh trang chủ: TẮT mặc định, chỉ bật sau khi người dùng bấm (chính sách autoplay của trình duyệt).
// Lựa chọn được nhớ trong localStorage; bọc try/catch vì có trình duyệt chặn storage.
const KEY = "hm-trang-chu-am-thanh";

function readSaved(): boolean {
  try { return localStorage.getItem(KEY) === "bat"; } catch { return false; }
}
function save(on: boolean) {
  try { localStorage.setItem(KEY, on ? "bat" : "tat"); } catch { /* không lưu được thì thôi */ }
}

type Sound = {
  on: boolean;
  toggle: () => Promise<void>;
  /** Phát một nốt hoặc hợp âm ngắn nếu đang bật tiếng; tự giới hạn tần suất để cuộn nhanh không bị ồn. */
  play: (notes: string[], duration?: string) => void;
};

const SoundContext = createContext<Sound>({ on: false, toggle: async () => {}, play: () => {} });

export function SoundProvider({ children }: { children: ReactNode }) {
  // Đã từng bật ở lần trước vẫn phải chờ một cú bấm mới phát được, nên trạng thái "bật" chỉ là mong muốn.
  const [on, setOn] = useState(readSaved);
  const last = useRef(0);

  const toggle = useCallback(async () => {
    const next = !on;
    if (next) {
      const engine = await loadEngine();
      await engine.ensureStarted();
      void engine.playChord(["C4", "E4", "G4", "C5"], "8n");
    }
    setOn(next);
    save(next);
  }, [on]);

  const play = useCallback((notes: string[], duration = "8n") => {
    if (!on || notes.length === 0) return;
    const now = performance.now();
    if (now - last.current < 90) return;
    last.current = now;
    void loadEngine().then((engine) => (notes.length === 1 ? engine.playNote(notes[0], duration) : engine.playChord(notes, duration)));
  }, [on]);

  const value = useMemo(() => ({ on, toggle, play }), [on, toggle, play]);
  return <SoundContext.Provider value={value}>{children}</SoundContext.Provider>;
}

export const useSound = () => useContext(SoundContext);

export function SoundToggle({ className = "" }: { className?: string }) {
  const { on, toggle } = useSound();
  return (
    <button
      type="button"
      onClick={() => void toggle()}
      aria-pressed={on}
      className={`wow-sound inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium ${className}`}
    >
      <span aria-hidden="true" className="wow-eq" data-on={on}>
        <i /><i /><i /><i />
      </span>
      {on ? "Đang bật âm thanh" : "Bật âm thanh"}
    </button>
  );
}
