import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { onSessionChange, refreshSession, setSession, type User } from "../lib/http";
import { authApi, type RegisterInput } from "./authApi";

type AuthStatus = "loading" | "authenticated" | "anonymous";
type AuthContextValue = {
  status: AuthStatus;
  user: User | null;
  login: (email: string, password: string) => Promise<User>;
  register: (input: RegisterInput) => Promise<User>;
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
    void refreshSession().catch(() => setSession(null));
    return unsubscribe;
  }, [queryClient]);

  const login = useCallback(async (email: string, password: string) => {
    const session = await authApi.login(email, password);
    setSession(session);
    return session.user;
  }, []);

  const register = useCallback(async (input: RegisterInput) => {
    const session = await authApi.register(input);
    setSession(session);
    return session.user;
  }, []);

  const logout = useCallback(async () => {
    // Dù gọi server lỗi vẫn xóa phiên phía trình duyệt để người dùng thoát được.
    try { await authApi.logout(); } finally { setSession(null); }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ status, user, login, register, logout, setUser: setUserState }),
    [status, user, login, register, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth phải nằm trong <AuthProvider>");
  return ctx;
}
