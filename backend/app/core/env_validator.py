import os
import sys
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class EnvValidationError(Exception):
    pass


class EnvironmentValidator:
    
    # Critical variables - app won't start without these
    REQUIRED_VARS = {
        'SECRET_KEY': {
            'description': 'JWT secret key for authentication',
            'min_length': 32,
            'example': 'python -c "import secrets; print(secrets.token_urlsafe(64))"'
        },
        'DATABASE_URL': {
            'description': 'PostgreSQL database connection string',
            'example': 'postgresql://user:password@localhost:5432/agridb'
        },
        'GEMINI_API_KEY': {
            'description': 'Google Gemini API key for AI features',
            'example': 'Get from https://makersuite.google.com/app/apikey'
        },
    }
    
    # Important but optional - app works with degraded functionality
    OPTIONAL_VARS = {
        'OPENWEATHER_API_KEY': {
            'description': 'OpenWeather API for real weather data',
            'fallback': 'Will use mock weather data'
        },
        'DATA_GOV_IN_API_KEY': {
            'description': 'Data.gov.in API for real market prices',
            'fallback': 'Will use synthetic price data'
        },
        'SENDGRID_API_KEY': {
            'description': 'SendGrid for email notifications',
            'fallback': 'Email notifications disabled'
        },
        'TWILIO_ACCOUNT_SID': {
            'description': 'Twilio for SMS notifications',
            'fallback': 'SMS notifications disabled'
        },
        'GOOGLE_CLIENT_ID': {
            'description': 'Google OAuth for social login',
            'fallback': 'Google login disabled'
        },
    }
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_required_var(self, var_name: str, config: Dict) -> bool:
        value = os.getenv(var_name)
        
        if not value:
            self.errors.append(
                f"[ERROR] Missing required variable: {var_name}\n"
                f"   Description: {config['description']}\n"
                f"   Example: {config['example']}"
            )
            return False
        
        # Additional validation for SECRET_KEY
        if var_name == 'SECRET_KEY':
            min_length = config.get('min_length', 0)
            if len(value) < min_length:
                self.errors.append(
                    f"[ERROR] {var_name} is too short (minimum {min_length} characters)\n"
                    f"   Generate with: {config['example']}"
                )
                return False
            
            # Check for default/weak keys
            weak_patterns = ['your-secret', 'change-me', 'example', 'test', 'default']
            if any(pattern in value.lower() for pattern in weak_patterns):
                self.errors.append(
                    f"[ERROR] {var_name} appears to be a default/weak key\n"
                    f"   Generate a secure one with: {config['example']}"
                )
                return False
        
        return True
    
    def validate_optional_var(self, var_name: str, config: Dict):
        value = os.getenv(var_name)
        
        if not value:
            self.warnings.append(
                f"[WARNING]  Optional variable missing: {var_name}\n"
                f"   Description: {config['description']}\n"
                f"   Fallback: {config['fallback']}"
            )
    
    def validate_database_url(self):
        db_url = os.getenv('DATABASE_URL')
        if db_url and not db_url.startswith('postgresql://'):
            self.errors.append(
                "[ERROR] DATABASE_URL must start with 'postgresql://'\n"
                f"   Current: {db_url[:30]}..."
            )
    
    def validate_all(self) -> bool:
        print("\n" + "="*70)
        print(" VALIDATING ENVIRONMENT CONFIGURATION")
        print("="*70 + "\n")
        
        # Validate required variables
        all_valid = True
        for var_name, config in self.REQUIRED_VARS.items():
            if not self.validate_required_var(var_name, config):
                all_valid = False
        
        # Additional validations
        self.validate_database_url()
        
        # Check optional variables
        for var_name, config in self.OPTIONAL_VARS.items():
            self.validate_optional_var(var_name, config)
        
        # Print results
        if self.errors:
            print("[ERROR] CRITICAL ERRORS - Application cannot start:\n")
            for error in self.errors:
                print(error)
                print()
            print("="*70)
            print("[INFO] Fix these errors and restart the application")
            print("="*70 + "\n")
            return False
        
        print("[OK] All required environment variables are valid!\n")
        
        if self.warnings:
            print("[WARNING]  WARNINGS - Some features will be limited:\n")
            for warning in self.warnings:
                print(warning)
                print()
        
        print("="*70)
        print("[OK] Environment validation complete")
        print("="*70 + "\n")
        
        return True
    
    def validate_or_exit(self):
        if not self.validate_all():
            print("\n Application startup aborted due to configuration errors\n")
            sys.exit(1)


def validate_environment():
    validator = EnvironmentValidator()
    validator.validate_or_exit()


if __name__ == "__main__":
    # Allow testing the validator independently
    validate_environment()
