// Production-safe API configuration
// This configuration NEVER crashes the app, even if VITE_API_BASE_URL is missing.
// Priority order:
// 1. VITE_API_BASE_URL (if set at build time)
// 2. Local backend in development, production backend in production

const isDev = import.meta.env.DEV;

// Absolute backend URL, used for OAuth redirects (e.g., /api/v1/auth/google/login).
export const BACKEND_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (isDev
    ? "http://localhost:8000"
    : "https://agriai-ecxt.onrender.com");

// In local development we proxy /api through the Vite dev server so that the
// frontend and backend appear same-origin to the browser. This is required for
// cookie-based auth with SameSite=Lax to work reliably during development.
// In production or when VITE_API_BASE_URL is explicitly set, use the full URL.
export const API_BASE_URL =
  isDev && !import.meta.env.VITE_API_BASE_URL
    ? "/api"
    : BACKEND_BASE_URL.replace(/\/$/, "") + "/api";
