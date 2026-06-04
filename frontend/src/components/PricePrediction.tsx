import React, { useState, useEffect, useCallback } from "react";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  AlertCircle,
} from "lucide-react";
import { priceAPI } from "../services/api";
import { logger } from "../utils/logger";
import type {
  PricePrediction as PricePredictionType,
  MarketComparisonData,
} from "../services/api";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const PricePrediction = () => {
  const [selectedCrop, setSelectedCrop] = useState("wheat");
  const [predictionDays, setPredictionDays] = useState(30);
  const [prediction, setPrediction] = useState<PricePredictionType | null>(
    null
  );
  const [marketComparison, setMarketComparison] =
    useState<MarketComparisonData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const crops = [
    { value: "wheat", label: "Wheat (गेहूं)", icon: "🌾" },
    { value: "rice", label: "Rice (चावल)", icon: "🍚" },
    { value: "tomato", label: "Tomato (टमाटर)", icon: "🍅" },
    { value: "onion", label: "Onion (प्याज)", icon: "🧅" },
    { value: "potato", label: "Potato (आलू)", icon: "🥔" },
    { value: "cotton", label: "Cotton (कपास)", icon: "🌱" },
    { value: "sugarcane", label: "Sugarcane (गन्ना)", icon: "🎋" },
    { value: "maize", label: "Maize (मक्का)", icon: "🌽" },
    { value: "soyabean", label: "Soybean (सोयाबीन)", icon: "🫘" },
  ];

  const fetchPredictions = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      // Fetch APIs independently so one failure doesn't block others
      const [predResult, marketResult] = await Promise.allSettled([
        priceAPI.getPrediction(selectedCrop, predictionDays),
        priceAPI.compareMarkets(selectedCrop),
      ]);

      // Handle prediction result (main data)
      if (predResult.status === "fulfilled") {
        setPrediction(predResult.value);
      } else {
        logger.error("Prediction error", {
          error: predResult.reason,
          component: "PricePrediction",
        });
        setError("Failed to fetch price predictions. Please try again.");
        return;
      }

      // Handle market comparison (optional)
      if (marketResult.status === "fulfilled") {
        setMarketComparison(marketResult.value);
      } else {
        logger.warn("Market comparison unavailable", {
          error: marketResult.reason,
        });
        setMarketComparison(null);
      }
    } catch (err) {
      setError("Failed to fetch price data. Please try again.");
      logger.error("Failed to fetch price data", { error: err });
    } finally {
      setLoading(false);
    }
  }, [selectedCrop, predictionDays]);

  // ✅ Clean useEffect
  useEffect(() => {
    fetchPredictions();
  }, [fetchPredictions]);

  // ✅ Safely prepare chart data
  const priceChartData =
    prediction?.historical_data && prediction?.predictions
      ? [
          ...prediction.historical_data.slice(-30).map((item) => ({
            date: new Date(item.date).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            }),
            actual: item.price,
            type: "Historical",
          })),
          ...prediction.predictions.map((item) => ({
            date: new Date(item.date).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            }),
            predicted: item.predicted_price,
            type: "Predicted",
          })),
        ]
      : [];

  const getRecommendationColor = (recommendation: string) => {
    if (recommendation.startsWith("SELL NOW"))
      return "bg-red-100 border-red-500 text-red-700";
    if (recommendation.startsWith("SELL"))
      return "bg-orange-100 border-orange-500 text-orange-700";
    if (recommendation.startsWith("HOLD"))
      return "bg-green-100 border-green-500 text-green-700";
    return "bg-blue-100 border-blue-500 text-blue-700";
  };

  return (
    <div className="min-h-full bg-slate-50 p-4 sm:p-8">
      <div className="max-w-7xl mx-auto">
        {" "}
        <div className="mb-8">
          <h1 className="text-3xl font-semibold text-slate-900 mb-2">
            Market Price Prediction
          </h1>
          <p className="text-slate-600">
            AI-powered price forecasts to help you sell at the right time
          </p>
        </div>{" "}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 mb-8">
          <div className="grid md:grid-cols-2 gap-6">
            {" "}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Crop
              </label>
              <div className="grid grid-cols-2 gap-2">
                {crops.map((crop) => (
                  <button
                    key={crop.value}
                    onClick={() => setSelectedCrop(crop.value)}
                    className={`p-3 rounded-lg border-2 transition ${
                      selectedCrop === crop.value
                        ? "border-green-500 bg-green-50"
                        : "border-gray-200 hover:border-green-300"
                    }`}
                  >
                    <span className="text-2xl mr-2">{crop.icon}</span>
                    <span className="text-sm font-medium">{crop.label}</span>
                  </button>
                ))}
              </div>
            </div>{" "}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Prediction Period: {predictionDays} days
              </label>
              <input
                type="range"
                min="7"
                max="90"
                step="1"
                value={predictionDays}
                onChange={(e) => setPredictionDays(Number(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-green-600"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>7 days</span>
                <span>90 days</span>
              </div>
            </div>
          </div>
        </div>
        {error && (
          <div className="mb-8 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={fetchPredictions}
              className="ml-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm font-medium"
            >
              Retry
            </button>
          </div>
        )}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading predictions...</p>
            </div>
          </div>
        ) : (
          prediction && (
            <>
              {" "}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 mb-8">
                <div className="bg-white p-6 rounded-xl shadow-lg">
                  <div className="flex items-center justify-between mb-4">
                    <DollarSign className="text-blue-500" size={32} />
                    <span className="text-sm text-gray-500">Current Price</span>
                  </div>
                  <p className="text-3xl font-bold text-gray-800">
                    ₹{prediction.current_price}
                  </p>
                  <p className="text-sm text-gray-600 mt-2">per quintal</p>
                </div>

                <div className="bg-white p-6 rounded-xl shadow-lg">
                  <div className="flex items-center justify-between mb-4">
                    <TrendingUp className="text-green-500" size={32} />
                    <span className="text-sm text-gray-500">Predicted Avg</span>
                  </div>
                  <p className="text-3xl font-bold text-gray-800">
                    ₹{prediction.predicted_average}
                  </p>
                  <p className="text-sm text-gray-600 mt-2">
                    next {predictionDays} days
                  </p>
                </div>

                <div className="bg-white p-6 rounded-xl shadow-lg">
                  <div className="flex items-center justify-between mb-4">
                    {prediction.trend === "increasing" ? (
                      <TrendingUp className="text-green-500" size={32} />
                    ) : (
                      <TrendingDown className="text-red-500" size={32} />
                    )}
                    <span className="text-sm text-gray-500">Price Change</span>
                  </div>
                  <p
                    className={`text-3xl font-bold ${
                      prediction.price_change_percentage > 0
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {prediction.price_change_percentage > 0 ? "+" : ""}
                    {prediction.price_change_percentage}%
                  </p>
                  <p className="text-sm text-gray-600 mt-2 capitalize">
                    {prediction.trend}
                  </p>
                </div>

                <div className="bg-emerald-900 p-6 rounded-xl shadow-lg text-white">
                  <div className="flex items-center justify-between mb-4">
                    <AlertCircle size={32} />
                    <span className="text-sm">Trend</span>
                  </div>
                  <p className="text-2xl font-bold capitalize">
                    {prediction.trend}
                  </p>
                  <p className="text-sm mt-2 opacity-90">Market Direction</p>
                </div>
              </div>{" "}
              <div
                className={`mb-8 p-6 rounded-xl border-l-4 ${getRecommendationColor(
                  prediction.recommendation
                )}`}
              >
                <div className="flex items-start">
                  <AlertCircle className="mr-3 shrink-0 mt-1" size={24} />
                  <div>
                    <h3 className="font-semibold text-lg mb-1">
                      Selling Recommendation
                    </h3>
                    <p className="text-sm">{prediction.recommendation}</p>
                  </div>
                </div>
              </div>{" "}
              <div className="bg-white p-6 rounded-xl shadow-lg mb-8">
                <h3 className="text-xl font-semibold text-gray-800 mb-4">
                  Price Trend & Forecast
                </h3>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={priceChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis
                      label={{
                        value: "Price (₹/quintal)",
                        angle: -90,
                        position: "insideLeft",
                      }}
                    />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="actual"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      name="Historical Price"
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="predicted"
                      stroke="#10b981"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name="Predicted Price"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>{" "}
              {marketComparison && (
                <div className="bg-white p-6 rounded-xl shadow-lg">
                  <h3 className="text-xl font-semibold text-gray-800 mb-4">
                    Market Comparison
                  </h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Best market:{" "}
                    <span className="font-semibold text-green-600">
                      {marketComparison.best_market}
                    </span>{" "}
                    - Price difference: ₹{marketComparison.price_difference}
                    /quintal
                  </p>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={marketComparison.comparison}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="mandi" />
                      <YAxis
                        label={{
                          value: "Price (₹/quintal)",
                          angle: -90,
                          position: "insideLeft",
                        }}
                      />
                      <Tooltip />
                      <Bar dataKey="price" fill="#10b981" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
          )
        )}
      </div>
    </div>
  );
};

export default React.memo(PricePrediction);
