import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from typing import Dict
from app.services.data_integration_service import data_service
from app.core.cache import cache_manager
from app.core.logging_config import logger

# Cache TTL constants
PRICE_PREDICTION_CACHE_TTL = 1800  # 30 minutes for predictions
PRICE_LIST_CACHE_TTL = 3600  # 1 hour for price lists

class PriceService:
    # Crop list for reference
    CROPS = ["wheat", "rice", "tomato", "onion", "potato", "cotton", "sugarcane", "maize", "soyabean"]
    CROP_ALIASES = {
        "corn": "maize",
        "soybean": "soyabean",
    }

    @staticmethod
    def normalize_crop(crop: str) -> str:
        crop_normalized = (crop or "").strip().lower()
        return PriceService.CROP_ALIASES.get(crop_normalized, crop_normalized)
    
    @staticmethod
    def predict_prices(crop: str, days_ahead: int = 30, use_real_data: bool = True) -> Dict:
        cache_key = f"{crop}:{days_ahead}:{use_real_data}"
        
        # Try to get from cache first
        cached = cache_manager.get("prices:prediction", cache_key)
        if cached:
            logger.info(f"Price prediction cache hit for {crop}", endpoint="prices")
            cached['cached'] = True
            return cached
        
        try:
            logger.info(f"Predicting prices for {crop} ({days_ahead} days ahead)")
            
            # Get historical data (180 days)
            historical_df = data_service.get_price_data(
                crop=crop, 
                days=180, 
                force_synthetic=not use_real_data
            )
            
            if historical_df.empty:
                return {"error": f"No data available for {crop}"}
            
            # Check data source
            data_source = "real_api" if 'mandi' in historical_df.columns and historical_df['mandi'].iloc[0] != 'Synthetic' else "synthetic"
            
            # Prepare data for ML model
            historical_df = historical_df.sort_values('date')
            historical_df['days_since_start'] = range(len(historical_df))
            
            X = historical_df[['days_since_start']].values
            y = historical_df['price'].values
            
            # Train linear regression model
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict future prices
            last_day = len(historical_df)
            future_days = np.array([[last_day + i] for i in range(1, days_ahead + 1)])
            predictions = model.predict(future_days)
            
            # Create prediction dataframe
            future_dates = pd.date_range(
                start=datetime.now() + timedelta(days=1),
                periods=days_ahead,
                freq='D'
            )
            
            prediction_df = pd.DataFrame({
                'date': future_dates,
                'predicted_price': predictions,
                'crop': crop.lower()
            })
            
            # Calculate statistics
            current_price = historical_df['price'].iloc[-1]
            predicted_avg = predictions.mean()
            price_change = ((predicted_avg - current_price) / current_price) * 100
            
            # Get last 30 days for display
            recent_history = historical_df.tail(30)[['date', 'price', 'crop']].to_dict('records')
            
            # [OK] Updated: Convert dates safely for JSON serialization
            for record in recent_history:
                if isinstance(record['date'], pd.Timestamp):
                    record['date'] = record['date'].strftime('%Y-%m-%d')
                elif hasattr(record['date'], 'strftime'):
                    record['date'] = record['date'].strftime('%Y-%m-%d')
                else:
                    record['date'] = str(record['date'])

            predictions_list = prediction_df.to_dict('records')
            for record in predictions_list:
                if isinstance(record['date'], pd.Timestamp):
                    record['date'] = record['date'].strftime('%Y-%m-%d')
                elif hasattr(record['date'], 'strftime'):
                    record['date'] = record['date'].strftime('%Y-%m-%d')
                else:
                    record['date'] = str(record['date'])
            
            result = {
                "crop": crop.lower(),
                "current_price": round(float(current_price), 2),
                "predicted_average": round(float(predicted_avg), 2),
                "price_change_percentage": round(float(price_change), 2),
                "trend": "increasing" if price_change > 0 else "decreasing",
                "historical_data": recent_history,
                "predictions": predictions_list,
                "recommendation": PriceService._get_recommendation(price_change),
                "data_source": data_source,
                "records_analyzed": len(historical_df),
                "ml_model": "Linear Regression",
                "confidence": "medium",
                "cached": False
            }
            
            # Cache the result
            cache_manager.set("prices:prediction", cache_key, result, PRICE_PREDICTION_CACHE_TTL)
            
            return result
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Error predicting prices: {str(e)}", exc_info=e, endpoint="prices")
            return {"error": str(e), "traceback": error_trace}
    
    @staticmethod
    def _get_recommendation(price_change: float) -> str:
        if price_change > 10:
            return "HOLD - Prices expected to rise significantly. Wait for better rates."
        elif price_change > 5:
            return "HOLD - Moderate price increase expected. Consider waiting."
        elif price_change > -5:
            return "NEUTRAL - Stable prices. Sell based on your needs."
        elif price_change > -10:
            return "SELL - Slight price decline expected. Consider selling soon."
        else:
            return "SELL NOW - Significant price drop expected. Sell immediately."
    
    @staticmethod
    def get_market_comparison(crop: str) -> Dict:
        try:
            logger.info(f"Getting market comparison for {crop}")
            
            # Get recent data (last 7 days)
            df = data_service.get_price_data(crop=crop, days=7, force_synthetic=False)
            
            if df.empty:
                return {"error": f"No data available for {crop}"}
            
            # Check if we have real mandi data
            if 'mandi' in df.columns and df['mandi'].iloc[0] != 'Synthetic':
                # Group by mandi and calculate average
                mandi_avg = df.groupby('mandi')['price'].mean().reset_index()
                
                comparison = []
                for _, row in mandi_avg.iterrows():
                    comparison.append({
                        "mandi": row['mandi'],
                        "price": round(float(row['price']), 2),
                        "variation_percent": 0
                    })
                
                # Calculate variation from mean
                if comparison:
                    mean_price = np.mean([m["price"] for m in comparison])
                    for market in comparison:
                        market["variation_percent"] = round(
                            ((market["price"] - mean_price) / mean_price) * 100, 2
                        )
                    
                    # Sort by price
                    comparison.sort(key=lambda x: x['price'], reverse=True)
                    
                    return {
                        "crop": crop.lower(),
                        "comparison": comparison[:10],  # Top 10 mandis
                        "best_market": comparison[0]["mandi"],
                        "price_difference": round(comparison[0]["price"] - comparison[-1]["price"], 2),
                        "data_source": "real_api",
                        "period": "last_7_days"
                    }
            
            # Fallback to synthetic comparison
            return PriceService._synthetic_market_comparison(crop, df)
            
        except Exception as e:
            logger.error(f"Error in market comparison: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _synthetic_market_comparison(crop: str, df: pd.DataFrame) -> Dict:
        mandis = ["Delhi", "Mumbai", "Kolkata", "Chennai", "Bangalore", "Hyderabad"]
        
        avg_price = df['price'].mean()
        
        comparison = []
        for mandi in mandis:
            variation = np.random.uniform(-15, 15)
            price = avg_price + (avg_price * variation / 100)
            
            comparison.append({
                "mandi": mandi,
                "price": round(float(price), 2),
                "variation_percent": round(variation, 2)
            })
        
        comparison.sort(key=lambda x: x['price'], reverse=True)
        
        return {
            "crop": crop.lower(),
            "comparison": comparison,
            "best_market": comparison[0]["mandi"],
            "price_difference": round(comparison[0]["price"] - comparison[-1]["price"], 2),
            "data_source": "synthetic",
            "period": "estimated"
        }
