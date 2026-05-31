import axios, { AxiosError } from "axios";
import { API_BASE_URL } from "../config/api";
import { getCookie } from "../utils/cookies";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 second timeout (agent analysis can take 30-40s)
  withCredentials: true,
});

apiClient.interceptors.request.use((config) => {
  const method = (config.method || "get").toLowerCase();
  if (["post", "put", "patch", "delete"].includes(method)) {
    const csrfToken = getCookie("csrf_token");
    if (csrfToken) {
      config.headers = config.headers || {};
      config.headers["X-CSRF-Token"] = csrfToken;
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status;
    const originalRequest = error.config as (typeof error.config & {
      _retry?: boolean;
    });

    if (
      status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !String(originalRequest.url || "").includes("/v1/auth/login") &&
      !String(originalRequest.url || "").includes("/v1/auth/refresh")
    ) {
      originalRequest._retry = true;
      try {
        await apiClient.post("/v1/auth/refresh");
        return apiClient(originalRequest);
      } catch {
        // Fall through to default error handling
      }
    }

    if (error.code === "ECONNABORTED") {
      throw new Error("Request timeout. Please try again.");
    }
    if (!error.response) {
      throw new Error("Network error. Please check your connection.");
    }
    if (error.response.status >= 500) {
      throw new Error("Server error. Please try again later.");
    }
    if (error.response.status === 404) {
      throw new Error("Resource not found.");
    }
    if (error.response.status === 400) {
      const detail = (error.response.data as { detail?: string })?.detail;
      throw new Error(detail || "Invalid request.");
    }
    throw error;
  }
);

export interface CurrentWeather {
  city: string;
  temperature: number;
  feels_like: number;
  humidity: number;
  description: string;
  wind_speed: number;
  timestamp: string;
}

export interface ForecastItem {
  datetime: string;
  temperature: number;
  description: string;
  rain_probability: number;
  humidity: number;
}

export interface WeatherForecast {
  city: string;
  forecasts: ForecastItem[];
}

export interface WeatherAlert {
  type: string;
  severity: string;
  message: string;
}

export interface WeatherAlerts {
  city: string;
  alerts: WeatherAlert[];
  current_conditions: CurrentWeather;
}

export const weatherAPI = {
  getCurrentWeather: async (city: string): Promise<CurrentWeather> => {
    const response = await apiClient.get("/weather/current", {
      params: { city },
    });
    return response.data;
  },

  getForecast: async (
    city: string,
    days: number = 5
  ): Promise<WeatherForecast> => {
    const response = await apiClient.get("/weather/forecast", {
      params: { city, days },
    });
    return response.data;
  },

  getAlerts: async (city: string): Promise<WeatherAlerts> => {
    const response = await apiClient.get("/weather/alerts", {
      params: { city },
    });
    return response.data;
  },
};

export interface HistoricalPrice {
  date: string;
  price: number;
  crop: string;
}

export interface PredictedPrice {
  date: string;
  predicted_price: number;
  crop: string;
}

export interface PricePrediction {
  crop: string;
  current_price: number;
  predicted_average: number;
  price_change_percentage: number;
  trend: string;
  historical_data: HistoricalPrice[];
  predictions: PredictedPrice[];
  recommendation: string;
}

export interface MarketComparison {
  mandi: string;
  price: number;
  variation_percent: number;
}

export interface MarketComparisonData {
  crop: string;
  comparison: MarketComparison[];
  best_market: string;
  price_difference: number;
}

export const priceAPI = {
  getPrediction: async (
    crop: string,
    days: number = 30
  ): Promise<PricePrediction> => {
    const response = await apiClient.get("/prices/predict", {
      params: { crop, days },
    });
    return response.data;
  },

  getHistorical: async (crop: string, days: number = 90) => {
    const response = await apiClient.get("/prices/historical", {
      params: { crop, days },
    });
    return response.data;
  },

  compareMarkets: async (crop: string): Promise<MarketComparisonData> => {
    const response = await apiClient.get("/prices/compare", {
      params: { crop },
    });
    return response.data;
  },

  getCrops: async () => {
    const response = await apiClient.get("/prices/crops");
    return response.data;
  },
};

export interface YieldPredictionRequest {
  crop: string;
  area: number;
  rainfall: number;
  temperature: number;
  soil_ph: number;
  nitrogen: number;
  phosphorus: number;
  potassium: number;
}

export interface OptimalConditions {
  temperature: string;
  rainfall: string;
  soil_ph: string;
  overall_score: number;
}

export interface Recommendation {
  type: string;
  priority: string;
  message: string;
}

export interface YieldPredictionResponse {
  crop: string;
  area_hectares: number;
  predicted_total_yield: number;
  predicted_yield_per_hectare: number;
  unit: string;
  expected_range: {
    min: number;
    max: number;
  };
  optimal_conditions: OptimalConditions;
  recommendations: Recommendation[];
  input_parameters: {
    rainfall_mm: number;
    temperature_celsius: number;
    soil_ph: number;
    nitrogen_kg_per_ha: number;
    phosphorus_kg_per_ha: number;
    potassium_kg_per_ha: number;
  };
}

// Yield API calls
export const yieldAPI = {
  predictYield: async (
    data: YieldPredictionRequest
  ): Promise<YieldPredictionResponse> => {
    const response = await apiClient.post("/yield/predict", data);
    return response.data;
  },

  getCrops: async () => {
    const response = await apiClient.get("/yield/crops");
    return response.data;
  },

  getCropInfo: async (crop: string) => {
    const response = await apiClient.get(`/yield/crop-info/${crop}`);
    return response.data;
  },
};

// AI Agent Interfaces
export interface MarketSignal {
  signal_type: string;
  signal: string;
  strength: number;
  explanation: string;
}

export interface Decision {
  action: string;
  confidence: number;
  reason: string;
  best_action_date: string | null;
  expected_price: number | null;
  risk_level: string;
}

export interface AgentAnalysis {
  id?: number;
  crop: string;
  city: string;
  current_price: number;
  predicted_price: number | null;
  days_ahead?: number;
  decision: Decision;
  market_signals: MarketSignal[];
  llm_insights: string | null;
  timestamp: string;
}

export interface AgentHistoryItem {
  id: number;
  crop: string;
  city: string;
  current_price: number;
  predicted_price: number | null;
  decision: {
    action: string;
    confidence: number;
    reason: string;
    best_action_date: string | null;
    expected_price: number | null;
    risk_level: string;
  };
  market_signals: MarketSignal[];
  llm_insights: string | null;
  timestamp: string;
}

export interface AgentStatus {
  is_running: boolean;
  last_run: string | null;
  next_scheduled_run: string | null;
  total_analyses: number;
}

// Agent API calls
export const agentAPI = {
  analyzeCrop: async (
    crop: string,
    city: string,
    days: number = 7
  ): Promise<AgentAnalysis> => {
    const response = await apiClient.post("/agent/analyze", {
      crop,
      city,
      days,
    });
    return response.data;
  },

  getStatus: async (): Promise<AgentStatus> => {
    const response = await apiClient.get("/agent/status");
    return response.data;
  },

  triggerMonitoring: async () => {
    const response = await apiClient.post("/agent/trigger-monitoring");
    return response.data;
  },

  getHealth: async () => {
    const response = await apiClient.get("/agent/health");
    return response.data;
  },

  getHistory: async (
    limit: number = 10,
    crop?: string
  ): Promise<{ total: number; analyses: AgentHistoryItem[] }> => {
    const params = new URLSearchParams();
    params.append("limit", limit.toString());
    if (crop) params.append("crop", crop);

    const response = await apiClient.get(`/agent/history?${params}`);
    return response.data;
  },
};

export interface Notification {
  id: number;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  priority: string;
  created_at: string;
  extra_data?: {
    crop?: string;
    action?: string;
    confidence?: number;
    expected_price?: number;
  };
}

// Notification API calls
export const notificationAPI = {
  getAll: async (): Promise<Notification[]> => {
    const response = await apiClient.get("/notifications/");
    return response.data;
  },

  getUnreadCount: async (): Promise<{ unread_count: number }> => {
    const response = await apiClient.get("/notifications/unread-count");
    return response.data;
  },

  markAsRead: async (notificationIds: number[]): Promise<void> => {
    await apiClient.post("/notifications/mark-read", {
      notification_ids: notificationIds,
    });
  },

  markAllAsRead: async (): Promise<void> => {
    await apiClient.post("/notifications/mark-all-read", {});
  },

  delete: async (notificationId: number): Promise<void> => {
    await apiClient.delete(`/notifications/${notificationId}`);
  },
};

// Chatbot API
export const chatbotAPI = {
  ask: async (
    message: string,
    history: Array<{ role: string; content: string }> = [],
    signal?: AbortSignal
  ): Promise<{ response: string }> => {
    const response = await apiClient.post(
      "/chatbot/ask",
      { message, history },
      { signal }
    );
    return response.data;
  },
};
