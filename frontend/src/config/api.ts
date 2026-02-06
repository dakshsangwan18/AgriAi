// Production-safe API configuration
// This configuration NEVER crashes the app, even if VITE_API_BASE_URL is missing.
// Priority order:
// 1. VITE_API_BASE_URL (if set at build time)
// 2. Production backend URL (hardcoded fallback)

const rawApiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ||
  "https://agriai-ecxt.onrender.com";

// Clean URL: remove trailing slash
export const API_BASE_URL = rawApiBaseUrl.replace(/\/$/, "") + "/api";

// Backend base URL for OAuth (without /api suffix)
export const BACKEND_BASE_URL = rawApiBaseUrl.replace(/\/$/, "");
