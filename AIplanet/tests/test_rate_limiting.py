import pytest
import asyncio
from fastapi import status

def test_api_rate_limiting(test_client):
    # Send multiple requests quickly
    responses = []
    for _ in range(10):
        response = test_client.get("/health")
        responses.append(response.status_code)
    
    # Should have some rate-limited responses
    assert status.HTTP_429_TOO_MANY_REQUESTS in responses

@pytest.mark.asyncio
async def test_concurrent_rate_limiting(test_client):
    async def make_request():
        return test_client.get("/health")
    
    # Make concurrent requests
    tasks = [make_request() for _ in range(10)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check if rate limiting worked
    status_codes = [r.status_code for r in responses if hasattr(r, 'status_code')]
    assert status.HTTP_429_TOO_MANY_REQUESTS in status_codes 