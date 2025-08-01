import pytest
from app.services.rag_chain import rag_chain

@pytest.mark.asyncio
async def test_rag_chain_generates_question():
    inputs = {
        "symptom": "cough",
        "history": "USER: I have had a cough for 2 days\nAI: When did the cough start?"
    }

    response = await rag_chain.ainvoke(inputs)
    assert response.content or isinstance(response, str)
    assert "?" in response.content