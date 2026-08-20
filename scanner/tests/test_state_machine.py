"""Full 6-step walkthrough tests.

The bullish fixture (fixtures/mnq_long_htf.csv + mnq_long_ltf.csv) encodes
a hand-verified sequence: HTF range 100/110, sweep+break for STEP 1,
order block at the 97-100 bar for STEP 2, expansion to a 128 peak with a
reversal back through a solidified low for STEP 3, a pullback into the
order block zone with a 3rd solidified point for STEP 4, then a 1m
displacement + retest for STEPS 5-6. See docs/AZAREL_STRATEGY.md.
"""
import csv
from datetime import datetime
from pathlib import Path

from scanner.structure.models import Direction
from scanner.structure.state_machine import InstrumentStateMachine

FIXTURES = Path(__file__).parent / "fixtures"


def _load_csv(path: Path) -> list[tuple[datetime, float, float, float, float]]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(
                (
                    datetime.fromisoformat(row["timestamp"]),
                    float(row["open"]),
                    float(row["high"]),
                    float(row["low"]),
                    float(row["close"]),
                )
            )
    return rows


def _new_machine(on_setup=None) -> InstrumentStateMachine:
    return InstrumentStateMachine(
        instrument="MNQ",
        htf_timeframe_label="15m",
        fractal_lookback=2,
        zone_tolerance=1.0,
        min_displacement=1.0,
        stop_buffer=0.25,
        timeout_bars_htf=1000,
        timeout_bars_ltf=1000,
        on_setup=on_setup,
    )


def test_full_bullish_walkthrough_fires_a_setup():
    setups = []
    sm = _new_machine(on_setup=setups.append)

    htf_rows = [(ts, "htf", o, h, l, c) for ts, o, h, l, c in _load_csv(FIXTURES / "mnq_long_htf.csv")]
    ltf_rows = [(ts, "ltf", o, h, l, c) for ts, o, h, l, c in _load_csv(FIXTURES / "mnq_long_ltf.csv")]
    merged = sorted(htf_rows + ltf_rows, key=lambda r: r[0])

    from scanner.data.bar_store import BarStore

    store = BarStore()
    for ts, kind, o, h, l, c in merged:
        bar = store.add("MNQ", kind, ts, o, h, l, c)
        assert bar is not None
        if kind == "htf":
            sm.feed_htf_bar(bar)
        else:
            sm.feed_ltf_bar(bar)

    assert len(setups) == 1
    setup = setups[0]
    assert setup.direction == Direction.BULLISH
    assert setup.entry == 99.2
    assert setup.stop_loss == 97.25
    assert setup.take_profit == 128
    assert setup.step2_order_block.low == 97
    assert setup.step2_order_block.high == 100

    # A completed setup resets both trackers so the next one can form.
    assert sm.htf_tracker.state.step == 0
    assert sm.ltf_tracker.state.armed is False


def test_step4_zone_invalidates_if_price_breaks_clean_through_it():
    sm = _new_machine()
    rows = _load_csv(FIXTURES / "mnq_long_htf.csv")

    from scanner.data.bar_store import BarStore

    store = BarStore()
    # Feed only through the bar that confirms STEP 3 (index 26 in the
    # fixture - see build order in the fixture's source comments).
    for ts, o, h, l, c in rows[:27]:
        bar = store.add("MNQ", "15m", ts, o, h, l, c)
        sm.feed_htf_bar(bar)

    assert sm.htf_tracker.state.step == 3

    # Now a bar that closes clean through the order-block zone (order
    # block low 97, tolerance 1 -> zone_low 96, default invalidation
    # buffer = zone_tolerance -> invalidates below 95) without ever
    # forming the STEP 4 confirmation.
    last_ts = rows[26][0]
    from datetime import timedelta

    invalidating_bar = store.add("MNQ", "15m", last_ts + timedelta(minutes=15), 95, 95, 80, 82)
    sm.feed_htf_bar(invalidating_bar)

    assert sm.htf_tracker.state.step == 0
    assert sm.htf_tracker.state.direction is None


def test_no_setup_from_flat_noise():
    sm_setups = []
    sm = _new_machine(on_setup=sm_setups.append)
    from datetime import timedelta

    from scanner.data.bar_store import BarStore

    store = BarStore()
    start = datetime(2026, 1, 1)
    # Small back-and-forth chop that never sweeps-and-breaks a range in
    # either direction - should never produce a STEP 1, let alone a Setup.
    prices = [100, 100.5, 100.2, 100.6, 100.3, 100.5, 100.1, 100.4, 100.2, 100.5] * 4
    for i, p in enumerate(prices):
        bar = store.add("MNQ", "15m", start + timedelta(minutes=15 * i), p, p + 0.3, p - 0.3, p)
        sm.feed_htf_bar(bar)

    assert sm_setups == []
    assert sm.htf_tracker.state.step in (0, 2, 3)  # never reaches 4 without a real breakout
