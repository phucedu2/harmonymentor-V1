import { lazy, type ReactNode } from "react";
import { createBrowserRouter, RouterProvider } from "react-router";
import { RequireAdmin, RequireAuth } from "./auth/guards";
import AppLayout from "./components/layout/AppLayout";
import PublicLayout from "./components/layout/PublicLayout";
import HomePage from "./pages/public/HomePage";

// Tách bundle theo route (docs/giai-doan/phase-A/PHASE_A_PLAN.md mục 3): trang chủ tải ngay, phần còn lại tải khi mở.
const LoginPage = lazy(() => import("./pages/public/LoginPage"));
const RegisterPage = lazy(() => import("./pages/public/RegisterPage"));
const DashboardPage = lazy(() => import("./pages/Dashboard"));
const LearnPage = lazy(() => import("./pages/Learn"));
const PracticePage = lazy(() => import("./pages/Practice"));
const ProgressPage = lazy(() => import("./pages/Progress"));
const CompositionLabPage = lazy(() => import("./pages/app/CompositionLabPage"));
const ProfilePage = lazy(() => import("./pages/app/ProfilePage"));
const AdminHomePage = lazy(() => import("./pages/app/AdminHomePage"));
const NotFoundPage = lazy(() => import("./pages/NotFoundPage"));

// Trang có từ v0.4.0 dùng CSS cũ; bọc lại cho tới khi chuyển sang Tailwind ở Giai đoạn C.
const legacy = (page: ReactNode) => <div className="legacy-page">{page}</div>;

const router = createBrowserRouter([
  {
    element: <PublicLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "dang-nhap", element: <LoginPage /> },
      { path: "dang-ky", element: <RegisterPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
  {
    path: "app",
    element: <RequireAuth><AppLayout /></RequireAuth>,
    children: [
      { index: true, element: legacy(<DashboardPage />) },
      { path: "hoc", element: legacy(<LearnPage />) },
      { path: "luyen-tap", element: legacy(<PracticePage />) },
      { path: "tien-do", element: legacy(<ProgressPage />) },
      { path: "composition", element: <CompositionLabPage /> },
      { path: "ho-so", element: <ProfilePage /> },
    ],
  },
  {
    path: "admin",
    element: <RequireAuth><AppLayout /></RequireAuth>,
    children: [{ index: true, element: <RequireAdmin><AdminHomePage /></RequireAdmin> }],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
