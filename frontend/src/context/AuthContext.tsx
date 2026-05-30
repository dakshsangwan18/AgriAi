/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";
import { logger } from "../utils/logger";
import { API_BASE_URL } from "../config/api";

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
  token: string | null;
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
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("token")
  );
  const [loading, setLoading] = useState(true);

  // API base URL - configured via centralized config

  // Fetch current user on mount if token exists
  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();

    const fetchUser = async () => {
      if (token) {
        try {
          const response = await axios.get(`${API_BASE_URL}/v1/auth/me`, {
            headers: { Authorization: `Bearer ${token}` },
            signal: controller.signal,
          });
          if (!cancelled) setUser(response.data);
        } catch (error) {
          if (axios.isCancel(error)) return;
          if (cancelled) return;
          logger.error("Failed to fetch user", { error });
          localStorage.removeItem("token");
          setToken(null);
        }
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
  }, [token]);

  const login = async (email: string, password: string) => {
    try {
      // OAuth2 password flow expects form data
      const formData = new FormData();
      formData.append("username", email); // OAuth2 uses 'username' field
      formData.append("password", password);

      const response = await axios.post(`${API_BASE_URL}/auth/login`, formData);
      const { access_token } = response.data;

      // Save token to localStorage FIRST
      localStorage.setItem("token", access_token);

      // Fetch user data
      const userResponse = await axios.get(`${API_BASE_URL}/v1/auth/me`, {
        headers: { Authorization: `Bearer ${access_token}` },
      });

      // Set all state
      setUser(userResponse.data);
      setToken(access_token);
    } catch (error) {
      // Clean up on error
      localStorage.removeItem("token");
      setToken(null);
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
      await axios.post(`${API_BASE_URL}/auth/register`, {
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
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    login,
    register,
    logout,
    isAuthenticated: !!user,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
