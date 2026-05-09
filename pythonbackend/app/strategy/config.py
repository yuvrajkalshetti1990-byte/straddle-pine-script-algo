"""
Strategy configuration — maps every Pine Script input() parameter.

Default values match the Pine Script exactly. The StrategyConfig
dataclass is the single source of truth for all user-configurable
parameters in the Python engine.

The UI (StrategySettingsModal.tsx, settings/page.tsx) already
has fields for every parameter here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.strategy.types import CalcMode, IndexType, BrokerType, SlippageMode


@dataclass
class StrikeConfig:
    """Per-strike slot configuration — maps to Pine Script strike rows."""
    label: str = "S3"          # S1..S5
    enabled: bool = True
    chart: bool = False
    show_index: bool = True
    price: float = 0.0        # Manual override (0 = auto from spot)


@dataclass
class ScopeConfig:
    """Which strike slots are in scope for a strategy leg."""
    s1: bool = False
    s2: bool = True
    s3: bool = True
    s4: bool = True
    s5: bool = False

    def is_in_scope(self, label: str) -> bool:
        return getattr(self, label.lower(), False)


@dataclass
class DayConfig:
    """Which weekdays are enabled for trading."""
    mon: bool = True
    tue: bool = True
    wed: bool = True
    thu: bool = True
    fri: bool = True

    def is_enabled(self, weekday: int) -> bool:
        """weekday: 0=Mon, 1=Tue, ..., 4=Fri"""
        names = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri"}
        name = names.get(weekday)
        if name is None:
            return False
        return getattr(self, name, False)


@dataclass
class TrailingStopConfig:
    """Trailing stop loss parameters."""
    enabled: bool = False
    activation_points: float = 20.0   # Points profit to activate
    trailing_distance: float = 10.0   # Distance from high/low


@dataclass
class ShortStrategyConfig:
    """
    Short (straddle selling) strategy configuration.
    Maps to Pine Script Section 4: SHORT STRATEGY.
    """
    enabled: bool = True
    lots: int = 2
    days: DayConfig = field(default_factory=DayConfig)
    max_trades: int = 0              # 0 = unlimited
    start_time: str = "09:15"        # HH:MM
    ignore_logic: bool = False       # Use start time instead of signal
    restrict_scope: bool = True
    scope: ScopeConfig = field(default_factory=lambda: ScopeConfig(
        s1=False, s2=True, s3=True, s4=True, s5=False
    ))
    time_exit_enabled: bool = True
    time_exit_hour: int = 14
    time_exit_minute: int = 30
    fixed_sl: float = 0.0           # 0 = disabled
    fixed_target: float = 0.0       # 0 = disabled
    smart_sl_disable: bool = True
    smart_sl_points: float = 10.0
    trailing_sl: TrailingStopConfig = field(default_factory=lambda: TrailingStopConfig(
        enabled=False, activation_points=20.0, trailing_distance=10.0
    ))


@dataclass
class LongStrategyConfig:
    """
    Long (directional buying) strategy configuration.
    Maps to Pine Script Section 5: LONG STRATEGY.
    """
    enabled: bool = True
    lots: int = 6
    days: DayConfig = field(default_factory=DayConfig)
    max_trades: int = 1              # 0 = unlimited
    start_time: str = "09:15"        # HH:MM
    ignore_logic: bool = True        # Use start time instead of signal
    adx_threshold: float = 20.0     # Min ADX for long entry
    strict_entry: bool = True        # Strict entry filter
    restrict_scope: bool = True
    scope: ScopeConfig = field(default_factory=lambda: ScopeConfig(
        s1=False, s2=True, s3=False, s4=True, s5=False
    ))
    time_exit_enabled: bool = True
    time_exit_hour: int = 15
    time_exit_minute: int = 10
    fixed_sl: float = 0.0           # 0 = disabled
    fixed_target: float = 0.0       # 0 = disabled
    trailing_sl: TrailingStopConfig = field(default_factory=lambda: TrailingStopConfig(
        enabled=False, activation_points=15.0, trailing_distance=10.0
    ))


@dataclass
class LogicConfig:
    """
    Logic / signal generation settings.
    Maps to Pine Script Section 3: LOGIC SETTINGS.
    """
    calc_mode: CalcMode = CalcMode.AUTO
    filter_chop: bool = True
    chop_threshold: float = 61.8
    breakdown_window: int = 0
    use_momentum: bool = True
    use_trend: bool = False
    use_vwap_rev: bool = False
    min_reversal_size: float = 5.0
    restrict_vwap_scope: bool = False
    vwap_scope: ScopeConfig = field(default_factory=ScopeConfig)


@dataclass
class VisualConfig:
    """
    Visual/display settings.
    Maps to Pine Script Section 6: VISUALS.
    """
    main_table: str = "Hide"
    pnl_table: str = "Bottom"
    show_regime: bool = True
    show_ind_reg: bool = True
    show_t_mode: bool = True
    show_t_type: bool = True
    show_supertrend: bool = False
    supertrend_factor: float = 3.0
    supertrend_period: int = 10
    show_ema20: bool = True
    show_vwap: bool = True
    show_vwma: bool = True
    vwma_length: int = 35
    show_momentum_labels: bool = False
    show_directional_labels: bool = False


@dataclass
class SlippageConfig:
    """Configuration for structured slippage models."""
    mode: SlippageMode = SlippageMode.FIXED
    fixed_points: float = 0.0
    percentage: float = 0.0        # e.g. 0.01 for 1%
    vol_multiplier: float = 0.0    # e.g. 0.1 for 10% of candle range

@dataclass
class RiskConfig:
    """Configuration for risk kill switches and safeguards."""
    max_daily_loss: float = 50000.0  # Stop all trading if daily loss exceeds this
    max_consecutive_losses: int = 5   # Stop if N trades in a row are losses
    stale_data_halt_sec: int = 300    # Halt if data is older than 5 minutes
    max_revisions_halt: int = 10      # Halt if > 10 candle revisions in a day
    api_stability_halt: bool = True  # Halt if API error rate > threshold

@dataclass
class StrategyConfig:
    """
    Root configuration object — contains ALL Pine Script input() parameters.

    This is the single source of truth for the Python engine.
    Every field has a default matching the Pine Script default value.
    """

    # Section 1: Setup
    index: IndexType = IndexType.NIFTY
    broker: BrokerType = BrokerType.FYERS
    expiry_dd: int = 12
    expiry_mm: int = 5
    expiry_yy: int = 26
    start_dd: int = 30
    start_mm: int = 12
    start_yy: int = 2025
    end_dd: int = 31
    end_mm: int = 12
    end_yy: int = 2099

    # Section 2: Strike Selection
    strikes: list[StrikeConfig] = field(default_factory=lambda: [
        StrikeConfig(label="S1", enabled=False, chart=False, show_index=True, price=0),
        StrikeConfig(label="S2", enabled=True, chart=False, show_index=True, price=0),
        StrikeConfig(label="S3", enabled=True, chart=False, show_index=True, price=0),
        StrikeConfig(label="S4", enabled=True, chart=True, show_index=True, price=0),
        StrikeConfig(label="S5", enabled=False, chart=False, show_index=True, price=0),
    ])

    # Section 3: Logic
    logic: LogicConfig = field(default_factory=LogicConfig)

    # Section 4: Short Strategy
    short: ShortStrategyConfig = field(default_factory=ShortStrategyConfig)

    # Section 5: Long Strategy
    long: LongStrategyConfig = field(default_factory=LongStrategyConfig)

    # Section 6: Visuals
    visuals: VisualConfig = field(default_factory=VisualConfig)

    # Strategy Tag
    strategy_tag: str = "Yuvi-N-Short/Long"
    
    # Trading Mode
    trading_mode: str = "live" # "paper" or "live"

    # Timeframe in minutes (3 for NIFTY straddle)
    timeframe_minutes: int = 3

    # Capital
    initial_capital: float = 2_334_515.0
    max_capital_per_trade: float = 10_000.0
    risk_percentage: float = 2.0

    # Risk Management
    risk: RiskConfig = field(default_factory=RiskConfig)

    # Strategy lag
    strategy_lag: int = 0

    # Simulation settings
    slippage: SlippageConfig = field(default_factory=SlippageConfig)

    def get_enabled_strikes(self) -> list[StrikeConfig]:
        """Return only strikes that are enabled."""
        return [s for s in self.strikes if s.enabled]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for API responses."""
        return {
            "index": self.index.value,
            "broker": self.broker.value,
            "lotSize": self.index_config.lot_size,
            "expiry_dd": self.expiry_dd,
            "expiry_mm": self.expiry_mm,
            "expiry_yy": self.expiry_yy,
            "start_dd": self.start_dd,
            "start_mm": self.start_mm,
            "start_yy": self.start_yy,
            "end_dd": self.end_dd,
            "end_mm": self.end_mm,
            "end_yy": self.end_yy,
            "strikes": [
                {
                    "label": s.label,
                    "enabled": s.enabled,
                    "chart": s.chart,
                    "show_index": s.show_index,
                    "price": s.price
                }
                for s in self.strikes
            ],
            "strategyTag": self.strategy_tag,
            "tradingMode": self.trading_mode,
            "timeframeMinutes": self.timeframe_minutes,
            "initialCapital": self.initial_capital,
            "logic": {
                "calcMode": self.logic.calc_mode.value,
                "filterChop": self.logic.filter_chop,
                "chopThreshold": self.logic.chop_threshold,
                "breakdownWindow": self.logic.breakdown_window,
                "useMomentum": self.logic.use_momentum,
                "useTrend": self.logic.use_trend,
                "useVwapRev": self.logic.use_vwap_rev,
                "minReversalSize": self.logic.min_reversal_size,
                "restrictVwapScope": self.logic.restrict_vwap_scope,
                "vwapScope": {
                    "s1": self.logic.vwap_scope.s1,
                    "s2": self.logic.vwap_scope.s2,
                    "s3": self.logic.vwap_scope.s3,
                    "s4": self.logic.vwap_scope.s4,
                    "s5": self.logic.vwap_scope.s5,
                }
            },
            "short": {
                "enabled": self.short.enabled,
                "lots": self.short.lots,
                "maxTrades": self.short.max_trades,
                "startTime": self.short.start_time,
                "ignoreLogic": self.short.ignore_logic,
                "restrictScope": self.short.restrict_scope,
                "scope": {
                    "s1": self.short.scope.s1,
                    "s2": self.short.scope.s2,
                    "s3": self.short.scope.s3,
                    "s4": self.short.scope.s4,
                    "s5": self.short.scope.s5,
                },
                "fixedSL": self.short.fixed_sl,
                "fixedTarget": self.short.fixed_target,
                "smartSlDisable": self.short.smart_sl_disable,
                "smartSlPoints": self.short.smart_sl_points,
                "trailingSL": {
                    "enabled": self.short.trailing_sl.enabled,
                    "activation": self.short.trailing_sl.activation_points,
                    "distance": self.short.trailing_sl.trailing_distance,
                },
                "timeExit": {
                    "enabled": self.short.time_exit_enabled,
                    "hour": self.short.time_exit_hour,
                    "minute": self.short.time_exit_minute,
                },
            },
            "long": {
                "enabled": self.long.enabled,
                "lots": self.long.lots,
                "maxTrades": self.long.max_trades,
                "startTime": self.long.start_time,
                "ignoreLogic": self.long.ignore_logic,
                "adxThreshold": self.long.adx_threshold,
                "strictEntry": self.long.strict_entry,
                "restrictScope": self.long.restrict_scope,
                "scope": {
                    "s1": self.long.scope.s1,
                    "s2": self.long.scope.s2,
                    "s3": self.long.scope.s3,
                    "s4": self.long.scope.s4,
                    "s5": self.long.scope.s5,
                },
                "fixedSL": self.long.fixed_sl,
                "fixedTarget": self.long.fixed_target,
                "trailingSL": {
                    "enabled": self.long.trailing_sl.enabled,
                    "activation": self.long.trailing_sl.activation_points,
                    "distance": self.long.trailing_sl.trailing_distance,
                },
                "timeExit": {
                    "enabled": self.long.time_exit_enabled,
                    "hour": self.long.time_exit_hour,
                    "minute": self.long.time_exit_minute,
                },
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategyConfig:
        """Deserialize from API request / saved config."""
        config = cls()

        if "index" in data:
            config.index = IndexType(data["index"])
        if "broker" in data:
            config.broker = BrokerType(data["broker"])
            
        # Setup
        for field in ["expiry_dd", "expiry_mm", "expiry_yy", "start_dd", "start_mm", "start_yy", "end_dd", "end_mm", "end_yy"]:
            if field in data:
                setattr(config, field, int(data[field]))
        
        # Strikes
        if "strikes" in data and isinstance(data["strikes"], list):
            config.strikes = []
            for s_data in data["strikes"]:
                config.strikes.append(StrikeConfig(
                    label=s_data.get("label", "S?"),
                    enabled=bool(s_data.get("enabled", False)),
                    chart=bool(s_data.get("chart", False)),
                    show_index=bool(s_data.get("show_index", True)),
                    price=float(s_data.get("price", 0))
                ))

        if "strategyTag" in data:
            config.strategy_tag = data["strategyTag"]
        if "tradingMode" in data:
            config.trading_mode = data["tradingMode"]
        if "timeframeMinutes" in data:
            config.timeframe_minutes = int(data["timeframeMinutes"])
        if "initialCapital" in data:
            config.initial_capital = float(data["initialCapital"])

        logic = data.get("logic") or {}
        if "calcMode" in logic:
            config.logic.calc_mode = CalcMode(logic["calcMode"])
        if "filterChop" in logic:
            config.logic.filter_chop = bool(logic["filterChop"])
        if "chopThreshold" in logic:
            config.logic.chop_threshold = float(logic["chopThreshold"])
        if "breakdownWindow" in logic:
            config.logic.breakdown_window = int(logic["breakdownWindow"])
        if "useMomentum" in logic:
            config.logic.use_momentum = bool(logic["useMomentum"])
        if "useTrend" in logic:
            config.logic.use_trend = bool(logic["useTrend"])
        if "useVwapRev" in logic:
            config.logic.use_vwap_rev = bool(logic["useVwapRev"])
        if "minReversalSize" in logic:
            config.logic.min_reversal_size = float(logic["minReversalSize"])
        if "restrictVwapScope" in logic:
            config.logic.restrict_vwap_scope = bool(logic["restrictVwapScope"])
        
        v_scope = logic.get("vwapScope") or {}
        for s in ["s1", "s2", "s3", "s4", "s5"]:
            if s in v_scope:
                setattr(config.logic.vwap_scope, s, bool(v_scope[s]))

        short = data.get("short") or {}
        if "enabled" in short:
            config.short.enabled = bool(short["enabled"])
        if "lots" in short:
            config.short.lots = int(short["lots"])
        if "maxTrades" in short:
            config.short.max_trades = int(short["maxTrades"])
        if "startTime" in short:
            config.short.start_time = str(short["startTime"])
        if "ignoreLogic" in short:
            config.short.ignore_logic = bool(short["ignoreLogic"])
        if "restrictScope" in short:
            config.short.restrict_scope = bool(short["restrictScope"])
            
        s_scope = short.get("scope") or {}
        for s in ["s1", "s2", "s3", "s4", "s5"]:
            if s in s_scope:
                setattr(config.short.scope, s, bool(s_scope[s]))

        if "fixedSL" in short:
            config.short.fixed_sl = float(short["fixedSL"])
        if "fixedTarget" in short:
            config.short.fixed_target = float(short["fixedTarget"])
        if "smartSlDisable" in short:
            config.short.smart_sl_disable = bool(short["smartSlDisable"])
        if "smartSlPoints" in short:
            config.short.smart_sl_points = float(short["smartSlPoints"])

        short_tsl = short.get("trailingSL") or {}
        if "enabled" in short_tsl:
            config.short.trailing_sl.enabled = bool(short_tsl["enabled"])
        if "activation" in short_tsl:
            config.short.trailing_sl.activation_points = float(short_tsl["activation"])
        if "distance" in short_tsl:
            config.short.trailing_sl.trailing_distance = float(short_tsl["distance"])

        short_te = short.get("timeExit") or {}
        if "enabled" in short_te:
            config.short.time_exit_enabled = bool(short_te["enabled"])
        if "hour" in short_te:
            config.short.time_exit_hour = int(short_te["hour"])
        if "minute" in short_te:
            config.short.time_exit_minute = int(short_te["minute"])

        lng = data.get("long") or {}
        if "enabled" in lng:
            config.long.enabled = bool(lng["enabled"])
        if "lots" in lng:
            config.long.lots = int(lng["lots"])
        if "maxTrades" in lng:
            config.long.max_trades = int(lng["maxTrades"])
        if "startTime" in lng:
            config.long.start_time = str(lng["startTime"])
        if "ignoreLogic" in lng:
            config.long.ignore_logic = bool(lng["ignoreLogic"])
        if "adxThreshold" in lng:
            config.long.adx_threshold = float(lng["adxThreshold"])
        if "strictEntry" in lng:
            config.long.strict_entry = bool(lng["strictEntry"])
        if "restrictScope" in lng:
            config.long.restrict_scope = bool(lng["restrictScope"])
            
        l_scope = lng.get("scope") or {}
        for s in ["s1", "s2", "s3", "s4", "s5"]:
            if s in l_scope:
                setattr(config.long.scope, s, bool(l_scope[s]))

        if "fixedSL" in lng:
            config.long.fixed_sl = float(lng["fixedSL"])
        if "fixedTarget" in lng:
            config.long.fixed_target = float(lng["fixedTarget"])

        long_tsl = lng.get("trailingSL") or {}
        if "enabled" in long_tsl:
            config.long.trailing_sl.enabled = bool(long_tsl["enabled"])
        if "activation" in long_tsl:
            config.long.trailing_sl.activation_points = float(long_tsl["activation"])
        if "distance" in long_tsl:
            config.long.trailing_sl.trailing_distance = float(long_tsl["distance"])

        long_te = lng.get("timeExit") or {}
        if "enabled" in long_te:
            config.long.time_exit_enabled = bool(long_te["enabled"])
        if "hour" in long_te:
            config.long.time_exit_hour = int(long_te["hour"])
        if "minute" in long_te:
            config.long.time_exit_minute = int(long_te["minute"])

        return config

    @staticmethod
    def _get_path(index: IndexType) -> str:
        import os
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        return os.path.join(data_dir, f"strategy_config_{index.value.lower()}.json")

    def save_to_disk(self):
        """Save the current configuration to disk."""
        import json
        path = self._get_path(self.index)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def load_from_disk(cls, index: IndexType) -> StrategyConfig:
        """Load configuration from disk or return default if not found."""
        import json
        import os
        path = cls._get_path(index)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                return cls.from_dict(data)
            except Exception:
                pass
        return cls(index=index)
