"""Entrypoint for the AZAREL scanner.

Usage:
    python -m scanner.main --replay-htf htf.csv --replay-ltf ltf.csv --instrument MNQ
    python -m scanner.main --check-connection
    python -m scanner.main --test-telegram

Live mode (continuous Tradovate streaming -> Telegram + vault) is
intentionally not wired up in this scaffold - see docs/OPEN_QUESTIONS.md.
Confirm Tradovate API access and calibrate against --replay first.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import logging
import sys
from datetime import datetime

from scanner.alerts.formatter import format_setup_message
from scanner.alerts.telegram_client import TelegramClient
from scanner.annotator.noop_annotator import NoopAnnotator
from scanner.config import Settings, load_settings
from scanner.data.bar_store import BarStore
from scanner.data.tradovate_client import TradovateClient
from scanner.logging.vault_writer import write_signal_note
from scanner.structure.state_machine import InstrumentStateMachine

logger = logging.getLogger(__name__)


def build_state_machine(instrument_key: str, settings: Settings, on_setup) -> InstrumentStateMachine:
    inst = settings.instruments[instrument_key]
    return InstrumentStateMachine(
        instrument=instrument_key,
        htf_timeframe_label=inst.htf_timeframes[-1] if inst.htf_timeframes else "15m",
        fractal_lookback=inst.fractal_lookback,
        zone_tolerance=inst.zone_tolerance,
        min_displacement=inst.min_displacement,
        stop_buffer=inst.stop_buffer,
        timeout_bars_htf=inst.timeout_bars_htf,
        timeout_bars_ltf=inst.timeout_bars_ltf,
        on_setup=on_setup,
    )


def _load_csv_bars(path: str) -> list[tuple[datetime, float, float, float, float]]:
    rows: list[tuple[datetime, float, float, float, float]] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                (
                    datetime.fromisoformat(row["timestamp"]),
                    float(row["open"]),
                    float(row["high"]),
                    float(row["low"]),
                    float(row["close"]),
                )
            )
    rows.sort(key=lambda r: r[0])
    return rows


def run_replay(htf_csv: str, ltf_csv: str, instrument_key: str, settings: Settings) -> int:
    """Feed HTF and LTF CSVs (columns: timestamp,open,high,low,close),
    interleaved by timestamp, through the state machine and print any
    Setups found. Use this to eyeball the scanner against historical
    examples before ever trusting a live alert - see
    docs/OPEN_QUESTIONS.md.
    """
    store = BarStore()
    setups = []

    def on_setup(setup):
        setups.append(setup)
        print(f"\n=== SETUP FOUND ===\n{format_setup_message(setup, vault_link='(replay - not written)')}\n")

    sm = build_state_machine(instrument_key, settings, on_setup)
    inst = settings.instruments[instrument_key]
    htf_tf = inst.htf_timeframes[-1] if inst.htf_timeframes else "15m"
    ltf_tf = inst.ltf_timeframes[0] if inst.ltf_timeframes else "1m"

    htf_rows = [(ts, "htf", o, h, l, c) for ts, o, h, l, c in _load_csv_bars(htf_csv)]
    ltf_rows = [(ts, "ltf", o, h, l, c) for ts, o, h, l, c in _load_csv_bars(ltf_csv)]
    merged = sorted(htf_rows + ltf_rows, key=lambda r: r[0])

    for ts, kind, o, h, l, c in merged:
        tf = htf_tf if kind == "htf" else ltf_tf
        bar = store.add(instrument_key, tf, ts, o, h, l, c)
        if bar is None:
            continue
        if kind == "htf":
            sm.feed_htf_bar(bar)
        else:
            sm.feed_ltf_bar(bar)

    print(f"\nReplay complete: {len(setups)} setup(s) found.")
    return 0


def check_connection(settings: Settings) -> int:
    client = TradovateClient(settings)
    client.authenticate()
    print("Tradovate authentication succeeded.")
    sample_key = next(iter(settings.instruments))
    sample = settings.instruments[sample_key]
    bars = client.fetch_history_bars(sample.tradovate_symbol, "1h", bars_back=5)
    print(f"Fetched {len(bars)} sample bars for {sample.tradovate_symbol}.")
    return 0


def test_telegram(settings: Settings) -> int:
    client = TelegramClient(settings.telegram)
    client.send_message(
        "AI-system scanner: test alert. If you see this, Telegram alerting is wired up correctly."
    )
    print("Test Telegram message sent.")
    return 0


async def _run_live_async(settings: Settings, instrument_keys: list[str]) -> None:
    client = TradovateClient(settings)
    telegram = TelegramClient(settings.telegram)
    annotator = NoopAnnotator()
    store = BarStore()
    machines: dict[str, InstrumentStateMachine] = {}

    def make_on_setup(key: str):
        def on_setup(setup) -> None:
            accounts_notified = [
                a["account_id"]
                for a in settings.accounts
                if key in a.get("instruments", []) and a.get("status") == "active"
            ]
            message = format_setup_message(setup)
            try:
                telegram.send_message(message)
            except Exception:
                logger.exception("Failed to send Telegram alert for %s", key)
            try:
                path = write_signal_note(settings.vault_path, setup, accounts_notified)
                logger.info("Wrote signal note: %s", path)
            except Exception:
                logger.exception("Failed to write vault signal note for %s", key)
            annotator.draw_setup(setup)

        return on_setup

    for key in instrument_keys:
        machines[key] = build_state_machine(key, settings, make_on_setup(key))

    async def watch(key: str, timeframe: str, kind: str) -> None:
        inst = settings.instruments[key]
        sm = machines[key]

        def handle(bar) -> None:
            stored = store.add(key, timeframe, bar.timestamp, bar.open, bar.high, bar.low, bar.close)
            if stored is None:
                return
            if kind == "htf":
                sm.feed_htf_bar(stored)
            else:
                sm.feed_ltf_bar(stored)

        # Warm up structure detection with recent history before switching
        # to the live stream, so Step 1+ has bars to work with immediately.
        for bar in client.fetch_history_bars(inst.tradovate_symbol, timeframe, bars_back=200):
            handle(bar)

        await client.stream_live_bars(inst.tradovate_symbol, timeframe, handle)

    tasks = []
    for key in instrument_keys:
        inst = settings.instruments[key]
        htf_tf = inst.htf_timeframes[-1] if inst.htf_timeframes else "15m"
        ltf_tf = inst.ltf_timeframes[0] if inst.ltf_timeframes else "1m"
        tasks.append(watch(key, htf_tf, "htf"))
        tasks.append(watch(key, ltf_tf, "ltf"))

    await asyncio.gather(*tasks)


def run_live(settings: Settings, instrument_keys: list[str]) -> int:
    print(
        "Starting live scanning. This has NOT been validated against a real "
        "Tradovate connection yet - watch the console closely on first run, "
        "and complete the calibration/shadow-period steps in "
        "docs/OPEN_QUESTIONS.md before trusting any alert.",
        file=sys.stderr,
    )
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run_live_async(settings, instrument_keys))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AZAREL structure scanner")
    parser.add_argument("--replay-htf", metavar="CSV_PATH", help="HTF (15m/1h) bar CSV for replay mode")
    parser.add_argument("--replay-ltf", metavar="CSV_PATH", help="LTF (1m) bar CSV for replay mode")
    parser.add_argument("--instrument", default="MNQ", help="Instrument key from config/instruments.yaml")
    parser.add_argument("--check-connection", action="store_true", help="Test Tradovate auth + a sample bar fetch")
    parser.add_argument("--test-telegram", action="store_true", help="Send a test Telegram message")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run continuously against live Tradovate data for all configured instruments (unvalidated - see docs/OPEN_QUESTIONS.md)",
    )
    args = parser.parse_args(argv)

    settings = load_settings()

    if args.check_connection:
        return check_connection(settings)
    if args.test_telegram:
        return test_telegram(settings)
    if args.replay_htf or args.replay_ltf:
        if not (args.replay_htf and args.replay_ltf):
            parser.error("--replay-htf and --replay-ltf must be used together")
        return run_replay(args.replay_htf, args.replay_ltf, args.instrument, settings)
    if args.live:
        return run_live(settings, list(settings.instruments.keys()))

    print(
        "No mode selected. Use --replay-htf/--replay-ltf to backtest, "
        "--check-connection or --test-telegram to verify credentials, or "
        "--live to run continuously (see docs/OPEN_QUESTIONS.md first).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
