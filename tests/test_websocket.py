import pytest
from fastapi.testclient import TestClient
from app import app

@pytest.mark.asyncio
async def test_websocket_connection():
    client = TestClient(app)
    with client.websocket_connect("/qa") as websocket:
        data = {"question": "What is this document about?", "document_id": 1}
        websocket.send_json(data)
        response = websocket.receive_json()
        assert "answer" in response

@pytest.mark.asyncio
async def test_websocket_rate_limiting():
    client = TestClient(app)
    with client.websocket_connect("/qa") as websocket:
        # Send multiple requests quickly
        for _ in range(5):
            data = {"question": "Test question", "document_id": 1}
            websocket.send_json(data)
        
        # Should receive rate limit error
        response = websocket.receive_json()
        assert "error" in response
        assert "rate limit exceeded" in response["error"].lower()