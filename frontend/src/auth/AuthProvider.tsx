import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { hasSessionHint, onSessionChange, refreshSession, setSession, type AuthResponse, type User } from "../lib/http";
import { authApi, isPending, type RegisterInput, type RegisterPending } from "./authApi";

type AuthStatus = "loading" | "authenticated" | "anonymous";
type AuthContextValue = {
  status: AuthStatus;
  user: User | null;
  login: (email: string, password: string, remember?: boolean) => Promise<User>;
  /** Trả người dùng (email mới, đã đăng nhập) hoặc RegisterPending (email đã có tài khoản, ADR-040 1A). */
  register: (input: RegisterInput) => Promise<User | RegisterPending>;
  /** Nhận phiên mới máy chủ cấp sau khi đổi mật khẩu (access token cũ đã hết hiệu lực). */
  adoptSession: (session: AuthResponse) => void;
  logout: () => Promise<void>;
  setUser: (user: User) => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUserState] = useState<User | null>(null);

  useEffect(() => {
    const unsubscribe = onSessionChange((session) => {
      setUserState(session?.user ?? null);
      setStatus(session ? "authenticated" : "anonymous");
      // Hết phiên thì bỏ dữ liệu cá nhân đã cache, tránh người sau thấy dữ liệu người trước.
      if (!session) queryClient.clear();
    });
    // Tải lại trang: thử lấy phiên từ cookie refresh; backend chưa có /auth/refresh thì coi như chưa đăng nhập.
    if (hasSessionHint()) void refreshSession().catch(() => setSession(null));
    else setSession(null);
    return unsubscribe;
  }, [queryClient]);

  const login = useCallback(async (email: string, password: string, remember = true) => {
    const session = await authApi.login(email, password, remember);
    setSession(session);
    return session.user;
  }, []);

  const register = useCallback(async (input: RegisterInput) => {
    const result = await authApi.register(input);
    if (isPending(result)) return result;
    setSession(result);
    return result.user;
  }, []);

  const adoptSession = useCallback((session: AuthResponse) => setSession(session), []);

  const logout = useCallback(async () => {
    // Dù gọi server lỗi vẫn xóa phiên phía trình duyệt để người dùng thoát được.
    try { await authApi.logout(); } finally { setSession(null); }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ status, user, login, register, logout, adoptSession, setUser: setUserState }),
    [status, user, login, register, logout, adoptSession],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth phải nằm trong <AuthProvider>");
  return ctx;
}
