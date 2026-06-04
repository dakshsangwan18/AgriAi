import React, { useState, useEffect, useCallback } from "react";
import {
  Bell,
  TrendingUp,
  Plus,
  Trash2,
  X,
  Loader,
  CheckCircle,
} from "lucide-react";
import { apiClient } from "../services/api";
import { logger } from "../utils/logger";

interface PriceAlert {
  id: string;
  crop: string;
  city: string;
  alert_type: "ABOVE" | "BELOW" | "CHANGE";
  threshold_price: number | null;
  threshold_percentage: number | null;
  is_active: boolean;
  notification_method: string;
  last_triggered_at: string | null;
  created_at: string;
}

export const AlertsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<PriceAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [success, setSuccess] = useState("");
  const [formData, setFormData] = useState({
    crop: "wheat",
    city: "Delhi",
    alert_type: "BELOW",
    threshold_price: "",
    threshold_percentage: "",
    notification_method: "EMAIL",
  });

  const fetchAlerts = useCallback(async () => {
    try {
      const response = await apiClient.get("/alerts");
      setAlerts(response.data);
    } catch (error) {
      logger.error("Error fetching alerts", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const createAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      interface AlertPayload {
        crop: string;
        city: string;
        alert_type: string;
        threshold_price?: number;
        threshold_percentage?: number;
        notification_method: string;
      }
      const payload: AlertPayload = {
        crop: formData.crop,
        city: formData.city,
        alert_type: formData.alert_type,
        notification_method: formData.notification_method,
      };

      if (formData.alert_type === "CHANGE") {
        payload.threshold_percentage = parseFloat(
          formData.threshold_percentage
        );
      } else {
        payload.threshold_price = parseFloat(formData.threshold_price);
      }

      await apiClient.post("/alerts", payload);

      setSuccess("Price alert created successfully!");
      setTimeout(() => setSuccess(""), 3000);

      setShowCreateModal(false);
      setFormData({
        crop: "wheat",
        city: "Delhi",
        alert_type: "BELOW",
        threshold_price: "",
        threshold_percentage: "",
        notification_method: "EMAIL",
      });
      fetchAlerts();
    } catch (error) {
      logger.error("Error creating alert", error);
      setSuccess("Failed to create alert");
      setTimeout(() => setSuccess(""), 3000);
    }
  };

  const deleteAlert = async (id: string) => {
    if (!confirm("Delete this alert?")) return;

    try {
      await apiClient.delete(`/alerts/${id}`);
      fetchAlerts();
    } catch (error) {
      logger.error("Error deleting alert", error);
    }
  };

  const toggleActive = async (alert: PriceAlert) => {
    try {
      await apiClient.patch(`/alerts/${alert.id}`, {
        is_active: !alert.is_active,
      });
      fetchAlerts();
    } catch (error) {
      logger.error("Error toggling alert", error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader className="animate-spin text-green-600" size={48} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-linear-to-br from-gray-50 via-green-50/30 to-blue-50/30 p-6">
      <div className="max-w-4xl mx-auto">
        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl flex items-center gap-2 text-green-700 animate-fadeIn">
            <CheckCircle className="w-5 h-5" />
            <span>{success}</span>
          </div>
        )}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl sm:text-4xl font-bold text-gray-900 mb-2">
              Price Alerts
            </h1>
            <p className="text-gray-600 text-sm sm:text-base">
              {alerts.length > 0
                ? `Managing ${alerts.length} alert${
                    alerts.length > 1 ? "s" : ""
                  }`
                : "Create alerts to get notified in the website when prices change"}
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            aria-label="Create new price alert"
            className="flex items-center justify-center gap-2 px-4 sm:px-6 py-3 bg-emerald-900 text-white rounded-xl font-semibold hover:bg-emerald-800 transition shadow-lg w-full sm:w-auto"
          >
            <Plus size={20} />
            Create Alert
          </button>
        </div>{" "}
        {alerts.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
            <Bell className="mx-auto text-gray-400 mb-4" size={64} />
            <h3 className="text-xl font-bold text-gray-900 mb-2">
              No Price Alerts Yet
            </h3>
            <p className="text-gray-600 mb-2">
              Set up alerts to get notified <strong>in the website</strong> when
              crop prices reach your target
            </p>
            <p className="text-sm text-gray-500 mb-6">
              💰 Hourly checks • 🔔 In-app notifications • 📧 Email alerts
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              aria-label="Create your first price alert"
              className="px-6 py-3 bg-emerald-900 text-white rounded-xl font-semibold hover:bg-emerald-800 transition"
            >
              Create Your First Alert
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`bg-white rounded-2xl shadow-lg p-6 border-l-4 ${
                  alert.is_active ? "border-l-green-500" : "border-l-gray-300"
                }`}
              >
                <div className="flex items-start gap-4">
                  <TrendingUp className="text-green-600 shrink-0" size={24} />

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <div>
                        <h3 className="text-lg font-bold text-gray-900 mb-1">
                          {alert.crop.toUpperCase()} - {alert.city}
                        </h3>
                        <p className="text-gray-600">
                          {alert.alert_type === "ABOVE" &&
                            `Alert when price goes above ₹${alert.threshold_price}/kg`}
                          {alert.alert_type === "BELOW" &&
                            `Alert when price drops below ₹${alert.threshold_price}/kg`}
                          {alert.alert_type === "CHANGE" &&
                            `Alert when price changes by ${alert.threshold_percentage}%`}
                        </p>
                      </div>
                      <div className="flex gap-2 shrink-0">
                        <button
                          onClick={() => toggleActive(alert)}
                          aria-label={
                            alert.is_active ? "Pause alert" : "Activate alert"
                          }
                          className={`px-4 py-2 rounded-lg font-medium transition ${
                            alert.is_active
                              ? "bg-green-100 text-green-700"
                              : "bg-gray-100 text-gray-600"
                          }`}
                        >
                          {alert.is_active ? "Active" : "Paused"}
                        </button>
                        <button
                          onClick={() => deleteAlert(alert.id)}
                          aria-label="Delete alert"
                          className="p-2 hover:bg-red-50 rounded-lg transition text-red-600"
                          title="Delete"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-500 mt-3">
                      <span>📧 {alert.notification_method}</span>
                      <span>•</span>
                      <span>
                        Created{" "}
                        {new Date(alert.created_at).toLocaleDateString()}
                      </span>
                      {alert.last_triggered_at && (
                        <>
                          <span>•</span>
                          <span className="text-yellow-600 font-medium">
                            Last triggered{" "}
                            {new Date(alert.last_triggered_at).toLocaleString()}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}{" "}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">
                  Create Price Alert
                </h2>
                <button
                  onClick={() => setShowCreateModal(false)}
                  aria-label="Close create alert form"
                  className="p-2 hover:bg-gray-100 rounded-lg transition"
                >
                  <X size={24} />
                </button>
              </div>

              <form onSubmit={createAlert} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Crop
                  </label>
                  <select
                    value={formData.crop}
                    onChange={(e) =>
                      setFormData({ ...formData, crop: e.target.value })
                    }
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    required
                  >
                    <option value="wheat">Wheat</option>
                    <option value="rice">Rice</option>
                    <option value="tomato">Tomato</option>
                    <option value="onion">Onion</option>
                    <option value="potato">Potato</option>
                    <option value="cotton">Cotton</option>
                    <option value="sugarcane">Sugarcane</option>
                    <option value="maize">Maize</option>
                    <option value="soyabean">Soybean</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    City
                  </label>
                  <input
                    type="text"
                    value={formData.city}
                    onChange={(e) =>
                      setFormData({ ...formData, city: e.target.value })
                    }
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="Delhi"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Alert Type
                  </label>
                  <select
                    value={formData.alert_type}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        alert_type: e.target.value as string,
                      })
                    }
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    required
                  >
                    <option value="ABOVE">Price goes above threshold</option>
                    <option value="BELOW">Price drops below threshold</option>
                    <option value="CHANGE">Price changes by percentage</option>
                  </select>
                </div>

                {formData.alert_type === "CHANGE" ? (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Percentage Change (%)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.threshold_percentage}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          threshold_percentage: e.target.value,
                        })
                      }
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      placeholder="5"
                      required
                    />
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Price Threshold (₹/kg)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={formData.threshold_price}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          threshold_price: e.target.value,
                        })
                      }
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      placeholder="2500"
                      required
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Notification Method
                  </label>
                  <select
                    value={formData.notification_method}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        notification_method: e.target.value,
                      })
                    }
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  >
                    <option value="EMAIL">Email + In-App Notification</option>
                    <option value="SMS">SMS (coming soon)</option>
                    <option value="BOTH">All Methods (coming soon)</option>
                  </select>
                  <p className="mt-2 text-xs text-gray-500">
                    🔔 In-app notifications are always enabled - check the bell
                    icon in header
                  </p>
                </div>

                <div className="flex gap-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    aria-label="Cancel alert creation"
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-xl font-semibold hover:bg-gray-50 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    aria-label="Submit new alert"
                    className="flex-1 px-4 py-3 bg-emerald-900 text-white rounded-xl font-semibold hover:bg-emerald-800 transition"
                  >
                    Create Alert
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
