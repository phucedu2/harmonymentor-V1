import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useAuth } from "../../auth/AuthProvider";
import { authApi } from "../../auth/authApi";
import type { User } from "../../lib/http";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { PageLoader } from "../../components/ui/PageLoader";
import { TextField } from "../../components/ui/TextField";
import { SecurityCard, VerifyEmailBanner } from "./profile/SecurityCard";
import { ANIMALS, ANIMAL_NAME, AnimalAvatar, animalFor, type Animal } from "../../components/ui/AnimalAvatar";

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
  const [avatar, setAvatar] = useState<Animal | null>(null);

  useEffect(() => {
    if (me.data) { setName(me.data.display_name); setInstrument(me.data.preferred_instrument); setAvatar(animalFor(me.data)); }
  }, [me.data]);

  const save = useMutation({
    mutationFn: () => authApi.updateMe({ display_name: name.trim(), preferred_instrument: instrument, ...(avatar ? { avatar } : {}) }),
    onSuccess: (user) => { setUser(user); me.refetch(); },
  });

  if (me.isPending) return <PageLoader label="Đang tải hồ sơ…" />;
  if (me.isError) {
    return <Alert tone="danger" action={<Button variant="ghost" onClick={() => me.refetch()}>Thử lại</Button>}>Chưa tải được hồ sơ. {me.error.message}</Alert>;
  }

  const current = animalFor(me.data);
  const dirty = name.trim() !== me.data.display_name || instrument !== me.data.preferred_instrument || (avatar !== null && avatar !== current);
  const submit = (e: FormEvent) => { e.preventDefault(); if (name.trim()) save.mutate(); };

  return (
    <section className="max-w-xl">
      <h1 className="text-2xl font-bold">Hồ sơ</h1>
      <p className="mt-1 text-muted">Thông tin này chỉ bạn xem được.</p>
      {me.data.email_verified === false && <VerifyEmailBanner />}

      <div className="mt-6 flex items-center gap-4">
        <AnimalAvatar animal={avatar ?? current} size={72} />
        <div><p className="text-lg font-semibold">{me.data.display_name}</p><p className="text-sm text-muted">{me.data.email}</p></div>
      </div>

      <dl className="mt-6 grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 rounded-xl border border-line bg-surface p-5 text-sm">
        <dt className="text-muted">Email</dt><dd className="font-medium">{me.data.email}</dd>
        <dt className="text-muted">Vai trò</dt><dd className="font-medium">{me.data.role === "admin" ? "Quản trị viên" : "Người học"}</dd>
      </dl>

      <form onSubmit={submit} className="mt-6 space-y-5 rounded-xl border border-line bg-surface p-5">
        {save.isSuccess && !dirty && <Alert tone="success">Đã lưu hồ sơ.</Alert>}
        {save.isError && <Alert tone="danger">Chưa lưu được. {save.error.message}</Alert>}
        <fieldset>
          <legend className="mb-2 text-sm font-medium">Ảnh đại diện</legend>
          <p className="mb-3 text-sm text-muted">Chọn một con vật. Ảnh hiện ở góc phải trên cùng mọi trang.</p>
          <div className="grid grid-cols-4 gap-2 sm:grid-cols-6">
            {ANIMALS.map((a) => (
              <label key={a} title={ANIMAL_NAME[a]} className={`grid cursor-pointer place-items-center gap-1 rounded-xl border p-2 text-xs has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-primary ${avatar === a ? "border-primary bg-primary-soft font-semibold text-primary-strong" : "border-line"}`}>
                <input type="radio" name="avatar" value={a} className="sr-only" checked={avatar === a} onChange={() => setAvatar(a)} />
                <AnimalAvatar animal={a} size={44} decorative />
                <span>{avatar === a && <span aria-hidden="true">✓ </span>}{ANIMAL_NAME[a]}</span>
              </label>
            ))}
          </div>
        </fieldset>
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

      <SecurityCard user={me.data} onChanged={() => me.refetch()} />
    </section>
  );
}
