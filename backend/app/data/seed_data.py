import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.db_session import get_db_session
from app.models.price_data import PriceData
from datetime import datetime, timedelta
import random
import numpy as np

def generate_realistic_price_data():
    
    # Crop configuration with realistic price ranges (Rs. per quintal)
    crops_config = {
        "wheat": {
            "base_price": 2100,
            "variance": 300,
            "seasonality_factor": 1.2,
            "trend": 50
        },
        "rice": {
            "base_price": 2800,
            "variance": 400,
            "seasonality_factor": 1.15,
            "trend": 60
        },
        "tomato": {
            "base_price": 2000,
            "variance": 1500,
            "seasonality_factor": 2.0,
            "trend": 20
        },
        "onion": {
            "base_price": 2500,
            "variance": 2000,
            "seasonality_factor": 1.8,
            "trend": 30
        },
        "potato": {
            "base_price": 1200,
            "variance": 600,
            "seasonality_factor": 1.4,
            "trend": 25
        },
        "cotton": {
            "base_price": 6500,
            "variance": 800,
            "seasonality_factor": 1.1,
            "trend": 100
        },
        "sugarcane": {
            "base_price": 3000,
            "variance": 300,
            "seasonality_factor": 1.05,
            "trend": 40
        }
    }
    
    # Major mandis across India
    mandis = [
        {"name": "Azadpur", "state": "Delhi"},
        {"name": "Vashi", "state": "Maharashtra"},
        {"name": "Koyambedu", "state": "Tamil Nadu"},
        {"name": "Yeshwanthpur", "state": "Karnataka"},
        {"name": "Mehrauli", "state": "Delhi"},
        {"name": "Lasalgaon", "state": "Maharashtra"},
        {"name": "Bangalore", "state": "Karnataka"},
        {"name": "Mumbai", "state": "Maharashtra"},
        {"name": "Kolkata", "state": "West Bengal"},
        {"name": "Chennai", "state": "Tamil Nadu"}
    ]
    
    # Generate data for last 2 years
    start_date = datetime.now() - timedelta(days=730)
    end_date = datetime.now()
    
    print(" Generating historical price data...")
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    print(f"Crops: {len(crops_config)}")
    print(f"Mandis: {len(mandis)}")
    
    total_records = 0
    
    with get_db_session() as db:
        for crop, config in crops_config.items():
            print(f"\n[DATA] Processing {crop}...")
            
            for mandi in mandis:
                current_date = start_date

                while current_date <= end_date:
                    days_from_start = (current_date - start_date).days

                    trend_factor = 1 + (config["trend"] * days_from_start / 36500)
                    base_price = config["base_price"] * trend_factor

                    day_of_year = current_date.timetuple().tm_yday
                    seasonal_factor = 1 + (config["seasonality_factor"] - 1) * np.sin(2 * np.pi * day_of_year / 365)

                    daily_variation = random.uniform(-config["variance"]/2, config["variance"]/2)

                    modal_price = base_price * seasonal_factor + daily_variation
                    modal_price = max(modal_price, config["base_price"] * 0.5)

                    min_price = modal_price * random.uniform(0.90, 0.95)
                    max_price = modal_price * random.uniform(1.05, 1.10)

                    price_record = PriceData(
                        crop=crop,
                        mandi=mandi["name"],
                        state=mandi["state"],
                        date=current_date.date(),
                        modal_price=float(round(modal_price, 2)),
                        min_price=float(round(min_price, 2)),
                        max_price=float(round(max_price, 2)),
                        variety="Standard"
                    )

                    db.add(price_record)
                    total_records += 1

                    current_date += timedelta(days=1)
            
            # Flush after each crop (keeps session active)
            db.flush()
            print(f"[OK] {crop.capitalize()} - Added {730 * len(mandis)} records")
        
        # Auto-commits all records when context exits
        print(f"\n Successfully generated {total_records:,} price records!")
        print(f"[DATA] Database is ready for production use!")


if __name__ == "__main__":
    print("=" * 50)
    print("SEEDING DATABASE WITH HISTORICAL PRICE DATA")
    print("=" * 50)
    
    generate_realistic_price_data()
    
    print("\n[OK] Database seeding completed!")
