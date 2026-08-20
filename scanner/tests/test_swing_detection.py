from datetime import datetime, timedelta

from scanner.structure.models import Bar, SwingKind
from scanner.structure.swing_detection import find_swing_points


def _bar(i: int, o: float, h: float, l: float, c: float) -> Bar:
    return Bar(index=i, timestamp=datetime(2026, 1, 1) + timedelta(minutes=i), open=o, high=h, low=l, close=c)


def test_confirms_a_clean_swing_high():
    highs = [10, 11, 12, 20, 12, 11, 10]
    bars = [_bar(i, h - 1, h, h - 2, h - 1) for i, h in enumerate(highs)]
    points = find_swing_points(bars, lookback=3)
    swing_highs = [p for p in points if p.kind == SwingKind.HIGH]
    assert len(swing_highs) == 1
    assert swing_highs[0].index == 3
    assert swing_highs[0].price == 20


def test_confirms_a_clean_swing_low():
    lows = [10, 9, 8, 1, 8, 9, 10]
    bars = [_bar(i, l + 1, l + 2, l, l + 1) for i, l in enumerate(lows)]
    points = find_swing_points(bars, lookback=3)
    swing_lows = [p for p in points if p.kind == SwingKind.LOW]
    assert len(swing_lows) == 1
    assert swing_lows[0].index == 3
    assert swing_lows[0].price == 1


def test_insufficient_bars_returns_nothing():
    bars = [_bar(0, 1, 2, 0, 1), _bar(1, 1, 2, 0, 1)]
    assert find_swing_points(bars, lookback=3) == []


def test_monotonic_run_has_no_swing_points():
    # A steadily rising sequence has no local extreme in the middle.
    bars = [_bar(i, i, i + 1, i - 1, i) for i in range(10)]
    assert find_swing_points(bars, lookback=2) == []
