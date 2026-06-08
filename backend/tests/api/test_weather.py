
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import patch


class TestWeatherEndpoints:
    
    @patch('app.services.weather_service.WeatherService.get_forecast')
    def test_get_forecast_success(self, mock_forecast, client: TestClient, auth_headers):
        mock_forecast.return_value = {
            "city": "Delhi",
            "forecasts": [
                {"datetime": "2025-01-01 12:00:00", "temperature": 25, "description": "Clear", "rain_probability": 10, "humidity": 50}
            ]
        }
        
        response = client.get(
            "/api/weather/forecast?city=Delhi",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "forecasts" in data
    
    def test_get_forecast_missing_params(self, client: TestClient, auth_headers):
        response = client.get("/api/weather/forecast", headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('app.services.weather_service.WeatherService.get_current_weather')
    def test_get_weather_alerts(self, mock_weather, client: TestClient, auth_headers):
        mock_weather.return_value = {
            "city": "Delhi",
            "temperature": 25,
            "feels_like": 24,
            "humidity": 50,
            "description": "Clear",
            "wind_speed": 5,
            "timestamp": "2025-01-01T12:00:00"
        }
        
        response = client.get(
            "/api/weather/alerts?city=Delhi",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
