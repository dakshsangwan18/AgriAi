/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";
import { logger } from "../utils/logger";
import { apiClient } from "../services/api";

interface User {
  id: number;
  email: string;
  full_name: string | null;
  phone: string | null;
  location: string | null;
  is_active: boolean;
  is_superuser?: boolean;
  created_at: string;
  favorite_crops?: string[];
  preferred_language?: string;
  notification_enabled?: boolean;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    fullName?: string,
    phone?: string,
    location?: string
  ) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // API base URL - configured via centralized config

  // Fetch current user on mount (cookie-based auth)
  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();

    const fetchUser = async () => {
      try {
        const response = await apiClient.get("/v1/auth/me", {
          signal: controller.signal,
        });
        if (!cancelled) setUser(response.data);
      } catch (error) {
        if (axios.isCancel(error)) return;
        if (cancelled) return;
        logger.error("Failed to fetch user", { error });
        setUser(null);
      }
      if (!cancelled) setLoading(false);
    };

    fetchUser().catch((error) => {
      if (cancelled) return;
      logger.error("Unexpected error during fetchUser", { error });
      setLoading(false);
    });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, []);

  const login = async (email: string, password: string) => {
    try {
      // OAuth2 password flow expects form data
      const formData = new FormData();
      formData.append("username", email); // OAuth2 uses 'username' field
      formData.append("password", password);

      await apiClient.post("/v1/auth/login", formData);

      const userResponse = await apiClient.get("/v1/auth/me");

      // Set all state
      setUser(userResponse.data);
    } catch (error) {
      setUser(null);

      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || "Login failed");
      }
      throw new Error("Login failed");
    }
  };

  const register = async (
    email: string,
    password: string,
    fullName?: string,
    phone?: string,
    location?: string
  ) => {
    try {
      await apiClient.post("/v1/auth/register", {
        email,
        password,
        full_name: fullName,
        phone,
        location,
      });

      // Auto-login after registration
      await login(email, password);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || "Registration failed");
      }
      throw new Error("Registration failed");
    }
  };

  const logout = () => {
    apiClient
      .post("/v1/auth/logout")
      .catch((error) => logger.error("Logout failed", { error }))
      .finally(() => setUser(null));
  };

  const value = {
    user,
    login,
    register,
    logout,
    isAuthenticated: !!user,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
