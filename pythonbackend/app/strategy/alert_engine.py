"""
Alert Engine — formats and sends webhooks compatible with Stoxxo.

Handles the dynamic placeholder replacement exactly as the Pine Script does:
- {index} -> NIFTY / BANKNIFTY
- {strike} -> 25000
- {lots} -> 2
- {action} -> LE, LX, SE, SX
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

import httpx

from app.strategy.types import TradeAction, TradeDirection, TradeState

logger = logging.getLogger(__name__)


class AlertEngine:
    """Manages outgoing webhooks and alerts."""

    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = webhook_url
        self._client = httpx.AsyncClient(timeout=5.0)

    async def send_entry_alert(self, trade: TradeState, strategy_tag: str) -> None:
        """Format and send an entry alert."""
        action = TradeAction.SE if trade.is_short else TradeAction.LE
        await self._dispatch_alert(trade, action, strategy_tag)

    async def send_exit_alert(self, trade: TradeState, strategy_tag: str) -> None:
        """Format and send an exit alert."""
        action = TradeAction.SX if trade.is_short else TradeAction.LX
        await self._dispatch_alert(trade, action, strategy_tag)

    def _format_message(self, trade: TradeState, action: TradeAction, strategy_tag: str) -> dict[str, Any]:
        """
        Format the alert JSON.
        This represents the standard payload required by auto-trading platforms like Stoxxo.
        """
        # Determine exact symbol based on action and trade type
        if trade.is_short:
            # For short straddles, we'd typically send two legs or a basket.
            # Represented conceptually here.
            symbol = f"{trade.index.value}{trade.strike_price}STR"
        else:
            # Long trades are directional options
            symbol = f"{trade.index.value}{trade.strike_price}{trade.option_type.value}"
            
        return {
            "strategy": strategy_tag,
            "index": trade.index.value,
            "strike": trade.strike_price,
            "type": trade.option_type.value,
            "action": action.value,
            "lots": trade.lots,
            "price": trade.current_price if action in {TradeAction.LX, TradeAction.SX} else trade.entry_price,
            "trade_id": trade.trade_id,
            "symbol": symbol,
            "timestamp": trade.exit_time.isoformat() if action in {TradeAction.LX, TradeAction.SX} and trade.exit_time else (trade.entry_time.isoformat() if trade.entry_time else None)
        }

    async def _dispatch_alert(self, trade: TradeState, action: TradeAction, strategy_tag: str) -> None:
        """Send the actual HTTP request."""
        if not self.webhook_url:
            logger.debug(f"Webhook URL not configured, skipping alert: {action.value} {trade.index.value}")
            return

        payload = self._format_message(trade, action, strategy_tag)

        try:
            response = await self._client.post(self.webhook_url, json=payload)
            response.raise_for_status()
            logger.info(f"Alert sent successfully: {action.value} {trade.trade_id}")
        except Exception as e:
            logger.error(f"Failed to send alert for {trade.trade_id}: {e}")

    async def emit_critical_halt(self, message: str) -> None:
        """Send a critical halt notification."""
        if not self.webhook_url:
            logger.warning(f"CRITICAL HALT: {message}")
            return
            
        try:
            payload = {"type": "CRITICAL_HALT", "message": message, "timestamp": datetime.now().isoformat()}
            response = await self._client.post(self.webhook_url, json=payload)
            response.raise_for_status()
            logger.info("Critical halt alert sent.")
        except Exception as e:
            logger.error(f"Failed to send critical halt alert: {e}")

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
