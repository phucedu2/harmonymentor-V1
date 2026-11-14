import { useState } from "react";
import AiDraftTab from "../../components/admin/AiDraftTab";
import LessonsTab from "../../components/admin/LessonsTab";
import StatsTab from "../../components/admin/StatsTab";
import UsersTab from "../../components/admin/UsersTab";
import { useAuth } from "../../auth/AuthProvider";
import { ToggleGroup } from "../../components/ui/Page";

type Tab = "stats" | "lessons" | "ai" | "users";

// Chỉ hiện được sau RequireAdmin (ADR-023). Quyền thật nằm ở backend: mọi /admin/* kiểm vai trò.
export default function AdminHomePage() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("stats");
  return (
    <section className="grid gap-4">
      <div>
        <h1 className="text-2xl font-bold">Quản trị</h1>
        <p className="mt-1 text-muted">Đăng nhập với quyền Quản trị viên: {user?.email}</p>
      </div>
      <ToggleGroup label="Mục quản trị" value={tab} onChange={setTab}
        options={[{ value: "stats", label: "Thống kê" }, { value: "lessons", label: "Bài học" }, { value: "ai", label: "AI soạn bài" }, { value: "users", label: "Người dùng" }]} />
      {tab === "stats" ? <StatsTab /> : tab === "lessons" ? <LessonsTab /> : tab === "ai" ? <AiDraftTab /> : <UsersTab />}
    </section>
  );
}
