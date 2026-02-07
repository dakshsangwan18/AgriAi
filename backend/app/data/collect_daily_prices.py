import sys
import logging
from datetime import datetime
from app.services.data_integration_service import DataIntegrationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_collection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Major crops to collect daily
CROPS_TO_COLLECT = [
    'wheat', 'rice', 'tomato', 'potato', 'onion',
    'maize', 'cotton', 'sugarcane'
]

def collect_daily_data():
    logger.info("="*60)
    logger.info(f" DAILY PRICE COLLECTION - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info("="*60)
    
    service = DataIntegrationService()
    results = {
        'success': [],
        'failed': [],
        'total_records': 0
    }
    
    for crop in CROPS_TO_COLLECT:
        try:
            logger.info(f"\n[DATA] Collecting {crop.upper()}...")
            
            # Fetch real API data (limit=5000 to get all today's markets)
            api_commodity = service.crop_to_commodity.get(crop.lower(), crop.title())
            api_data = service.fetch_real_api_data(commodity=api_commodity, limit=5000)
            
            if api_data and 'records' in api_data and len(api_data['records']) > 0:
                # Process and store in database
                processed_data = service._process_api_data(api_data, crop)
                
                if processed_data is not None and not processed_data.empty:
                    service._store_in_database(processed_data)
                    
                    records_count = len(processed_data)
                    states_count = processed_data['state'].nunique()
                    markets_count = processed_data['mandi'].nunique()
                    
                    logger.info(f"[OK] {crop.upper()}: {records_count} records | {states_count} states | {markets_count} markets")
                    
                    results['success'].append(crop)
                    results['total_records'] += records_count
                else:
                    logger.warning(f"[WARNING] {crop.upper()}: No valid data after processing")
                    results['failed'].append(crop)
            else:
                logger.warning(f"[WARNING] {crop.upper()}: No data from API")
                results['failed'].append(crop)
                
        except Exception as e:
            logger.error(f"[ERROR] {crop.upper()}: Error - {str(e)}")
            results['failed'].append(crop)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("[UP] COLLECTION SUMMARY")
    logger.info("="*60)
    logger.info(f"[OK] Success: {len(results['success'])} crops")
    logger.info(f"[ERROR] Failed: {len(results['failed'])} crops")
    logger.info(f"[DATA] Total Records: {results['total_records']}")
    
    if results['success']:
        logger.info(f"Successful: {', '.join(results['success'])}")
    if results['failed']:
        logger.info(f"Failed: {', '.join(results['failed'])}")
    
    logger.info("="*60)
    
    return results

if __name__ == "__main__":
    try:
        results = collect_daily_data()
        
        # Exit with appropriate code
        if len(results['failed']) == 0:
            logger.info("[OK] All crops collected successfully")
            sys.exit(0)
        elif len(results['success']) > 0:
            logger.warning("[WARNING] Some crops failed but collection partially successful")
            sys.exit(0)  # Don't fail if we got some data
        else:
            logger.error("[ERROR] All crops failed to collect")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"[ERROR] Critical error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
