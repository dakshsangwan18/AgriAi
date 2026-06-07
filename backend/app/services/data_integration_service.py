import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.core.db_session import get_db_session, get_db_session_no_commit
from app.models.price_data import PriceData
from app.core.logging_config import logger
import os
from dotenv import load_dotenv

load_dotenv()


class DataIntegrationService:
    def __init__(self):
        self.data_gov_api_key = os.getenv("DATA_GOV_IN_API_KEY")
        self.resource_id = "9ef84268-d588-465a-a308-a864a43d0070"
        self.base_url = "https://api.data.gov.in/resource"
        
        # Map our crop names to API commodity names (case-sensitive)
        self.crop_to_commodity = {
            "wheat": "Wheat",
            "tomato": "Tomato",
            "rice": "Rice",
            "potato": "Potato",
            "onion": "Onion",
            "maize": "Maize",
            "cotton": "Cotton",
            "sugarcane": "Sugarcane"
        }
        
    def fetch_real_api_data(self, commodity: str = None, limit: int = 1000, offset: int = 0) -> Optional[Dict]:
        try:
            # Map crop name to API commodity name (case-sensitive)
            api_commodity = None
            if commodity:
                api_commodity = self.crop_to_commodity.get(commodity.lower(), commodity)
            
            logger.info(f"Attempting to fetch data from data.gov.in API (crop={commodity}, api_commodity={api_commodity}, limit={limit}, offset={offset})")
            
            url = f"{self.base_url}/{self.resource_id}"
            
            params = {
                "api-key": self.data_gov_api_key,
                "format": "json",
                "limit": limit,
                "offset": offset
            }
            
            # Add commodity filter if specified
            if api_commodity:
                params["filters[commodity]"] = api_commodity
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if data exists
                if 'records' in data and len(data['records']) > 0:
                    logger.info(f"[OK] Successfully fetched {data['count']} records from API (total available: {data.get('total', 'unknown')})")
                    return data
                else:
                    logger.warning("[WARNING] API returned empty data")
                    return None
                    
            elif response.status_code == 502:
                logger.error("[ERROR] API returned 502 Bad Gateway - Server issue")
                return None
            elif response.status_code == 429:
                logger.error("[ERROR] API rate limit exceeded")
                return None
            else:
                logger.error(f"[ERROR] API returned status code: {response.status_code}")
                logger.error(f"Response: {response.text[:200]}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("[ERROR] API request timed out after 30 seconds")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("[ERROR] Could not connect to API server")
            return None
        except Exception as e:
            logger.error(f"[ERROR] Unexpected error fetching API data: {str(e)}")
            return None
    
    def generate_hybrid_historical_data(self, crop: str, days: int = 180, current_price: float = None) -> pd.DataFrame:
        logger.info(f"[DATA] Generating hybrid historical data for {crop} ({days} days, current_price={current_price})")
        
        # Realistic price ranges per crop (per quintal)
        crop_config = {
            "wheat": {"base": 2100, "variance": 300, "seasonality": 1.2},
            "rice": {"base": 2800, "variance": 400, "seasonality": 1.15},
            "tomato": {"base": 2000, "variance": 1500, "seasonality": 2.0},
            "onion": {"base": 2500, "variance": 2000, "seasonality": 1.8},
            "potato": {"base": 1200, "variance": 600, "seasonality": 1.4},
            "cotton": {"base": 6500, "variance": 800, "seasonality": 1.1},
            "sugarcane": {"base": 3000, "variance": 300, "seasonality": 1.05},
            "soyabean": {"base": 3500, "variance": 500, "seasonality": 1.15}
        }
        
        config = crop_config.get(crop.lower(), crop_config["wheat"])
        
        # If we have real current price, adjust base to match reality
        if current_price:
            config["base"] = current_price
            logger.info(f"[OK] Using real current price Rs.{current_price:.2f} as base for historical backfill")
        
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        # Generate realistic price patterns
        # [OK] Key fix: Use date-specific seed so each date gets same price every time
        prices = []
        for date in dates:
            # Set seed based on crop AND specific date
            date_str = date.strftime("%Y-%m-%d")
            seed_value = hash(f"{crop.lower()}:{date_str}") % (2**32)
            np.random.seed(seed_value)
            
            # Base price with long-term trend
            days_since_epoch = (date - datetime(2024, 1, 1)).days
            base_price = config["base"] * (1 + days_since_epoch * 0.0001)
            
            # Seasonal variation
            day_of_year = date.timetuple().tm_yday
            seasonal = np.sin(2 * np.pi * day_of_year / 365) * config["variance"] * 0.3
            
            # Random daily variation (deterministic per date)
            random_var = np.random.uniform(-config["variance"]/2, config["variance"]/2)
            
            price = base_price + seasonal + random_var
            prices.append(max(price, config["base"] * 0.5))
        
        # Reset random seed to avoid affecting other code
        np.random.seed(None)
        
        df = pd.DataFrame({
            'date': dates,
            'price': prices,
            'min_price': [p * 0.95 for p in prices],
            'max_price': [p * 1.05 for p in prices],
            'crop': crop.lower(),
            'mandi': 'Synthetic',
            'state': 'Multiple',
            'variety': 'Standard'
        })
        
        return df
    
    def get_price_data(self, crop: str, days: int = 180, force_synthetic: bool = False) -> pd.DataFrame:
        # Check database cache first
        db_data = self._get_from_database(crop, days)
        if db_data is not None and not db_data.empty:
            data_age_days = (datetime.now().date() - db_data['date'].max().date()).days
            
            if data_age_days < 1:  # Data is fresh (less than 1 day old)
                logger.info(f"[OK] Using cached data from database (age: {data_age_days} days)")
                return db_data
        
       # Try real API first (unless forced to use synthetic)
        if not force_synthetic:
            # Use the commodity mapping from __init__
            api_commodity = self.crop_to_commodity.get(crop.lower(), crop.title())
            
            api_data = self.fetch_real_api_data(commodity=api_commodity, limit=5000)
            
            if api_data is not None:
                # Process and store API data
                processed_data = self._process_api_data(api_data, crop)
            else:
                processed_data = None
            
            if processed_data is not None and not processed_data.empty:
                    self._store_in_database(processed_data)
                    logger.info(f"[OK] Got {len(processed_data)} records from REAL API")
                    
                    # Check if we need historical backfill (API only provides today's data)
                    unique_dates = processed_data['date'].dt.date.nunique()
                    
                    if unique_dates < days and unique_dates <= 5:  # Need historical data
                        logger.info(f"[WARNING] API provided only {unique_dates} unique dates, need {days} days")
                        
                        # Get average current price from real data
                        current_avg_price = processed_data['price'].mean()
                        
                        # Generate historical backfill based on real current price
                        historical_data = self.generate_hybrid_historical_data(
                            crop, 
                            days=days, 
                            current_price=current_avg_price
                        )
                        
                        # Replace today's synthetic data with real API data
                        today = datetime.now().date()
                        historical_data = historical_data[historical_data['date'].dt.date < today]
                        
                        # Combine: historical synthetic + today's real
                        combined_data = pd.concat([historical_data, processed_data], ignore_index=True)
                        combined_data = combined_data.sort_values('date').tail(days)
                        
                        # [OK] Store hybrid data in database for consistency
                        self._store_in_database(historical_data)
                        
                        logger.info(f"[OK] Using HYBRID data: {len(historical_data)} historical + {len(processed_data)} real (today)")
                        return combined_data
                    else:
                        # Have enough historical data from API
                        processed_data = processed_data.sort_values('date', ascending=False).head(days)
                        logger.info(f"[OK] Using REAL API data: {len(processed_data)} records")
                        return processed_data
        
        # Fallback to pure synthetic (no real data available)
        logger.warning("[WARNING] No real API data available, using pure synthetic fallback")
        synthetic_data = self.generate_hybrid_historical_data(crop, days)
        
        return synthetic_data
    
    def _get_from_database(self, crop: str, days: int) -> Optional[pd.DataFrame]:
        with get_db_session_no_commit() as db:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            records = db.query(PriceData).filter(
                PriceData.crop == crop.lower(),
                PriceData.date >= start_date
            ).order_by(PriceData.date).all()
            
            if not records:
                return None
            
            df = pd.DataFrame([{
                'date': pd.to_datetime(r.date),
                'price': r.modal_price,
                'min_price': r.min_price,
                'max_price': r.max_price,
                'crop': r.crop,
                'mandi': r.mandi,
                'state': r.state,
                'variety': r.variety
            } for r in records])
            
            return df
    
    def _process_api_data(self, api_data: Dict, crop_filter: str = None) -> Optional[pd.DataFrame]:
        try:
            if 'records' not in api_data or len(api_data['records']) == 0:
                logger.warning("No records in API response")
                return None
            
            records = api_data['records']
            df = pd.DataFrame(records)
            
            logger.info(f"Processing {len(df)} raw records from API")
            
            # Filter by crop if specified (API column is lowercase 'commodity')
            if crop_filter and 'commodity' in df.columns:
                original_count = len(df)
                df = df[df['commodity'].str.lower().str.contains(crop_filter.lower(), na=False)]
                logger.info(f"Filtered from {original_count} to {len(df)} records for {crop_filter}")
            
            if df.empty:
                logger.warning(f"No records found for crop: {crop_filter}")
                return None
            
            # Convert date format (dd/mm/yyyy to datetime) - API column is lowercase 'arrival_date'
            df['date'] = pd.to_datetime(df['arrival_date'], format='%d/%m/%Y', errors='coerce')
            
            # Convert prices to float (API columns are lowercase and already numeric)
            df['modal_price_val'] = pd.to_numeric(df['modal_price'], errors='coerce')
            df['min_price_val'] = pd.to_numeric(df['min_price'], errors='coerce')
            df['max_price_val'] = pd.to_numeric(df['max_price'], errors='coerce')
            
            # Create clean dataframe
            processed = pd.DataFrame({
                'date': df['date'],
                'price': df['modal_price_val'],
                'min_price': df['min_price_val'],
                'max_price': df['max_price_val'],
                'crop': df['commodity'].str.lower(),
                'mandi': df['market'],
                'state': df['state'],
                'variety': df.get('variety', pd.Series(['Standard'] * len(df)))
            })
            
            # Remove rows with invalid data
            processed = processed.dropna(subset=['date', 'price'])
            
            # Sort by date
            processed = processed.sort_values('date')
            
            logger.info(f"[OK] Processed {len(processed)} valid records")
            return processed
            
        except Exception as e:
            logger.error(f"Error processing API data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _store_in_database(self, df: pd.DataFrame):
        with get_db_session() as db:
            if df.empty:
                return

            crops = df['crop'].unique().tolist()
            min_date = df['date'].min().date()
            max_date = df['date'].max().date()

            existing = db.query(
                PriceData.crop, PriceData.mandi, PriceData.date
            ).filter(
                PriceData.crop.in_(crops),
                PriceData.date >= min_date,
                PriceData.date <= max_date,
            ).all()

            existing_keys = {(r.crop, r.mandi, r.date) for r in existing}

            new_records = []
            skipped_count = 0

            for _, row in df.iterrows():
                key = (row['crop'], row['mandi'], row['date'].date())
                if key in existing_keys:
                    skipped_count += 1
                    continue

                new_records.append(PriceData(
                    crop=row['crop'],
                    mandi=row['mandi'],
                    state=row['state'],
                    date=row['date'].date(),
                    modal_price=float(row['price']),
                    min_price=float(row['min_price']) if pd.notna(row['min_price']) else float(row['price']) * 0.95,
                    max_price=float(row['max_price']) if pd.notna(row['max_price']) else float(row['price']) * 1.05,
                    variety=row['variety']
                ))

            if new_records:
                db.bulk_save_objects(new_records)

            logger.info(f"[OK] Stored {len(new_records)} new records in database (skipped {skipped_count} duplicates)")


# Singleton instance
data_service = DataIntegrationService()
