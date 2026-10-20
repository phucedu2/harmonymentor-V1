// Đổi tên Harmony Lab → Composition Lab theo SRS (quyết định M3). Trình soạn thật làm ở Giai đoạn F.
export default function CompositionLabPage() {
  return (
    <section>
      <h1 className="text-2xl font-bold">Sáng tác (Composition Lab)</h1>
      <p className="mt-1 text-muted">Nơi ghép vòng hợp âm, giai điệu và nhịp trống thành một đoạn nhạc ngắn.</p>
      <div className="mt-6 rounded-xl border border-dashed border-line bg-surface p-8 text-center">
        <p className="font-semibold">Sắp mở</p>
        <p className="mx-auto mt-2 max-w-md text-sm text-muted">
          Khu sáng tác sẽ mở sau khi bạn đã quen với hợp âm và vòng hợp âm. Trong lúc chờ, hãy học Bài 1–4 ở mục Học: đó chính là nguyên liệu để sáng tác.
        </p>
      </div>
    </section>
  );
}
