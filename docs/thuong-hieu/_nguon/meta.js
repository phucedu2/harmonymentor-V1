// Nội dung chữ: lãnh thổ sáng tạo, câu chuyện, điểm số của từng phác thảo.
// Điểm 1–5 là đánh giá của người thiết kế (chưa thử với người dùng thật), xem ghi chú trong BRAND_NOTE.md.

const CRITERIA = ['Độc đáo', 'Ý nghĩa piano/nhạc lý', 'Tò mò + thông minh', 'Nhận ra ở 16px', 'Đẹp khi đứng một mình', 'Hợp người mới học', 'Chuyển động được'];

const INTRO = {
  why: [
    'Logo âm nhạc và edtech nhàm vì cùng lấy một kho hình: khóa Sol, nốt móc đơn, tai nghe, sóng âm, mũ tốt nghiệp, bóng đèn. Những hình đó nói "đây là âm nhạc" hoặc "đây là học tập", nhưng không nói gì về riêng sản phẩm này, nên mắt người xem lướt qua.',
    'Piano thì thường bị vẽ thành một dải phím nằm ngang. Trong khi đó, cây đàn còn nhiều thứ có hình rất rõ mà gần như chưa ai dùng: nhóm 2 và 3 phím đen (cách người học tìm nốt C), độ dài dây giảm theo đúng một công thức, cái búa nỉ, cần phím như cái bập bênh, cuộn giấy đục lỗ của đàn tự chơi, và những con số 1–5 thầy giáo ghi lên bản nhạc.',
    'Hướng đi của bộ này: mỗi logo phải lấy hình từ một sự thật có thật của cây đàn, và sự thật đó giải thích được trong một câu. Phần "dị" nằm ở chỗ người xem nhận ra sự thật ấy sau vài giây.',
  ],
};

const TERRITORIES = [
  { code: 'A', name: 'Mã nhóm 2–3 phím đen', ref: 'Peter Saville, bìa "Power, Corruption & Lies" của New Order (1983): chữ được mã hóa thành các ô màu, ai biết mã mới đọc được.',
    story: 'Phím đen trên đàn luôn chia thành nhóm 2 rồi nhóm 3. Đây là "mã" đầu tiên người mới học phải đọc được, vì nốt C nằm ngay bên trái nhóm 2.', odd: 'Chữ được dựng từ đúng vị trí phím đen thật, không vẽ phím trang trí.', hidden: 'Nhóm 2 phím có 2 nét như chữ H, nhóm 3 phím có 3 nét như chữ m: một quãng tám tự viết ra "Hm".', risk: 'Dễ trượt về dải phím clip-art nếu vẽ thêm phím trắng.' },
  { code: 'B', name: 'Dây đàn và độ dài dây', ref: 'Iannis Xenakis, "Metastaseis" (1954) và Philips Pavilion (1958): những đường thẳng của dây đàn dây tạo thành mặt cong.',
    story: 'Dây đàn càng ngắn thì càng cao. Cứ lên một quãng tám, dây ngắn còn một nửa. Đường cong hông đàn grand chính là đồ thị của quy luật đó.', odd: 'Hình dáng logo được tính bằng công thức 2^(-n/12), không vẽ tay.', hidden: 'Hai chân chữ H dài theo tỉ lệ 2:1, đúng tỉ lệ quãng tám.', risk: 'Nét dây mảnh nên dễ mất ở cỡ nhỏ.' },
  { code: 'C', name: 'Cuộn giấy pianola', ref: 'Conlon Nancarrow, "Studies for Player Piano" (1948–1992): ông tự tay đục lỗ cuộn giấy để đàn tự chơi những bản người không chơi nổi.',
    story: 'Pianola là cây đàn tự chơi theo cuộn giấy đục lỗ, tổ tiên của nhạc "lập trình". Mỗi lỗ là một nốt, chiều dài lỗ là thời gian giữ nốt.', odd: 'Logo là một đoạn cuộn có thể chơi thành nhạc thật.', hidden: 'Gợi AI rất nhẹ: máy đọc "bài" rồi chơi, nhưng không cần robot hay mạch điện.', risk: 'Lưới lỗ dễ giống "gam pixel" đã có, cần lỗ dài ngắn khác nhau.' },
  { code: 'D', name: 'Khoảng cách phím của hợp âm', ref: 'Cornelius Cardew, "Treatise" (1963–67): bản nhạc đồ họa 193 trang, nhạc được viết bằng hình học.',
    story: 'Một hợp âm trưởng là "nhảy 4 phím rồi nhảy 3 phím". Đổi thành 3 rồi 4 là ra hợp âm thứ. Người mới nhớ hợp âm bằng khoảng cách tay, không phải bằng tên nốt.', odd: 'Chữ cái có độ rộng không đều, vì độ rộng chính là quãng.', hidden: 'Chữ m có hai vòm rộng 4 và 3: một hợp âm trưởng nằm trong chữ Mentor.', risk: 'Người xem cần được kể một lần mới thấy lớp nghĩa.' },
  { code: 'E', name: 'Cơ cấu action, búa, bàn đạp', ref: 'Wassily Kandinsky, "Point and Line to Plane" (Bauhaus, 1926): điểm, đường, mặt là ba chất liệu gốc của hình.',
    story: 'Bên trong đàn, phím là một cái bập bênh. Ấn nhẹ đầu trước, đầu sau bẩy búa nỉ bay lên gõ vào dây. Một lực nhỏ của ngón tay thành một âm thanh lớn.', odd: 'Vẽ phần bên trong đàn mà người chơi không bao giờ thấy.', hidden: 'Cần bẩy là ẩn dụ cho người thầy: một gợi ý nhỏ đúng chỗ giúp người học đi xa.', risk: 'Hình cơ khí dễ thành sơ đồ kỹ thuật khô khan.' },
  { code: 'F', name: 'Ngón tay đánh số 1–5', ref: 'Sagmeister & Walsh, nhận diện Casa da Música (Porto, 2007): một hình gốc, mỗi lần dùng lại biến đổi theo nội dung.',
    story: 'Thầy dạy piano ghi các số nhỏ 1–5 lên bản nhạc để chỉ ngón nào bấm phím nào. Đó là "chữ viết tay" của người thầy, thứ gần nhất với một gia sư.', odd: 'Dùng ký hiệu sư phạm thay cho ký hiệu âm nhạc.', hidden: 'Ngón 1-3-5 cùng bấm là một hợp âm ba, tư thế đầu tiên mọi người học piano được dạy.', risk: 'Chữ số đứng riêng dễ thành huy hiệu chung chung.' },
];

// kind: main (dùng được ngay), bold (táo bạo kiểu triển lãm), cut (bị loại)
const LOGOS = {
  'hai-ba': { name: 'Hai–Ba', t: 'A', kind: 'main', s: [5, 5, 5, 4, 5, 4, 4],
    story: 'Năm phím đen của một quãng tám, đặt đúng vị trí thật. Nhóm 2 phím có thêm thanh đồng thau thành chữ H, nhóm 3 phím nối đầu thành chữ m. Cây đàn tự viết tên mình: "Hm".',
    twist: 'Wordmark: độ đậm 13 chữ đi theo 13 phím liên tiếp từ C đến C (phím đen = nét đậm, phím trắng = nét mảnh). Ai để ý sẽ đọc được một quãng tám trong chữ.',
    motion: 'Lần lượt "bấm" 5 phím đen. Chơi 5 phím đen theo thứ tự nào cũng nghe hay, vì đó là gam ngũ cung.' },
  'do-giua': { name: 'Đô giữa', t: 'A', kind: 'main', s: [3, 5, 4, 5, 4, 5, 4],
    story: 'Ba phím trắng C, D, E và nhóm 2 phím đen. Chấm đồng thau nằm trên phím C, ngay bên trái nhóm 2: bài học đầu tiên của mọi người học piano là "tìm nốt Đô". Gia sư chỉ cho bạn chỗ bắt đầu.',
    twist: 'Wordmark: chữ "o" đầu tiên màu đồng thau, tròn như chấm Đô trong biểu tượng, nhắc lại đúng một điểm nhấn.',
    motion: 'Chấm đồng thau rơi xuống đúng phím C như một ngón tay đặt vào.' },
  'quang-tam': { name: 'H quãng tám', t: 'B', kind: 'main', s: [4, 5, 4, 4, 4, 3, 4],
    story: 'Hai sợi dây làm hai chân chữ H, chân trái dài gấp đôi chân phải. Tỉ lệ 2:1 là quãng tám, hòa âm đơn giản nhất. Thanh ngang đồng thau là cái búa gõ vào cả hai.',
    twist: 'Wordmark đứng trên một sợi dây, chấm đồng thau đặt đúng giữa dây: chạm nhẹ vào điểm giữa sẽ nghe âm bồi quãng tám (harmonic, cùng gốc với chữ Harmony).',
    motion: 'Búa bật lên, hai dây rung.' },
  'm-43': { name: 'm 4:3', t: 'D', kind: 'main', s: [4, 5, 5, 4, 4, 3, 5],
    story: 'Chữ m của Mentor có hai vòm không đều: vòm trái rộng 4 nửa cung, vòm phải rộng 3. Đó là công thức hợp âm trưởng. Hàng chấm bên dưới là 8 phím, ba chấm đồng thau là ba nốt của hợp âm.',
    twist: 'Wordmark: chữ m trong "Harmony" được vẽ lại với hai vòm 4:3, các chữ còn lại giữ nguyên Be Vietnam Pro.',
    motion: 'Hai vòm đổi thành 3:4 rồi trở lại. Người xem thấy hợp âm trưởng thành hợp âm thứ.' },
  'hai-bua': { name: 'Hai búa', t: 'E', kind: 'main', s: [4, 4, 3, 4, 4, 3, 4],
    story: 'Hai cái búa đàn quay đầu nỉ vào nhau thành chữ H. Ở giữa là một sợi dây đồng: âm thanh sinh ra ở đúng chỗ hai búa gặp nhau, như hòa âm sinh ra khi hai nốt gặp nhau.',
    twist: 'Wordmark: dấu cách giữa hai chữ là sợi dây đồng thau. "Harmony" và "Mentor" là hai búa cùng gõ một dây.',
    motion: 'Hai búa lùi ra rồi bật vào chạm dây.' },
  'can-bay': { name: 'Cần bẩy', t: 'E', kind: 'main', s: [4, 5, 4, 3, 4, 4, 5],
    story: 'Mặt cắt một phím đàn: phím là cái bập bênh trên điểm tựa đồng thau. Ngón tay ấn đầu trước, đầu sau bẩy búa lên chạm dây. Gợi ý nhỏ, kết quả lớn: đó là việc của người thầy.',
    twist: 'Wordmark: "Harmony" hạ thấp, "Mentor" nâng lên, điểm tựa nằm ở dấu cách, như chữ đang ngồi trên bập bênh.',
    motion: 'Ngón tay ấn xuống, cần bẩy nghiêng, búa bay lên chạm dây.' },
  'ban-tay': { name: 'Bàn tay 1–5', t: 'F', kind: 'main', s: [3, 4, 4, 3, 4, 5, 4],
    story: 'Năm ngón tay đánh số 1–5 đặt trên phím. Ngón 1, 3, 5 màu đậm đang bấm: tư thế hợp âm ba đầu tiên của mọi người học piano.',
    twist: 'Wordmark: số ngón 1-3-5 nhỏ màu đồng ghi phía trên chữ, như thầy ghi số ngón lên bản nhạc.',
    motion: 'Ba ngón 1-3-5 cùng bấm xuống.' },
  'lo-duc': { name: 'H lỗ đục', t: 'C', kind: 'main', s: [4, 4, 4, 5, 4, 3, 4], tile: true,
    story: 'Một ô cuộn giấy pianola. Hai lỗ dài là nốt C và C cao giữ suốt (quãng tám), hai lỗ ngắn ở cột E và G chen vào giữa: khoảnh khắc đó cả bốn lỗ cùng mở và đàn chơi hợp âm Đô trưởng. Các lỗ xếp thành chữ H.',
    twist: 'Wordmark: chữ máy IBM Plex Mono như các cột lỗ; hai chữ "o" thành lỗ đục dọc.',
    motion: 'Cuộn giấy chạy lên, chữ H trôi vào khung.' },
  'duong-cong': { name: 'Đường cong dây', t: 'B', kind: 'bold', s: [5, 5, 5, 3, 5, 3, 4], notes: true,
    story: '13 dây của một quãng tám, mỗi dây ngắn hơn dây trước 2^(-1/12). Dây cuối dài đúng một nửa dây đầu. Đường bao các đầu dây chính là hông đàn grand: hình dáng cây đàn là một đồ thị toán học. Dây tô theo 12 màu nốt của app.',
    twist: 'Wordmark: mỗi chữ nhỏ hơn chữ trước một nửa cung. 13 chữ là 12 bước, nên chữ "r" cuối cao đúng một nửa chữ "H" đầu.',
    motion: 'Từng dây được căng từ trái sang phải.' },
  'cuon-tien-trinh': { name: 'Cuộn I–IV–V–I', t: 'C', kind: 'bold', s: [5, 5, 4, 2, 4, 2, 5], notes: true, tile: true, fullTile: true,
    story: 'Một đoạn cuộn pianola chơi được thật: bốn hàng lỗ là bốn hợp âm I–IV–V–I của Đô trưởng (C–E–G, F–A–C, D–G–B, C–E–G–C), tiến trình đầu tiên trong mọi giáo trình hòa âm. Mỗi lỗ tô màu của nốt đó.',
    twist: 'Wordmark: dấu cách thay bằng ba lỗ đục của hợp âm Đô trưởng.',
    motion: 'Cuộn giấy chạy qua thanh đọc như đang chơi.' },
  'op-art': { name: 'Op-art 2–3', t: 'A', kind: 'bold', s: [5, 4, 4, 2, 5, 2, 4],
    story: 'Hai quãng tám phím đen lặp thành 10 hàng, nén ở mép và giãn ở giữa để mặt phẳng phồng thành khối cầu, theo cách Bridget Riley làm trong "Movement in Squares" (1961). Hàng xanh là hàng giữa.',
    twist: 'Wordmark: chữ Fraunces đậm nhất bị cắt bởi các khe theo đúng nhịp 2–3 phím đen.',
    motion: 'Các hàng lần lượt hiện ra từ trên xuống.' },
  'kandinsky': { name: 'Điểm, đường, mặt', t: 'E', kind: 'bold', s: [4, 4, 3, 3, 4, 3, 4],
    story: 'Bài học Bauhaus của Kandinsky áp vào cây đàn: điểm là búa nỉ (tròn, xanh gỉ), đường là dây đàn, mặt là phím (tam giác đồng thau), thanh đen là phím đen, ô đỏ nhỏ là miếng nỉ đỏ thật trong đàn.',
    twist: 'Wordmark: "Harmony" mảnh như sợi dây, "Mentor" đậm như cái búa.',
    motion: 'Búa bật vào dây.' },
  // Phác thảo bị loại
  'ma-vach': { name: 'Mã vạch quãng tám', t: 'A', kind: 'cut', s: [2, 4, 2, 3, 3, 3, 3], why: 'Vẫn là một dải phím nằm ngang, thêm cảm giác mã vạch siêu thị. Gần danh sách cấm.' },
  'hm-chung': { name: 'Hm chung cọc', t: 'A', kind: 'cut', s: [3, 2, 3, 4, 4, 3, 3], why: 'Cho H và m dùng chung một nét thì chỉ còn 4 phím đen, sai sự thật "2 rồi 3". Logo dạy nhạc mà dạy sai là không được.' },
  'xenakis': { name: 'Mặt kẻ Xenakis', t: 'B', kind: 'cut', s: [5, 3, 3, 1, 4, 1, 4], why: 'Đẹp kiểu triển lãm nhưng ở 16px thành dấu X. Người mới không nhận ra dây đàn.' },
  'nap-dan': { name: 'Nắp đàn mở', t: 'B', kind: 'cut', s: [2, 3, 2, 3, 3, 4, 3], why: 'Thành bóng đàn grand quen thuộc, kiểu clip-art.' },
  'don-huyen': { name: 'Đơn huyền 6:4:3', t: 'B', kind: 'cut', s: [2, 4, 2, 4, 3, 3, 3], why: 'Ba dây theo tỉ lệ thật nhưng nhìn như biểu đồ cột hoặc thanh âm lượng (gần "sóng âm").' },
  'cuon-hm': { name: 'Cuộn chữ HM', t: 'C', kind: 'cut', s: [3, 3, 2, 3, 3, 3, 4], why: 'Lưới lỗ đều nhau thành chữ pixel, quá gần "gam pixel" đã có.' },
  'thanh-doc': { name: 'Thanh đọc', t: 'C', kind: 'cut', s: [2, 2, 1, 3, 2, 2, 3], why: 'Một hàng chấm không kể được gì, nhìn như thanh trượt.' },
  'ban-tay-8': { name: 'Tay quãng tám 1⌒5', t: 'D', kind: 'cut', s: [2, 3, 2, 3, 3, 3, 3], why: 'Vòm với hai con số đọc thành cầu vồng hoặc cây cầu.' },
  'treatise': { name: 'Treatise', t: 'D', kind: 'cut', s: [4, 2, 2, 2, 3, 1, 3], why: 'Quá trừu tượng, không còn dấu vết piano.' },
  'ba-ban-dap': { name: 'Ba bàn đạp', t: 'E', kind: 'cut', s: [3, 4, 2, 3, 3, 2, 3], why: 'Ba bàn đạp treo dưới hộp đọc thành âm thoa hoặc đinh ba. Âm thoa nằm trong danh sách cấm.' },
  'bua-day': { name: 'Búa chạm dây', t: 'E', kind: 'cut', s: [2, 3, 2, 4, 2, 3, 3], why: 'Hình tròn trên que nhìn như kẹo mút hoặc đinh ghim.' },
  'so-ngon': { name: 'Số ngón trên phím', t: 'F', kind: 'cut', s: [1, 3, 1, 4, 2, 4, 2], why: 'Một phím và số 1: giống huy hiệu, không có lớp nghĩa ẩn.' },
  'mot-ba-nam': { name: '1·3·5', t: 'F', kind: 'cut', s: [2, 3, 2, 3, 2, 3, 3], why: 'Ý "hợp âm 1-3-5" quá gần bản C-E-G xếp chồng đã có; chữ số không có tính hình.' },
  'vong-but': { name: 'Vòng bút của thầy', t: 'F', kind: 'cut', s: [1, 2, 1, 4, 2, 3, 2], why: 'Số 3 trong vòng tròn là huy hiệu chung chung, dùng cho app nào cũng được.' },
};

const TOP3 = [
  { id: 'hai-ba', rank: 1, why: 'Điểm cao nhất (32/35). Lớp nghĩa mạnh nhất và đúng tuyệt đối: một quãng tám phím đen tự viết ra "Hm". Hình chỉ có thanh thẳng nên in một màu, khắc, thêu đều được. Người mới nhìn thấy phím đàn ngay, người học lâu thấy thêm chữ.' },
  { id: 'do-giua', rank: 2, why: 'Dễ hiểu nhất cho người mới và rõ nhất ở 16px. Câu chuyện "tìm nốt Đô" chính là bài đầu tiên của app, nên logo cũng là lời chào. Kém hơn Hai–Ba ở độ độc đáo vì ai cũng nhận ra phím đàn.' },
  { id: 'm-43', rank: 3, why: 'Thông minh nhất khi chuyển động: trưởng đổi thành thứ ngay trên logo, hợp làm màn hình chờ khi AI Tutor đang trả lời. Đứng sau vì khi đứng yên, người xem cần được kể một lần mới thấy 4:3.' },
];

// Nhóm chốt ngày 30/10/2026: dùng "Cuộn I–IV–V–I" làm logo chính thức.
const CHOSEN = 'cuon-tien-trinh';
// Các bản được dựng bộ đầy đủ (Top 3 đề xuất + bản nhóm chọn)
const KIT = [...TOP3.map((t) => t.id), CHOSEN];

module.exports = { CRITERIA, INTRO, TERRITORIES, LOGOS, TOP3, CHOSEN, KIT };
