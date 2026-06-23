import pytest
import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Ensure database tables are created before any tests run"""
    Base.metadata.create_all(bind=engine)
    yield
