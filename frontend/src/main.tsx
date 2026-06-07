import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { logResourceTiming } from "./hooks/useWebVitals";
import * as Sentry from "@sentry/react";
import { ToastProvider } from "./components/ui/Toast";

const sentryDsn = import.meta.env.VITE_SENTRY_DSN as string | undefined;
if (sentryDsn) {
  Sentry.init({
    dsn: sentryDsn,
    environment: (import.meta.env.VITE_SENTRY_ENV as string | undefined) || import.meta.env.MODE,
    release: import.meta.env.VITE_SENTRY_RELEASE as string | undefined,
    tracesSampleRate: Number(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || 0),
  });
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ToastProvider>
      <App />
    </ToastProvider>
  </StrictMode>
);

if (import.meta.env.PROD) {
  window.addEventListener("load", () => {
    setTimeout(logResourceTiming, 3000);
  });
}

