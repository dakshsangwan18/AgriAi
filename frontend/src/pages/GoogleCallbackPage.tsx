import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Loader2, AlertCircle } from "lucide-react";
import { apiClient } from "../services/api";

export const GoogleCallbackPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const error = searchParams.get("error");

    if (error) {
      console.error("[GoogleCallback] OAuth error from provider:", error);
      navigate(`/login?error=google_auth_failed&error_detail=${encodeURIComponent(error)}`, { replace: true });
      return;
    }

    apiClient
      .get("/v1/auth/me")
      .then(() => {
        navigate("/dashboard", { replace: true });
      })
      .catch((err) => {
        const status = err.response?.status;
        const detail = err.response?.data?.detail || err.message;
        console.error("[GoogleCallback] Failed to verify session:", {
          status,
          detail,
          isAxiosError: err.isAxiosError,
        });

        // Surface the failure briefly so the user (and dev tools) can see it.
        setErrorMessage(
          status === 401
            ? "Session cookie missing. Make sure third-party cookies are enabled and the backend redirect URI matches Google Console."
            : `Login verification failed (${status || "network"}). Please try again.`
        );

        // Redirect to login with a meaningful error flag after a short delay.
        setTimeout(() => {
          navigate(
            `/login?error=google_session_failed&status=${status || "unknown"}`,
            { replace: true }
          );
        }, 2000);
      });
  }, []);

  return (
    <div className="min-h-screen bg-linear-to-br from-green-50 via-blue-50 to-emerald-50 flex items-center justify-center">
      <div className="text-center max-w-md px-6">
        {errorMessage ? (
          <>
            <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
            <p className="text-red-700 text-lg font-medium">{errorMessage}</p>
            <p className="text-gray-500 mt-2">Redirecting to login...</p>
          </>
        ) : (
          <>
            <Loader2 className="w-12 h-12 text-green-600 animate-spin mx-auto mb-4" />
            <p className="text-gray-600 text-lg">Completing Google Sign In...</p>
          </>
        )}
      </div>
    </div>
  );
};
