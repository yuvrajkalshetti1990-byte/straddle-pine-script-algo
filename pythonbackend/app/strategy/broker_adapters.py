"""
Broker Adapters for multi-broker support (HDFC Sky, Zerodha, Fyers).
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.strategy.types import BrokerType

logger = logging.getLogger(__name__)


class BaseBrokerAdapter(ABC):
    """Abstract base class for all broker interactions."""
    
    def __init__(self, config: Any):
        self.config = config

    @abstractmethod
    async def fetch_straddle_candles(self) -> list[dict[str, Any]]:
        """Fetch real-time candle data for the strategy runner."""
        pass

    @abstractmethod
    async def fetch_historical_candles(
        self, from_dt: datetime, to_dt: datetime
    ) -> list[dict[str, Any]]:
        """Fetch historical candle data for backfilling/warm-up."""
        pass


class HDFCSkyAdapter(BaseBrokerAdapter):
    """HDFC Sky Broker Adapter."""

    async def fetch_straddle_candles(self) -> list[dict[str, Any]]:
        # TODO: Implement actual HDFC Sky API calls here.
        # This will be wired up to app/models/hdfc_sky_model.py
        logger.debug("HDFCSkyAdapter: fetch_straddle_candles called (placeholder)")
        return []
    async def fetch_historical_candles(
        self, from_dt: datetime, to_dt: datetime
    ) -> list[dict[str, Any]]:
        return []


class ZerodhaAdapter(BaseBrokerAdapter):
    """Zerodha Kite Broker Adapter."""

    async def fetch_straddle_candles(self) -> list[dict[str, Any]]:
        from app.models import zerodha_model
        price_data = zerodha_model.fetch_nifty_price()
        if price_data:
            return [{
                "timestamp": None,
                "open": price_data["price"],
                "high": price_data["price"],
                "low": price_data["price"],
                "close": price_data["price"],
                "volume": 0
            }]
        return []
    async def fetch_historical_candles(
        self, from_dt: datetime, to_dt: datetime
    ) -> list[dict[str, Any]]:
        return []


class FyersAdapter(BaseBrokerAdapter):
    """Fyers Broker Adapter."""

    async def fetch_straddle_candles(self) -> list[dict[str, Any]]:
        from app.models import fyers_model
        # For now, just return a single candle with the current price to keep it running
        # Real implementation would fetch the last N minutes of candles
        price_data = fyers_model.fetch_nifty_price()
        if price_data:
            return [{
                "timestamp": None,
                "open": price_data["price"],
                "high": price_data["price"],
                "low": price_data["price"],
                "close": price_data["price"],
                "volume": 0
            }]
        return []
    async def fetch_historical_candles(
        self, from_dt: datetime, to_dt: datetime
    ) -> list[dict[str, Any]]:
        from app.models import fyers_model
        symbol = "NSE:NIFTY50-INDEX" # Default for now
        resolution = str(self.config.timeframe_minutes) if hasattr(self.config, 'timeframe_minutes') else "3"
        
        from_str = from_dt.strftime("%Y-%m-%d")
        to_str = to_dt.strftime("%Y-%m-%d")
        
        return await fyers_model.fetch_symbol_history(
            symbol=symbol,
            resolution=resolution,
            range_from=from_str,
            range_to=to_str
        )


def get_broker_adapter(broker_type: BrokerType, config: Any) -> BaseBrokerAdapter:
    """Factory method to get the correct broker adapter."""
    if broker_type == BrokerType.HDFC_SKY:
        return HDFCSkyAdapter(config)
    elif broker_type == BrokerType.ZERODHA:
        return ZerodhaAdapter(config)
    elif broker_type == BrokerType.FYERS:
        return FyersAdapter(config)
    else:
        logger.warning(f"Unknown broker type {broker_type}, defaulting to HDFC Sky")
        return HDFCSkyAdapter(config)
