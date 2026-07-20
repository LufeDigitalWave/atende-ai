"""Integration test — FakeLLMProvider streaming smoke tests."""
import pytest

from app.services.llm import FakeLLMProvider


@pytest.mark.asyncio
async def test_fake_provider_greeting():
    """FakeLLMProvider responds to greeting."""
    provider = FakeLLMProvider()
    messages = [{"role": "user", "content": "Oi!"}]
    response = ""
    async for token, *_ in provider.chat_stream("", messages):
        response += token
    assert "Sofia" in response or "Bem-vindo" in response or "Clínica" in response


@pytest.mark.asyncio
async def test_fake_provider_service_question():
    """FakeLLMProvider responds to service question."""
    provider = FakeLLMProvider()
    messages = [{"role": "user", "content": "Quanto custa melasma?"}]
    response = ""
    async for token, *_ in provider.chat_stream("", messages):
        response += token
    assert len(response) > 0


@pytest.mark.asyncio
async def test_fake_provider_confirmation():
    """FakeLLMProvider responds to confirmation."""
    provider = FakeLLMProvider()
    messages = [{"role": "user", "content": "Sim, quero agendar!"}]
    response = ""
    async for token, *_ in provider.chat_stream("", messages):
        response += token
    assert "Paula" in response or "agendamento" in response.lower() or len(response) > 0
