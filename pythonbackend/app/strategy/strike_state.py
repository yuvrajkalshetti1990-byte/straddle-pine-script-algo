"""
Per-strike state machine — exact Pine Script parity.

Each strike (S1–S5) maintains independent state for:
- Short position tracking (lSig)
- Long position tracking (lSigLong)
- Entry/exit prices and times
- Lowest low / highest high for TSL
- Banked P&L points
- SL-safe flag
- Trade counters per strike per day

This is a 1:1 mapping of Pine Script's per-strike var declarations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.strategy.types import IndicatorSnapshot, StrikeLabel


@dataclass
class StrikeState:
    """
    Per-strike state — maps exactly to Pine Script vars for one strike.

    Pine equivalents:
        lSig1      → lSig          (0=flat, -1=short active)
        lSigLong1  → lSigLong      (0=flat, 2=long active)
        ep1        → ep            (short entry price)
        epLong1    → epLong        (long entry price)
        et1        → et            (entry time)
        xt1        → xt            (exit time)
        banked1    → banked        (realized P&L in points)
        ll1        → ll            (lowest low since short entry)
        hh1        → hh            (highest high since long entry)
        slSafe1    → sl_safe       (smart SL disable flag)
        isLong1    → is_long       (direction flag)
        trig1      → trig          (trigger string)
        cntShort1  → cnt_short     (short trade count today)
        cntLong1   → cnt_long      (long trade count today)
    """
    label: StrikeLabel = StrikeLabel.S3
    strike_price: float = 0.0

    # Position state
    lSig: int = 0          # 0=flat, -1=short active
    lSigLong: int = 0      # 0=flat, 2=long active
    ep: float | None = None       # short entry price
    epLong: float | None = None   # long entry price
    et: datetime | None = None    # entry time
    xt: datetime | None = None    # exit time
    banked: float = 0.0           # realized P&L points (accumulated)
    ll: float | None = None       # lowest low (TSL tracking for short)
    hh: float | None = None       # highest high (TSL tracking for long)
    sl_safe: bool = False         # smart SL disable flag
    is_long: bool = False         # direction flag for P&L calc
    trig: str = "—"               # trigger description
    current_trade_id: str | None = None  # tracks the database ID of the active trade

    # Trade counters (per day)
    cnt_short: int = 0
    cnt_long: int = 0

    # Regime Tracking
    current_regime: str = "SIDEWAYS"
    prev_regime: str = "SIDEWAYS"

    # Latest candle OHLC for this strike's straddle
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0

    # Day open values
    day_open: float | None = None
    ce_day_open: float | None = None
    pe_day_open: float | None = None

    # Latest CE/PE close (for regime/tType calc)
    ce_close: float = 0.0
    pe_close: float = 0.0

    # Per-strike indicators
    indicators: IndicatorSnapshot = field(default_factory=IndicatorSnapshot)
    prev_indicators: IndicatorSnapshot | None = None

    # Per-strike overlays (EMA, VWAP, VWMA) — needed for signal/exit logic
    ema: float | None = None
    vwap: float | None = None
    vwma: float | None = None

    # Per-strike candle buffer for indicator computation
    candle_buffer: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_flat(self) -> bool:
        """True if no position (neither short nor long)."""
        return self.lSig == 0 and self.lSigLong == 0

    @property
    def has_short(self) -> bool:
        return self.lSig == -1

    @property
    def has_long(self) -> bool:
        return self.lSigLong == 2

    @property
    def is_ready(self) -> bool:
        """True if we have valid data and indicators are fully warmed up."""
        if self.close <= 0 or self.day_open is None:
            return False
        # Indicators are ready if EMA and VWMA are populated (meaning warmup is complete)
        if not self.indicators.has_values():
            return False
        return self.indicators.ema is not None and self.indicators.vwma is not None

    @property
    def current_pnl_points(self) -> float:
        """
        Running P&L in points (banked + floating).
        Matches Pine's _runPnl calculation in the P&L table.
        """
        run = self.banked
        if self.lSig == -1 and self.ep is not None:
            run += (self.ep - self.close)
        elif self.lSigLong == 2 and self.epLong is not None:
            run += (self.close - self.epLong)
        return run

    def daily_reset(self) -> None:
        """
        Reset all per-day state. Called on ta.change(time("D"))!=0.
        Matches Pine Script's daily reset block exactly.
        """
        self.lSig = 0
        self.lSigLong = 0
        self.ep = None
        self.epLong = None
        self.et = None
        self.xt = None
        self.banked = 0.0
        self.hh = None
        self.ll = None
        self.sl_safe = False
        self.is_long = False
        self.trig = "—"
        self.current_trade_id = None
        self.cnt_short = 0
        self.cnt_long = 0
        self.day_open = None
        self.ce_day_open = None
        self.pe_day_open = None
        self.candle_buffer.clear()
        self.prev_indicators = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for API responses."""
        return {
            "label": self.label.value,
            "strikePrice": self.strike_price,
            "lSig": self.lSig,
            "lSigLong": self.lSigLong,
            "ep": self.ep,
            "epLong": self.epLong,
            "entryTime": self.et.isoformat() if self.et else None,
            "exitTime": self.xt.isoformat() if self.xt else None,
            "banked": round(self.banked, 2),
            "pnlPoints": round(self.current_pnl_points, 2),
            "slSafe": self.sl_safe,
            "isLong": self.is_long,
            "trig": self.trig,
            "cntShort": self.cnt_short,
            "cntLong": self.cnt_long,
            "close": round(self.close, 2),
            "dayOpen": self.day_open,
        }


# Map Pine's table labels (ITM2, ITM1, ATM, OTM1, OTM2) to StrikeLabel
PINE_LABEL_MAP: dict[StrikeLabel, str] = {
    StrikeLabel.S1: "ITM2",
    StrikeLabel.S2: "ITM1",
    StrikeLabel.S3: "ATM",
    StrikeLabel.S4: "OTM1",
    StrikeLabel.S5: "OTM2",
}
