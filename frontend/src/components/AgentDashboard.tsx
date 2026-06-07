import { useState, useEffect } from "react";
import {
  TrendingUp,
  Loader,
  CheckCircle,
  AlertTriangle,
  Clock,
  Target,
  BarChart3,
  Share2,
  Download,
  Calculator,
} from "lucide-react";
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";
import { agentAPI, priceAPI } from "../services/api";
import type { AgentAnalysis } from "../services/api";
import { CROPS, CITIES } from "../config/constants";
import { useToast } from "./ui/Toast";

interface HistoryItem {
  id: string;
  crop: string;
  city: string;
  days: number;
  timestamp: string;
  result: AgentAnalysis;
}

interface ChartDataPoint {
  date: string;
  historical?: number;
  predicted?: number;
}

interface HistoricalPriceItem {
  date: string;
  price: number;
}

interface PredictionItem {
  date: string;
  predicted_price: number;
}

interface MarketSignal {
  signal_type: string;
  explanation: string;
  signal: string;
  strength: number;
}

export default function AgentDashboard() {
  const [selectedCrop, setSelectedCrop] = useState("wheat");
  const [selectedCity, setSelectedCity] = useState("Delhi");
  const [selectedDays, setSelectedDays] = useState(7);
  const [quantity, setQuantity] = useState<number>(100);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AgentAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const { showToast } = useToast();

  const crops = CROPS;

  const cities = CITIES;

  const dayOptions = [
    { value: 7, label: "7 Days" },
    { value: 30, label: "30 Days" },
    { value: 90, label: "90 Days" },
    { value: 180, label: "180 Days" },
  ];

  useEffect(() => {
    try {
      const savedHistory = localStorage.getItem("agri_analysis_history");
      if (savedHistory) {
        const parsed = JSON.parse(savedHistory);
        if (Array.isArray(parsed)) {
          setHistory(parsed.slice(0, 10)); // Limit to 10 items
        }
      }
    } catch (err) {
      console.warn('Failed to load analysis history:', err);
      localStorage.removeItem("agri_analysis_history"); // Clear corrupted data
    }
  }, []);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await agentAPI.analyzeCrop(selectedCrop, selectedCity, selectedDays);
      setAnalysis(result);

      const historicalData = await priceAPI.getHistorical(selectedCrop, 30);
      const predictionData = await priceAPI.getPrediction(selectedCrop, selectedDays);

      const combined: ChartDataPoint[] = [];
      if (historicalData?.prices) {
        historicalData.prices.forEach((item: HistoricalPriceItem) => {
          combined.push({
            date: new Date(item.date).toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
            historical: item.price,
          });
        });
      }
      if (predictionData?.predictions) {
        predictionData.predictions.forEach((item: PredictionItem) => {
          combined.push({
            date: new Date(item.date).toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
            predicted: item.predicted_price,
          });
        });
      }
      setChartData(combined);

      const newHistoryItem: HistoryItem = {
        id: Date.now().toString(),
        crop: selectedCrop,
        city: selectedCity,
        days: selectedDays,
        timestamp: new Date().toISOString(),
        result: result,
      };
      const updatedHistory = [newHistoryItem, ...history].slice(0, 10);
      setHistory(updatedHistory);
      localStorage.setItem("agri_analysis_history", JSON.stringify(updatedHistory));
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to analyze. Please try again.";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleShare = () => {
    if (!analysis) return;
    const shareText = `${selectedCrop.toUpperCase()} Price Analysis\nCurrent: ₹${analysis.current_price}/kg\nPredicted: ₹${analysis.predicted_price}/kg\nAction: ${analysis.decision.action}\n\nVia AgriAI`;
    if (navigator.share) {
      navigator.share({ title: "AgriAI Analysis", text: shareText }).catch(() => { });
    } else {
      navigator.clipboard.writeText(shareText);
      showToast("Copied to clipboard!", "success");
    }
  };

  const handleDownload = () => {
    if (!analysis) return;
    const data = { crop: selectedCrop, city: selectedCity, days: selectedDays, analysis, timestamp: new Date().toISOString() };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `agri-analysis-${selectedCrop}-${Date.now()}.json`;
    a.click();
  };

  const profitCalc = analysis?.predicted_price ? {
    currentTotal: analysis.current_price * quantity,
    predictedTotal: analysis.predicted_price * quantity,
    profit: (analysis.predicted_price - analysis.current_price) * quantity,
  } : null;

  const getActionStyle = (action: string) => {
    switch (action) {
      case "SELL_NOW": return { bg: "bg-red-50", border: "border-red-200", text: "text-red-700", icon: AlertTriangle };
      case "WAIT": return { bg: "bg-emerald-50", border: "border-emerald-200", text: "text-emerald-700", icon: CheckCircle };
      case "HOLD": return { bg: "bg-slate-100", border: "border-slate-300", text: "text-slate-700", icon: Clock };
      default: return { bg: "bg-slate-50", border: "border-slate-200", text: "text-slate-700", icon: Target };
    }
  };

  // Helper to clean text and return numbered points
  const formatAnalysisText = (text: string): string[] => {
    if (!text) return [];
    const cleaned = text
      .replace(/\*\*/g, '')
      .replace(/\[RIGHT\]/gi, '')
      .replace(/\[WRONG\]/gi, '')
      .replace(/Decision:\s*/gi, '')
      .replace(/Analysis:\s*/gi, '')
      .replace(/Recommendation:\s*/gi, '')
      .replace(/HOLD|WAIT|SELL_NOW|BUY/gi, '');

    // Split by numbered points
    const points = cleaned.split(/(?=\d+\.\s)/).map(s => s.trim()).filter(s => s.length > 5);
    return points;
  };

  return (
    <div className="min-h-screen bg-slate-50 p-4 sm:p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-2">AI Crop Advisor</h1>
          <p className="text-slate-600">Get smart price predictions to maximize your farming profits</p>
        </div>

        {/* Input Card */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 sm:p-8 mb-6">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Crop</label>
              <select
                value={selectedCrop}
                onChange={(e) => setSelectedCrop(e.target.value)}
                className="w-full px-4 py-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
              >
                {crops.map((c) => (
                  <option key={c.value} value={c.value}>{c.icon} {c.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Market Location</label>
              <select
                value={selectedCity}
                onChange={(e) => setSelectedCity(e.target.value)}
                className="w-full px-4 py-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
              >
                {cities.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Forecast</label>
              <select
                value={selectedDays}
                onChange={(e) => setSelectedDays(Number(e.target.value))}
                className="w-full px-4 py-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
              >
                {dayOptions.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Quantity (kg)</label>
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
                min="1"
                className="w-full px-4 py-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
              />
            </div>
          </div>

          <div className="mt-6 flex flex-col sm:flex-row gap-3">
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="flex-1 sm:flex-none px-8 py-3 bg-emerald-900 text-white font-semibold rounded-lg hover:bg-emerald-800 disabled:bg-slate-400 transition flex items-center justify-center gap-2"
            >
              {loading ? <><Loader size={20} className="animate-spin" /> Analyzing...</> : <><TrendingUp size={20} /> Get Recommendation</>}
            </button>

            {analysis && (
              <div className="flex gap-2">
                <button onClick={handleShare} className="px-4 py-3 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 flex items-center gap-2">
                  <Share2 size={18} /> Share
                </button>
                <button onClick={handleDownload} className="px-4 py-3 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 flex items-center gap-2">
                  <Download size={18} /> Export
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg flex items-start gap-3">
            <AlertTriangle size={20} className="shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">Analysis failed</p>
              <p className="text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="space-y-6 animate-pulse">
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <div className="h-8 bg-slate-200 rounded w-1/3 mb-4"></div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="h-24 bg-slate-100 rounded-lg"></div>
                <div className="h-24 bg-slate-100 rounded-lg"></div>
                <div className="h-24 bg-slate-100 rounded-lg"></div>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {analysis && !loading && (
          <div className="space-y-6">
            {/* Decision */}
            {(() => {
              const style = getActionStyle(analysis.decision.action);
              const Icon = style.icon;
              return (
                <div className={`rounded-xl p-6 ${style.bg} border ${style.border}`}>
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <Icon size={32} className={style.text} />
                      <div>
                        <p className="text-sm text-slate-600">Recommendation</p>
                        <p className={`text-2xl font-bold ${style.text}`}>{analysis.decision.action.replace('_', ' ')}</p>
                      </div>
                    </div>
                    <div className="flex gap-6 text-sm">
                      <div><p className="text-slate-500">Confidence</p><p className="font-semibold text-slate-900">{Math.round(analysis.decision.confidence * 100)}%</p></div>
                      <div><p className="text-slate-500">Risk</p><p className="font-semibold text-slate-900">{analysis.decision.risk_level}</p></div>
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* Price Cards */}
            <div className="grid sm:grid-cols-3 gap-4">
              <div className="bg-white rounded-xl p-6 border border-slate-200">
                <p className="text-sm text-slate-500 mb-1">Current Price</p>
                <p className="text-3xl font-bold text-slate-900">₹{analysis.current_price.toFixed(2)}<span className="text-sm font-normal text-slate-400 ml-1">/kg</span></p>
              </div>
              <div className="bg-white rounded-xl p-6 border border-slate-200">
                <p className="text-sm text-slate-500 mb-1">Predicted ({selectedDays}d)</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-3xl font-bold text-emerald-600">₹{analysis.predicted_price?.toFixed(2) || 'N/A'}<span className="text-sm font-normal text-slate-400 ml-1">/kg</span></p>
                  {analysis.predicted_price && analysis.predicted_price > analysis.current_price && <TrendingUp size={20} className="text-emerald-500" />}
                </div>
              </div>
              <div className={`rounded-xl p-6 border ${analysis.predicted_price && analysis.predicted_price >= analysis.current_price ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'}`}>
                <p className="text-sm text-slate-500 mb-1">{analysis.predicted_price && analysis.predicted_price >= analysis.current_price ? 'Profit' : 'Loss'} per kg</p>
                {analysis.predicted_price ? (
                  <p className={`text-3xl font-bold ${analysis.predicted_price >= analysis.current_price ? 'text-emerald-600' : 'text-red-600'}`}>
                    {analysis.predicted_price >= analysis.current_price ? '+' : ''}₹{(analysis.predicted_price - analysis.current_price).toFixed(2)}
                  </p>
                ) : <p className="text-2xl text-slate-400">N/A</p>}
              </div>
            </div>

            {/* Profit Calculator */}
            {profitCalc && (
              <div className="bg-emerald-900 rounded-xl p-6 text-white">
                <div className="flex items-center gap-2 mb-4">
                  <Calculator size={20} className="text-emerald-300" />
                  <h3 className="font-semibold">Profit Calculator</h3>
                  <span className="text-sm text-emerald-300">({quantity} kg)</span>
                </div>
                <div className="grid sm:grid-cols-3 gap-4">
                  <div className="bg-white/10 rounded-lg p-4">
                    <p className="text-sm text-emerald-200 mb-1">Sell Now</p>
                    <p className="text-2xl font-semibold">₹{Math.round(profitCalc.currentTotal).toLocaleString('en-IN')}</p>
                  </div>
                  <div className="bg-white/10 rounded-lg p-4">
                    <p className="text-sm text-emerald-200 mb-1">Sell in {selectedDays}d</p>
                    <p className="text-2xl font-semibold">₹{Math.round(profitCalc.predictedTotal).toLocaleString('en-IN')}</p>
                  </div>
                  <div className={`rounded-lg p-4 ${profitCalc.profit >= 0 ? 'bg-emerald-700' : 'bg-red-400/80'}`}>
                    <p className="text-sm text-white/80 mb-1">{profitCalc.profit >= 0 ? 'Expected Profit' : 'Expected Loss'}</p>
                    <p className="text-2xl font-semibold text-white">
                      {profitCalc.profit >= 0 ? '+' : ''}₹{Math.abs(Math.round(profitCalc.profit)).toLocaleString('en-IN')}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Chart */}
            {chartData.length > 0 && (
              <div className="bg-white rounded-xl p-6 border border-slate-200">
                <h3 className="font-semibold text-slate-900 mb-4">Price Trend & Forecast</h3>
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="colorHist" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#94a3b8" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="colorPred" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" strokeOpacity={0.5} />
                    <XAxis dataKey="date" stroke="#94a3b8" style={{ fontSize: '11px' }} />
                    <YAxis stroke="#94a3b8" style={{ fontSize: '11px' }} />
                    <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', fontSize: '12px' }} formatter={(v: number) => [`₹${v}/kg`, '']} />
                    <Area type="monotone" dataKey="historical" stroke="#94a3b8" fillOpacity={1} fill="url(#colorHist)" name="Historical" />
                    <Area type="monotone" dataKey="predicted" stroke="#10b981" fillOpacity={1} fill="url(#colorPred)" name="Predicted" strokeDasharray="5 5" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Reason - Numbered list */}
            {analysis.decision.reason && (
              <div className="bg-white rounded-xl p-6 border border-slate-200">
                <h3 className="font-medium text-slate-900 mb-4">Why This Recommendation?</h3>
                <ol className="text-slate-600 text-sm leading-relaxed space-y-2 list-decimal list-inside">
                  {formatAnalysisText(analysis.decision.reason).map((point, idx) => (
                    <li key={idx}>{point.replace(/^\d+\.\s*/, '')}</li>
                  ))}
                </ol>
              </div>
            )}

            {/* AI Insights - Numbered list */}
            {analysis.llm_insights && (
              <div className="bg-emerald-50 rounded-xl p-6 border border-emerald-200">
                <div className="flex items-center gap-2 mb-4">
                  <span className="px-3 py-1 bg-emerald-100 text-emerald-700 text-xs font-medium rounded-full">🤖 AI Expert Analysis</span>
                </div>
                <ol className="text-slate-700 text-sm leading-relaxed space-y-2 list-decimal list-inside">
                  {formatAnalysisText(analysis.llm_insights).map((point, idx) => (
                    <li key={idx}>{point.replace(/^\d+\.\s*/, '')}</li>
                  ))}
                </ol>
              </div>
            )}

            {/* Market Signals */}
            {analysis.market_signals && analysis.market_signals.length > 0 && (
              <div className="bg-white rounded-xl p-6 border border-slate-200">
                <h3 className="font-semibold text-slate-900 mb-4">Market Signals</h3>
                <div className="divide-y divide-slate-100">
                  {analysis.market_signals.slice(0, 4).map((s: MarketSignal, i: number) => (
                    <div key={i} className="py-3 flex items-center justify-between first:pt-0 last:pb-0">
                      <div>
                        <p className="font-medium text-slate-800 text-sm">{s.signal_type}</p>
                        <p className="text-xs text-slate-500">{s.explanation}</p>
                      </div>
                      <div className="text-right">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${s.signal === 'BUY' ? 'bg-emerald-100 text-emerald-700' : s.signal === 'SELL' ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-600'}`}>{s.signal}</span>
                        <p className="text-xs text-slate-400 mt-0.5">{Math.round(s.strength * 100)}%</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!analysis && !loading && !error && (
          <div className="bg-white rounded-xl p-8 border border-slate-200 text-center">
            <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <BarChart3 size={32} className="text-slate-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Ready to Analyze</h3>
            <p className="text-slate-500 text-sm max-w-md mx-auto">
              Select your crop, market location, and forecast period above, then click "Get Recommendation" to see AI-powered price predictions.
            </p>
          </div>
        )}

        {/* History */}
        {history.length > 0 && (
          <div className="mt-8">
            <h3 className="text-sm font-medium text-slate-500 mb-3">Recent Analyses</h3>
            <div className="flex gap-2 overflow-x-auto pb-2">
              {history.slice(0, 5).map((item) => (
                <button
                  key={item.id}
                  onClick={() => { setSelectedCrop(item.crop); setSelectedCity(item.city); setSelectedDays(item.days); setAnalysis(item.result); }}
                  className="shrink-0 px-4 py-2 bg-white border border-slate-200 rounded-lg hover:border-emerald-300 transition text-sm"
                >
                  <span className="font-medium text-slate-800">{item.crop}</span>
                  <span className="text-slate-400 mx-1">•</span>
                  <span className="text-slate-500">{item.city}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
