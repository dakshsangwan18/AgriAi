
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
    
    @patch('app.routers.prices.data_service.get_price_data')
    def test_get_historical_prices_success(self, mock_data, client: TestClient, auth_headers):
        import pandas as pd
        from datetime import datetime, timedelta
        dates = pd.date_range(end=datetime.now(), periods=2, freq='D')
        mock_data.return_value = pd.DataFrame({
            'date': dates,
            'price': [2500.0, 2550.0],
            'min_price': [2400.0, 2450.0],
            'max_price': [2600.0, 2650.0],
            'crop': ['wheat', 'wheat'],
            'mandi': ['Delhi', 'Delhi'],
            'state': ['Delhi', 'Delhi'],
            'variety': ['Standard', 'Standard']
        })

        response = client.get(
            "/api/prices/historical?crop=wheat&days=30",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["crop"] == "wheat"
    
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
