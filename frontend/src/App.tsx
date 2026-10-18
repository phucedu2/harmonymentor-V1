import { useState } from "react";
import DashboardPage from "./pages/Dashboard";
import HarmonyLabPage from "./pages/HarmonyLab";
import LearnPage from "./pages/Learn";
import PracticePage from "./pages/Practice";
import ProgressPage from "./pages/Progress";

type Page = "dashboard" | "learn" | "practice" | "lab" | "progress";
const NAV: { id: Page; label: string; short: string }[] = [
  { id: "dashboard", label: "Tổng quan", short: "Home" },
  { id: "learn", label: "Học lý thuyết", short: "Learn" },
  { id: "practice", label: "Luyện tập", short: "Practice" },
  { id: "lab", label: "Harmony Lab", short: "Create" },
  { id: "progress", label: "Tiến độ", short: "Progress" },
];

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">H</span><div><b>HarmonyMentor</b><small>v0.4.0-dev</small></div></div>
        <nav className="main-nav" aria-label="Điều hướng chính">
          {NAV.map((item) => <button key={item.id} className={page === item.id ? "active" : ""} onClick={() => setPage(item.id)}>
            <small>{item.short}</small><span>{item.label}</span></button>)}
        </nav>
        <div className="sidebar-note">Phase 1<br/>learning vertical slice</div>
      </aside>
      <main className="workspace">
        {page === "dashboard" && <DashboardPage onNavigate={(next) => setPage(next)} />}
        {page === "learn" && <LearnPage />}
        {page === "practice" && <PracticePage />}
        {page === "lab" && <HarmonyLabPage />}
        {page === "progress" && <ProgressPage />}
        <footer>Phase 1: Learn → checkpoint → quiz → review · Music Engine deterministic · AI chưa nằm trên critical path.</footer>
      </main>
    </div>
  );
}
