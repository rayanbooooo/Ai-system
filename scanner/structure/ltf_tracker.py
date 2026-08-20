"""STEPS 5-6 (1-minute) state machine for one instrument.

Only does anything once `arm()` is called with the STEP 4 hot zone from
HTFTracker. See docs/AZAREL_STRATEGY.md.

Interpretation note (see docs/OPEN_QUESTIONS.md): the spec names both a
"1m Last Opposite Push" (STEP 5) and a "1m Solidified Point anchor" (STEP 6
stop-loss reference) - here the stop is placed beyond the Last Opposite
Push candle's own extreme, treating it as that anchor. This is the
simplest defensible reading and a first calibration target if live
behavior doesn't match expectations.
"""
from __future__ import annotations

from scanner.structure.models import Bar, Direction, LTFState, PriceZone, SwingPoint


class LTFTracker:
    def __init__(self, instrument: str, min_displacement: float, timeout_bars: int = 60) -> None:
        self.instrument = instrument
        self.min_displacement = min_displacement
        self.timeout_bars = timeout_bars

        self._recent_bars: list[Bar] = []
        self._bars_since_progress = 0
        self._zone: PriceZone | None = None
        self._direction: Direction | None = None

        self.state = LTFState(armed=False)

    def arm(self, zone: PriceZone, direction: Direction) -> None:
        self.state = LTFState(armed=True)
        self._zone = zone
        self._direction = direction
        self._recent_bars = []
        self._bars_since_progress = 0

    def disarm(self) -> None:
        self.state = LTFState(armed=False)
        self._zone = None
        self._direction = None

    def observe_swing_point(self, point: SwingPoint) -> None:
        # Reserved: a future refinement could use fractal 1m swing points
        # for a more precise "1m Solidified Point anchor" stop-loss
        # placement instead of the Last Opposite Push candle's own extreme
        # (see the module docstring and docs/OPEN_QUESTIONS.md). Not
        # currently used - state_machine.py still calls this on every new
        # 1m swing point so that refinement can be added without an
        # interface change.
        return

    def observe_bar(self, bar: Bar) -> None:
        if not self.state.armed:
            return

        self._recent_bars.append(bar)
        if len(self._recent_bars) > 200:
            self._recent_bars.pop(0)

        assert self._zone is not None
        in_zone = (self._zone.low <= bar.high) and (bar.low <= self._zone.high)

        if self.state.displacement_bar is None:
            if not in_zone or not self._is_displacement(bar):
                self._bars_since_progress += 1
                self._check_timeout()
                return

            last_push = self._find_last_opposite_push(bar)
            if last_push is None:
                self._bars_since_progress += 1
                self._check_timeout()
                return

            self.state.displacement_bar = bar
            self.state.last_opposite_push = last_push
            self._bars_since_progress = 0
            return

        # STEP 5 done - now watching for the STEP 6 retest.
        push = self.state.last_opposite_push
        assert push is not None
        touched = (push.low <= bar.high) and (bar.low <= push.high)
        if touched:
            self.state.step = 6
        else:
            self._bars_since_progress += 1
            self._check_timeout()

    def _is_displacement(self, bar: Bar) -> bool:
        if bar.body_size < self.min_displacement:
            return False
        return bar.is_bullish if self._direction == Direction.BULLISH else bar.is_bearish

    def _find_last_opposite_push(self, displacement_bar: Bar) -> Bar | None:
        candidates = [b for b in self._recent_bars if b.index < displacement_bar.index]
        for b in reversed(candidates):
            if self._direction == Direction.BULLISH and b.is_bearish:
                return b
            if self._direction == Direction.BEARISH and b.is_bullish:
                return b
        return None

    def _check_timeout(self) -> None:
        if self._bars_since_progress > self.timeout_bars:
            self.disarm()
