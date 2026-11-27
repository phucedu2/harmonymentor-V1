// Vite nhập file chữ thô bằng hậu tố ?raw (danh sách mật khẩu phổ biến, ADR-040).
declare module "*?raw" {
  const content: string;
  export default content;
}
