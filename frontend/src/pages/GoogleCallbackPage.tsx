import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { apiClient } from "../services/api";

export const GoogleCallbackPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const error = searchParams.get("error");

    if (error) {
      navigate("/login?error=google_auth_failed", { replace: true });
      return;
    }

    apiClient
      .get("/v1/auth/me")
      .then(() => {
        navigate("/dashboard", { replace: true });
      })
      .catch(() => navigate("/login", { replace: true }));
  }, []);

  return (
    <div className="min-h-screen bg-linear-to-br from-green-50 via-blue-50 to-emerald-50 flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="w-12 h-12 text-green-600 animate-spin mx-auto mb-4" />
        <p className="text-gray-600 text-lg">Completing Google Sign In...</p>
      </div>
    </div>
  );
};
