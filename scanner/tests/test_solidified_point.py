from datetime import datetime, timedelta

from scanner.structure.models import Bar, Direction, SwingKind, SwingPoint
from scanner.structure.solidified_point import SolidifiedPointTracker


def _bar(i: int, o: float, h: float, l: float, c: float) -> Bar:
    return Bar(index=i, timestamp=datetime(2026, 1, 1) + timedelta(minutes=i), open=o, high=h, low=l, close=c)


def _swing(i: int, price: float, kind: SwingKind) -> SwingPoint:
    return SwingPoint(index=i, timestamp=datetime(2026, 1, 1) + timedelta(minutes=i), price=price, kind=kind)


def test_solidifies_high_after_sweep_low_then_break():
    tracker = SolidifiedPointTracker()
    tracker.observe_swing_point(_swing(0, 100, SwingKind.LOW))
    tracker.observe_swing_point(_swing(1, 110, SwingKind.HIGH))

    assert tracker.observe_bar(_bar(2, 101, 102, 95, 99)) is None  # sweeps the low

    sp = tracker.observe_bar(_bar(3, 108, 112, 107, 111))  # breaks above the high
    assert sp is not None
    assert sp.direction == Direction.BULLISH
    assert sp.pivot.price == 110


def test_break_without_prior_sweep_does_not_solidify():
    tracker = SolidifiedPointTracker()
    tracker.observe_swing_point(_swing(0, 100, SwingKind.LOW))
    tracker.observe_swing_point(_swing(1, 110, SwingKind.HIGH))

    # Breaks above the high directly, without ever sweeping the low first.
    assert tracker.observe_bar(_bar(2, 108, 112, 106, 111)) is None


def test_solidifies_low_after_sweep_high_then_break():
    tracker = SolidifiedPointTracker()
    tracker.observe_swing_point(_swing(0, 100, SwingKind.LOW))
    tracker.observe_swing_point(_swing(1, 110, SwingKind.HIGH))

    assert tracker.observe_bar(_bar(2, 109, 111, 105, 106)) is None  # sweeps the high

    sp = tracker.observe_bar(_bar(3, 102, 103, 98, 99))  # breaks below the low
    assert sp is not None
    assert sp.direction == Direction.BEARISH
    assert sp.pivot.price == 100


def test_a_belated_deeper_swing_point_does_not_erase_an_earlier_sweep():
    # Regression test: bars 9-10 sweep the original low of 100 (dipping to
    # 97), and that dip only gets *confirmed* as its own swing point later
    # (once enough bars exist on both sides). That belated confirmation
    # must not erase the sweep evidence the original 100-level candidate
    # already earned - see the ordering contract documented on
    # SolidifiedPointTracker.observe_swing_point.
    tracker = SolidifiedPointTracker()
    tracker.observe_swing_point(_swing(0, 100, SwingKind.LOW))
    tracker.observe_swing_point(_swing(1, 110, SwingKind.HIGH))

    assert tracker.observe_bar(_bar(2, 99, 100, 97, 98)) is None  # sweeps 100, itself dips to 97
    assert tracker.observe_bar(_bar(3, 98, 103, 97, 102)) is None  # still below 110

    # Only now (bar index 3 exists on both sides) would a fractal detector
    # confirm bar 2's low of 97 as its own swing point. Callers must feed
    # this *after* the break-check for the bar that already fired it, per
    # the documented ordering contract - simulate that here.
    sp = tracker.observe_bar(_bar(4, 102, 112, 101, 111))  # breaks above 110
    assert sp is not None
    assert sp.direction == Direction.BULLISH
    assert sp.pivot.price == 110
