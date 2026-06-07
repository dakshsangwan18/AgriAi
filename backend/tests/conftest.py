import pytest
import os
import warnings
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone, timedelta
from typing import Generator, Dict
from unittest.mock import MagicMock, patch

# Suppress warnings for cleaner test output
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*redis.*")

# Set test environment variables BEFORE importing app
os.environ["ENVIRONMENT"] = "testing"
os.environ["CACHE_ENABLED"] = "false"  # Disable Redis for tests


from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.notification import Notification
from app.core.security import get_password_hash, create_access_token
from app.core.config import settings


@pytest.fixture(scope="function")
def test_engine():
    test_db_url = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test.db")

    engine = create_engine(
        test_db_url,
        echo=False,
        connect_args={"check_same_thread": False} if "sqlite" in test_db_url else {},
    )

    Base.metadata.create_all(bind=engine)

    yield engine

    engine.dispose()
    if "sqlite" in test_db_url:
        import os as _os
        try:
            _os.remove("./test.db")
        except FileNotFoundError:
            pass


@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator[Session, None, None]:
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()  # Rollback any uncommitted changes
        db.close()


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db: Session) -> User:
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("testpassword123"),
        phone="1234567890",
        location="Test City",
        is_active=True,
        is_superuser=False,
        favorite_crops=["wheat", "rice"],
        preferred_language="en",
        notification_enabled=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def admin_user(test_db: Session) -> User:
    user = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("adminpass123"),
        phone="0987654321",
        location="Admin City",
        is_active=True,
        is_superuser=True,
        favorite_crops=["wheat"],
        preferred_language="en",
        notification_enabled=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def inactive_user(test_db: Session) -> User:
    user = User(
        email="inactive@example.com",
        full_name="Inactive User",
        hashed_password=get_password_hash("password123"),
        phone="5555555555",
        location="Nowhere",
        is_active=False,  # Inactive
        is_superuser=False,
        favorite_crops=[]
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def user_token(test_user: User) -> str:
    return create_access_token(
        data={
            "sub": test_user.email,
            "user_id": test_user.id
        }
    )


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token(
        data={
            "sub": admin_user.email,
            "user_id": admin_user.id
        }
    )


@pytest.fixture
def expired_token(test_user: User) -> str:
    return create_access_token(
        data={
            "sub": test_user.email,
            "user_id": test_user.id
        },
        expires_delta=timedelta(seconds=-1)  # Already expired
    )


@pytest.fixture
def auth_headers(user_token: str) -> Dict[str, str]:
    return{"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def sample_notification(test_db: Session, test_user: User) -> Notification:
    notification = Notification(
        user_id=test_user.id,
        type="price_alert",
        title="Test Notification",
        message="This is a test notification",
        priority="normal",
        is_read=False,
        extra_data={"test": "data"}  # Now using dict directly with JSON column
    )
    test_db.add(notification)
    test_db.commit()
    test_db.refresh(notification)
    return notification



# Utility Fixtures


@pytest.fixture
def faker_seed():
    from faker import Faker
    fake = Faker()
    Faker.seed(12345)
    return fake



# Cleanup Hooks


@pytest.fixture(autouse=True)
def reset_app_state():
    """
    Reset application state before each test.
    
    This ensures tests don't interfere with each other through
    global state or cached values.
    """
    # Clear any dependency overrides
    app.dependency_overrides.clear()
    
    yield
    
    # Cleanup after test
    app.dependency_overrides.clear()



# Markers & Configuration


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (> 1 second)"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication-related"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API endpoint test"
    )
