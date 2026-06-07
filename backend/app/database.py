from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv
from app.core.logging_config import logger

load_dotenv()

# Get database URL from environment or use SQLite fallback
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./agri_ai.db"
)

is_sqlite = "sqlite" in DATABASE_URL

if is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600,
        pool_pre_ping=True,
        echo=False
    )
    
    # Pool event listeners for monitoring
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        logger.info(
            "Database connection opened",
            extra={"pool_size": engine.pool.size()}
        )
        cursor = dbapi_conn.cursor()
        cursor.execute("SET statement_timeout = 30000")
        cursor.close()
    
    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        logger.info(
            "Connection checked out from pool",
            extra={
                "checked_out": engine.pool.checkedout(),
                "overflow": engine.pool.overflow()
            }
        )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_pool_status():
    if is_sqlite:
        return {
            "type": "sqlite",
            "status": "no pooling (single connection)"
        }
    
    return {
        "type": "pooled",
        "size": engine.pool.size(),
        "checked_in": engine.pool.checkedin(),
        "checked_out": engine.pool.checkedout(),
        "overflow": engine.pool.overflow(),
        "total_connections": engine.pool.size() + engine.pool.overflow(),
        "max_connections": 30,  # pool_size + max_overflow
        "utilization_percent": round(
            (engine.pool.checkedout() / 30) * 100, 2
        )
    }


def init_db():
    from app.models import user, price_data, prediction_history, agent_analysis, notification, refresh_token
    
    # Import all models to ensure they're registered
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
