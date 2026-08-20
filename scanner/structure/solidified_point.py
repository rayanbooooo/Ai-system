"""STEP 1 core logic: detecting when a swing point becomes "solidified".

Per docs/AZAREL_STRATEGY.md STEP 1:
    "A point is ONLY solidified if structure broke in BOTH directions
    (swept a low then broke above a high, or swept a high then broke
    below a low)."

Interpretation implemented here (documented in docs/OPEN_QUESTIONS.md as a
calibration target, not an assumed-correct final answer):

- We track a running "candidate range": the most recent not-yet-broken
  swing high and swing low.
- A "sweep" of the low means some bar's low traded below the candidate
  low's price (liquidity taken). A "sweep" of the high is the mirror.
- A "break" of the high means some bar's *close* trades above the
  candidate high's price (and mirror for the low).
- The candidate high solidifies (becomes a bullish SolidifiedPoint) only
  if a sweep of the candidate low happened *before* the break of the
  candidate high. Symmetrically for the candidate low solidifying bearish.
- Once a point solidifies, the tracker resets its candidates so the next
  swing points define a fresh range - "the first break after a new range
  is a continuation break confirming the target."
"""
from __future__ import annotations

from dataclasses import dataclass

from scanner.structure.models import Bar, Direction, SolidifiedPoint, SwingKind, SwingPoint


@dataclass
class _Candidate:
    point: SwingPoint
    swept: bool = False


class SolidifiedPointTracker:
    """Stateful, single-direction-of-travel tracker for one instrument +
    timeframe. Feed it swing points as they're confirmed and bars as they
    close; it emits SolidifiedPoint events via `update`.
    """

    def __init__(self) -> None:
        self.candidate_high: _Candidate | None = None
        self.candidate_low: _Candidate | None = None

    def observe_swing_point(self, point: SwingPoint) -> None:
        """Register a newly confirmed swing point as the latest candidate
        on its side, provided it's more extreme than the current
        candidate.

        IMPORTANT - call order per bar (enforced by callers, see
        state_machine.py): `observe_bar` for a given bar must be called
        *before* `observe_swing_point` for any swing point newly
        confirmed as of that same bar. Swing points are only confirmed
        `fractal_lookback` bars after they form, so a point that is
        itself part of a sweep (e.g. the exact low of a sweep move) gets
        confirmed a few bars later - if it replaced the candidate before
        that bar's own break check ran, the sweep evidence that candidate
        just earned would be erased before it could be used. Checking
        breaks first, against the *not-yet-updated* candidate, then
        advancing the candidate for future bars, avoids that.
        """
        if point.kind == SwingKind.HIGH:
            if self.candidate_high is None or point.price >= self.candidate_high.point.price:
                self.candidate_high = _Candidate(point=point)
        else:
            if self.candidate_low is None or point.price <= self.candidate_low.point.price:
                self.candidate_low = _Candidate(point=point)

    def observe_bar(self, bar: Bar) -> SolidifiedPoint | None:
        """Feed one closed bar. Returns a SolidifiedPoint if this bar's
        close confirmed one (sweep-then-break, both directions satisfied).
        """
        # Sweeps: does this bar's wick take out the opposing candidate?
        if self.candidate_low is not None and bar.low < self.candidate_low.point.price:
            self.candidate_low.swept = True
        if self.candidate_high is not None and bar.high > self.candidate_high.point.price:
            self.candidate_high.swept = True

        result: SolidifiedPoint | None = None

        if (
            self.candidate_high is not None
            and bar.close > self.candidate_high.point.price
            and self.candidate_low is not None
            and self.candidate_low.swept
        ):
            result = SolidifiedPoint(
                pivot=self.candidate_high.point,
                direction=Direction.BULLISH,
                swept_index=self._swept_index(self.candidate_low.point, bar),
                solidified_index=bar.index,
            )
            self._reset_after_solidify()
        elif (
            self.candidate_low is not None
            and bar.close < self.candidate_low.point.price
            and self.candidate_high is not None
            and self.candidate_high.swept
        ):
            result = SolidifiedPoint(
                pivot=self.candidate_low.point,
                direction=Direction.BEARISH,
                swept_index=self._swept_index(self.candidate_high.point, bar),
                solidified_index=bar.index,
            )
            self._reset_after_solidify()

        return result

    def _reset_after_solidify(self) -> None:
        # The broken point is used up; the surviving/opposite candidate
        # carries forward so the very next swing on the used side can
        # immediately start building the next range.
        self.candidate_high = None
        self.candidate_low = None

    @staticmethod
    def _swept_index(swept_point: SwingPoint, break_bar: Bar) -> int:
        return swept_point.index
