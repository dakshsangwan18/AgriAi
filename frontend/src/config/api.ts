// Production-safe API configuration
// This configuration NEVER crashes the app, even if VITE_API_BASE_URL is missing.
// Priority order:
// 1. VITE_API_BASE_URL (if set at build time)
// 2. Local backend in development, production backend in production

const rawApiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV
    ? "http://localhost:8000"
    : "https://agriai-ecxt.onrender.com");

// Clean URL: remove trailing slash
export const API_BASE_URL = rawApiBaseUrl.replace(/\/$/, "") + "/api";

// Backend base URL for OAuth (without /api suffix)
export const BACKEND_BASE_URL = rawApiBaseUrl.replace(/\/$/, "");
