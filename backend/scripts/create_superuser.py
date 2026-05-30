import sys
import os
import argparse
from getpass import getpass
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from app.core.validators import validate_email, validate_password
from fastapi import HTTPException


def create_superuser(email: str, password: str, full_name: str = "Admin User"):
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            if existing_user.is_superuser:
                print(f"✓ Superuser already exists: {email}")
                return existing_user
            else:
                # Upgrade existing user to superuser
                existing_user.is_superuser = True
                db.commit()
                print(f"✓ Upgraded existing user to superuser: {email}")
                return existing_user
        
        # Create new superuser
        superuser = User(
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_superuser=True
        )
        db.add(superuser)
        db.commit()
        db.refresh(superuser)
        print(f"✓ Created new superuser: {email}")
        return superuser
    
    except Exception as e:
        print(f"✗ Error creating superuser: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create or promote a superuser account")
    parser.add_argument("--email", help="Superuser email (or set SUPERUSER_EMAIL)")
    parser.add_argument("--password", help="Superuser password (or set SUPERUSER_PASSWORD)")
    parser.add_argument("--full-name", help="Full name (or set SUPERUSER_FULL_NAME)")
    return parser


def _prompt_value(label: str, secret: bool = False) -> str | None:
    if not sys.stdin.isatty():
        return None
    prompt = f"{label}: "
    return getpass(prompt) if secret else input(prompt).strip()


if __name__ == "__main__":
    parser = _build_arg_parser()
    args = parser.parse_args()

    print("Creating superuser account...")
    print("-" * 50)

    email = args.email or os.getenv("SUPERUSER_EMAIL")
    password = args.password or os.getenv("SUPERUSER_PASSWORD")
    full_name = args.full_name or os.getenv("SUPERUSER_FULL_NAME", "Admin User")

    if not email:
        email = _prompt_value("Email")
    if not password:
        password = _prompt_value("Password", secret=True)

    if not email or not password:
        print("Missing required values. Provide --email/--password or set SUPERUSER_EMAIL/SUPERUSER_PASSWORD.")
        sys.exit(1)

    try:
        email = validate_email(email)
        password = validate_password(password)
        superuser = create_superuser(email, password, full_name)
        print("-" * 50)
        print("Superuser ready:")
        print(f"  Email: {superuser.email}")
        print("-" * 50)
    except HTTPException as e:
        print(f"Validation failed: {e.detail}")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to create superuser: {e}")
        sys.exit(1)
