"""
Index-level constants for the strategy engine.

All values are taken directly from the Pine Script defaults
and must NOT be changed without explicit approval.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.strategy.types import IndexType


# ---------------------------------------------------------------------------
# Per-index configuration constants
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IndexConfig:
    """Immutable configuration for a single index."""

    index: IndexType
    timeframe_minutes: int        # Candle interval in minutes
    lot_size: int                 # Shares per lot
    strike_step: float            # Distance between adjacent strikes
    exchange: str                 # Exchange code for symbol generation
    symbol_prefix: str            # Prefix for option symbols
    underlying_symbol: str        # Underlying index symbol
    weekly_expiry: bool           # Whether weekly expiry is used


NIFTY_CONFIG = IndexConfig(
    index=IndexType.NIFTY,
    timeframe_minutes=5,
    lot_size=65,
    strike_step=50.0,
    exchange="NFO",
    symbol_prefix="NIFTY",
    underlying_symbol="NIFTY 50",
    weekly_expiry=True,
)

BANKNIFTY_CONFIG = IndexConfig(
    index=IndexType.BANKNIFTY,
    timeframe_minutes=3,
    lot_size=15,
    strike_step=100.0,
    exchange="NFO",
    symbol_prefix="BANKNIFTY",
    underlying_symbol="NIFTY BANK",
    weekly_expiry=True,
)

SENSEX_CONFIG = IndexConfig(
    index=IndexType.SENSEX,
    timeframe_minutes=3,
    lot_size=10,
    strike_step=100.0,
    exchange="BFO",
    symbol_prefix="SENSEX",
    underlying_symbol="SENSEX",
    weekly_expiry=True,
)


INDEX_CONFIGS: dict[IndexType, IndexConfig] = {
    IndexType.NIFTY: NIFTY_CONFIG,
    IndexType.BANKNIFTY: BANKNIFTY_CONFIG,
    IndexType.SENSEX: SENSEX_CONFIG,
}


def get_index_config(index: IndexType) -> IndexConfig:
    """Return the IndexConfig for a given index type."""
    config = INDEX_CONFIGS.get(index)
    if config is None:
        raise ValueError(f"Unsupported index: {index}")
    return config


# ---------------------------------------------------------------------------
# Indicator period defaults — from Pine Script input() calls
# ---------------------------------------------------------------------------

INDICATOR_LENGTH = 14        # RSI, DMI, ADX, CHOP period
ROC_LENGTH = 9               # Rate of Change period
EMA_LENGTH = 20              # EMA period
VWMA_LENGTH = 35             # VWMA period (from settings UI default)
VWAP_ANCHOR = "Session"      # VWAP anchoring (daily reset)
SUPERTREND_FACTOR = 3.0      # SuperTrend multiplier
SUPERTREND_PERIOD = 10       # SuperTrend ATR period


# ---------------------------------------------------------------------------
# Strike offset mapping — Pine Script strike architecture
# ---------------------------------------------------------------------------

# s1=ITM2, s2=ITM1, s3=ATM, s4=OTM1, s5=OTM2
# For CE: ITM means lower strike, OTM means higher strike
# For PE: ITM means higher strike, OTM means lower strike
# For STR (straddle): offsets are from ATM
STRIKE_OFFSETS: dict[str, int] = {
    "S1": -4,   # ITM2 (-200)
    "S2": -2,   # ITM1 (-100)
    "S3": 0,    # ATM
    "S4": 2,    # OTM1 (+100)
    "S5": 4,    # OTM2 (+200)
}


# ---------------------------------------------------------------------------
# Market session times (IST)
# ---------------------------------------------------------------------------

MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 15
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 30


# ---------------------------------------------------------------------------
# Trading day codes (for day-of-week filters)
# ---------------------------------------------------------------------------

WEEKDAY_NAMES = {
    0: "mon",
    1: "tue",
    2: "wed",
    3: "thu",
    4: "fri",
}
