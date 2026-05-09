"""
Typed models for the strategy engine.

Every enum and dataclass here maps 1:1 to a Pine Script concept.
Names are kept as close to the Pine source as possible.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Any


# ---------------------------------------------------------------------------
# Enums — Pine Script categorical states
# ---------------------------------------------------------------------------

class IndexType(str, enum.Enum):
    """Supported indices."""
    NIFTY = "NIFTY"
    BANKNIFTY = "BANKNIFTY"
    SENSEX = "SENSEX"

    @property
    def strike_step(self) -> int:
        if self == IndexType.NIFTY: return 50
        if self == IndexType.BANKNIFTY: return 100
        if self == IndexType.SENSEX: return 100
        return 100

    def round_to_strike(self, price: float) -> float:
        step = self.strike_step
        return round(price / step) * step

class BrokerType(str, enum.Enum):
    """Supported brokers for data and execution."""
    HDFC_SKY = "HDFC_SKY"
    ZERODHA = "ZERODHA"
    FYERS = "FYERS"


class SlippageMode(str, enum.Enum):
    """Modes for slippage simulation."""
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    VOLATILITY = "volatility"


class StrikeLabel(str, enum.Enum):
    """
    Strike slot labels used by the Pine Script.
    s1=ITM2, s2=ITM1, s3=ATM, s4=OTM1, s5=OTM2
    """
    S1 = "S1"  # ITM2
    S2 = "S2"  # ITM1
    S3 = "S3"  # ATM
    S4 = "S4"  # OTM1
    S5 = "S5"  # OTM2


class OptionType(str, enum.Enum):
    """Option leg type."""
    CE = "CE"
    PE = "PE"
    STR = "STR"  # Combined CE+PE synthetic straddle


class TradeSource(str, enum.Enum):
    LIVE = "LIVE"
    BACKFILL = "BACKFILL"
    REPLAY = "REPLAY"


class RegimeState(str, enum.Enum):
    """
    Full regime classification from Pine Script.
    Matches the 10-state regime engine exactly.
    """
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    SHORT_COV = "SHORT COV"
    DECAY = "DECAY"
    SIDEWAYS = "SIDEWAYS"
    WAIT = "WAIT"
    LONG_STR = "LONG STR"
    BUY_CE = "BUY CE"
    BUY_PE = "BUY PE"
    SHORT = "SHORT"


class DirectionalState(str, enum.Enum):
    """
    Directional state machine from Pine Script.
    Controls bull/bear building → active transitions.
    """
    NEUTRAL = "NEUTRAL"
    BULL_BUILDING = "BULL_BUILDING"
    BEAR_BUILDING = "BEAR_BUILDING"
    BULL_ACTIVE = "BULL_ACTIVE"
    BEAR_ACTIVE = "BEAR_ACTIVE"


class TradeDirection(str, enum.Enum):
    """Trade direction."""
    LONG = "LONG"
    SHORT = "SHORT"


class SignalType(str, enum.Enum):
    """Signal source type from procSignal()."""
    MOMENTUM = "MOMENTUM"
    TREND = "TREND"
    VWAP_REV = "VWAP_REV"
    NONE = "NONE"


class ExitReason(str, enum.Enum):
    """Why a trade was exited."""
    FIXED_SL = "FIXED_SL"
    FIXED_TARGET = "FIXED_TARGET"
    TRAILING_SL = "TRAILING_SL"
    SMART_EXIT = "SMART_EXIT"
    STRUCTURE_BREAK = "STRUCTURE_BREAK"
    PANIC_EXIT = "PANIC_EXIT"
    TIME_EXIT = "TIME_EXIT"
    REGIME_EXIT = "REGIME_EXIT"
    MANUAL_EXIT = "MANUAL_EXIT"
    ENGINE_STOP = "ENGINE_STOP"
    KILL_SWITCH = "KILL_SWITCH"


class CalcMode(str, enum.Enum):
    """Calculation mode from Pine Script input."""
    AUTO = "Auto"
    MANUAL = "Manual"


class TradeAction(str, enum.Enum):
    """Actions for QTP / manual trade panel."""
    LE = "LE"   # Long Entry
    LX = "LX"   # Long Exit
    SE = "SE"   # Short Entry
    SX = "SX"   # Short Exit


# ---------------------------------------------------------------------------
# Data containers — candle and indicator snapshots
# ---------------------------------------------------------------------------

@dataclass
class OHLCV:
    """Single OHLCV candle."""
    timestamp: datetime | None = None
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0

    @property
    def is_valid(self) -> bool:
        return self.high >= self.low > 0 and self.open > 0 and self.close > 0


@dataclass
class StraddleCandle:
    """Combined CE+PE synthetic straddle candle."""
    timestamp: datetime | None = None
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    ce_ltp: float = 0.0
    pe_ltp: float = 0.0
    ce_volume: float = 0.0
    pe_volume: float = 0.0
    total_volume: float = 0.0


@dataclass
class IndicatorSnapshot:
    """
    All indicator values at a single point in time.
    Matches the Pine Script indicator set exactly.
    """
    rsi: float | None = None
    roc: float | None = None
    plus_di: float | None = None
    minus_di: float | None = None
    adx: float | None = None
    chop: float | None = None
    ema: float | None = None
    vwap: float | None = None
    vwma: float | None = None
    supertrend: float | None = None
    supertrend_direction: int | None = None  # 1 = up, -1 = down

    def has_values(self) -> bool:
        return any(
            v is not None
            for v in [self.rsi, self.roc, self.plus_di, self.minus_di, self.adx, self.chop]
        )

    def to_dict(self) -> dict[str, float | None]:
        return {
            "rsi": self.rsi,
            "roc": self.roc,
            "plusDI": self.plus_di,
            "minusDI": self.minus_di,
            "adx": self.adx,
            "chop": self.chop,
            "ema": self.ema,
            "vwap": self.vwap,
            "vwma": self.vwma,
            "supertrend": self.supertrend,
            "supertrendDir": self.supertrend_direction,
        }


# ---------------------------------------------------------------------------
# Trade state containers
# ---------------------------------------------------------------------------

@dataclass
class TradeState:
    """
    Per-trade state — mirrors Pine Script trade variables exactly.
    One instance per active trade.
    """
    trade_id: str = ""
    index: IndexType = IndexType.NIFTY
    strike_label: StrikeLabel = StrikeLabel.S3
    strike_price: float = 0.0
    option_type: OptionType = OptionType.STR
    direction: TradeDirection = TradeDirection.SHORT
    signal_type: SignalType = SignalType.NONE

    # Entry state
    entry_price: float = 0.0  # ep in Pine Script
    entry_time: datetime | None = None
    lots: int = 0

    # Running state
    highest_high: float = 0.0      # HH tracking
    lowest_low: float = math.inf   # LL tracking
    current_price: float = 0.0
    sl_safe: bool = False          # SL-safe flag from Pine Script
    trailing_sl_active: bool = False
    trailing_sl_level: float = 0.0

    # Exit state
    exit_price: float = 0.0
    exit_time: datetime | None = None
    exit_reason: ExitReason | None = None

    # Analytical safeguards
    prev_regime: str | None = None
    execution_score: float | None = None
    source: TradeSource = TradeSource.LIVE
    is_replay: bool = False
    
    # P&L
    floating_pnl: float = 0.0
    realized_pnl: float = 0.0

    @property
    def is_active(self) -> bool:
        return self.entry_time is not None and self.exit_time is None

    @property
    def is_short(self) -> bool:
        return self.direction == TradeDirection.SHORT

    @property
    def is_long(self) -> bool:
        return self.direction == TradeDirection.LONG


@dataclass
class SignalState:
    """
    lSig state per strike — tracks signal progression.
    Maps to Pine Script's lSig variables.
    """
    active: bool = False
    direction: TradeDirection | None = None
    signal_type: SignalType = SignalType.NONE
    signal_bar: int = 0       # Bar index when signal fired
    confirmed: bool = False


@dataclass
class DailyCounters:
    """
    Per-day trade counters with daily reset.
    Maps to Pine Script's day-scoped counters.
    """
    date: str = ""  # YYYY-MM-DD
    short_trades: int = 0
    long_trades: int = 0
    realized_pnl: float = 0.0
    floating_pnl: float = 0.0

    def reset(self, new_date: str) -> None:
        self.date = new_date
        self.short_trades = 0
        self.long_trades = 0
        self.realized_pnl = 0.0
        self.floating_pnl = 0.0


@dataclass
class AccountState:
    """
    Account/wallet state — tracks capital and P&L.
    Maps to Pine Script's account engine.
    """
    initial_capital: float = 100_000.0
    current_capital: float = 100_000.0
    realized_pnl: float = 0.0
    floating_pnl: float = 0.0
    historical_pnl: list[float] = field(default_factory=list)

    @property
    def total_pnl(self) -> float:
        return self.realized_pnl + self.floating_pnl

    @property
    def wallet_balance(self) -> float:
        return self.initial_capital + self.realized_pnl


# ---------------------------------------------------------------------------
# Strategy engine state container
# ---------------------------------------------------------------------------

@dataclass
class StrategyState:
    """
    Complete strategy state at any point in time.
    This is the root state object persisted and restored.
    """
    index: IndexType = IndexType.NIFTY
    bar_index: int = 0
    current_time: datetime | None = None
    is_warming_up: bool = False

    # Regime
    regime: RegimeState = RegimeState.WAIT
    directional_state: DirectionalState = DirectionalState.NEUTRAL

    # Indicators (latest)
    indicators: dict[str, IndicatorSnapshot] = field(default_factory=dict)
    # Key = strike_label string, e.g. "S1", "S2", etc.

    # Signals per strike
    signals: dict[str, SignalState] = field(default_factory=dict)

    # Active trades
    active_trades: list[TradeState] = field(default_factory=list)
    closed_trades: list[TradeState] = field(default_factory=list)

    # Daily counters
    daily: DailyCounters = field(default_factory=DailyCounters)

    # Account
    account: AccountState = field(default_factory=AccountState)

    # Day tracking
    day_open: float = 0.0
    day_open_set: bool = False

    # Engine control
    engine_running: bool = False
    
    # ATM Tracking
    current_atm_strike: float = 0.0
