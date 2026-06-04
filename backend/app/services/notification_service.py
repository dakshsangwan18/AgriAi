
import logging
from typing import Dict
import os

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        # Twilio setup (for SMS) - optional
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")
        
        if self.twilio_account_sid and self.twilio_auth_token:
            try:
                from twilio.rest import Client
                self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
                self.sms_enabled = True
                logger.info("[OK] Twilio SMS enabled")
            except Exception as e:
                self.sms_enabled = False
                logger.warning(f"Twilio initialization failed: {e}")
        else:
            self.sms_enabled = False
            logger.info("Twilio not configured - SMS disabled (console only)")
    
    def send_alert(self, alert: Dict):

        logger.info(f" Sending alert to {alert.get('user_email', 'unknown')}")
        
        # Format message
        message = self._format_message(alert)
        
        # Send via console (always)
        self._send_console(message, alert.get('user_email', 'unknown'))
        
        # Save to database
        if alert.get('user_id'):
            self._save_to_database(alert, message)
        
        # Send via SMS (if enabled and phone number available)
        if self.sms_enabled:
            # In production, get user's phone from database
            # For now, just log
            logger.info(f"SMS would be sent: {message[:160]}")
    
    def _save_to_database(self, alert: Dict, message: str):
        try:
            from app.core.db_session import get_db_session
            from app.models.notification import Notification
            
            with get_db_session() as db:
                # Determine priority based on action
                action = alert.get('action', 'HOLD')
                priority = 'urgent' if action == 'SELL_NOW' else 'high' if action == 'WAIT' else 'normal'
                
                # Create notification
                notification = Notification(
                    user_id=alert['user_id'],
                    type='agent_recommendation',
                    title=f" {alert.get('crop', 'Crop').upper()} - {action.replace('_', ' ')}",
                    message=message,
                    priority=priority,
                    extra_data={
                        'crop': alert.get('crop'),
                        'action': action,
                        'confidence': alert.get('confidence'),
                        'expected_price': alert.get('expected_price')
                    }
                )
                
                db.add(notification)
                # Auto-commits on success
                logger.info(f"[OK] Notification saved to database for user {alert['user_id']}")
            
        except Exception as e:
            logger.error(f"Failed to save notification to database: {e}")
    
    def _format_message(self, alert: Dict) -> str:
        action = alert.get('action', 'HOLD')
        crop = alert.get('crop', 'crop')
        confidence = alert.get('confidence', 0)
        expected_price = alert.get('expected_price')
        
        emoji = "" if action == 'SELL_NOW' else "🟡" if action == 'WAIT' else "🟢"
        
        message = f"""{emoji} {crop.upper()} Alert

Recommendation: {action}
Confidence: {confidence:.0%}
"""
        
        if expected_price:
            message += f"Expected Price: Rs.{expected_price:.2f}/kg\n"
        
        message += f"\n{alert.get('reasoning', '')[:300]}\n"
        message += "\n- Smart Crop Advisory Agent"
        
        return message
    
    def _send_console(self, message: str, email: str):
        logger.info(f" ALERT TO: {email}")
        logger.info(f"MESSAGE: {message}")
    
    def send_sms(self, phone: str, message: str):
        if not self.sms_enabled:
            logger.warning("SMS not enabled")
            return False
        
        try:
            self.twilio_client.messages.create(
                body=message[:1600],  # SMS limit
                from_=self.twilio_phone,
                to=phone
            )
            logger.info(f"[OK] SMS sent to {phone}")
            return True
        except Exception as e:
            logger.error(f"SMS failed: {str(e)}")
            return False


# Singleton instance
notification_service = NotificationService()
