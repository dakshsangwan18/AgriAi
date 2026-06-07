
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def start(self):
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        # Import here to avoid circular dependency
        from app.services.agent_service import smart_agent
        from app.services.notification_service import notification_service
        
        # Daily price data collection at 6 PM IST (after markets close)
        self.scheduler.add_job(
            self._daily_data_collection_job,
            CronTrigger(hour=18, minute=0),
            id='daily_price_collection',
            name='Daily Market Price Collection',
            replace_existing=True
        )
        
        # Daily analysis at 6 AM
        self.scheduler.add_job(
            lambda: self._daily_monitoring_job(smart_agent, notification_service),
            CronTrigger(hour=6, minute=0),
            id='daily_monitoring',
            name='Daily Crop Monitoring',
            replace_existing=True
        )
        
        # Price alerts every hour
        self.scheduler.add_job(
            self._price_alert_job,
            CronTrigger(minute=0),
            id='price_alerts',
            name='Price Alert Check',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("[OK] Production scheduler started - monitoring 24/7")
        logger.info("[DATA] Daily data collection: 6 PM IST")
        logger.info(" Daily analysis: 6 AM IST")
        logger.info(" Price alerts: Hourly (minute 0)")
    
    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler stopped")
    
    def _daily_monitoring_job(self, smart_agent, notification_service):
        logger.info(f" Daily monitoring at {datetime.now()}")
        
        try:
            alerts = smart_agent.run_daily_monitoring()
            
            # Send notifications
            for alert in alerts:
                notification_service.send_alert(alert)
            
            logger.info(f"[OK] Sent {len(alerts)} alerts")
            
        except Exception as e:
            logger.error(f"Daily job failed: {e}")
    
    def _price_alert_job(self):
        logger.info(f" Price alert check at {datetime.now()}")
        
        try:
            from app.services.alert_service import alert_service
            import asyncio

            result = asyncio.run(alert_service.check_all_alerts())
            
            logger.info(f"[OK] Alert check: {result['triggered']}/{result['checked']} triggered")
            
        except Exception as e:
            logger.error(f"[ERROR] Price alert job failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _daily_data_collection_job(self):
        logger.info(f"[DATA] Daily price collection at {datetime.now()}")
        
        try:
            from app.services.data_integration_service import DataIntegrationService
            
            service = DataIntegrationService()
            crops = ['wheat', 'rice', 'tomato', 'potato', 'onion', 'maize', 'cotton', 'sugarcane']
            
            total_records = 0
            success_count = 0
            
            for crop in crops:
                try:
                    # Fetch today's data
                    api_commodity = service.crop_to_commodity.get(crop.lower(), crop.title())
                    api_data = service.fetch_real_api_data(commodity=api_commodity, limit=5000)
                    
                    if api_data and 'records' in api_data and len(api_data['records']) > 0:
                        processed_data = service._process_api_data(api_data, crop)
                        
                        if processed_data is not None and not processed_data.empty:
                            service._store_in_database(processed_data)
                            records_count = len(processed_data)
                            total_records += records_count
                            success_count += 1
                            logger.info(f"[OK] {crop.upper()}: {records_count} records collected")
                        else:
                            logger.warning(f"[WARNING] {crop.upper()}: No valid data")
                    else:
                        logger.warning(f"[WARNING] {crop.upper()}: No data from API")
                        
                except Exception as e:
                    logger.error(f"[ERROR] {crop.upper()}: {str(e)}")
            
            logger.info(f"[OK] Daily collection complete: {success_count}/{len(crops)} crops, {total_records} total records")
            
        except Exception as e:
            logger.error(f"[ERROR] Daily collection job failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def run_now(self, job_id: str):
        job = self.scheduler.get_job(job_id)
        if job:
            job.func()
            logger.info(f"Manually ran job: {job_id}")
        else:
            logger.warning(f"Job not found: {job_id}")


# Singleton instance
scheduler_service = SchedulerService()
