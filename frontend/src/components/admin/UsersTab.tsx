import { useEffect, useState } from "react";
import { api, type AdminUser } from "../../api";
import { useAuth } from "../../auth/AuthProvider";
import { Button } from "../ui/Button";
import { Badge, Card } from "../ui/Page";

export default function UsersTab() {
  const { user: me } = useAuth();
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<AdminUser[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = (query: string) => api.adminUsers(query).then((r) => { setRows(r.items); setError(null); }).catch(() => setError("Chưa tải được danh sách."));
  useEffect(() => { load(""); }, []);
  const toggle = async (u: AdminUser) => {
    if (u.is_active && !window.confirm(`Khóa tài khoản ${u.email}? Người này sẽ không đăng nhập được nữa.`)) return;
    try { await api.adminSetActive(u.id, !u.is_active); await load(q); }
    catch (e) { setError((e as { message?: string }).message ?? "Không đổi được trạng thái."); }
  };
  return <div className="grid gap-3">
    <form onSubmit={(e) => { e.preventDefault(); load(q); }} className="flex gap-2">
      <label htmlFor="user-q" className="sr-only">Tìm người dùng</label>
      <input id="user-q" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Tìm theo email hoặc tên"
        className="min-h-11 flex-1 rounded-lg border border-line bg-surface px-3" />
      <Button type="submit" variant="secondary">Tìm</Button>
    </form>
    {error && <p role="alert" className="text-danger">{error}</p>}
    {!rows ? <p className="text-muted">Đang tải…</p> : rows.length === 0 ? <p className="text-muted">Không có tài khoản nào.</p>
      : <ul className="grid gap-2">{rows.map((u) => <li key={u.id}><Card className="flex flex-wrap items-center justify-between gap-2 p-3">
        <div>
          <p className="font-semibold">{u.display_name || u.email} {u.role === "admin" && <Badge>Quản trị</Badge>} {!u.is_active && <Badge tone="warning">Đã khóa</Badge>}</p>
          <p className="text-sm text-muted">{u.email} · {u.lessons_completed} bài xong · {u.attempts} lượt làm · {u.last_activity ? `gần nhất ${u.last_activity.slice(0, 10)}` : "chưa hoạt động"}</p>
        </div>
        {u.id !== me?.id && <Button variant="secondary" onClick={() => toggle(u)}>{u.is_active ? "Khóa" : "Mở khóa"}</Button>}
      </Card></li>)}</ul>}
  </div>;
}
