"""Rolling per-instrument/timeframe OHLC buffer.

Assigns each bar a strictly increasing index (required by the swing
detection / structure pipeline, which reasons about bar order) and
de-duplicates by timestamp so re-fetching overlapping history doesn't
double-count bars.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime

from scanner.structure.models import Bar


class BarStore:
    def __init__(self, max_bars: int = 2000) -> None:
        self._max_bars = max_bars
        self._buffers: dict[tuple[str, str], deque[Bar]] = {}
        self._seen_timestamps: dict[tuple[str, str], set[datetime]] = {}
        self._next_index: dict[tuple[str, str], int] = {}

    def add(
        self,
        instrument: str,
        timeframe: str,
        timestamp: datetime,
        open_: float,
        high: float,
        low: float,
        close: float,
    ) -> Bar | None:
        key = (instrument, timeframe)
        seen = self._seen_timestamps.setdefault(key, set())
        if timestamp in seen:
            return None
        seen.add(timestamp)

        idx = self._next_index.get(key, 0)
        bar = Bar(index=idx, timestamp=timestamp, open=open_, high=high, low=low, close=close)
        self._next_index[key] = idx + 1

        buf = self._buffers.setdefault(key, deque(maxlen=self._max_bars))
        buf.append(bar)
        return bar

    def bars(self, instrument: str, timeframe: str) -> list[Bar]:
        return list(self._buffers.get((instrument, timeframe), []))
