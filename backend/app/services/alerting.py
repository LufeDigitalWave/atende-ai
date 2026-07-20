"""Budget alerting service — sends notifications when usage crosses thresholds.

Supports webhook (n8n/generic) and Telegram Bot API.
Cooldown prevents duplicate alerts within a configurable window.
"""
from __future__ import annotations

from datetime import datetime, timezone

import httpx
import structlog

from app.core.config import get_settings

logger = structlog.get_logger("alerting")

# In-memory cooldown tracker: {threshold_pct: last_sent_at}
_alert_cooldown: dict[int, datetime] = {}


def _recently_alerted(threshold: int) -> bool:
    """Check if we already sent an alert for this threshold within the cooldown window."""
    settings = get_settings()
    last_sent = _alert_cooldown.get(threshold)
    if not last_sent:
        return False
    elapsed_hours = (datetime.now(timezone.utc) - last_sent).total_seconds() / 3600
    return elapsed_hours < settings.budget_alert_cooldown_hours


def _record_alert(threshold: int) -> None:
    """Record that we sent an alert for this threshold."""
    _alert_cooldown[threshold] = datetime.now(timezone.utc)


async def _send_webhook(msg: str, pct: float, used: int, budget: int) -> None:
    """Send alert to generic webhook (n8n, Slack, etc)."""
    settings = get_settings()
    if not settings.budget_alert_webhook_url:
        return

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                settings.budget_alert_webhook_url,
                json={
                    "text": msg,
                    "pct": pct,
                    "used_tokens": used,
                    "budget_tokens": budget,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        logger.info(f"budget alert sent to webhook: {pct}%")
    except Exception as e:
        logger.warning(f"webhook alert failed: {e}")


async def _send_telegram(msg: str) -> None:
    """Send alert via Telegram Bot API."""
    settings = get_settings()
    token = settings.budget_alert_telegram_token
    chat_id = settings.budget_alert_telegram_chat_id
    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
        logger.info("budget alert sent to telegram")
    except Exception as e:
        logger.warning(f"telegram alert failed: {e}")


async def check_budget_and_alert(used_tokens: int, budget_tokens: int) -> dict:
    """
    Check if budget crossed any threshold and send alerts if so.

    Called after each chat turn with current usage totals.
    Returns dict with usage info.
    """
    settings = get_settings()

    if not settings.budget_alert_enabled or budget_tokens <= 0:
        return {"used": used_tokens, "budget": budget_tokens, "pct": 0, "alerted": False}

    pct = round(100 * used_tokens / budget_tokens, 2)
    alerted = False

    for threshold in sorted(settings.budget_alert_thresholds_list):
        if pct >= threshold and not _recently_alerted(threshold):
            msg = (
                f"\U0001f6a8 <b>Atende AI Budget Alert</b>\n"
                f"Usage: {pct}% ({used_tokens:,}/{budget_tokens:,} tokens)\n"
                f"Threshold: {threshold}%"
            )
            await _send_webhook(msg, pct, used_tokens, budget_tokens)
            await _send_telegram(msg)
            _record_alert(threshold)
            alerted = True
            logger.info(f"budget alert triggered: {threshold}% (actual {pct}%)")

    return {"used": used_tokens, "budget": budget_tokens, "pct": pct, "alerted": alerted}


def reset_cooldown() -> None:
    """Clear cooldown state (useful for daily reset job)."""
    _alert_cooldown.clear()
