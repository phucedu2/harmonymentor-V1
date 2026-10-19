// Lớp gọi API dùng chung: gắn access token, đọc lỗi theo SRS 7.4, tự refresh một lần khi 401 (ADR-004).
export const API_BASE = "/api/v1";

export type User = {
  id: string;
  email: string;
  display_name: string;
  role: "learner" | "admin";
  preferred_instrument: "piano" | "guitar" | "drums" | null;
  goal_text: string | null;
};

export type AuthResponse = {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: User;
};

export class ApiRequestError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
    public retryable = false,
    public fields?: Record<string, string>,
    public retryAfterSeconds?: number,
  ) {
    super(message);
  }
}

// Token chỉ nằm trong bộ nhớ, không ghi localStorage: tải lại trang thì lấy lại qua cookie refresh.
let accessToken: string | null = null;
let refreshInFlight: Promise<AuthResponse | null> | null = null;
const sessionListeners = new Set<(session: AuthResponse | null) => void>();

export function onSessionChange(listener: (session: AuthResponse | null) => void) {
  sessionListeners.add(listener);
  return () => { sessionListeners.delete(listener); };
}

export function setSession(session: AuthResponse | null) {
  accessToken = session?.access_token ?? null;
  sessionListeners.forEach((listener) => listener(session));
}

async function parseError(res: Response): Promise<ApiRequestError> {
  let body: unknown = null;
  try { body = await res.json(); } catch { /* proxy trả HTML khi backend tắt */ }
  const retryAfter = Number(res.headers.get("Retry-After")) || undefined;
  const obj = (body ?? {}) as Record<string, unknown>;
  // Định dạng SRS 7.4: { error: { code, message, retryable, fields? } }
  const std = obj.error as Record<string, unknown> | undefined;
  if (std && typeof std === "object" && typeof std.code === "string") {
    return new ApiRequestError(std.code, String(std.message ?? std.code), res.status, Boolean(std.retryable),
      std.fields as Record<string, string> | undefined, retryAfter);
  }
  // Router cũ trả { detail: { code, message } } hoặc { detail: "..." } của FastAPI.
  const detail = obj.detail;
  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    const d = detail as Record<string, unknown>;
    return new ApiRequestError(String(d.code ?? `HTTP_${res.status}`), String(d.message ?? JSON.stringify(d)), res.status);
  }
  if (res.status >= 502) {
    return new ApiRequestError("SERVER_UNAVAILABLE", "Máy chủ chưa sẵn sàng. Hãy thử lại sau ít phút.", res.status, true);
  }
  return new ApiRequestError(`HTTP_${res.status}`, typeof detail === "string" ? detail : `Lỗi HTTP ${res.status}`, res.status);
}

async function rawFetch(path: string, init: RequestInit, withToken: boolean): Promise<Response> {
  const headers = new Headers(init.headers);
  if (init.body !== undefined && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (withToken && accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  try {
    return await fetch(API_BASE + path, { ...init, headers, credentials: "same-origin" });
  } catch {
    throw new ApiRequestError("NETWORK_ERROR", "Không kết nối được máy chủ. Kiểm tra mạng hoặc backend.", 0, true);
  }
}

/** Đổi cookie refresh lấy access token mới; các lời gọi đồng thời dùng chung một request
 *  vì refresh token bị xoay vòng, gọi hai lần song song sẽ làm lần sau thất bại. */
export function refreshSession(): Promise<AuthResponse | null> {
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      const res = await rawFetch("/auth/refresh", { method: "POST" }, false);
      if (!res.ok) { setSession(null); return null; }
      const session = (await res.json()) as AuthResponse;
      setSession(session);
      return session;
    })().finally(() => { refreshInFlight = null; });
  }
  return refreshInFlight;
}

type HttpOptions = { auth?: boolean };

export async function http<T>(path: string, init: RequestInit = {}, { auth = true }: HttpOptions = {}): Promise<T> {
  let res = await rawFetch(path, init, auth);
  if (res.status === 401 && auth && accessToken) {
    const session = await refreshSession().catch(() => null);
    if (session) res = await rawFetch(path, init, true);
  }
  if (!res.ok) throw await parseError(res);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const httpPost = <T,>(path: string, data?: unknown, options?: HttpOptions) =>
  http<T>(path, { method: "POST", body: data === undefined ? undefined : JSON.stringify(data) }, options);
