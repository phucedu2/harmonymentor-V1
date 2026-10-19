import { ButtonLink } from "../components/ui/Button";

export default function NotFoundPage() {
  return (
    <section className="mx-auto max-w-lg px-4 py-20 text-center">
      <p className="font-mono text-sm text-muted">404</p>
      <h1 className="mt-2 text-2xl font-bold">Không tìm thấy trang</h1>
      <p className="mt-3 text-muted">Đường dẫn có thể đã đổi hoặc gõ nhầm.</p>
      <ButtonLink to="/" className="mt-6">Về trang chủ</ButtonLink>
    </section>
  );
}
