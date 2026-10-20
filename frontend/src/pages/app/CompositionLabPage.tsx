// Đổi tên Harmony Lab → Composition Lab theo SRS (quyết định M3). Trình soạn thật làm ở Giai đoạn F.
export default function CompositionLabPage() {
  return (
    <section>
      <h1 className="text-2xl font-bold">Composition Lab</h1>
      <p className="mt-1 text-muted">Nơi ghép vòng hợp âm, giai điệu và nhịp trống thành một đoạn nhạc ngắn.</p>
      <div className="mt-6 rounded-xl border border-dashed border-line bg-surface p-8 text-center">
        <p className="font-semibold">Chưa mở</p>
        <p className="mx-auto mt-2 max-w-md text-sm text-muted">
          Composition Lab đang được xây ở Giai đoạn F (18/11 – 24/11). Trong lúc chờ, bạn có thể học và luyện tập hợp âm ở mục Học.
        </p>
      </div>
    </section>
  );
}
