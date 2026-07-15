"""LLM provider abstraction — ClaudeProvider, OpenAIProvider, and FakeLLMProvider."""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import AsyncIterator

import openai
from anthropic import AsyncAnthropic

from app.core.config import get_settings


class LLMProvider(ABC):
    """Abstract LLM provider."""

    @abstractmethod
    async def chat_stream(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float = 0.4,
    ) -> AsyncIterator[tuple[str, int, int, int]]:
        """Stream chat response as tokens.

        Yields: (token_delta, input_tokens, output_tokens, cached_tokens)
        """
        pass


class FakeLLMProvider(LLMProvider):
    """Scripted offline provider for testing and demo mode.

    Routes responses by keywords for predictable behavior.
    """

    async def chat_stream(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float = 0.4,
    ) -> AsyncIterator[tuple[str, int, int, int]]:
        """Generate scripted response based on keywords."""

        # Extract user message (last message from user)
        user_input = ""
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "user":
                user_input = msg.get("content", "").lower()
                break

        # Detect greeting / first message
        if any(w in user_input for w in ["oi", "olá", "opa", "tudo bem"]):
            response = (
                "Oi! Bem-vindo à Clínica Renova 😊 Meu nome é Sofia, sou uma agente de IA aqui "
                "pra qualificar seu interesse em tratamentos estéticos. Qual é a principal queixa "
                "que te traz aqui?"
            )
            for chunk in response.split():
                yield chunk + " ", 100, 20, 0
                await asyncio.sleep(0.01)  # simulate latency
            return

        # Detect name extraction
        if any(w in user_input for w in ["meu nome", "eu sou", "chamo", "sou"]):
            response = (
                "Perfeito! Agora me fala um pouco mais — qual é o tratamento que você procura? "
                "Temos várias opções: limpeza de pele, peeling, depilação a laser, microagulhamento... "
                "O que te interessa?"
            )
            for chunk in response.split():
                yield chunk + " ", 100, 15, 0
                await asyncio.sleep(0.01)
            return

        # Detect service/problem keywords
        if any(w in user_input for w in ["melasma", "mancha", "acne", "cicatriz", "limpeza", "depilação"]):
            response = (
                "Ótimo! A gente trata muito bem isso aqui com protocolo combinado. "
                "Qual é seu orçamento aproximado? Temos opções a partir de R$ 1.068."
            )
            for chunk in response.split():
                yield chunk + " ", 100, 18, 0
                await asyncio.sleep(0.01)
            return

        # Detect price/budget
        if any(w in user_input for w in ["preço", "custa", "quanto", "valor", "orçamento"]):
            response = (
                "Depende do tratamento! Limpeza profunda sai a partir de 12x R$ 89 ou R$ 1.068 à vista. "
                "Peeling médio a partir de 12x R$ 180. Na avaliação gratuita a gente monta um "
                "protocolo personalizado pra você!"
            )
            for chunk in response.split():
                yield chunk + " ", 150, 22, 0
                await asyncio.sleep(0.01)
            return

        # Detect urgent language
        if any(w in user_input for w in ["urgente", "logo", "já", "amanhã", "rápido"]):
            response = (
                "Entendo a urgência! A gente consegue agendar sua avaliação bem rápido. "
                "Qual é melhor pra você — amanhã de manhã, à tarde ou próxima semana?"
            )
            for chunk in response.split():
                yield chunk + " ", 100, 16, 0
                await asyncio.sleep(0.01)
            return

        # Detect confirmation
        if any(w in user_input for w in ["sim", "ok", "perfeito", "ótimo", "bora", "quero", "vamos"]):
            response = (
                "Ótimo! Vou conectar você com a Paula, nossa recepcionista, pra finalizar "
                "o agendamento. Um momento 😊"
            )
            for chunk in response.split():
                yield chunk + " ", 100, 14, 0
                await asyncio.sleep(0.01)
            return

        # Fallback
        response = (
            "Entendi! Pra eu te dar a melhor orientação, me fala mais sobre o que você procura. "
            "É um tratamento facial, corporal, ou para o cabelo?"
        )
        for chunk in response.split():
            yield chunk + " ", 100, 17, 0
            await asyncio.sleep(0.01)


class ClaudeProvider(LLMProvider):
    """Claude API provider with streaming, prompt caching, and usage logging."""

    def __init__(self):
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.agent_model

    async def chat_stream(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float = 0.4,
    ) -> AsyncIterator[tuple[str, int, int, int]]:
        """Stream chat with prompt caching on system prompt.

        Yields: (token_delta, input_tokens, output_tokens, cached_tokens)
        """
        # Build request with cache control on system prompt
        system_blocks = [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]

        try:
            # Stream response
            input_tokens = 0
            output_tokens = 0
            cached_tokens = 0

            with self.client.messages.stream(
                model=self.model,
                max_tokens=500,
                system=system_blocks,
                messages=messages,
                temperature=temperature,
            ) as stream:
                for event in stream:
                    # Extract token from content_block_delta
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield event.delta.text, input_tokens, output_tokens, cached_tokens

                # Get usage from final message
                if hasattr(stream, "get_final_message"):
                    final_msg = stream.get_final_message()
                    if hasattr(final_msg, "usage"):
                        input_tokens = final_msg.usage.input_tokens
                        output_tokens = final_msg.usage.output_tokens
                        cached_tokens = getattr(
                            final_msg.usage, "cache_read_input_tokens", 0
                        )

        except Exception as e:
            # Log error but don't crash
            import structlog
            logger = structlog.get_logger("claude_provider")
            logger.error(f"claude api error: {e}")
            raise


class OpenAIProvider(LLMProvider):
    """OpenAI API provider with streaming and token counting."""

    PRICING = {
        # USD per 1M tokens (input/output)
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4o": (5.00, 15.00),
        "gpt-4.1-mini": (0.40, 1.60),
        "gpt-4.1": (10.00, 30.00),
        "gpt-3.5-turbo": (0.50, 1.50),
    }

    def __init__(self):
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.agent_model

    async def chat_stream(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float = 0.4,
    ) -> AsyncIterator[tuple[str, int, int, int]]:
        """Stream chat response from OpenAI.

        Yields: (token_delta, input_tokens, output_tokens, cached_tokens=0)
        """
        try:
            # OpenAI uses 'system' role first
            openai_messages = [{"role": "system", "content": system_prompt}]
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                openai_messages.append({"role": role, "content": content})

            input_tokens = 0
            output_tokens = 0

            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=200,  # short responses (WhatsApp style)
                stream=True,
                stream_options={"include_usage": True},
            )

            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta, input_tokens, output_tokens, 0
                if hasattr(chunk, "usage") and chunk.usage:
                    input_tokens = chunk.usage.prompt_tokens
                    output_tokens = chunk.usage.completion_tokens

        except Exception as e:
            import structlog
            logger = structlog.get_logger("openai_provider")
            logger.error(f"openai api error: {e}")
            raise


def get_llm_provider() -> LLMProvider:
    """Factory."""
    settings = get_settings()
    if settings.llm_provider == "claude":
        return ClaudeProvider()
    if settings.llm_provider == "openai":
        return OpenAIProvider()
    return FakeLLMProvider()
