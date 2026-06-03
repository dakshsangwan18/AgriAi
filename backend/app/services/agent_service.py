
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from google import genai
import os

from app.services.decision_engine import decision_engine, Decision
from app.services.price_service import PriceService
from app.services.weather_service import WeatherService
from app.services.data_integration_service import data_service
from app.models.user import User
from app.models.prediction_history import PredictionHistory
from app.models.agent_analysis import AgentAnalysis
from app.core.db_session import get_db_session
from app.core.logging_config import logger


class SmartCropAgent:
    
    def __init__(self):
        self.price_service = PriceService()
        self.weather_service = WeatherService()
        
        try:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self.llm = genai.GenerativeModel('gemini-flash-latest')  # Using free tier compatible model
        except Exception as e:
            logger.warning(f"Gemini initialization failed: {e}. LLM insights will be disabled.")
            self.llm = None
    
    def analyze_crop(
        self, 
        crop: str, 
        city: str = "Delhi",
        user_preferences: Optional[Dict] = None,
        days_ahead: int = 7
    ) -> Dict:
        
        start_time = datetime.now()
        logger.info(f"🤖 Agent analyzing {crop} in {city} for {days_ahead} days")
        
        try:
            # Step 1: Gather data (get more historical data for longer predictions)
            historical_days = max(30, days_ahead * 2)  # 2x the prediction period
            price_data = data_service.get_price_data(crop, days=historical_days)
            
            if price_data.empty:
                logger.warning(f"No price data for {crop}")
                return self._create_error_response("No price data available")
            
            current_price = price_data.iloc[-1]['price']
            
            # Step 2: Get price predictions for requested period
            prediction_result = PriceService.predict_prices(crop, days_ahead=days_ahead)
            
            # Convert prediction format to match what decision engine expects
            predictions = []
            if prediction_result and 'predictions' in prediction_result:
                for pred in prediction_result['predictions']:
                    predictions.append({
                        'date': pred['date'],
                        'price': pred['predicted_price'],
                        'confidence': 0.75  # Default confidence
                    })
            
            # Step 3: Calculate price trends
            price_trend = self._calculate_trend(price_data)
            
            # Step 4: Get weather forecast
            weather_forecast = None
            try:
                weather_forecast = self.weather_service.get_forecast(city)
            except Exception as e:
                logger.warning(f"Weather fetch failed: {e}")
            
            # Step 5: Run decision engine (FAST - no LLM calls)
            decision = decision_engine.analyze(
                crop=crop,
                current_price=current_price,
                predicted_prices=predictions,
                price_trend=price_trend,
                weather_forecast=weather_forecast,
                user_preferences=user_preferences
            )
            
            # Step 6: Get LLM insights (optional, for explanation only)
            llm_insights = self._get_llm_insights(crop, decision)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[OK] Analysis complete in {elapsed:.2f}s")
            
            # Convert MarketSignal dataclasses to dicts for JSON serialization
            market_signals = [
                {
                    'signal_type': s.data_source,
                    'signal': s.signal_type,
                    'strength': s.strength,
                    'explanation': s.reason
                }
                for s in decision.signals
            ]
            
            # Save analysis to database using context manager
            with get_db_session() as save_db:
                # Use the LAST prediction (end of period) not the first
                final_predicted_price = float(predictions[-1]['price']) if predictions else None
                
                analysis_record = AgentAnalysis(
                    crop=crop,
                    city=city,
                    current_price=float(current_price),  # Convert numpy float to Python float
                    predicted_price=final_predicted_price,  # Price at end of prediction period
                    action=decision.action,
                    confidence=float(decision.confidence),  # Convert numpy float to Python float
                    reason=decision.reasoning,
                    best_action_date=decision.best_sell_date,
                    expected_price=float(decision.expected_price) if decision.expected_price else None,
                    risk_level=decision.risk_level,
                    market_signals=market_signals,
                    llm_insights=llm_insights,
                    analysis_duration=elapsed
                )
                save_db.add(analysis_record)
                save_db.flush()  # Assign primary key before we log it
                logger.info(f" Analysis saved to database (ID: {analysis_record.id})")
                    
            # Format response to match frontend expectations
            final_predicted_price = predictions[-1]['price'] if predictions else None
            
            return {
                'crop': crop,
                'city': city,
                'current_price': current_price,
                'predicted_price': final_predicted_price,  # Price at end of prediction period
                'days_ahead': days_ahead,  # Include prediction period in response
                'decision': {
                    'action': decision.action,
                    'confidence': decision.confidence,
                    'reason': decision.reasoning,
                    'best_action_date': decision.best_sell_date,
                    'expected_price': decision.expected_price,
                    'risk_level': decision.risk_level
                },
                'market_signals': market_signals,
                'llm_insights': llm_insights,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            return self._create_error_response(str(e))
    
    def _calculate_trend(self, price_data) -> Dict:
        
        if len(price_data) < 7:
            return {'change_7d': 0, 'change_30d': 0, 'volatility': 0}
        
        prices = price_data['price'].values
        
        # 7-day change
        change_7d = ((prices[-1] - prices[-7]) / prices[-7]) * 100 if len(prices) >= 7 else 0
        
        # 30-day change
        change_30d = ((prices[-1] - prices[-30]) / prices[-30]) * 100 if len(prices) >= 30 else 0
        
        # Volatility (standard deviation)
        volatility = (prices.std() / prices.mean()) * 100 if len(prices) > 1 else 0
        
        return {
            'change_7d': change_7d,
            'change_30d': change_30d,
            'volatility': volatility
        }
    
    def _get_llm_insights(self, crop: str, decision: Decision) -> str:
        
        if not self.llm:
            return decision.reasoning  # Fallback if LLM not initialized
        
        try:
            prompt = f"""You are an agricultural advisor. Explain this crop analysis to a farmer in simple Hindi-English mix (Hinglish).

Crop: {crop}
Decision: {decision.action}
Reasoning: {decision.reasoning}
Risk Level: {decision.risk_level}

Create a SHORT (3-4 lines) WhatsApp-style message explaining:
1. What should farmer do NOW
2. Why (in simple words)
3. Expected outcome

Keep it practical and friendly. Use Rs. for prices."""

            response = self.llm.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.warning(f"LLM insights failed: {e}")
            return decision.reasoning  # Fallback to rule-based reasoning
    
    def _create_error_response(self, error: str) -> Dict:
        return {
            'action': 'HOLD',
            'confidence': 0.0,
            'reasoning': f"Analysis failed: {error}",
            'risk_level': 'UNKNOWN',
            'timestamp': datetime.now().isoformat()
        }
    
    def run_daily_monitoring(self) -> List[Dict]:
        logger.info(" Running daily automated monitoring...")
        
        alerts = []
        
        with get_db_session() as db:
            # Get all active users with notifications enabled
            users = db.query(User).filter(
                User.is_active == True,
                User.notification_enabled == True
            ).all()
            
            logger.info(f"[DATA] Monitoring {len(users)} active users")
            
            for user in users:
                # Get user's favorite crops
                favorite_crops = user.favorite_crops if user.favorite_crops else []
                
                # If no favorites set, skip this user
                if not favorite_crops:
                    logger.info(f"⏭ Skipping {user.email} - no favorite crops set")
                    continue
                
                logger.info(f" Analyzing {len(favorite_crops)} crops for {user.email}")
                
                # Get user's location (default to Delhi if not set)
                city = user.location if user.location else "Delhi"
                
                # Analyze each favorite crop
                for crop in favorite_crops:
                    try:
                        analysis = self.analyze_crop(crop, city)
                        decision = analysis.get('decision') or {}
                        action = decision.get('action')
                        confidence = decision.get('confidence', 0)

                        # Create alert if action needed
                        if action in ['SELL_NOW', 'WAIT'] and confidence > 0.6:
                            alert = {
                                'user_id': user.id,
                                'user_email': user.email,
                                'crop': crop,
                                'action': action,
                                'reasoning': (analysis.get('llm_insights') or decision.get('reason', ''))[:500],
                                'confidence': confidence,
                                'expected_price': decision.get('expected_price'),
                                'timestamp': analysis.get('timestamp')
                            }
                            alerts.append(alert)
                            logger.info(f" Alert created for {user.email}: {crop} - {action}")
                    except Exception as e:
                        logger.error(f"Error analyzing {crop} for {user.email}: {str(e)}")
                        continue
            
            logger.info(f"[OK] Daily monitoring complete! Created {len(alerts)} alerts")
            return alerts


# Singleton instance
smart_agent = SmartCropAgent()
