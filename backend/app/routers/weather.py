
from fastapi import APIRouter, HTTPException, Query, Request
from app.services.weather_service import WeatherService
from app.services.weather_impact_service import weather_impact_service
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.logging_config import logger
from app.core.config import settings

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Environment-aware rate limits
# Development: Higher limits for testing
# Production: Lower limits to prevent abuse
RATE_LIMIT_CURRENT = "1000/hour" if settings.ENVIRONMENT == "development" else "200/hour"
RATE_LIMIT_FORECAST = "1000/hour" if settings.ENVIRONMENT == "development" else "100/hour"
RATE_LIMIT_ALERTS = "1000/hour" if settings.ENVIRONMENT == "development" else "100/hour"


@router.get("/current")
@limiter.limit(RATE_LIMIT_CURRENT)
async def get_current_weather(
    request: Request,
    city: str = Query(..., description="City name"),
    country: str = Query("IN", description="Country code")
):
    try:
        weather_data = WeatherService.get_current_weather(city, country)
        
        if "error" in weather_data:
            logger.warning(f"Weather API error for {city}: {weather_data['error']}")
            raise HTTPException(status_code=400, detail=weather_data["error"])
        
        return weather_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching weather for {city}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch weather data")


@router.get("/forecast")
@limiter.limit(RATE_LIMIT_FORECAST)
async def get_weather_forecast(
    request: Request,
    city: str = Query(..., description="City name"),
    country: str = Query("IN", description="Country code"),
    days: int = Query(5, description="Number of days", ge=1, le=5)
):
    try:
        forecast_data = WeatherService.get_forecast(city, country, days)
        
        if "error" in forecast_data:
            logger.warning(f"Forecast API error for {city}: {forecast_data['error']}")
            raise HTTPException(status_code=400, detail=forecast_data["error"])
        
        return forecast_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching forecast for {city}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch forecast data")


@router.get("/alerts")
@limiter.limit(RATE_LIMIT_ALERTS)
async def get_weather_alerts(
    request: Request, 
    city: str = Query(..., description="City name")
):
    try:
        weather_data = WeatherService.get_current_weather(city)
        
        if "error" in weather_data:
            logger.warning(f"Weather alerts API error for {city}: {weather_data['error']}")
            raise HTTPException(status_code=400, detail=weather_data["error"])
        
        alerts = []
        temp = weather_data["temperature"]
        humidity = weather_data["humidity"]
        wind = weather_data["wind_speed"]
        
        # Temperature alerts
        if temp > 40:
            alerts.append({
                "type": "extreme_heat",
                "severity": "high",
                "message": f"Extreme heat alert! Temperature is {temp}°C. Avoid field work during peak hours.",
                "recommendation": "Work early morning or evening. Ensure adequate water for crops and livestock."
            })
        elif temp > 35:
            alerts.append({
                "type": "heat_warning",
                "severity": "medium",
                "message": f"Heat warning. Temperature is {temp}°C.",
                "recommendation": "Increase irrigation frequency. Provide shade for sensitive crops."
            })
        elif temp < 5:
            alerts.append({
                "type": "frost_warning",
                "severity": "high",
                "message": f"Frost warning! Temperature is {temp}°C.",
                "recommendation": "Cover sensitive plants. Delay sowing of frost-sensitive crops."
            })
        
        # Humidity alerts
        if humidity > 85:
            alerts.append({
                "type": "high_humidity",
                "severity": "medium",
                "message": f"High humidity at {humidity}%. Disease risk increased.",
                "recommendation": "Monitor for fungal diseases. Ensure good air circulation."
            })
        elif humidity < 30:
            alerts.append({
                "type": "low_humidity",
                "severity": "low",
                "message": f"Low humidity at {humidity}%.",
                "recommendation": "Increase irrigation. Consider mulching to retain soil moisture."
            })
        
        # Wind alerts
        if wind > 15:
            alerts.append({
                "type": "strong_wind",
                "severity": "medium",
                "message": f"Strong winds at {wind} m/s.",
                "recommendation": "Avoid spraying pesticides. Secure greenhouse covers and shade nets."
            })
        
        return {
            "city": city,
            "alerts": alerts,
            "current_conditions": weather_data,
            "timestamp": weather_data.get("timestamp"),
            "cached": weather_data.get("cached", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching alerts for {city}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch weather alerts")


@router.get("/impact/{crop}")
@limiter.limit(RATE_LIMIT_FORECAST)
async def get_weather_impact(
    request: Request,
    crop: str,
    city: str = Query(..., description="City name")
):
    try:
        impact = await weather_impact_service.analyze_weather_impact(crop=crop, city=city)

        if "error" in impact:
            logger.warning(f"Weather impact error for {crop} in {city}: {impact['error']}")
            raise HTTPException(status_code=400, detail=impact["error"])

        return impact
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error analyzing weather impact: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze weather impact")
