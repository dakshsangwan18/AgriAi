from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.core.logging_config import logger


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()  # Auto-commit on success
    except Exception as e:
        session.rollback()  # Auto-rollback on error
        logger.error(f"Database session error: {str(e)}", exc_info=e, endpoint="database")
        raise  # Re-raise exception after rollback
    finally:
        session.close()  # Always close session


@contextmanager
def get_db_session_no_commit() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        logger.error(f"Database session error: {str(e)}", exc_info=e, endpoint="database")
        raise
    finally:
        session.close()


class DatabaseSessionManager:
    
    def __init__(self):
        self._session: Session = None
    
    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        self._session = SessionLocal()
        try:
            yield self._session
        except Exception as e:
            self.rollback()
            logger.error(f"Database transaction error: {str(e)}", exc_info=e, endpoint="database")
            raise
        finally:
            if self._session:
                self._session.close()
                self._session = None
    
    def commit(self):
        if self._session:
            try:
                self._session.commit()
                logger.info("Database transaction committed", endpoint="database")
            except Exception as e:
                self.rollback()
                logger.error(f"Commit failed: {str(e)}", exc_info=e, endpoint="database")
                raise
    
    def rollback(self):
        if self._session:
            self._session.rollback()
            logger.warning("Database transaction rolled back", endpoint="database")
    
    def flush(self):
        if self._session:
            self._session.flush()
