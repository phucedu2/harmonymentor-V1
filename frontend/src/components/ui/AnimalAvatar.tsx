import type { ReactNode } from "react";

// Ảnh đại diện con vật (ADR-029, 10A): vẽ bằng SVG ngay trong mã, không tải ảnh, không gửi gì ra ngoài.
// Khóa con vật trùng với backend/app/auth/avatars.py. Màu nền cố định (là "ảnh"), đọc rõ ở cả giao diện sáng và tối.

export const ANIMALS = ["meo", "cao", "gau", "cu", "chim_canh_cut", "tho", "gau_truc", "ech", "ho", "koala", "su_tu", "ca_voi"] as const;
export type Animal = (typeof ANIMALS)[number];

export const ANIMAL_NAME: Record<Animal, string> = {
  meo: "Mèo", cao: "Cáo", gau: "Gấu", cu: "Cú", chim_canh_cut: "Chim cánh cụt", tho: "Thỏ",
  gau_truc: "Gấu trúc", ech: "Ếch", ho: "Hổ", koala: "Koala", su_tu: "Sư tử", ca_voi: "Cá voi",
};

const INK = "#2B2238";
const eyes = (y = 33, dx = 7, r = 2.6) => <><circle cx={32 - dx} cy={y} r={r} fill={INK} /><circle cx={32 + dx} cy={y} r={r} fill={INK} /></>;
const smile = (y = 41, w = 4) => <path d={`M${32 - w} ${y} Q32 ${y + 3.5} ${32 + w} ${y}`} stroke={INK} strokeWidth="1.8" fill="none" strokeLinecap="round" />;

const ART: Record<Animal, { bg: string; draw: ReactNode }> = {
  meo: { bg: "#FDE2C8", draw: <>
    <path d="M14 26 L17 9 L29 19 Z" fill="#F4A261" /><path d="M50 26 L47 9 L35 19 Z" fill="#F4A261" />
    <path d="M17.5 22 L19 13.5 L25 18.5 Z" fill="#F7B8C4" /><path d="M46.5 22 L45 13.5 L39 18.5 Z" fill="#F7B8C4" />
    <ellipse cx="32" cy="36" rx="19" ry="16" fill="#F4A261" />
    <path d="M26 22 L28 28 M32 21 L32 27 M38 22 L36 28" stroke="#D9803F" strokeWidth="2" strokeLinecap="round" />
    {eyes(34)}<path d="M30 39.5 L34 39.5 L32 42 Z" fill="#E76F8A" />
    <path d="M32 42 Q29.5 45 27 43.5 M32 42 Q34.5 45 37 43.5" stroke={INK} strokeWidth="1.5" fill="none" strokeLinecap="round" />
    <path d="M12 38 L22 39.5 M12 43 L22 42 M52 38 L42 39.5 M52 43 L42 42" stroke={INK} strokeWidth="1.1" strokeLinecap="round" opacity="0.55" />
  </> },
  cao: { bg: "#FFE7D1", draw: <>
    <path d="M12 14 L24 22 L18 32 Z" fill="#E76F2E" /><path d="M52 14 L40 22 L46 32 Z" fill="#E76F2E" />
    <path d="M14.5 18 L21 22.5 L18 27 Z" fill="#5A3A2E" /><path d="M49.5 18 L43 22.5 L46 27 Z" fill="#5A3A2E" />
    <path d="M14 28 Q32 14 50 28 L36 50 Q32 54 28 50 Z" fill="#E76F2E" />
    <path d="M18 34 Q26 36 30 46 L28 50 Q31 53 32 53 Q33 53 36 50 L34 46 Q38 36 46 34 Q40 46 32 53 Q24 46 18 34 Z" fill="#FFF6EC" />
    {eyes(33, 7, 2.4)}<ellipse cx="32" cy="50" rx="2.6" ry="2" fill={INK} />
  </> },
  gau: { bg: "#EADBC8", draw: <>
    <circle cx="16" cy="18" r="7" fill="#8B5E3C" /><circle cx="48" cy="18" r="7" fill="#8B5E3C" />
    <circle cx="16" cy="18" r="3.5" fill="#C99A6E" /><circle cx="48" cy="18" r="3.5" fill="#C99A6E" />
    <circle cx="32" cy="35" r="19" fill="#8B5E3C" />
    <ellipse cx="32" cy="42" rx="9" ry="7" fill="#D9B48F" />
    {eyes(32, 8)}<ellipse cx="32" cy="39" rx="3.2" ry="2.3" fill={INK} />{smile(43, 3)}
  </> },
  cu: { bg: "#E7DDF7", draw: <>
    <path d="M14 14 L22 24 L14 26 Z" fill="#7A5C45" /><path d="M50 14 L42 24 L50 26 Z" fill="#7A5C45" />
    <ellipse cx="32" cy="37" rx="19" ry="18" fill="#9C7A5B" />
    <path d="M24 46 Q32 56 40 46 Q32 50 24 46 Z" fill="#C9A882" />
    <circle cx="24" cy="33" r="8" fill="#FFF8EC" /><circle cx="40" cy="33" r="8" fill="#FFF8EC" />
    <circle cx="24" cy="33" r="4" fill={INK} /><circle cx="40" cy="33" r="4" fill={INK} />
    <circle cx="25.3" cy="31.7" r="1.3" fill="#fff" /><circle cx="41.3" cy="31.7" r="1.3" fill="#fff" />
    <path d="M29.5 39 L34.5 39 L32 44 Z" fill="#F2A541" />
  </> },
  chim_canh_cut: { bg: "#D6ECF7", draw: <>
    <ellipse cx="32" cy="36" rx="19" ry="20" fill="#2F3A4A" />
    <path d="M32 26 Q22 18 18 30 Q16 44 32 52 Q48 44 46 30 Q42 18 32 26 Z" fill="#FFFFFF" />
    {eyes(33, 6.5, 2.4)}
    <path d="M27.5 38 Q32 36 36.5 38 L32 43 Z" fill="#F2A541" />
    <ellipse cx="22" cy="40" rx="2.6" ry="1.6" fill="#F7B8C4" opacity="0.8" /><ellipse cx="42" cy="40" rx="2.6" ry="1.6" fill="#F7B8C4" opacity="0.8" />
  </> },
  tho: { bg: "#FBE3EC", draw: <>
    <ellipse cx="24" cy="15" rx="5" ry="13" fill="#F4F1F6" /><ellipse cx="40" cy="15" rx="5" ry="13" fill="#F4F1F6" />
    <ellipse cx="24" cy="16" rx="2.4" ry="9" fill="#F7B8C4" /><ellipse cx="40" cy="16" rx="2.4" ry="9" fill="#F7B8C4" />
    <ellipse cx="32" cy="39" rx="18" ry="16" fill="#F4F1F6" />
    {eyes(37, 7)}<path d="M30 42 L34 42 L32 44.5 Z" fill="#E76F8A" />
    <path d="M32 44.5 L32 47 M32 47 Q29.5 49 28 47.5 M32 47 Q34.5 49 36 47.5" stroke={INK} strokeWidth="1.4" fill="none" strokeLinecap="round" />
  </> },
  gau_truc: { bg: "#DDF0DC", draw: <>
    <circle cx="16" cy="19" r="7" fill={INK} /><circle cx="48" cy="19" r="7" fill={INK} />
    <circle cx="32" cy="35" r="19" fill="#FFFFFF" />
    <ellipse cx="24" cy="34" rx="5" ry="6.5" transform="rotate(-25 24 34)" fill={INK} />
    <ellipse cx="40" cy="34" rx="5" ry="6.5" transform="rotate(25 40 34)" fill={INK} />
    <circle cx="24.5" cy="33.5" r="1.8" fill="#fff" /><circle cx="39.5" cy="33.5" r="1.8" fill="#fff" />
    <ellipse cx="32" cy="42" rx="3" ry="2.2" fill={INK} />{smile(45, 3)}
  </> },
  ech: { bg: "#E3F4D7", draw: <>
    <circle cx="21" cy="22" r="8" fill="#5DB35A" /><circle cx="43" cy="22" r="8" fill="#5DB35A" />
    <circle cx="21" cy="22" r="5" fill="#fff" /><circle cx="43" cy="22" r="5" fill="#fff" />
    <circle cx="21.5" cy="22.5" r="2.6" fill={INK} /><circle cx="43.5" cy="22.5" r="2.6" fill={INK} />
    <ellipse cx="32" cy="38" rx="21" ry="15" fill="#5DB35A" />
    <path d="M20 40 Q32 50 44 40" stroke={INK} strokeWidth="2" fill="none" strokeLinecap="round" />
    <ellipse cx="18" cy="37" rx="3" ry="2" fill="#F7B8C4" opacity="0.8" /><ellipse cx="46" cy="37" rx="3" ry="2" fill="#F7B8C4" opacity="0.8" />
  </> },
  ho: { bg: "#FFF0C9", draw: <>
    <circle cx="16" cy="19" r="6.5" fill="#F08A24" /><circle cx="48" cy="19" r="6.5" fill="#F08A24" />
    <circle cx="16" cy="19" r="3" fill="#FFF6EC" /><circle cx="48" cy="19" r="3" fill="#FFF6EC" />
    <circle cx="32" cy="35" r="19" fill="#F08A24" />
    <path d="M32 17 L32 24 M26 18 L27.5 24 M38 18 L36.5 24 M13.5 32 L20 33 M14 38 L20 37.5 M50.5 32 L44 33 M50 38 L44 37.5" stroke={INK} strokeWidth="2.2" strokeLinecap="round" />
    <ellipse cx="32" cy="43" rx="9" ry="6.5" fill="#FFF6EC" />
    {eyes(32, 7.5)}<path d="M29.5 39.5 L34.5 39.5 L32 42.5 Z" fill="#E76F8A" />{smile(44, 3)}
  </> },
  koala: { bg: "#E2E8EF", draw: <>
    <circle cx="14" cy="24" r="10" fill="#9AA5B1" /><circle cx="50" cy="24" r="10" fill="#9AA5B1" />
    <circle cx="14" cy="24" r="5.5" fill="#E9D5DC" /><circle cx="50" cy="24" r="5.5" fill="#E9D5DC" />
    <circle cx="32" cy="36" r="18" fill="#9AA5B1" />
    {eyes(32, 8, 2.4)}<ellipse cx="32" cy="40" rx="4.5" ry="6" fill={INK} />
    <ellipse cx="22" cy="42" rx="2.6" ry="1.6" fill="#F7B8C4" opacity="0.7" /><ellipse cx="42" cy="42" rx="2.6" ry="1.6" fill="#F7B8C4" opacity="0.7" />
  </> },
  su_tu: { bg: "#FFE9B8", draw: <>
    <circle cx="32" cy="34" r="25" fill="#C8691C" />
    <path d="M32 9 L36 14 L42 11 L43 17 L49 17 L47 23 L53 26 L48 30 L52 35 L46 37 L48 43 L42 43 L40 49 L35 45 L32 51 L29 45 L24 49 L22 43 L16 43 L18 37 L12 35 L16 30 L11 26 L17 23 L15 17 L21 17 L22 11 L28 14 Z" fill="#B85A12" opacity="0.9" />
    <circle cx="32" cy="34" r="16" fill="#F6B94A" />
    {eyes(32, 6.5)}<ellipse cx="32" cy="41" rx="6.5" ry="4.5" fill="#FFE2A6" />
    <path d="M30 38.5 L34 38.5 L32 41 Z" fill={INK} />{smile(43, 3)}
  </> },
  ca_voi: { bg: "#D3E9FB", draw: <>
    <path d="M30 14 Q30 8 26 6 M30 14 Q30 8 34 6 M30 14 L30 9" stroke="#5AA9E6" strokeWidth="2" fill="none" strokeLinecap="round" />
    <path d="M10 36 Q10 18 30 18 Q50 18 52 32 L58 26 Q60 34 56 40 Q58 44 58 48 L52 43 Q48 52 30 52 Q10 52 10 36 Z" fill="#3D7FC1" />
    <path d="M13 40 Q20 50 34 49 Q46 48 50 42 Q36 46 13 40 Z" fill="#CFE6FA" />
    <circle cx="23" cy="32" r="2.6" fill={INK} /><circle cx="23.8" cy="31.2" r="0.9" fill="#fff" />
    <path d="M18 38 Q22 40.5 26 38.5" stroke={INK} strokeWidth="1.6" fill="none" strokeLinecap="round" />
  </> },
};

export function isAnimal(value: unknown): value is Animal {
  return typeof value === "string" && (ANIMALS as readonly string[]).includes(value);
}

/** Máy chủ luôn trả `avatar`; phòng khi gọi máy chủ cũ thì suy một con cố định từ id (không đổi giữa các lần tải). */
export function animalFor(user: { id: string; avatar?: string | null } | null | undefined): Animal {
  if (user && isAnimal(user.avatar)) return user.avatar;
  let h = 0;
  for (const ch of user?.id ?? "") h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return ANIMALS[h % ANIMALS.length];
}

export function AnimalAvatar({ animal, size = 36, className = "", decorative = false }: {
  animal: Animal; size?: number; className?: string; decorative?: boolean;
}) {
  const art = ART[animal];
  return <svg viewBox="0 0 64 64" width={size} height={size} className={`shrink-0 rounded-full ${className}`}
    {...(decorative ? { "aria-hidden": true } : { role: "img", "aria-label": `Ảnh đại diện: ${ANIMAL_NAME[animal]}` })}>
    <clipPath id={`av-${animal}`}><circle cx="32" cy="32" r="32" /></clipPath>
    <g clipPath={`url(#av-${animal})`}><rect width="64" height="64" fill={art.bg} />{art.draw}</g>
  </svg>;
}
