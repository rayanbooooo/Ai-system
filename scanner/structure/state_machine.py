"""Per-instrument orchestration: feeds HTF bars into HTFTracker, arms
LTFTracker once STEP 4 confirms, and assembles a Setup once STEP 6 fires.
"""
from __future__ import annotations

from typing import Callable

from scanner.structure.htf_tracker import HTFTracker
from scanner.structure.ltf_tracker import LTFTracker
from scanner.structure.models import Bar, Direction, Setup
from scanner.structure.swing_detection import find_new_swing_points

OnSetup = Callable[[Setup], None]


class InstrumentStateMachine:
    def __init__(
        self,
        instrument: str,
        htf_timeframe_label: str,
        fractal_lookback: int,
        zone_tolerance: float,
        min_displacement: float,
        stop_buffer: float,
        timeout_bars_htf: int = 300,
        timeout_bars_ltf: int = 60,
        on_setup: OnSetup | None = None,
    ) -> None:
        self.instrument = instrument
        self.fractal_lookback = fractal_lookback
        self.stop_buffer = stop_buffer
        self.on_setup = on_setup

        self.htf_tracker = HTFTracker(
            instrument=instrument,
            timeframe_label=htf_timeframe_label,
            zone_tolerance=zone_tolerance,
            timeout_bars=timeout_bars_htf,
        )
        self.ltf_tracker = LTFTracker(
            instrument=instrument,
            min_displacement=min_displacement,
            timeout_bars=timeout_bars_ltf,
        )

        self._htf_bars: list[Bar] = []
        self._ltf_bars: list[Bar] = []
        self._htf_confirmed_through = -1
        self._ltf_confirmed_through = -1

    def feed_htf_bar(self, bar: Bar) -> None:
        self._htf_bars.append(bar)

        # Order matters: check this bar's sweeps/breaks against the
        # candidates as they stood *before* this bar, then advance the
        # candidates to any swing point this same bar just confirmed. See
        # the docstring on SolidifiedPointTracker.observe_swing_point.
        self.htf_tracker.observe_bar(bar)

        new_points = find_new_swing_points(self._htf_bars, self.fractal_lookback, self._htf_confirmed_through)
        for point in new_points:
            self.htf_tracker.observe_swing_point(point)
            self._htf_confirmed_through = max(self._htf_confirmed_through, point.index)

        if self.htf_tracker.state.step == 4 and not self.ltf_tracker.state.armed:
            zone = self.htf_tracker.state.zone
            direction = self.htf_tracker.state.direction
            assert zone is not None and direction is not None
            self.ltf_tracker.arm(zone, direction)

    def feed_ltf_bar(self, bar: Bar) -> Setup | None:
        self._ltf_bars.append(bar)
        self.ltf_tracker.observe_bar(bar)

        new_points = find_new_swing_points(self._ltf_bars, self.fractal_lookback, self._ltf_confirmed_through)
        for point in new_points:
            self.ltf_tracker.observe_swing_point(point)
            self._ltf_confirmed_through = max(self._ltf_confirmed_through, point.index)

        if self.ltf_tracker.state.step != 6:
            return None

        setup = self._build_setup(bar)
        self.ltf_tracker.disarm()
        self.htf_tracker.reset()
        if self.on_setup is not None:
            self.on_setup(setup)
        return setup

    def _build_setup(self, trigger_bar: Bar) -> Setup:
        htf_state = self.htf_tracker.state
        ltf_state = self.ltf_tracker.state
        push = ltf_state.last_opposite_push
        direction = htf_state.direction
        assert push is not None and direction is not None
        assert htf_state.expansion is not None
        assert htf_state.order_block is not None
        assert htf_state.target is not None
        assert htf_state.zone is not None
        assert ltf_state.displacement_bar is not None

        if direction == Direction.BULLISH:
            entry = push.high
            stop_loss = push.low - self.stop_buffer
        else:
            entry = push.low
            stop_loss = push.high + self.stop_buffer

        take_profit = htf_state.target.pivot.price

        return Setup(
            instrument=self.instrument,
            direction=direction,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            triggered_at=trigger_bar.timestamp,
            step1_htf_timeframe=self.htf_tracker.timeframe_label,
            step1_solidified_point=htf_state.expansion.solidified_point,
            step2_order_block=htf_state.order_block,
            step3_target=htf_state.target,
            step4_zone=htf_state.zone,
            step5_displacement_bar=ltf_state.displacement_bar,
            step5_last_opposite_push=push,
        )
