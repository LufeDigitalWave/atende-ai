"""Conditional tracing — uses Langfuse when configured, no-op otherwise.

Usage:
    from app.services.tracing import get_tracer

    tracer = get_tracer()
    with tracer.span(name="chat_turn", session_id=sid) as span:
        span.set_input(messages)
        response = await llm.chat_stream(...)
        span.set_output(response)
        span.set_metadata({"tokens": ..., "cost": ...})

If Langfuse is not configured (no LANGFUSE_PUBLIC_KEY), all methods are no-ops.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any

import structlog

logger = structlog.get_logger("tracing")


class NoOpSpan:
    """No-op span when tracing is disabled."""

    def set_input(self, value: Any) -> None:
        pass

    def set_output(self, value: Any) -> None:
        pass

    def set_metadata(self, value: dict) -> None:
        pass

    def end(self) -> None:
        pass


class NoOpTracer:
    """No-op tracer when Langfuse is not configured."""

    @contextmanager
    def span(self, name: str = "default", session_id: str | None = None, **kwargs):
        yield NoOpSpan()

    def flush(self) -> None:
        pass


class LangfuseTracer:
    """Langfuse tracer wrapper."""

    def __init__(self):
        try:
            from langfuse import Langfuse
            self._client = Langfuse()
            logger.info("langfuse tracing enabled")
        except Exception as e:
            logger.warning(f"langfuse init failed, falling back to no-op: {e}")
            self._client = None

    @contextmanager
    def span(self, name: str = "default", session_id: str | None = None, **kwargs):
        if not self._client:
            yield NoOpSpan()
            return

        try:
            trace = self._client.trace(name=name, session_id=session_id, **kwargs)
            span = trace.span(name=name)

            class LangfuseSpan:
                def set_input(self, value: Any) -> None:
                    span.update(input=value)

                def set_output(self, value: Any) -> None:
                    span.update(output=value)

                def set_metadata(self, value: dict) -> None:
                    span.update(metadata=value)

                def end(self) -> None:
                    span.end()

            yield LangfuseSpan()
            span.end()
        except Exception as e:
            logger.warning(f"langfuse span error: {e}")
            yield NoOpSpan()

    def flush(self) -> None:
        if self._client:
            try:
                self._client.flush()
            except Exception:
                pass


_tracer: NoOpTracer | LangfuseTracer | None = None


def get_tracer() -> NoOpTracer | LangfuseTracer:
    """Get or create the global tracer instance."""
    global _tracer
    if _tracer is not None:
        return _tracer

    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    if public_key:
        _tracer = LangfuseTracer()
    else:
        _tracer = NoOpTracer()
        logger.info("langfuse not configured, tracing disabled")

    return _tracer
