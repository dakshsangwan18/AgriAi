
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import patch


class TestPriceEndpoints:
    
    @patch('app.services.price_service.PriceService.predict_prices')
    def test_get_current_price_success(self, mock_predict, client: TestClient, auth_headers):
        mock_predict.return_value = {
            "crop": "wheat",
            "current_price": 2500.00,
            "predicted_average": 2520.00,
            "price_change_percentage": 0.8,
            "trend": "increasing",
            "historical_data": [],
            "predictions": [
                {"date": "2025-01-01", "predicted_price": 2510, "crop": "wheat"}
            ],
            "recommendation": "HOLD",
            "data_source": "synthetic",
            "cached": False
        }
        
        response = client.get("/api/prices/predict?crop=wheat", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["crop"] == "wheat"
    
    @patch('app.services.price_service.PriceService.predict_prices')
    def test_get_historical_prices_success(self, mock_predict, client: TestClient, auth_headers):
        mock_predict.return_value = {
            "crop": "wheat",
            "current_price": 2500.00,
            "historical_data": [
                {"date": "2024-01-01", "price": 2500, "crop": "wheat"},
                {"date": "2024-01-02", "price": 2550, "crop": "wheat"}
            ],
            "predictions": [],
            "trend": "stable"
        }
        
        response = client.get(
            "/api/prices/historical?crop=wheat&days=30",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data["historical_data"], list)
        assert len(data["historical_data"]) == 2
    
    @patch('app.services.price_service.PriceService.get_market_comparison')
    def test_get_price_trends(self, mock_compare, client: TestClient, auth_headers):
        mock_compare.return_value = {
            "crop": "wheat",
            "comparison": [{"mandi": "Delhi", "price": 2500, "variation_percent": 0}]
        }
        
        response = client.get(
            "/api/prices/compare?crop=wheat",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "comparison" in data
