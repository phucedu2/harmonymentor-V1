import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@fontsource/be-vietnam-pro/400.css";
import "@fontsource/be-vietnam-pro/500.css";
import "@fontsource/be-vietnam-pro/600.css";
import "@fontsource/be-vietnam-pro/700.css";
import "@fontsource/fraunces/600.css";
import "@fontsource/fraunces/700.css";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/600.css";
import App from "./App";
import { AuthProvider } from "./auth/AuthProvider";
import "./index.css";

// Lỗi 4xx (sai quyền, không tồn tại) thử lại cũng vô ích; chỉ thử lại lỗi mạng/5xx một lần.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (count, error) => count < 1 && (error as { retryable?: boolean }).retryable === true,
      refetchOnWindowFocus: false,
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
