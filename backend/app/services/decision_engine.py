
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MarketSignal:
    signal_type: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    strength: float  # 0.0 to 1.0
    reason: str
    data_source: str


@dataclass
class Decision:
    action: str  # 'SELL_NOW', 'WAIT', 'HOLD'
    confidence: float  # 0.0 to 1.0
    reasoning: str
    best_sell_date: Optional[str]
    expected_price: Optional[float]
    risk_level: str  # 'LOW', 'MEDIUM', 'HIGH'
    signals: List[MarketSignal]
    metadata: Dict


class DecisionEngine:
    # Decision thresholds (tuned for Indian agriculture)
    PRICE_DROP_ALERT = -5.0  # Alert if price drops >5%
    PRICE_RISE_OPPORTUNITY = 10.0  # Sell if price rises >10%
    WEATHER_IMPACT_THRESHOLD = 0.3  # Rain probability > 30%
    TREND_STRENGTH_THRESHOLD = 0.6  # Confidence > 60%
    HISTORY_MAX_SIZE = 500  # Cap in-memory history to avoid unbounded growth

    def __init__(self):
        self.decision_history = []
    
    def analyze(
        self,
        crop: str,
        current_price: float,
        predicted_prices: List[Dict],  # [{date, price, confidence}]
        price_trend: Dict,  # {change_7d, change_30d, volatility}
        weather_forecast: Optional[Dict] = None,
        user_preferences: Optional[Dict] = None
    ) -> Decision:
        logger.info(f"🧮 Analyzing {crop} at Rs.{current_price:.2f}/kg")
        
        signals = []
        
        # Signal 1: Price Prediction Analysis
        price_signal = self._analyze_price_predictions(
            current_price, predicted_prices
        )
        signals.append(price_signal)
        
        # Signal 2: Price Trend Analysis
        trend_signal = self._analyze_price_trend(price_trend)
        signals.append(trend_signal)
        
        # Signal 3: Weather Impact
        if weather_forecast:
            weather_signal = self._analyze_weather_impact(
                crop, weather_forecast
            )
            signals.append(weather_signal)
        
        # Signal 4: Volatility Risk
        volatility_signal = self._analyze_volatility(price_trend)
        signals.append(volatility_signal)
        
        # Combine signals into decision
        decision = self._make_decision(
            crop, current_price, predicted_prices, signals, user_preferences
        )
        
        # Store for learning
        self.decision_history.append({
            'timestamp': datetime.now(),
            'crop': crop,
            'decision': decision
        })
        if len(self.decision_history) > self.HISTORY_MAX_SIZE:
            # Trim oldest entries — keeps memory bounded in long-running process
            self.decision_history = self.decision_history[-self.HISTORY_MAX_SIZE:]

        return decision
    
    def _analyze_price_predictions(
        self, 
        current_price: float,
        predictions: List[Dict]
    ) -> MarketSignal:
        if not predictions or len(predictions) == 0:
            return MarketSignal(
                signal_type='NEUTRAL',
                strength=0.0,
                reason="No prediction data available",
                data_source='ML_MODEL'
            )
        
        # Get 7-day prediction
        future_price = predictions[min(6, len(predictions)-1)]['price']
        price_change = ((future_price - current_price) / current_price) * 100
        avg_confidence = np.mean([p['confidence'] for p in predictions])
        
        # Determine signal
        if price_change > self.PRICE_RISE_OPPORTUNITY:
            signal_type = 'BULLISH'
            strength = min(1.0, price_change / 20.0)  # Cap at 20% = 1.0
            reason = f"Price predicted to rise {price_change:+.1f}% in 7 days (Rs.{current_price:.2f} → Rs.{future_price:.2f})"
        
        elif price_change < self.PRICE_DROP_ALERT:
            signal_type = 'BEARISH'
            strength = min(1.0, abs(price_change) / 20.0)
            reason = f"Price predicted to drop {price_change:.1f}% in 7 days (Rs.{current_price:.2f} → Rs.{future_price:.2f})"
        
        else:
            signal_type = 'NEUTRAL'
            strength = 0.3
            reason = f"Price stable around Rs.{current_price:.2f}/kg (change: {price_change:+.1f}%)"
        
        # Adjust strength by confidence
        strength *= avg_confidence
        
        return MarketSignal(
            signal_type=signal_type,
            strength=strength,
            reason=reason,
            data_source='ML_MODEL'
        )
    
    def _analyze_price_trend(self, trend: Dict) -> MarketSignal:
        change_7d = trend.get('change_7d', 0)
        change_30d = trend.get('change_30d', 0)
        
        # Strong uptrend
        if change_7d > 5 and change_30d > 10:
            return MarketSignal(
                signal_type='BULLISH',
                strength=0.8,
                reason=f"Strong upward trend: +{change_7d:.1f}% (7d), +{change_30d:.1f}% (30d)",
                data_source='HISTORICAL_TREND'
            )
        
        # Strong downtrend
        elif change_7d < -5 and change_30d < -10:
            return MarketSignal(
                signal_type='BEARISH',
                strength=0.8,
                reason=f"Strong downward trend: {change_7d:.1f}% (7d), {change_30d:.1f}% (30d)",
                data_source='HISTORICAL_TREND'
            )
        
        # Reversal pattern (7d up but 30d down)
        elif change_7d > 5 and change_30d < -5:
            return MarketSignal(
                signal_type='BULLISH',
                strength=0.6,
                reason=f"Price recovering: +{change_7d:.1f}% this week after 30d decline",
                data_source='HISTORICAL_TREND'
            )
        
        else:
            return MarketSignal(
                signal_type='NEUTRAL',
                strength=0.3,
                reason=f"Stable trend: {change_7d:+.1f}% (7d), {change_30d:+.1f}% (30d)",
                data_source='HISTORICAL_TREND'
            )
    
    def _analyze_weather_impact(
        self, 
        crop: str, 
        forecast: Dict
    ) -> MarketSignal:
        # Weather-sensitive crops
        perishables = ['tomato', 'onion', 'potato']
        grains = ['wheat', 'rice', 'soyabean']
        
        # Extract rain probability from forecast
        rain_days = 0
        total_rain = 0
        
        if 'list' in forecast:
            for item in forecast['list'][:5]:  # Next 5 days
                if 'rain' in item:
                    rain_days += 1
                    total_rain += item.get('rain', {}).get('3h', 0)
        
        rain_probability = rain_days / 5.0 if forecast.get('list') else 0
        
        # Decision logic based on crop type
        if crop.lower() in perishables and rain_probability > self.WEATHER_IMPACT_THRESHOLD:
            return MarketSignal(
                signal_type='BULLISH',
                strength=0.7,
                reason=f"Heavy rain forecast ({rain_days} days). {crop.title()} prices likely to spike due to supply disruption. SELL NOW before spoilage.",
                data_source='WEATHER_FORECAST'
            )
        
        elif crop.lower() in grains and rain_probability > 0.5:
            return MarketSignal(
                signal_type='BEARISH',
                strength=0.4,
                reason=f"Good rainfall forecast. {crop.title()} supply will improve, prices may soften.",
                data_source='WEATHER_FORECAST'
            )
        
        else:
            return MarketSignal(
                signal_type='NEUTRAL',
                strength=0.2,
                reason=f"Normal weather conditions. Minimal price impact expected.",
                data_source='WEATHER_FORECAST'
            )
    
    def _analyze_volatility(self, trend: Dict) -> MarketSignal:
        volatility = trend.get('volatility', 0)
        
        if volatility > 15:
            return MarketSignal(
                signal_type='BEARISH',
                strength=0.5,
                reason=f"High price volatility ({volatility:.1f}%). Risky to hold - consider selling.",
                data_source='VOLATILITY_INDEX'
            )
        
        elif volatility < 5:
            return MarketSignal(
                signal_type='NEUTRAL',
                strength=0.3,
                reason=f"Low volatility ({volatility:.1f}%). Stable market conditions.",
                data_source='VOLATILITY_INDEX'
            )
        
        else:
            return MarketSignal(
                signal_type='NEUTRAL',
                strength=0.4,
                reason=f"Moderate volatility ({volatility:.1f}%). Normal market fluctuations.",
                data_source='VOLATILITY_INDEX'
            )
    
    def _make_decision(
        self,
        crop: str,
        current_price: float,
        predictions: List[Dict],
        signals: List[MarketSignal],
        user_preferences: Optional[Dict]
    ) -> Decision:
        # Calculate weighted score
        bullish_score = sum(s.strength for s in signals if s.signal_type == 'BULLISH')
        bearish_score = sum(s.strength for s in signals if s.signal_type == 'BEARISH')
        
        total_signals = len(signals)
        confidence = (bullish_score + bearish_score) / total_signals if total_signals > 0 else 0.5
        
        # Get user risk tolerance (default: medium)
        risk_tolerance = user_preferences.get('risk_tolerance', 'medium') if user_preferences else 'medium'
        
        # Decision rules
        if bearish_score > 1.5:  # Strong sell signal
            action = 'SELL_NOW'
            risk_level = 'HIGH'
            reasoning = self._format_reasoning(signals, 'SELL_NOW')
            best_sell_date = datetime.now().strftime('%Y-%m-%d')
            expected_price = current_price
        
        elif bullish_score > 1.5:  # Strong hold signal
            action = 'WAIT'
            risk_level = 'LOW'
            reasoning = self._format_reasoning(signals, 'WAIT')
            # Find peak price in predictions
            if predictions:
                peak = max(predictions, key=lambda x: x['price'])
                best_sell_date = peak['date']
                expected_price = peak['price']
            else:
                best_sell_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                expected_price = current_price * 1.1
        
        else:  # Neutral
            action = 'HOLD'
            risk_level = 'MEDIUM'
            reasoning = self._format_reasoning(signals, 'HOLD')
            best_sell_date = None
            expected_price = current_price
        
        # Adjust for risk tolerance
        if risk_tolerance == 'low' and action == 'WAIT':
            action = 'SELL_NOW'
            reasoning += "\n\n[WARNING] Adjusted to SELL_NOW based on your low risk tolerance."
        
        return Decision(
            action=action,
            confidence=min(confidence, 1.0),
            reasoning=reasoning,
            best_sell_date=best_sell_date,
            expected_price=expected_price,
            risk_level=risk_level,
            signals=signals,
            metadata={
                'crop': crop,
                'current_price': current_price,
                'analysis_date': datetime.now().isoformat(),
                'bullish_score': bullish_score,
                'bearish_score': bearish_score
            }
        )
    
    def _format_reasoning(self, signals: List[MarketSignal], action: str) -> str:
        reasoning_parts = [f"**Decision: {action}**\n"]
        
        reasoning_parts.append("**Analysis:**")
        for i, signal in enumerate(signals, 1):
            emoji = "[UP]" if signal.signal_type == 'BULLISH' else "[DOWN]" if signal.signal_type == 'BEARISH' else "[RIGHT]"
            reasoning_parts.append(f"{i}. {emoji} {signal.reason} (Confidence: {signal.strength:.0%})")
        
        if action == 'SELL_NOW':
            reasoning_parts.append("\n**Recommendation:** Sell immediately to avoid losses or lock in profits.")
        elif action == 'WAIT':
            reasoning_parts.append("\n**Recommendation:** Hold your stock. Price is expected to rise further.")
        else:
            reasoning_parts.append("\n**Recommendation:** Monitor the market. No urgent action needed.")
        
        return "\n".join(reasoning_parts)


# Singleton instance
decision_engine = DecisionEngine()
