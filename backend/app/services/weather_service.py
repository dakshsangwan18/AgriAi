import os
import requests
import random
from dotenv import load_dotenv
from datetime import datetime
from app.core.cache import cache_manager
from app.core.logging_config import logger

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5"

# Cache TTL constants
WEATHER_CACHE_TTL = 3600  # 1 hour for current weather
FORECAST_CACHE_TTL = 7200  # 2 hours for forecasts


class WeatherService:
    @staticmethod
    def _mock_current_weather(city: str, country_code: str = "IN") -> dict:
        """Return deterministic mock weather when no API key is configured."""
        # Use the city name to seed values so the same city always gets similar weather.
        seed = sum(ord(c) for c in f"{city.lower()}:{country_code.lower()}")
        rng = random.Random(seed)

        temperature = round(rng.uniform(20, 40), 1)
        return {
            "city": city.title(),
            "temperature": temperature,
            "feels_like": round(temperature + rng.uniform(-3, 3), 1),
            "humidity": int(rng.uniform(30, 90)),
            "description": rng.choice(["clear sky", "few clouds", "scattered clouds", "light rain"]),
            "wind_speed": round(rng.uniform(1, 10), 1),
            "timestamp": datetime.now().isoformat(),
            "cached": False,
            "data_source": "mock",
        }

    @staticmethod
    def _mock_forecast(city: str, country_code: str = "IN", days: int = 5) -> dict:
        """Return deterministic mock forecast when no API key is configured."""
        seed = sum(ord(c) for c in f"{city.lower()}:{country_code.lower()}")
        rng = random.Random(seed)
        forecasts = []
        for i in range(days * 8):  # 8 forecasts per day
            temperature = round(rng.uniform(20, 40), 1)
            forecasts.append({
                "datetime": f"{(i // 8) + 1} day {(i % 8) * 3:02d}:00:00",
                "temperature": temperature,
                "description": rng.choice(["clear sky", "few clouds", "scattered clouds", "light rain"]),
                "rain_probability": int(rng.uniform(0, 60)),
                "humidity": int(rng.uniform(30, 90)),
            })
        return {
            "city": city.title(),
            "forecasts": forecasts,
            "cached": False,
            "data_source": "mock",
        }

    @staticmethod
    def get_current_weather(city: str, country_code: str = "IN"):
        cache_key = f"{city}:{country_code}"

        # Try to get from cache first
        cached = cache_manager.get("weather:current", cache_key)
        if cached:
            logger.info(f"Weather cache hit for {city}", endpoint="weather")
            return cached

        if not OPENWEATHER_API_KEY:
            logger.warning(f"OPENWEATHER_API_KEY not configured; returning mock weather for {city}")
            mock = WeatherService._mock_current_weather(city, country_code)
            cache_manager.set("weather:current", cache_key, mock, WEATHER_CACHE_TTL)
            return mock

        try:
            url = f"{BASE_URL}/weather"
            params = {
                "q": f"{city},{country_code}",
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"  # Celsius
            }
            
            logger.info(f"Fetching weather from API for {city}", endpoint="weather")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            result = {
                "city": data["name"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"],
                "wind_speed": data["wind"]["speed"],
                "timestamp": datetime.now().isoformat(),
                "cached": False
            }
            
            # Cache the result
            cache_manager.set("weather:current", cache_key, result, WEATHER_CACHE_TTL)
            
            return result
            
        except requests.Timeout:
            logger.error(f"Weather API timeout for {city}", endpoint="weather")
            return {"error": "Weather service timeout - try again"}
        except requests.RequestException as e:
            logger.error(f"Weather API error for {city}: {str(e)}", exc_info=e, endpoint="weather")
            return {"error": f"Weather service error: {str(e)}"}
    
    @staticmethod
    def get_forecast(city: str, country_code: str = "IN", days: int = 5):
        cache_key = f"{city}:{country_code}:{days}"

        # Try to get from cache first
        cached = cache_manager.get("weather:forecast", cache_key)
        if cached:
            logger.info(f"Forecast cache hit for {city}", endpoint="weather")
            return cached

        if not OPENWEATHER_API_KEY:
            logger.warning(f"OPENWEATHER_API_KEY not configured; returning mock forecast for {city}")
            mock = WeatherService._mock_forecast(city, country_code, days)
            cache_manager.set("weather:forecast", cache_key, mock, FORECAST_CACHE_TTL)
            return mock

        try:
            url = f"{BASE_URL}/forecast"
            params = {
                "q": f"{city},{country_code}",
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            }
            
            logger.info(f"Fetching forecast from API for {city}", endpoint="weather")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            forecast_list = []
            for item in data["list"][:days * 8]:  # 8 forecasts per day
                forecast_list.append({
                    "datetime": item["dt_txt"],
                    "temperature": item["main"]["temp"],
                    "description": item["weather"][0]["description"],
                    "rain_probability": item.get("pop", 0) * 100,
                    "humidity": item["main"]["humidity"]
                })
            
            result = {
                "city": data["city"]["name"],
                "forecasts": forecast_list,
                "cached": False
            }
            
            # Cache the result
            cache_manager.set("weather:forecast", cache_key, result, FORECAST_CACHE_TTL)
            
            return result
            
        except requests.Timeout:
            logger.error(f"Forecast API timeout for {city}", endpoint="weather")
            return {"error": "Forecast service timeout - try again"}
        except requests.RequestException as e:
            logger.error(f"Forecast API error for {city}: {str(e)}", exc_info=e, endpoint="weather")
            return {"error": f"Forecast service error: {str(e)}"}
        
