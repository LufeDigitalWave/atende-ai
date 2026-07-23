"""Operational kill switch service.

In-memory overrides that take precedence over settings defaults.
Lost on restart (acceptable for demo); admin can re-toggle.
"""
from __future__ import annotations

from app.core.config import get_settings

# In-memory override cache: {component_name: enabled_bool}
_overrides: dict[str, bool] = {}


def is_enabled(component: str) -> bool:
    """Return True if the given component is enabled (not killed)."""
    if component in _overrides:
        return _overrides[component]
    settings = get_settings()
    return getattr(settings, f"kill_switch_{component}", True)


def set_override(component: str, enabled: bool) -> None:
    """Set runtime override for a component."""
    _overrides[component] = enabled


def get_state() -> dict[str, bool]:
    """Get current state of all known components."""
    return {
        "chat": is_enabled("chat"),
        "handoff": is_enabled("handoff"),
    }


def clear_overrides() -> None:
    """Clear all overrides (for tests)."""
    _overrides.clear()
