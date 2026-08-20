"""STEPS 1-4 (higher-timeframe) state machine for one instrument.

See docs/AZAREL_STRATEGY.md for the spec this implements, and
docs/OPEN_QUESTIONS.md for the interpretation choices called out below
that still need calibration against real historical examples.
"""
from __future__ import annotations

from scanner.structure.models import (
    Bar,
    Direction,
    ExpansionRange,
    HTFState,
    OrderBlock,
    PriceZone,
    SolidifiedPoint,
    SwingPoint,
)
from scanner.structure.solidified_point import SolidifiedPointTracker

# HTFState.step meanings:
#   0 = idle, watching for STEP 1
#   1 = (transient, immediately advances to 2 - kept for readability)
#   2 = STEP 1 + STEP 2 confirmed, tracking the expansion for STEP 3
#   3 = STEP 3 confirmed (target locked), watching the pullback for STEP 4
#   4 = STEP 4 confirmed (zone armed) - HTF work is done; LTF tracker takes over


class HTFTracker:
    def __init__(
        self,
        instrument: str,
        timeframe_label: str,
        zone_tolerance: float,
        invalidation_buffer: float | None = None,
        timeout_bars: int = 300,
    ) -> None:
        self.instrument = instrument
        self.timeframe_label = timeframe_label
        self.zone_tolerance = zone_tolerance
        self.invalidation_buffer = invalidation_buffer if invalidation_buffer is not None else zone_tolerance
        self.timeout_bars = timeout_bars

        self._range_tracker = SolidifiedPointTracker()
        self._reversal_tracker: SolidifiedPointTracker | None = None
        self._reversal_tracker_start_index = -1
        self._zone_tracker: SolidifiedPointTracker | None = None
        self._zone_tracker_start_index = -1
        self._recent_bars: list[Bar] = []
        self._bars_since_progress = 0

        self.state = HTFState()

    def observe_swing_point(self, point: SwingPoint) -> None:
        self._range_tracker.observe_swing_point(point)
        # A sub-tracker must never absorb a swing point that formed before
        # it existed - e.g. a pre-breakout low that only gets fractal-
        # confirmed on the same bar the breakout fires would otherwise be
        # mistaken for the reversal tracker's own baseline low.
        if self._reversal_tracker is not None and point.index > self._reversal_tracker_start_index:
            self._reversal_tracker.observe_swing_point(point)
        if self._zone_tracker is not None and point.index > self._zone_tracker_start_index:
            self._zone_tracker.observe_swing_point(point)

    def observe_bar(self, bar: Bar) -> None:
        self._recent_bars.append(bar)
        if len(self._recent_bars) > 500:
            self._recent_bars.pop(0)

        if self.state.step == 0:
            self._process_step1_and_2(bar)
        elif self.state.step == 2:
            self._process_step3(bar)
        elif self.state.step == 3:
            self._process_step4(bar)
        # step == 4: nothing left to advance here; the state machine hands
        # off to LTFTracker and will call reset() once a Setup completes
        # (or the zone times out).

        self._check_timeout()

    def reset(self) -> None:
        self.state = HTFState()
        self._range_tracker = SolidifiedPointTracker()
        self._reversal_tracker = None
        self._reversal_tracker_start_index = -1
        self._zone_tracker = None
        self._zone_tracker_start_index = -1
        self._bars_since_progress = 0

    # -- Step 1 + 2 -----------------------------------------------------

    def _process_step1_and_2(self, bar: Bar) -> None:
        sp = self._range_tracker.observe_bar(bar)
        if sp is None:
            return

        self.state.direction = sp.direction
        self.state.expansion = ExpansionRange(
            direction=sp.direction,
            breakout_bar=bar,
            solidified_point=sp,
            running_extreme=bar.high if sp.direction == Direction.BULLISH else bar.low,
        )
        self.state.order_block = self._find_order_block(sp.direction, bar)
        self.state.step = 2
        self._reversal_tracker = SolidifiedPointTracker()
        self._reversal_tracker_start_index = bar.index
        self._bars_since_progress = 0

    def _find_order_block(self, direction: Direction, breakout_bar: Bar) -> OrderBlock:
        candidates = [b for b in self._recent_bars if b.index < breakout_bar.index]
        for b in reversed(candidates):
            if direction == Direction.BULLISH and b.is_bearish:
                return OrderBlock(bar=b, direction=direction, timeframe=self.timeframe_label)
            if direction == Direction.BEARISH and b.is_bullish:
                return OrderBlock(bar=b, direction=direction, timeframe=self.timeframe_label)
        # No clean opposite candle found in the recent window - fall back to
        # the breakout bar itself so downstream logic has a defined zone.
        # Worth investigating if this fires often in practice.
        return OrderBlock(bar=breakout_bar, direction=direction, timeframe=self.timeframe_label)

    # -- Step 3 -----------------------------------------------------------

    def _process_step3(self, bar: Bar) -> None:
        exp = self.state.expansion
        assert exp is not None
        if exp.direction == Direction.BULLISH:
            exp.running_extreme = max(exp.running_extreme, bar.high)
        else:
            exp.running_extreme = min(exp.running_extreme, bar.low)

        assert self._reversal_tracker is not None
        peak_before = self._reversal_tracker.candidate_high.point if self._reversal_tracker.candidate_high else None
        trough_before = self._reversal_tracker.candidate_low.point if self._reversal_tracker.candidate_low else None

        sp = self._reversal_tracker.observe_bar(bar)
        if sp is None:
            self._bars_since_progress += 1
            return

        original_dir = self.state.direction
        target_point = None
        if original_dir == Direction.BULLISH and sp.direction == Direction.BEARISH and peak_before is not None:
            target_point = peak_before
        elif original_dir == Direction.BEARISH and sp.direction == Direction.BULLISH and trough_before is not None:
            target_point = trough_before

        if target_point is None:
            # The reversal tracker solidified a point in the *continuation*
            # direction, not the pullback reversal we need for Step 3 -
            # keep waiting.
            self._bars_since_progress += 1
            return

        self.state.target = SolidifiedPoint(
            pivot=target_point,
            direction=original_dir,
            swept_index=sp.solidified_index,
            solidified_index=bar.index,
        )
        self.state.step = 3
        self._zone_tracker = SolidifiedPointTracker()
        self._zone_tracker_start_index = bar.index
        self._bars_since_progress = 0

    # -- Step 4 -----------------------------------------------------------

    def _process_step4(self, bar: Bar) -> None:
        ob = self.state.order_block
        direction = self.state.direction
        assert ob is not None and direction is not None
        zone_low = ob.low - self.zone_tolerance
        zone_high = ob.high + self.zone_tolerance

        if direction == Direction.BULLISH and bar.close < zone_low - self.invalidation_buffer:
            self.reset()
            return
        if direction == Direction.BEARISH and bar.close > zone_high + self.invalidation_buffer:
            self.reset()
            return

        assert self._zone_tracker is not None
        sp = self._zone_tracker.observe_bar(bar)
        if sp is None:
            self._bars_since_progress += 1
            return

        in_zone = zone_low <= sp.pivot.price <= zone_high or (zone_low <= bar.close <= zone_high)
        if sp.direction != direction or not in_zone:
            self._bars_since_progress += 1
            return

        self.state.zone = PriceZone(
            order_block=ob,
            confirmed_at_index=bar.index,
            third_solidified_point=sp,
            low=zone_low,
            high=zone_high,
        )
        self.state.step = 4
        self._bars_since_progress = 0

    def _check_timeout(self) -> None:
        if self.state.step in (2, 3) and self._bars_since_progress > self.timeout_bars:
            self.reset()
