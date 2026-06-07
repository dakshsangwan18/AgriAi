import React, { useState } from "react";
import {
  Leaf,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { yieldAPI } from "../services/api";
import type { YieldPredictionResponse } from "../services/api";
import type { AxiosError } from "axios";
import { logger } from "../utils/logger";
import { CROPS } from "../config/constants";

const YieldPrediction = () => {
  const [formData, setFormData] = useState({
    crop: "wheat",
    area: 5,
    rainfall: 600,
    temperature: 25,
    soil_ph: 7.0,
    nitrogen: 50,
    phosphorus: 40,
    potassium: 40,
  });

  const [prediction, setPrediction] = useState<YieldPredictionResponse | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const crops = CROPS;

  const handleInputChange = (field: string, value: number | string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handlePredict = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await yieldAPI.predictYield(formData);
      setPrediction(result);
    } catch (err: unknown) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      const message =
        axiosError.response?.data?.detail ||
        (err instanceof Error
          ? err.message
          : "Failed to predict yield. Please try again.");
      setError(message);
      logger.error("Failed to predict yield", { error: err });
    } finally {
      setLoading(false);
    }
  };

  const getConditionIcon = (status: string) => {
    if (status === "optimal")
      return <CheckCircle className="text-green-500" size={20} />;
    if (status === "suboptimal")
      return <AlertCircle className="text-yellow-500" size={20} />;
    return <XCircle className="text-red-500" size={20} />;
  };

  const getConditionColor = (status: string) => {
    if (status === "optimal") return "text-green-600 bg-green-50";
    if (status === "suboptimal") return "text-yellow-600 bg-yellow-50";
    return "text-red-600 bg-red-50";
  };

  const getPriorityColor = (priority: string) => {
    if (priority === "high") return "bg-red-100 border-red-500 text-red-700";
    if (priority === "medium")
      return "bg-yellow-100 border-yellow-500 text-yellow-700";
    return "bg-blue-100 border-blue-500 text-blue-700";
  };

  return (
    <div className="min-h-screen bg-slate-50 p-4 sm:p-8">
      <div className="max-w-7xl mx-auto">
        {" "}
        <div className="mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-2">
            Crop Yield Prediction
          </h1>
          <p className="text-slate-600">
            AI-powered yield estimates based on your farming conditions
          </p>
        </div>
        <div className="grid lg:grid-cols-2 gap-6 sm:gap-8">
          {" "}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h2 className="text-2xl font-semibold text-slate-900 mb-6 flex items-center">
              <Leaf className="mr-2 text-emerald-600" />
              Enter Your Details
            </h2>{" "}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Select Crop
              </label>
              <div className="grid grid-cols-2 gap-2">
                {crops.map((crop) => (
                  <button
                    key={crop.value}
                    onClick={() => handleInputChange("crop", crop.value)}
                    className={`p-3 rounded-lg border-2 transition text-left ${
                      formData.crop === crop.value
                        ? "border-emerald-500 bg-emerald-50"
                        : "border-slate-200 hover:border-emerald-300"
                    }`}
                  >
                    <span className="text-xl mr-2">{crop.icon}</span>
                    <span className="text-sm font-medium">{crop.label}</span>
                  </button>
                ))}
              </div>
            </div>{" "}
            <div className="mb-4">
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Land Area (hectares): {formData.area}
              </label>
              <input
                type="range"
                min="0.5"
                max="50"
                step="0.5"
                value={formData.area}
                onChange={(e) =>
                  handleInputChange("area", parseFloat(e.target.value))
                }
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
              />
              <div className="flex justify-between text-xs text-slate-500 mt-1">
                <span>0.5 ha</span>
                <span>50 ha</span>
              </div>
            </div>{" "}
            <div className="mb-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">
                Weather Conditions
              </h3>

              <div className="mb-3">
                <label className="block text-sm text-slate-600 mb-1">
                  Expected Rainfall (mm): {formData.rainfall}
                </label>
                <input
                  type="range"
                  min="200"
                  max="2000"
                  step="50"
                  value={formData.rainfall}
                  onChange={(e) =>
                    handleInputChange("rainfall", parseFloat(e.target.value))
                  }
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Average Temperature (°C): {formData.temperature}
                </label>
                <input
                  type="range"
                  min="10"
                  max="40"
                  step="1"
                  value={formData.temperature}
                  onChange={(e) =>
                    handleInputChange("temperature", parseFloat(e.target.value))
                  }
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-orange-600"
                />
              </div>
            </div>{" "}
            <div className="mb-6 p-4 bg-amber-50 rounded-lg">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">
                Soil & Nutrients
              </h3>

              <div className="mb-3">
                <label className="block text-sm text-gray-600 mb-1">
                  Soil pH: {formData.soil_ph.toFixed(1)}
                </label>
                <input
                  type="range"
                  min="5"
                  max="9"
                  step="0.1"
                  value={formData.soil_ph}
                  onChange={(e) =>
                    handleInputChange("soil_ph", parseFloat(e.target.value))
                  }
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-amber-600"
                />
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">
                    N: {formData.nitrogen}
                  </label>
                  <input
                    type="range"
                    min="20"
                    max="100"
                    value={formData.nitrogen}
                    onChange={(e) =>
                      handleInputChange("nitrogen", parseFloat(e.target.value))
                    }
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-green-600"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">
                    P: {formData.phosphorus}
                  </label>
                  <input
                    type="range"
                    min="20"
                    max="80"
                    value={formData.phosphorus}
                    onChange={(e) =>
                      handleInputChange(
                        "phosphorus",
                        parseFloat(e.target.value)
                      )
                    }
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">
                    K: {formData.potassium}
                  </label>
                  <input
                    type="range"
                    min="20"
                    max="80"
                    value={formData.potassium}
                    onChange={(e) =>
                      handleInputChange("potassium", parseFloat(e.target.value))
                    }
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                NPK values in kg/hectare
              </p>
            </div>{" "}
            <button
              onClick={handlePredict}
              disabled={loading}
              className="w-full py-3 bg-emerald-900 text-white rounded-lg font-semibold hover:bg-emerald-800 disabled:bg-slate-400 transition flex items-center justify-center shadow-sm"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Calculating...
                </>
              ) : (
                <>
                  <TrendingUp className="mr-2" size={20} />
                  Predict Yield
                </>
              )}
            </button>
          </div>{" "}
          <div>
            {error && (
              <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg flex items-center justify-between">
                <span>{error}</span>
                <button
                  onClick={handlePredict}
                  className="ml-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm font-medium"
                >
                  Retry
                </button>
              </div>
            )}

            {!prediction && !error && (
              <div className="bg-white p-12 rounded-xl shadow-lg text-center">
                <Leaf className="mx-auto text-gray-300 mb-4" size={64} />
                <p className="text-gray-500">
                  Enter your farming details and click "Predict Yield" to see
                  results
                </p>
              </div>
            )}

            {prediction && (
              <>
                {" "}
                <div className="bg-emerald-900 p-8 rounded-xl shadow-lg text-white mb-6">
                  <h3 className="text-2xl font-semibold mb-2">
                    Predicted Yield
                  </h3>
                  <div className="flex items-end gap-4 mb-4">
                    <div>
                      <p className="text-5xl font-bold">
                        {prediction.predicted_total_yield}
                      </p>
                      <p className="text-lg opacity-90">
                        {prediction.unit} (total)
                      </p>
                    </div>
                    <div className="mb-2">
                      <p className="text-2xl font-semibold">
                        {prediction.predicted_yield_per_hectare}
                      </p>
                      <p className="text-sm opacity-90">
                        {prediction.unit}/hectare
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-sm opacity-90">
                    <span>
                      Expected range: {prediction.expected_range.min} -{" "}
                      {prediction.expected_range.max} {prediction.unit}
                    </span>
                  </div>
                </div>{" "}
                <div className="bg-white p-6 rounded-xl shadow-lg mb-6">
                  <h3 className="text-xl font-semibold text-gray-800 mb-4">
                    Optimal Conditions Score
                  </h3>
                  <div className="mb-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-700">Overall Score</span>
                      <span className="text-2xl font-bold text-green-600">
                        {prediction.optimal_conditions.overall_score}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-green-600 h-3 rounded-full transition-all"
                        style={{
                          width: `${prediction.optimal_conditions.overall_score}%`,
                        }}
                      ></div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div
                      className={`flex items-center justify-between p-3 rounded-lg ${getConditionColor(
                        prediction.optimal_conditions.temperature
                      )}`}
                    >
                      <span className="flex items-center gap-2">
                        {getConditionIcon(
                          prediction.optimal_conditions.temperature
                        )}
                        <span className="font-medium">Temperature</span>
                      </span>
                      <span className="capitalize">
                        {prediction.optimal_conditions.temperature}
                      </span>
                    </div>

                    <div
                      className={`flex items-center justify-between p-3 rounded-lg ${getConditionColor(
                        prediction.optimal_conditions.rainfall
                      )}`}
                    >
                      <span className="flex items-center gap-2">
                        {getConditionIcon(
                          prediction.optimal_conditions.rainfall
                        )}
                        <span className="font-medium">Rainfall</span>
                      </span>
                      <span className="capitalize">
                        {prediction.optimal_conditions.rainfall}
                      </span>
                    </div>

                    <div
                      className={`flex items-center justify-between p-3 rounded-lg ${getConditionColor(
                        prediction.optimal_conditions.soil_ph
                      )}`}
                    >
                      <span className="flex items-center gap-2">
                        {getConditionIcon(
                          prediction.optimal_conditions.soil_ph
                        )}
                        <span className="font-medium">Soil pH</span>
                      </span>
                      <span className="capitalize">
                        {prediction.optimal_conditions.soil_ph}
                      </span>
                    </div>
                  </div>
                </div>{" "}
                {prediction.recommendations.length > 0 && (
                  <div className="bg-white p-6 rounded-xl shadow-lg">
                    <h3 className="text-xl font-semibold text-gray-800 mb-4">
                      Recommendations
                    </h3>
                    <div className="space-y-3">
                      {prediction.recommendations.map((rec, index) => (
                        <div
                          key={index}
                          className={`p-4 rounded-lg border-l-4 ${getPriorityColor(
                            rec.priority
                          )}`}
                        >
                          <div className="flex items-start gap-2">
                            <AlertCircle
                              size={20}
                              className="shrink-0 mt-0.5"
                            />
                            <div>
                              <p className="font-medium capitalize mb-1">
                                {rec.type}
                              </p>
                              <p className="text-sm">{rec.message}</p>
                              <span className="text-xs uppercase font-semibold mt-1 inline-block">
                                {rec.priority} Priority
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default React.memo(YieldPrediction);
