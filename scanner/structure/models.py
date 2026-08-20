"""Data structures shared across the structure-detection pipeline.

Every shape here corresponds directly to a concept in
`docs/AZAREL_STRATEGY.md` (the 6-step checklist) - keep the two in sync.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SwingKind(str, Enum):
    HIGH = "high"
    LOW = "low"


class Direction(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"

    @property
    def opposite(self) -> "Direction":
        return Direction.BEARISH if self is Direction.BULLISH else Direction.BULLISH


@dataclass(frozen=True)
class Bar:
    """One OHLC candle for a given instrument/timeframe."""

    index: int
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        return self.close < self.open

    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)


@dataclass(frozen=True)
class SwingPoint:
    """A fractal swing high/low, confirmed `lookback` bars after it forms."""

    index: int
    timestamp: datetime
    price: float
    kind: SwingKind


@dataclass
class SolidifiedPoint:
    """A swing point confirmed per the AZAREL rule: structure broke in BOTH
    directions relative to it (the opposite extreme was swept, then this
    side was broken). See STEP 1 in docs/AZAREL_STRATEGY.md.
    """

    pivot: SwingPoint
    direction: Direction  # BULLISH = this was a solidified HIGH broken upward
    swept_index: int  # bar index where the opposite extreme was swept
    solidified_index: int  # bar index where the break confirmed this point
    status: str = "active"  # active | target_hit | invalidated


@dataclass(frozen=True)
class OrderBlock:
    """STEP 2: the last opposite candle/wick before the breakout impulse."""

    bar: Bar
    direction: Direction  # direction of the breakout this OB precedes
    timeframe: str

    @property
    def low(self) -> float:
        return self.bar.low

    @property
    def high(self) -> float:
        return self.bar.high


@dataclass
class ExpansionRange:
    """STEP 1 output: the breakout leg and the new range it opened."""

    direction: Direction
    breakout_bar: Bar
    solidified_point: SolidifiedPoint
    running_extreme: float  # highest high (bullish) / lowest low (bearish) since breakout


@dataclass
class PriceZone:
    """STEP 4: the Step-2 order block zone, confirmed by a 3rd solidified
    point shift inside it.
    """

    order_block: OrderBlock
    confirmed_at_index: int
    third_solidified_point: SolidifiedPoint
    low: float
    high: float


@dataclass
class Setup:
    """A completed STEP 6 signal - the thing that gets sent to Telegram and
    logged to the vault.
    """

    instrument: str
    direction: Direction
    entry: float
    stop_loss: float
    take_profit: float
    triggered_at: datetime
    step1_htf_timeframe: str
    step1_solidified_point: SolidifiedPoint
    step2_order_block: OrderBlock
    step3_target: SolidifiedPoint
    step4_zone: PriceZone
    step5_displacement_bar: Bar
    step5_last_opposite_push: Bar

    @property
    def risk_reward(self) -> float:
        risk = abs(self.entry - self.stop_loss)
        reward = abs(self.take_profit - self.entry)
        return reward / risk if risk else 0.0


@dataclass
class HTFState:
    """Steps 1-4 state for one instrument."""

    step: int = 0  # 0 = idle/watching, 1..4 = furthest confirmed step
    direction: Direction | None = None
    expansion: ExpansionRange | None = None
    order_block: OrderBlock | None = None
    target: SolidifiedPoint | None = None
    zone: PriceZone | None = None


@dataclass
class LTFState:
    """Steps 5-6 state for one instrument, only active once HTF reaches
    step 4.
    """

    armed: bool = False
    step: int = 4  # mirrors HTF step until 5/6 progress
    displacement_bar: Bar | None = None
    last_opposite_push: Bar | None = None
    local_solidified_point: SolidifiedPoint | None = None


@dataclass
class InstrumentState:
    instrument: str
    htf: HTFState = field(default_factory=HTFState)
    ltf: LTFState = field(default_factory=LTFState)
