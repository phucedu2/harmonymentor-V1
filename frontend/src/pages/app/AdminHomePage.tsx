import { useAuth } from "../../auth/AuthProvider";

// Chỉ hiện được sau RequireAdmin. Các màn quản trị (người dùng, nội dung, nhập YAML, cấu hình AI) làm ở Giai đoạn F.
export default function AdminHomePage() {
  const { user } = useAuth();
  return (
    <section>
      <h1 className="text-2xl font-bold">Quản trị</h1>
      <p className="mt-1 text-muted">Đăng nhập với quyền Quản trị viên: {user?.email}</p>
      <div className="mt-6 rounded-xl border border-dashed border-line bg-surface p-8 text-center">
        <p className="font-semibold">Chưa có công cụ quản trị</p>
        <p className="mx-auto mt-2 max-w-md text-sm text-muted">Quản lý người dùng, nội dung và cấu hình AI được xây ở Giai đoạn F.</p>
      </div>
    </section>
  );
}
