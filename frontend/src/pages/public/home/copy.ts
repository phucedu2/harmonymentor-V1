// Toàn bộ chữ của các mục mới ở trang chủ nằm ở đây để nhóm sửa nội dung mà không phải đụng vào code.
// Quy tắc: chỉ hứa những gì bài học và bài tập thật sự dạy; mọi CON SỐ (số bài, số câu, thời lượng)
// đều tính từ API /lessons, không viết tay ở file này.

export const roadmap = {
  kicker: "Lộ trình",
  title: "Bốn chặng, đi từ con số 0",
  lead: "Mỗi chặng mở khóa thứ bạn làm được ở chặng sau. Học xong cả bốn chặng, bạn tự viết được vòng hợp âm của mình.",
  /** Chặng cuối của đường đi; không phải một module trong API nên viết tay ở đây. */
  finish: {
    name: "Tự sáng tác",
    body: "Mang vòng hợp âm vừa học vào Harmony Lab, nghe nó thành một bài có Intro, Verse, Chorus.",
  },
  /** Nhãn phụ dưới mỗi chặng. {n} được thay bằng số thật. */
  lessonsLabel: "{n} bài",
  exercisesLabel: "{n} câu hỏi",
  minutesLabel: "khoảng {n} phút",
  outcomePrefix: "Xong chặng này bạn sẽ",
};

export const outcomes = {
  kicker: "Học gì và làm được gì",
  title: "Hiểu, nghe được, rồi tự tạo ra",
  lead: "Ba việc đi cùng nhau trong mọi bài học, không học lý thuyết suông.",
  columns: [
    {
      id: "hieu",
      name: "Hiểu",
      body: "Lý thuyết chia thành từng phần ngắn, đọc vài phút là xong một ý: tên nốt, nửa cung, quãng, âm giai, hợp âm ba và hợp âm bảy, chức năng hòa âm, vòng hợp âm Pop và Jazz.",
      items: [
        "Đọc được ký hiệu quãng M3, m3, P5, d5 và gọi tên quãng giữa hai nốt bất kỳ",
        "Gọi tên bậc của một hợp âm trong giọng bằng số La Mã",
        "Phân biệt chức năng T – PD – D trong một vòng hợp âm ngắn",
      ],
    },
    {
      id: "nghe",
      name: "Nghe và chơi",
      body: "Mọi hợp âm đều bấm được trên piano ảo và nghe được ngay. Nốt nào hiện sáng là do bộ máy nhạc lý của web tính ra, không phải ảnh chụp sẵn.",
      items: [
        "Dựng đúng hợp âm trưởng, thứ, giảm và hợp âm bảy trên bàn phím",
        "Nghe một vòng hợp âm rồi nói nó đang căng hay đã về nhà",
        "Chơi shell voicing ba nốt root – 3 – 7 của một ii–V–I",
      ],
    },
    {
      id: "tao",
      name: "Tạo ra",
      body: "Harmony Lab cho bạn viết vòng hợp âm của riêng mình, rồi nghe nó thành bài có đoạn, có nhạc nền thật.",
      items: [
        "Tự viết một vòng ii–V–I và nghe nó với nhạc nền bossa",
        "Nghe vòng hợp âm của mình thành bài có Intro, Verse, Chorus",
        "Đổi phong cách và mức năng lượng để so hai bản phối của cùng một vòng",
      ],
    },
  ],
  /** Ghi chú trung thực: Harmony Lab chưa xuất file nhạc. */
  note: "Harmony Lab phát ngay trong trình duyệt; phần xuất file nhạc chưa làm.",
};

export const features = {
  kicker: "Tính năng",
  title: "Những thứ bạn dùng mỗi ngày",
  lead: "Tất cả đều đang chạy trong khu học, không có mục nào là sắp ra mắt.",
  cards: {
    lab: {
      id: "harmony-lab",
      name: "Harmony Lab",
      tagline: "Xưởng sáng tác của bạn",
      body: "Viết vòng 4 đến 8 ô hợp âm, chấm độ lạ của vòng, rồi nghe nó ở chế độ Vòng lặp hoặc dựng thành bài có Intro, Verse, Chorus, Bridge. Chín phong cách nhạc nền, sáu kênh nhạc cụ chỉnh được âm lượng.",
      alt: "Màn hình Harmony Lab: dải ô hợp âm, danh sách phong cách nhạc nền và các thanh chỉnh âm lượng",
    },
    tutor: {
      id: "ai-tutor",
      name: "AI Tutor",
      tagline: "Hỏi bằng tiếng Việt, có dẫn nguồn",
      body: "Khung chat nổi, kéo thả được, đi theo bạn trong suốt bài học. Mỗi câu trả lời dẫn về đúng phần bài học đã dạy điều đó, và mọi tên nốt, quãng, hợp âm trong câu trả lời đều được máy chủ kiểm lại bằng bộ máy nhạc lý.",
      alt: "Khung chat AI Tutor trả lời một câu hỏi nhạc lý kèm liên kết trích dẫn về bài học",
    },
    lesson: {
      id: "hoc-va-lam",
      name: "Học xong là làm ngay",
      body: "Hết một ý lý thuyết là tới câu hỏi: trắc nghiệm, dựng hợp âm trên piano, nhớ lại, câu theo ngữ cảnh, câu áp dụng, và cả câu tự luận chấm theo bảng tiêu chí.",
      alt: "Một câu trắc nghiệm trong bài học với bốn lựa chọn",
    },
    build: {
      id: "dung-hop-am",
      name: "Chấm bằng bộ máy nhạc lý",
      body: "Bấm hợp âm trên piano ảo, máy chấm theo đúng tên nốt chứ không chỉ theo phím, nên B♯ và C được phân biệt.",
      alt: "Câu hỏi dựng hợp âm trên bàn phím piano ảo",
    },
    review: {
      id: "on-tap",
      name: "Ôn tập đúng lúc",
      body: "Thẻ ghi nhớ tự hẹn ngày ôn theo 5 hộp 1–2–4–8–16 ngày: nhớ tốt thì giãn ra, quên thì gặp lại sớm.",
      alt: "Màn hình ôn tập thẻ ghi nhớ",
    },
    placement: {
      id: "kiem-tra-dau-vao",
      name: "Kiểm tra đầu vào",
      body: "Biết ít nhiều rồi thì làm bài kiểm tra ngắn, web bỏ qua phần bạn đã vững và bắt đầu từ chỗ vừa sức.",
      alt: "Màn hình bài kiểm tra đầu vào",
    },
    progress: {
      id: "tien-do",
      name: "Tiến độ theo kỹ năng",
      body: "Từng kỹ năng có mức thành thạo riêng, nhìn là biết nên ôn lại chỗ nào.",
      alt: "Màn hình tiến độ với mức thành thạo của từng kỹ năng",
    },
    explain: {
      id: "loi-giai",
      name: "Sai hai lần là có lời giải",
      body: "Không chỉ báo Sai: web chỉ ra nốt nào lệch và vì sao, ví dụ bạn dùng quãng 7 trưởng thay cho quãng 7 thứ.",
      alt: "Lời giải hiện ra sau khi trả lời sai",
    },
  },
};

export const curriculum = {
  kicker: "Chương trình học",
  title: "Chín bài, xem trước tất cả",
  lead: "Rê chuột vào một bài để xem đầy đủ mục tiêu của bài đó.",
  draftBadge: "Đang soạn",
  openLabel: "Xem bài",
};

export const footer = {
  about: "HarmonyMentor dạy nhạc lý cho người bắt đầu từ con số 0: học lý thuyết ngắn, làm bài ngay, hỏi AI Tutor khi bí, rồi tự viết vòng hợp âm trong Harmony Lab.",
  // Nhóm tự sửa thành họ tên đầy đủ.
  team: ["Trần Thiên Phúc", "Thắng", "Đạt"],
  github: "https://github.com/phucedu2/harmonymentor-V1",
  email: "HarmonyMentor@gmail.com",
  note: "Đồ án sinh viên",
};
