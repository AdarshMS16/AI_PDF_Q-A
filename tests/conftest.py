import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import asyncio
from app import app
from database import Base, engine

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def test_pdf():
    # Create a sample PDF file for testing
    pdf_path = Path("tests/resources/test.pdf")
    return pdf_path

@pytest.fixture(autouse=True)
async def setup_database():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

