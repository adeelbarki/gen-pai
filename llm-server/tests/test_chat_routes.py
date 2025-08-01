import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_generate_answer():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "session_id": "test_session",
            "message": "I have a sore throat and cough"
        }
        response = await client.post("/generate-answer", json=payload)
        assert response.status_code == 200
        chunks = [chunk async for chunk in response.aiter_text()]
        combined = "".join(chunks)
        assert "?" in combined or len(combined) > 10
