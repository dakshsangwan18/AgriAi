import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.price_alert import PriceAlert
from app.services.email_service import EmailService
from app.services.data_integration_service import data_service
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class AlertService:
    def __init__(self):
        self.email_service = EmailService()
    
    async def check_all_alerts(self) -> dict:
        triggered_count = 0
        checked_count = 0
        db = SessionLocal()
        try:
            # Get all active alerts
            alerts = db.query(PriceAlert).filter(
                PriceAlert.is_active == True
            ).all()

            logger.info(f"Checking {len(alerts)} active price alerts")

            for alert in alerts:
                checked_count += 1

                # Skip if triggered recently (within 1 hour)
                if alert.last_triggered_at and \
                   datetime.now(timezone.utc) - alert.last_triggered_at < timedelta(hours=1):
                    continue

                # Get current price
                try:
                    current_price = await self._get_current_price(alert.crop, alert.city)

                    if current_price is None:
                        logger.warning(f"No price data for {alert.crop} in {alert.city}")
                        continue

                    # Check if alert should trigger
                    should_trigger, message = self._should_trigger_alert(alert, current_price)

                    if should_trigger:
                        await self._trigger_alert(alert, current_price, message, db)
                        triggered_count += 1

                except Exception as e:
                    logger.error(f"Error checking alert {alert.id}: {e}")
                    continue

            logger.info(f"Alert check complete: {triggered_count}/{checked_count} triggered")

            return {
                "checked": checked_count,
                "triggered": triggered_count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        finally:
            db.close()
    
    async def _get_current_price(self, crop: str, city: str) -> float | None:
        try:
            # Get latest price from database
            prices_df = data_service.get_price_data(crop, days=1)
            
            if prices_df.empty:
                return None
            
            # Get most recent price
            latest = prices_df.iloc[-1]
            return float(latest['price'])
            
        except Exception as e:
            logger.error(f"Error getting price for {crop}: {e}")
            return None
    
    def _should_trigger_alert(self, alert: PriceAlert, current_price: float) -> tuple[bool, str]:
        if alert.alert_type == 'ABOVE':
            if current_price > alert.threshold_price:
                return True, f"Price Rs.{current_price:.2f} is above your threshold of Rs.{alert.threshold_price:.2f}"
        
        elif alert.alert_type == 'BELOW':
            if current_price < alert.threshold_price:
                return True, f"Price Rs.{current_price:.2f} is below your threshold of Rs.{alert.threshold_price:.2f}"
        
        elif alert.alert_type == 'CHANGE':
            # Get price from 24 hours ago
            try:
                prices_df = data_service.get_price_data(alert.crop, days=2)
                
                if len(prices_df) >= 2:
                    previous_price = float(prices_df.iloc[0]['price'])
                    change_percent = ((current_price - previous_price) / previous_price) * 100
                    
                    if abs(change_percent) >= alert.threshold_percentage:
                        direction = "increased" if change_percent > 0 else "decreased"
                        return True, f"Price {direction} by {abs(change_percent):.1f}% (Rs.{current_price:.2f})"
            
            except Exception as e:
                logger.error(f"Error calculating price change: {e}")
        
        return False, ""
    
    async def _trigger_alert(self, alert: PriceAlert, current_price: float, message: str, db: Session):
        try:
            # Send email notification
            if alert.notification_method in ['EMAIL', 'BOTH']:
                user_email = alert.user.email
                subject = f"Price Alert: {alert.crop.upper()} in {alert.city}"
                
                html_content = f"""
                <h2> Price Alert Triggered</h2>
                <p><strong>{message}</strong></p>
                <hr>
                <p><strong>Crop:</strong> {alert.crop.upper()}</p>
                <p><strong>Location:</strong> {alert.city}</p>
                <p><strong>Current Price:</strong> Rs.{current_price:.2f}/kg</p>
                <p><strong>Alert Type:</strong> {alert.alert_type}</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    This alert was triggered at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}.
                    You can manage your alerts in your dashboard.
                </p>
                """
                
                await self.email_service.send_email(
                    to_email=user_email,
                    subject=subject,
                    html_content=html_content
                )
            
            # Create in-app notification
            from app.models.notification import Notification
            notification = Notification(
                user_id=alert.user_id,
                type='price_alert',
                title=f" {alert.crop.upper()} Price Alert",
                message=message,
                priority='high' if abs(current_price - (alert.threshold_price or 0)) > 100 else 'normal',
                extra_data={
                    "crop": alert.crop,
                    "city": alert.city,
                    "current_price": current_price,
                    "alert_type": alert.alert_type,
                }
            )
            db.add(notification)
            
            alert.last_triggered_at = datetime.now(timezone.utc)
            db.commit()
            
            logger.info(f"Alert {alert.id} triggered for user {alert.user_id} - in-app notification created")
            
        except Exception as e:
            logger.error(f"Error sending alert notification: {e}")


# Singleton instance
alert_service = AlertService()
