"""Fractal swing high/low detection.

A bar at index i is a confirmed swing high if its high is the maximum
within the window [i-lookback, i+lookback], and a swing low if its low is
the minimum within that window. Because a swing point needs bars *after*
it to be confirmed, a point at index i is only knowable once bar
i+lookback has arrived - this is why callers process bars in order and
call `find_new_swing_points` incrementally (see state_machine.py).
"""
from __future__ import annotations

from scanner.structure.models import Bar, SwingKind, SwingPoint


def find_swing_points(bars: list[Bar], lookback: int) -> list[SwingPoint]:
    """Return every confirmed swing point in `bars`.

    `lookback` bars on each side are required to confirm a pivot, so the
    first and last `lookback` bars can never produce a swing point.
    """
    points: list[SwingPoint] = []
    n = len(bars)
    if lookback < 1 or n < (2 * lookback + 1):
        return points

    for i in range(lookback, n - lookback):
        center = bars[i]
        window = bars[i - lookback : i + lookback + 1]

        if _is_unique_extreme(window, lookback, lambda b: b.high, center.high, high=True):
            points.append(
                SwingPoint(index=center.index, timestamp=center.timestamp, price=center.high, kind=SwingKind.HIGH)
            )

        if _is_unique_extreme(window, lookback, lambda b: b.low, center.low, high=False):
            points.append(
                SwingPoint(index=center.index, timestamp=center.timestamp, price=center.low, kind=SwingKind.LOW)
            )

    return points


def find_new_swing_points(bars: list[Bar], lookback: int, already_confirmed_through: int) -> list[SwingPoint]:
    """Incremental variant: only returns swing points centered after
    `already_confirmed_through` (a bar index), so callers don't need to
    re-scan the whole history on every new bar.
    """
    all_points = find_swing_points(bars, lookback)
    return [p for p in all_points if p.index > already_confirmed_through]


def _is_unique_extreme(window: list[Bar], lookback: int, key, center_value: float, high: bool) -> bool:
    center_pos = lookback
    values = [key(b) for b in window]
    extreme = max(values) if high else min(values)
    if center_value != extreme:
        return False
    # Require the center to be the *first* bar achieving the extreme within
    # the window, so flat tops/bottoms resolve to a single, earliest pivot
    # rather than firing once per matching bar.
    return values.index(extreme) == center_pos
