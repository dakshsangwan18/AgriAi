from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):

    # AI Provider API Keys

    # Gemini: Used for AI Crop Advisor (agent_service)
    # Get key from: https://aistudio.google.com/app/apikey
    GEMINI_API_KEY: Optional[str] = None
    
    # Groq: Used for Farmer Chatbot (chatbot_service)
    # Get key from: https://console.groq.com/keys
    # Limits: 30 RPM, 14,400 RPD (free tier)
    GROQ_API_KEY: Optional[str] = None
    

    # External API Keys

    OPENWEATHER_API_KEY: str
    DATA_GOV_IN_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: Optional[str] = None
    
    # Redis Cache
    REDIS_URL: str = "redis://redis:6379/0"
    CACHE_ENABLED: bool = True
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # Cookie auth
    ACCESS_TOKEN_COOKIE_NAME: str = "access_token"
    REFRESH_TOKEN_COOKIE_NAME: str = "refresh_token"
    CSRF_COOKIE_NAME: str = "csrf_token"
    CSRF_HEADER_NAME: str = "X-CSRF-Token"
    COOKIE_DOMAIN: Optional[str] = None
    COOKIE_SAMESITE: Optional[str] = None
    COOKIE_SECURE: Optional[bool] = None
    
    # Email Configuration (Choose one method)
    # Method 1: SendGrid (Recommended for production)
    SENDGRID_API_KEY: Optional[str] = None
    
    # Method 2: SMTP (Gmail, Outlook, etc.)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_FROM_NAME: str = "AgriAI Platform"
    
    # Email settings
    EMAIL_ENABLED: bool = False  # Set to True when configured
    
    # OAuth - Google Login
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost/auth/google/callback"  # Docker deployment
    
    # CORS - Allow multiple origins for development
    FRONTEND_URL: str = "http://localhost"  # Docker deployment
    # Comma-separated list for production (e.g., https://app.example.com,https://admin.example.com)
    CORS_ORIGINS: Optional[str] = None

    def get_cors_origins(self) -> List[str]:
        if self.CORS_ORIGINS:
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

        origins: List[str] = []

        if self.FRONTEND_URL:
            origins.append(self.FRONTEND_URL.rstrip("/"))

        if self.ENVIRONMENT != "production":
            origins.extend([
                "http://localhost",
                "http://localhost:80",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:5174",
                "http://127.0.0.1:5174",
            ])

        # Preserve order while removing duplicates
        return list(dict.fromkeys(origins))
    
    # Environment
    ENVIRONMENT: str = "development"

    # Proxy and error logging controls
    FORWARDED_ALLOW_IPS: Optional[str] = None
    ALLOW_ANON_ERRORS: Optional[bool] = None
    ANON_ERROR_RATE_LIMIT: str = "10/minute"

    # Docs exposure (disable in production by default)
    ENABLE_DOCS: Optional[bool] = None

    # Content Security Policy (CSP)
    CSP_REPORT_ONLY: Optional[bool] = None
    CSP_REPORT_URI: Optional[str] = None
    # Comma-separated list of extra connect-src origins (e.g., https://api.example.com)
    CSP_CONNECT_SRC: Optional[str] = None

    # Sentry
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENV: Optional[str] = None
    SENTRY_RELEASE: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.0
    SENTRY_SEND_PII: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_secret_key()

    def docs_enabled(self) -> bool:
        if self.ENABLE_DOCS is not None:
            return self.ENABLE_DOCS
        return self.ENVIRONMENT != "production"

    def cookie_secure(self) -> bool:
        if self.COOKIE_SECURE is not None:
            return self.COOKIE_SECURE
        return self.ENVIRONMENT == "production"

    def cookie_samesite(self) -> str:
        if self.COOKIE_SAMESITE:
            return self.COOKIE_SAMESITE
        return "none" if self.ENVIRONMENT == "production" else "lax"

    def allow_anonymous_errors(self) -> bool:
        if self.ALLOW_ANON_ERRORS is not None:
            return self.ALLOW_ANON_ERRORS
        return self.ENVIRONMENT != "production"
    
    def _validate_secret_key(self):
        # Minimum length check
        if len(self.SECRET_KEY) < 32:
            raise ValueError(
                "[ERROR] SECURITY ERROR: SECRET_KEY must be at least 32 characters long.\n"
                "Generate a secure key with:\n"
                "  python -c \"import secrets; print(secrets.token_urlsafe(64))\"\n"
                f"Current length: {len(self.SECRET_KEY)} characters"
            )
        
        # Check for insecure placeholder patterns
        insecure_patterns = [
            "your-secret",
            "change-me",
            "replace",
            "example",
            "test-key",
            "default",
            "secret-key",
            "my-secret",
            "password",
            "123456"
        ]
        
        secret_lower = self.SECRET_KEY.lower()
        for pattern in insecure_patterns:
            if pattern in secret_lower:
                if self.ENVIRONMENT == "production":
                    raise ValueError(
                        f"[ERROR] CRITICAL SECURITY ERROR: SECRET_KEY contains insecure pattern '{pattern}'.\n"
                        "This is NOT allowed in production!\n"
                        "Generate a secure random key immediately."
                    )
                else:
                    print(
                        f"[WARNING]  WARNING: SECRET_KEY contains pattern '{pattern}'. "
                        "This is insecure! Generate a proper key for development too."
                    )
                    break
        
        # Production-specific validation
        if self.ENVIRONMENT == "production":
            # Ensure key looks random (has variety of characters)
            unique_chars = len(set(self.SECRET_KEY))
            if unique_chars < 20:  # Should have good character variety
                raise ValueError(
                    "[ERROR] PRODUCTION SECURITY ERROR: SECRET_KEY lacks sufficient randomness.\n"
                    f"Only {unique_chars} unique characters found. Expected at least 20.\n"
                    "Use a cryptographically secure random generator."
                )
            
            # Log success in production
            print("[OK] SECRET_KEY validation passed")
        
        # Development warning
        elif self.ENVIRONMENT == "development":
            if "your-secret" in secret_lower or len(self.SECRET_KEY) < 64:
                print(
                    "[WARNING]  DEVELOPMENT WARNING: Using non-production SECRET_KEY.\n"
                    "   This is acceptable for local development only.\n"
                    "   NEVER use this key in staging or production!"
                )


settings = Settings()
