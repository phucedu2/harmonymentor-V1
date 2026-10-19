import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useAuth } from "../../auth/AuthProvider";
import { authApi } from "../../auth/authApi";
import type { User } from "../../lib/http";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { PageLoader } from "../../components/ui/PageLoader";
import { TextField } from "../../components/ui/TextField";

const INSTRUMENTS: { value: NonNullable<User["preferred_instrument"]>; label: string }[] = [
  { value: "piano", label: "Piano" },
  { value: "guitar", label: "Guitar" },
  { value: "drums", label: "Trống" },
];

// FR-AUTH-06 (xem hồ sơ), FR-AUTH-07 (sửa), FR-AUTH-10 (nhạc cụ ưa thích).
export default function ProfilePage() {
  const { setUser } = useAuth();
  const me = useQuery({ queryKey: ["me"], queryFn: authApi.me });
  const [name, setName] = useState("");
  const [instrument, setInstrument] = useState<User["preferred_instrument"]>(null);

  useEffect(() => {
    if (me.data) { setName(me.data.display_name); setInstrument(me.data.preferred_instrument); }
  }, [me.data]);

  const save = useMutation({
    mutationFn: () => authApi.updateMe({ display_name: name.trim(), preferred_instrument: instrument }),
    onSuccess: (user) => { setUser(user); me.refetch(); },
  });

  if (me.isPending) return <PageLoader label="Đang tải hồ sơ…" />;
  if (me.isError) {
    return <Alert tone="danger" action={<Button variant="ghost" onClick={() => me.refetch()}>Thử lại</Button>}>Chưa tải được hồ sơ. {me.error.message}</Alert>;
  }

  const dirty = name.trim() !== me.data.display_name || instrument !== me.data.preferred_instrument;
  const submit = (e: FormEvent) => { e.preventDefault(); if (name.trim()) save.mutate(); };

  return (
    <section className="max-w-xl">
      <h1 className="text-2xl font-bold">Hồ sơ</h1>
      <p className="mt-1 text-muted">Thông tin này chỉ bạn xem được.</p>

      <dl className="mt-6 grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 rounded-xl border border-line bg-surface p-5 text-sm">
        <dt className="text-muted">Email</dt><dd className="font-medium">{me.data.email}</dd>
        <dt className="text-muted">Vai trò</dt><dd className="font-medium">{me.data.role === "admin" ? "Quản trị viên" : "Người học"}</dd>
      </dl>

      <form onSubmit={submit} className="mt-6 space-y-5 rounded-xl border border-line bg-surface p-5">
        {save.isSuccess && !dirty && <Alert tone="success">Đã lưu hồ sơ.</Alert>}
        {save.isError && <Alert tone="danger">Chưa lưu được. {save.error.message}</Alert>}
        <TextField label="Tên hiển thị" value={name} onChange={(e) => setName(e.target.value)} error={name.trim() ? undefined : "Tên hiển thị không được để trống."} />
        <fieldset>
          <legend className="mb-2 text-sm font-medium">Nhạc cụ ưa thích</legend>
          <p className="mb-3 text-sm text-muted">Bài tập sẽ ưu tiên hiện nhạc cụ này khi có thể.</p>
          <div className="flex flex-wrap gap-2">
            {INSTRUMENTS.map((opt) => (
              <label key={opt.value} className={`cursor-pointer rounded-lg border px-4 py-2 text-sm has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-primary ${instrument === opt.value ? "border-primary bg-primary-soft font-semibold text-primary-strong" : "border-line"}`}>
                <input type="radio" name="instrument" value={opt.value} className="sr-only" checked={instrument === opt.value} onChange={() => setInstrument(opt.value)} />
                {instrument === opt.value && <span aria-hidden="true">✓ </span>}{opt.label}
              </label>
            ))}
          </div>
        </fieldset>
        <Button type="submit" loading={save.isPending} disabled={!dirty || !name.trim()}>Lưu thay đổi</Button>
      </form>
    </section>
  );
}
